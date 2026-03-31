"""
LLM 调用服务 — 智谱 GLM 系列
支持 429 限频自动重试 + 指数退避 + 完整错误处理
"""
from __future__ import annotations

import asyncio
import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any, Optional

import openai
from openai import AsyncOpenAI, APIError, APITimeoutError, RateLimitError, APIConnectionError

from src.utils.logger import setup_logger
from src.models.schemas import ChatMessage, LLMRequest, LLMResponse

logger = setup_logger("llm_service")

# ──────────────────────────────────────────────
# 智谱 GLM 模型支持的工具/函数调用 schema
# ──────────────────────────────────────────────


class ToolFunction:
    """工具函数描述"""

    def __init__(self, name: str, description: str, parameters: dict[str, Any] | None = None):
        self.name = name
        self.description = description
        self.parameters = parameters or {
            "type": "object",
            "properties": {},
            "required": [],
        }

    def to_openai_tool(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


# ──────────────────────────────────────────────
# 重试工具
# ──────────────────────────────────────────────


async def _retry_with_backoff(
    coro_factory,       # callable that returns a new coroutine each time
    max_retries: int = 3,
    base_delay: float = 3.0,
    max_delay: float = 60.0,
) -> Any:
    """
    对 LLM 调用做指数退避重试，处理可重试的错误。

    可重试错误:
    - RateLimitError (429): 限频
    - APITimeoutError: 超时
    - APIConnectionError: 连接问题
    - APIError (5xx): 服务器错误

    不可重试错误直接抛出:
    - 认证错误 (401)
    - 权限错误 (403)
    - 无效请求 (400)
    """
    last_error = None

    for attempt in range(max_retries + 1):
        try:
            return await coro_factory()

        except RateLimitError as e:
            last_error = e
            if attempt >= max_retries:
                logger.error(f"LLM 429: 重试 {max_retries} 次仍失败")
                raise

            delay = min(base_delay * (2 ** attempt), max_delay)
            logger.warning(f"LLM 429 限频，第 {attempt + 1}/{max_retries} 次重试，等待 {delay:.1f}s")
            await asyncio.sleep(delay)

        except (APITimeoutError, asyncio.TimeoutError) as e:
            last_error = e
            if attempt >= max_retries:
                logger.error(f"LLM 超时: 重试 {max_retries} 次仍失败")
                raise

            delay = min(base_delay * (2 ** attempt), max_delay)
            logger.warning(f"LLM 超时，第 {attempt + 1}/{max_retries} 次重试，等待 {delay:.1f}s")
            await asyncio.sleep(delay)

        except APIConnectionError as e:
            last_error = e
            if attempt >= max_retries:
                logger.error(f"LLM 连接失败: 重试 {max_retries} 次仍失败")
                raise

            delay = min(base_delay * (2 ** attempt), max_delay)
            logger.warning(f"LLM 连接问题，第 {attempt + 1}/{max_retries} 次重试，等待 {delay:.1f}s")
            await asyncio.sleep(delay)

        except APIError as e:
            # 只对 5xx 服务器错误重试
            if hasattr(e, 'status_code') and 500 <= e.status_code < 600:
                last_error = e
                if attempt >= max_retries:
                    logger.error(f"LLM 服务器错误: 重试 {max_retries} 次仍失败")
                    raise

                delay = min(base_delay * (2 ** attempt), max_delay)
                logger.warning(f"LLM 服务器错误 {e.status_code}，第 {attempt + 1}/{max_retries} 次重试")
                await asyncio.sleep(delay)
            else:
                # 4xx 错误直接抛出
                logger.error(f"LLM 客户端错误: {e}")
                raise

        except Exception as e:
            # 未预期的错误直接抛出
            logger.error(f"LLM 调用未预期错误: {type(e).__name__}: {e}")
            raise

    # 理论上不会到达这里，但为了类型安全
    if last_error:
        raise last_error


# ──────────────────────────────────────────────
# LLM Service
# ──────────────────────────────────────────────


class LLMService:
    """
    智谱 LLM 调用封装（OpenAI SDK 兼容，内置 429 重试）

    使用方式:
        service = LLMService(api_key="...")
        async with service:
            response = await service.chat(request)
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://open.bigmodel.cn/api/paas/v4/",
        default_model: str = "glm-5-turbo",
        max_retries: int = 3,
        base_delay: float = 3.0,
        max_delay: float = 60.0,
        timeout: float = 120.0,
    ):
        self._api_key = api_key
        self._base_url = base_url
        self.default_model = default_model
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self._timeout = timeout
        self._client: Optional[AsyncOpenAI] = None

    async def __aenter__(self):
        """异步上下文管理器入口"""
        self._client = AsyncOpenAI(
            api_key=self._api_key,
            base_url=self._base_url,
            timeout=self._timeout,
            max_retries=0,  # 我们自己实现重试
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        if self._client:
            await self._client.close()
            self._client = None
        return False

    @property
    def client(self) -> AsyncOpenAI:
        """获取客户端（延迟初始化）"""
        if self._client is None:
            self._client = AsyncOpenAI(
                api_key=self._api_key,
                base_url=self._base_url,
                timeout=self._timeout,
                max_retries=0,
            )
        return self._client

    async def close(self):
        """显式关闭客户端"""
        if self._client:
            await self._client.close()
            self._client = None

    # ── 核心调用 ──────────────────────────────

    async def chat(self, request: LLMRequest) -> LLMResponse:
        """
        发送聊天请求（非流式），自动重试

        Args:
            request: LLM 请求对象

        Returns:
            LLMResponse: 响应对象

        Raises:
            RateLimitError: 限频错误（重试失败）
            APITimeoutError: 超时错误（重试失败）
            APIConnectionError: 连接错误（重试失败）
            APIError: API 错误（5xx 重试失败，4xx 直接抛出）
        """
        start = time.perf_counter()
        logger.debug(
            f"LLM request: model={request.model}, "
            f"messages={len(request.messages)}, "
            f"tools={len(request.tools) if request.tools else 0}"
        )

        kwargs = self._build_kwargs(request)

        response = await _retry_with_backoff(
            coro_factory=lambda: self.client.chat.completions.create(**kwargs),
            max_retries=self.max_retries,
            base_delay=self.base_delay,
            max_delay=self.max_delay,
        )
        return self._parse_response(response, request.model, start)

    async def chat_stream(self, request: LLMRequest) -> AsyncGenerator[str, None]:
        """
        流式聊天 — 逐 token yield

        Args:
            request: LLM 请求对象

        Yields:
            str: 每个 token 的内容

        Raises:
            与 chat() 方法相同的异常
        """
        logger.debug(f"LLM stream: model={request.model}, messages={len(request.messages)}")
        request.stream = True
        kwargs = self._build_kwargs(request)

        try:
            stream = await _retry_with_backoff(
                coro_factory=lambda: self.client.chat.completions.create(**kwargs),
                max_retries=self.max_retries,
                base_delay=self.base_delay,
                max_delay=self.max_delay,
            )
            async for chunk in stream:
                delta = chunk.choices[0].delta if chunk.choices else None
                if delta and delta.content:
                    yield delta.content
        except Exception as e:
            logger.error(f"LLM stream failed: {type(e).__name__}: {e}")
            raise

    async def chat_with_tools(
        self,
        request: LLMRequest,
        tools: list[ToolFunction],
        tool_choice: Any = "auto",
    ) -> LLMResponse:
        """
        带工具调用的聊天

        Args:
            request: LLM 请求对象
            tools: 工具函数列表
            tool_choice: 工具选择策略 ("auto", "required", "none" 或具体函数)

        Returns:
            LLMResponse: 响应对象
        """
        request.tools = [t.to_openai_tool() for t in tools]
        request.tool_choice = tool_choice
        return await self.chat(request)

    # ── 快捷方法 ──────────────────────────────

    async def simple_chat(
        self,
        prompt: str,
        system: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
    ) -> str:
        """简单聊天快捷方法"""
        messages = []
        if system:
            messages.append(ChatMessage(role="system", content=system))
        messages.append(ChatMessage(role="user", content=prompt))

        request = LLMRequest(
            model=model or self.default_model,
            messages=messages,
            temperature=temperature,
        )
        response = await self.chat(request)
        return response.content

    # ── 内部方法 ──────────────────────────────

    def _build_kwargs(self, request: LLMRequest) -> dict[str, Any]:
        """构建 OpenAI SDK 请求参数"""
        messages = [{"role": msg.role.value, "content": msg.content} for msg in request.messages]

        kwargs: dict[str, Any] = {
            "model": request.model or self.default_model,
            "messages": messages,
            "temperature": request.temperature,
            "stream": request.stream,
        }

        if request.max_tokens:
            kwargs["max_tokens"] = request.max_tokens

        if getattr(request, "tools", None):
            kwargs["tools"] = request.tools

        if getattr(request, "tool_choice", None):
            kwargs["tool_choice"] = request.tool_choice

        return kwargs

    @staticmethod
    def _parse_response(response: Any, model: str, start: float) -> LLMResponse:
        """解析 OpenAI 格式响应"""
        choice = response.choices[0]
        content = choice.message.content or ""

        usage = {}
        if response.usage:
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }

        latency = (time.perf_counter() - start) * 1000
        logger.info(f"LLM response: tokens={usage.get('total_tokens', 0)}, latency={latency:.0f}ms")

        return LLMResponse(
            content=content,
            model=model,
            usage=usage,
            finish_reason=choice.finish_reason or "stop",
            latency_ms=latency,
        )

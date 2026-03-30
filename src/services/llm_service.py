"""
LLM 调用服务 — 智谱 GLM 系列
支持 429 限频自动重试 + 指数退避
"""
from __future__ import annotations

import asyncio
import time
from collections.abc import AsyncGenerator
from typing import Any, Optional

import openai
from openai import AsyncOpenAI

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
) -> Any:
    """
    对 LLM 调用做指数退避重试，处理 429 (RateLimitError) 和超时错误。
    其他错误直接抛出。
    """
    for attempt in range(max_retries + 1):
        try:
            return await coro_factory()
        except openai.RateLimitError:
            if attempt >= max_retries:
                logger.error(f"LLM 429: 重试 {max_retries} 次仍失败")
                raise
            delay = base_delay * (2 ** attempt)
            logger.warning(f"LLM 429 限频，第 {attempt + 1} 次重试，等待 {delay:.1f}s")
            await asyncio.sleep(delay)
        except (openai.APITimeoutError, asyncio.TimeoutError) as e:
            if attempt >= max_retries:
                logger.error(f"LLM 超时: 重试 {max_retries} 次仍失败")
                raise
            delay = base_delay * (2 ** attempt)
            logger.warning(f"LLM 超时，第 {attempt + 1} 次重试，等待 {delay:.1f}s")
            await asyncio.sleep(delay)


# ──────────────────────────────────────────────
# LLM Service
# ──────────────────────────────────────────────


class LLMService:
    """智谱 LLM 调用封装（OpenAI SDK 兼容，内置 429 重试）"""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://open.bigmodel.cn/api/paas/v4/",
        default_model: str = "glm-5-turbo",
        max_retries: int = 3,
        base_delay: float = 3.0,
    ):
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=120.0,
            max_retries=0,
        )
        self.default_model = default_model
        self.max_retries = max_retries
        self.base_delay = base_delay

    # ── 核心调用 ──────────────────────────────

    async def chat(self, request: LLMRequest) -> LLMResponse:
        """发送聊天请求（非流式），自动 429 重试"""
        start = time.perf_counter()
        logger.info(
            f"LLM request: model={request.model}, "
            f"messages={len(request.messages)}, "
            f"tools={len(request.tools) if request.tools else 0}"
        )

        kwargs = self._build_kwargs(request)

        response = await _retry_with_backoff(
            coro_factory=lambda: self.client.chat.completions.create(**kwargs),
            max_retries=self.max_retries,
            base_delay=self.base_delay,
        )
        return self._parse_response(response, request.model, start)

    async def chat_stream(self, request: LLMRequest) -> AsyncGenerator[str, None]:
        """流式聊天 — 逐 token yield"""
        logger.info(f"LLM stream: model={request.model}, messages={len(request.messages)}")
        request.stream = True
        kwargs = self._build_kwargs(request)

        try:
            stream = await _retry_with_backoff(
                coro_factory=lambda: self.client.chat.completions.create(**kwargs),
                max_retries=self.max_retries,
                base_delay=self.base_delay,
            )
            async for chunk in stream:
                delta = chunk.choices[0].delta if chunk.choices else None
                if delta and delta.content:
                    yield delta.content
        except Exception as e:
            logger.error(f"LLM stream failed: {e}")
            raise

    async def chat_with_tools(
        self,
        request: LLMRequest,
        tools: list[ToolFunction],
    ) -> LLMResponse:
        """带工具调用的聊天"""
        request.tools = [t.to_openai_tool() for t in tools]
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

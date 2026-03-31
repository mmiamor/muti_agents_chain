"""
Agent 基类 - 提供通用的 Agent 实现
"""
from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, TypeVar

from langchain_core.messages import AIMessage

from src.config import settings
from src.models.state import AgentState
from src.agents.factory import create_llm, get_revision_count
from src.services.llm_service import _retry_with_backoff
from src.memory.agent_context import prepare_messages_for_llm

T = TypeVar('T')


class BaseAgentImpl(ABC):
    """
    Agent 基类实现

    提供通用功能:
    - 自动延迟（避免 429）
    - 审查反馈处理
    - LLM 调用封装
    - 消息准备
    """

    # 子类必须定义这些属性
    name: str
    role: str
    system_prompt: str

    def __init__(self, llm=None):
        """
        初始化 Agent

        Args:
            llm: LLM 实例（可选，默认自动创建）
        """
        self.llm = llm
        if self.llm is None:
            self.llm = create_llm(agent_name=self.name)
        self.logger = logging.getLogger(self.name)

    async def run(self, state: AgentState) -> dict:
        """
        执行 Agent 逻辑

        Args:
            state: 当前 Agent 状态

        Returns:
            dict: 状态更新
        """
        sender = state.get("sender", "N/A")
        self.logger.info(f"[{self.role}] processing, sender={sender}")

        # 节点间冷却
        await self._apply_delay()

        # 准备消息
        messages = await self._prepare_messages(state)

        # 调用 LLM
        response = await self._call_llm(messages)

        # 解析响应
        result = await self._parse_response(response, state)

        # 构建返回值
        return self._build_result(result, state)

    @abstractmethod
    async def _parse_response(self, response: str, state: AgentState) -> Any:
        """
        解析 LLM 响应

        Args:
            response: LLM 响应内容
            state: 当前状态

        Returns:
            解析后的结果对象
        """
        ...

    @abstractmethod
    def _get_result_key(self) -> str:
        """
        获取结果在 state 中的 key

        Returns:
            str: 状态键名（如 "prd", "trd"）
        """
        ...

    def _build_summary(self, result: Any) -> str:
        """
        构建结果摘要

        Args:
            result: 解析后的结果对象

        Returns:
            str: 摘要文本
        """
        return f"{self.role} 完成任务"

    async def _prepare_messages(self, state: AgentState) -> list[dict]:
        """
        准备 LLM 消息

        Args:
            state: 当前状态

        Returns:
            list[dict]: 消息列表
        """
        # 审查反馈上下文
        review_context = await self._get_review_context(state)

        # 使用优化的上下文管理器
        system_prompt = self.system_prompt + review_context
        messages = prepare_messages_for_llm(
            state.get("messages", []),
            system_prompt=system_prompt,
            agent_name=self.name,
        )

        return messages

    async def _get_review_context(self, state: AgentState) -> str:
        """
        获取审查反馈上下文

        Args:
            state: 当前状态

        Returns:
            str: 审查反馈文本
        """
        latest_review = state.get("latest_review")
        revision_count = get_revision_count(state, self.name)

        if latest_review and latest_review.status == "REJECTED":
            return (
                f"\n\n## ⚠️ 审查员反馈（第 {revision_count} 次修改）\n"
                f"{latest_review.comments}\n"
                f"请根据以上反馈修改你的产出物。"
            )

        return ""

    async def _call_llm(self, messages: list[dict]) -> str:
        """
        调用 LLM

        Args:
            messages: 消息列表

        Returns:
            str: LLM 响应内容
        """
        response = await _retry_with_backoff(
            coro_factory=lambda: self.llm.client.chat.completions.create(
                model=self.llm.default_model,
                messages=messages,
                temperature=0,
            ),
            max_retries=self.llm.max_retries,
            base_delay=self.llm.base_delay,
        )

        content = response.choices[0].message.content
        self.logger.debug(f"[{self.role}] raw response: {content[:200]}")

        return content

    async def _apply_delay(self):
        """应用节点间延迟"""
        if settings.NODE_DELAY > 0:
            await asyncio.sleep(settings.NODE_DELAY)

    def _build_result(self, result: Any, state: AgentState) -> dict:
        """
        构建返回结果

        Args:
            result: 解析后的结果对象
            state: 当前状态

        Returns:
            dict: 状态更新
        """
        result_key = self._get_result_key()
        summary = self._build_summary(result)

        return {
            result_key: result,
            "sender": self.name,
            "messages": [AIMessage(content=summary)],
        }


class BaseReviewerAgent(ABC):
    """
    Reviewer Agent 基类

    提供通用的审查功能
    """

    # 审查目标映射：agent_name → (state_key, 审查标题)
    ARTIFACT_MAP: dict[str, tuple[str, str]] = {}

    def __init__(self, llm=None):
        self.llm = llm
        if self.llm is None:
            self.llm = create_llm()
        self.logger = logging.getLogger("reviewer_agent")

    async def run(self, state: AgentState) -> dict:
        """
        执行审查

        Args:
            state: 当前状态

        Returns:
            dict: 状态更新
        """
        sender = state.get("sender", "")
        self.logger.info(f"[Reviewer Agent] reviewing output from {sender}")

        # 节点间冷却
        await self._apply_delay()

        # 确定审查目标
        artifact_key, review_title, review_target = self._get_review_target(state, sender)

        if not artifact_key:
            self.logger.warning(f"[Reviewer Agent] no review target, sender={sender}")
            return self._build_rejected_result("无法识别审查目标")

        # 构建审查消息
        messages = self._build_review_messages(review_title, review_target)

        # 调用 LLM
        response = await self._call_llm(messages)

        # 解析反馈
        feedback = self._parse_feedback(response)

        # 构建返回值
        return self._build_review_result(feedback, sender, state)

    def _get_review_target(self, state: AgentState, sender: str) -> tuple[str, str, str]:
        """
        获取审查目标

        Args:
            state: 当前状态
            sender: 发送者名称

        Returns:
            tuple: (artifact_key, review_title, review_target)
        """
        for agent_name, (key, title) in self.ARTIFACT_MAP.items():
            if sender == agent_name and state.get(key) is not None:
                review_target = (
                    f"审查以下{title}：\n\n"
                    f"```json\n{state[key].model_dump_json(indent=2)}\n```"
                )
                return key, title, review_target

        return "", "", ""

    def _build_review_messages(self, review_title: str, review_target: str) -> list[dict]:
        """
        构建审查消息

        Args:
            review_title: 审查标题
            review_target: 审查目标内容

        Returns:
            list[dict]: 消息列表
        """
        return [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": review_target},
        ]

    async def _call_llm(self, messages: list[dict]) -> str:
        """调用 LLM（同 BaseAgentImpl）"""
        from src.config import settings
        response = await _retry_with_backoff(
            coro_factory=lambda: self.llm.client.chat.completions.create(
                model=settings.DEFAULT_MODEL,
                messages=messages,
                temperature=0,
            ),
            max_retries=self.llm.max_retries,
            base_delay=self.llm.base_delay,
        )

        content = response.choices[0].message.content
        self.logger.debug(f"[Reviewer Agent] raw response: {content[:200]}")

        return content

    def _parse_feedback(self, response: str):
        """
        解析审查反馈

        Args:
            response: LLM 响应

        Returns:
            ReviewFeedback: 反馈对象
        """
        from src.models.agent_models import ReviewFeedback
        from src.utils.json_extract import extract_json

        try:
            feedback_data = extract_json(response)

            # 确保 comments 字段是字符串
            if isinstance(feedback_data.get("comments"), list):
                feedback_data["comments"] = "\n".join(
                    item if isinstance(item, str) else str(item)
                    for item in feedback_data["comments"]
                )
            elif not isinstance(feedback_data.get("comments"), str):
                feedback_data["comments"] = str(feedback_data.get("comments", ""))

            # 确保 status 字段有效
            if feedback_data.get("status") not in ["APPROVED", "REJECTED"]:
                self.logger.warning(f"[Reviewer Agent] invalid status: {feedback_data.get('status')}")
                feedback_data["status"] = "REJECTED"

            feedback = ReviewFeedback(**feedback_data)
            self.logger.info(f"[Reviewer Agent] result: {feedback.status}")

            return feedback

        except Exception as e:
            self.logger.error(f"[Reviewer Agent] failed to parse feedback: {e}")
            # 如果解析失败，默认拒绝
            return ReviewFeedback(
                status="REJECTED",
                comments=f"审查反馈解析失败: {str(e)}。原始响应: {response[:200]}..."
            )

    def _build_review_result(self, feedback, sender: str, state: AgentState) -> dict:
        """
        构建审查结果

        Args:
            feedback: 反馈对象
            sender: 发送者
            state: 当前状态

        Returns:
            dict: 状态更新
        """
        from src.agents.factory import next_revision_count
        from langchain_core.messages import AIMessage

        update = {
            "latest_review": feedback,
            "sender": self.name,
            "messages": [AIMessage(content=f"Reviewer: {feedback.status} — {feedback.comments}")],
        }

        if feedback.status == "REJECTED":
            update.update(next_revision_count(state, sender))

        return update

    def _build_rejected_result(self, reason: str) -> dict:
        """构建拒绝结果"""
        from src.models.agent_models import ReviewFeedback
        from langchain_core.messages import AIMessage

        return {
            "latest_review": ReviewFeedback(status="REJECTED", comments=reason),
            "sender": self.name,
        }

    async def _apply_delay(self):
        """应用延迟"""
        if settings.NODE_DELAY > 0:
            await asyncio.sleep(settings.NODE_DELAY)


__all__ = ["BaseAgentImpl", "BaseReviewerAgent"]

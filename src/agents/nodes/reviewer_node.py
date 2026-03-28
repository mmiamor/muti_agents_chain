"""Reviewer Agent — LangGraph 节点函数"""
from __future__ import annotations

import asyncio
import logging

from langchain_core.messages import AIMessage

from src.config import settings
from src.models.state import AgentState
from src.models.agent_models import ReviewFeedback
from src.services.llm_service import LLMService, _retry_with_backoff
from src.prompts.reviewer_agent import SYSTEM_PROMPT
from src.utils.json_extract import extract_json

logger = logging.getLogger("reviewer_node")


def _create_llm() -> LLMService:
    return LLMService(
        api_key=settings.ZAI_API_KEY,
        base_url=settings.OPENAI_BASE_URL,
        default_model=settings.DEFAULT_MODEL,
        max_retries=settings.LLM_RETRY_MAX,
        base_delay=settings.LLM_RETRY_BASE_DELAY,
    )


class ReviewerAgent:
    """Reviewer Agent 实现"""

    name = "reviewer_agent"
    role = "审查专家"

    def __init__(self, llm: LLMService | None = None):
        self.llm = llm
        if self.llm is None:
            self.llm = _create_llm()

    async def run(self, state: AgentState) -> dict:
        """审查产出物，返回 APPROVED 或 REJECTED"""
        sender = state.get("sender", "")
        logger.info(f"[Reviewer Agent] reviewing output from {sender}")

        # 节点间冷却
        if settings.NODE_DELAY > 0:
            await asyncio.sleep(settings.NODE_DELAY)

        # 确定审查目标
        if sender == "architect_agent" and state.get("trd"):
            review_target = (
                f"审查以下 TRD（技术设计文档）：\n\n"
                f"```json\n{state['trd'].model_dump_json(indent=2)}\n```"
            )
        elif state.get("prd"):
            review_target = (
                f"审查以下 PRD（产品需求文档）：\n\n"
                f"```json\n{state['prd'].model_dump_json(indent=2)}\n```"
            )
        else:
            logger.warning(f"[Reviewer Agent] no review target, sender={sender}")
            return {
                "latest_review": ReviewFeedback(status="REJECTED", comments="无法识别审查目标"),
                "sender": self.name,
            }

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": review_target},
        ]

        # 使用重试包装
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
        logger.debug(f"[Reviewer Agent] raw response: {content[:200]}")

        feedback_data = extract_json(content)
        feedback = ReviewFeedback(**feedback_data)
        logger.info(f"[Reviewer Agent] result: {feedback.status}")

        update = {
            "latest_review": feedback,
            "sender": self.name,
            "messages": [AIMessage(content=f"Reviewer: {feedback.status} — {feedback.comments}")],
        }

        if feedback.status == "REJECTED":
            if sender == "architect_agent":
                update["architect_revision_count"] = state.get("architect_revision_count", 0) + 1
            else:
                update["revision_count"] = state.get("revision_count", 0) + 1

        return update


# ── 模块级节点函数 ─────────────────────────

_reviewer_agent: ReviewerAgent | None = None


def get_reviewer_agent() -> ReviewerAgent:
    global _reviewer_agent
    if _reviewer_agent is None:
        _reviewer_agent = ReviewerAgent()
    return _reviewer_agent


async def reviewer_node(state: AgentState) -> dict:
    return await get_reviewer_agent().run(state)

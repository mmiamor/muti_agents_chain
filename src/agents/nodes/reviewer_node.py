"""Reviewer Agent — LangGraph 节点函数"""
from __future__ import annotations

import asyncio
import logging

from langchain_core.messages import AIMessage

from src.config import settings
from src.models.state import AgentState
from src.models.agent_models import ReviewFeedback
from src.agents.factory import create_llm, get_revision_count, next_revision_count
from src.services.llm_service import _retry_with_backoff
from src.prompts.reviewer_agent import SYSTEM_PROMPT
from src.utils.json_extract import extract_json

logger = logging.getLogger("reviewer_node")


# ── 产出物审查映射 ──
# agent_name → (产出物 key, 审查标题)
_ARTIFACT_MAP = {
    "qa_agent": ("qa_report", "QA 质量报告"),
    "frontend_dev_agent": ("frontend_code", "前端代码"),
    "backend_dev_agent": ("backend_code", "后端代码"),
    "design_agent": ("design_doc", "UI/UX 设计文档"),
    "architect_agent": ("trd", "技术设计文档"),
    "pm_agent": ("prd", "产品需求文档"),
}


class ReviewerAgent:
    """Reviewer Agent 实现"""

    name = "reviewer_agent"
    role = "审查专家"

    def __init__(self, llm=None):
        self.llm = llm
        if self.llm is None:
            self.llm = create_llm()

    async def run(self, state: AgentState) -> dict:
        """审查产出物，返回 APPROVED 或 REJECTED"""
        sender = state.get("sender", "")
        logger.info(f"[Reviewer Agent] reviewing output from {sender}")

        # 节点间冷却
        if settings.NODE_DELAY > 0:
            await asyncio.sleep(settings.NODE_DELAY)

        # 确定审查目标：按 _ARTIFACT_MAP 优先匹配当前 sender
        artifact_key = None
        review_title = ""
        for agent_name, (key, title) in _ARTIFACT_MAP.items():
            if sender == agent_name and state.get(key) is not None:
                artifact_key = key
                review_title = title
                break

        if not artifact_key:
            logger.warning(f"[Reviewer Agent] no review target, sender={sender}")
            return {
                "latest_review": ReviewFeedback(status="REJECTED", comments="无法识别审查目标"),
                "sender": self.name,
            }

        review_target = (
            f"审查以下{review_title}：\n\n"
            f"```json\n{state[artifact_key].model_dump_json(indent=2)}\n```"
        )

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": review_target},
        ]

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
            update.update(next_revision_count(state, sender))

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

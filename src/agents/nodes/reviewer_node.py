"""Reviewer Agent — LangGraph 节点函数"""
from __future__ import annotations

import json
import logging

from langchain_core.messages import SystemMessage, AIMessage

from src.config import settings
from src.models.state import AgentState
from src.models.agent_models import ReviewFeedback
from src.services.llm_service import LLMService
from src.prompts.reviewer_agent import SYSTEM_PROMPT

logger = logging.getLogger("reviewer_node")


def _create_llm() -> LLMService:
    """延迟创建 LLM 实例"""
    return LLMService(
        api_key=settings.ZAI_API_KEY,
        base_url=settings.OPENAI_BASE_URL,
        default_model=settings.DEFAULT_MODEL,
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

        # 确定审查目标
        review_target = ""
        if sender == "pm_agent" and state.get("prd"):
            review_target = (
                f"请审查以下 PRD（产品需求文档）：\n\n"
                f"```json\n{state['prd'].model_dump_json(indent=2)}\n```\n\n"
                f"请检查：完整性、用户故事质量、非功能需求是否量化、Mermaid 语法。"
            )
        elif sender == "architect_agent" and state.get("trd"):
            review_target = (
                f"请审查以下 TRD（技术设计文档）：\n\n"
                f"```json\n{state['trd'].model_dump_json(indent=2)}\n```\n\n"
                f"请检查：技术栈合理性、API 设计、数据库设计、与 PRD 的一致性。"
            )
        else:
            logger.warning(f"[Reviewer Agent] no review target found for sender={sender}")
            return {
                "latest_review": ReviewFeedback(
                    status="REJECTED",
                    comments=f"无法识别审查目标（sender={sender}），请重新生成。"
                ),
                "sender": self.name,
            }

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": review_target},
        ]

        response = await self.llm.client.chat.completions.create(
            model=settings.DEFAULT_MODEL,
            messages=messages,
            temperature=0,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content
        logger.debug(f"[Reviewer Agent] raw response: {content[:200]}")

        feedback_data = json.loads(content)
        feedback = ReviewFeedback(**feedback_data)

        logger.info(f"[Reviewer Agent] result: {feedback.status}")

        return {
            "latest_review": feedback,
            "sender": self.name,
            "messages": [
                AIMessage(content=f"Reviewer: {feedback.status} — {feedback.comments}")
            ],
        }

    async def review(self, state: AgentState) -> bool:
        """检查是否有审查结果"""
        return state.get("latest_review") is not None


# ── 模块级节点函数（LangGraph 使用）────────────────

_reviewer_agent: ReviewerAgent | None = None


def get_reviewer_agent() -> ReviewerAgent:
    """获取或创建 Reviewer Agent 单例（延迟初始化）"""
    global _reviewer_agent
    if _reviewer_agent is None:
        _reviewer_agent = ReviewerAgent()
    return _reviewer_agent


async def reviewer_node(state: AgentState) -> dict:
    """LangGraph 节点函数 — Reviewer Agent 入口"""
    return await get_reviewer_agent().run(state)

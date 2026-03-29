"""Architect Agent — LangGraph 节点函数"""
from __future__ import annotations

import asyncio
import logging

from langchain_core.messages import AIMessage

from src.config import settings
from src.models.state import AgentState
from src.models.document_models import TRD
from src.agents.factory import create_llm, get_revision_count
from src.services.llm_service import _retry_with_backoff
from src.prompts.architect_agent import SYSTEM_PROMPT
from src.utils.json_extract import extract_json

logger = logging.getLogger("architect_node")


class ArchitectAgent:
    """Architect Agent 实现"""

    name = "architect_agent"
    role = "资深架构师"

    def __init__(self, llm=None):
        self.llm = llm
        if self.llm is None:
            self.llm = create_llm()

    async def run(self, state: AgentState) -> dict:
        """阅读 PRD，生成 TRD"""
        logger.info(f"[Architect Agent] processing, sender={state.get('sender', 'N/A')}")

        prd = state.get("prd")
        if not prd:
            logger.error("[Architect Agent] no PRD found in state")
            return {
                "sender": self.name,
                "messages": [AIMessage(content="Architect Agent: 缺少 PRD 输入，无法生成 TRD。")],
            }

        # 节点间冷却
        if settings.NODE_DELAY > 0:
            await asyncio.sleep(settings.NODE_DELAY)

        # 审查反馈上下文
        review_context = ""
        latest_review = state.get("latest_review")
        revision_count = get_revision_count(state, self.name)
        if latest_review and latest_review.status == "REJECTED":
            review_context = (
                f"\n\n审查员反馈（第 {revision_count} 次修改）:\n"
                f"{latest_review.comments}\n请据此修改 TRD。"
            )

        prd_context = f"根据以下 PRD 设计技术方案：\n\n```json\n{prd.model_dump_json(indent=2)}\n```"

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT + review_context},
            {"role": "user", "content": prd_context},
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
        logger.debug(f"[Architect Agent] raw response: {content[:200]}")

        trd_data = extract_json(content)
        trd = TRD(**trd_data)

        logger.info(f"[Architect Agent] TRD generated: {trd.tech_stack.backend}, APIs={len(trd.api_endpoints)}")

        return {
            "trd": trd,
            "sender": self.name,
            "messages": [
                AIMessage(
                    content=(
                        f"Architect Agent 已生成 TRD:\n"
                        f"后端: {trd.tech_stack.backend}\n"
                        f"数据库: {trd.tech_stack.database}\n"
                        f"API 数量: {len(trd.api_endpoints)}"
                    )
                )
            ],
        }


# ── 模块级节点函数 ─────────────────────────

_architect_agent: ArchitectAgent | None = None


def get_architect_agent() -> ArchitectAgent:
    global _architect_agent
    if _architect_agent is None:
        _architect_agent = ArchitectAgent()
    return _architect_agent


async def architect_node(state: AgentState) -> dict:
    return await get_architect_agent().run(state)

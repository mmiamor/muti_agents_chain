"""Design Agent — LangGraph 节点函数"""
from __future__ import annotations

import asyncio
import logging

from langchain_core.messages import AIMessage

from src.config import settings
from src.models.state import AgentState
from src.models.document_models import DesignDocument
from src.agents.factory import create_llm, get_revision_count
from src.services.llm_service import _retry_with_backoff
from src.prompts.design_agent import SYSTEM_PROMPT
from src.utils.json_extract import extract_json

logger = logging.getLogger("design_node")


class DesignAgent:
    """Design Agent 实现"""

    name = "design_agent"
    role = "资深 UI/UX 设计师"

    def __init__(self, llm=None):
        self.llm = llm
        if self.llm is None:
            self.llm = create_llm()

    async def run(self, state: AgentState) -> dict:
        """阅读 PRD + TRD，生成 DesignDocument"""
        logger.info(f"[Design Agent] processing, sender={state.get('sender', 'N/A')}")

        prd = state.get("prd")
        trd = state.get("trd")

        if not prd or not trd:
            logger.error("[Design Agent] missing PRD or TRD")
            return {
                "sender": self.name,
                "messages": [AIMessage(content="Design Agent: 缺少 PRD 或 TRD 输入，无法生成设计文档。")],
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
                f"{latest_review.comments}\n请据此修改 DesignDocument。"
            )

        context = (
            f"根据以下 PRD 和 TRD 设计 UI/UX 方案：\n\n"
            f"### PRD\n```json\n{prd.model_dump_json(indent=2)}\n```\n\n"
            f"### TRD\n```json\n{trd.model_dump_json(indent=2)}\n```"
        )

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT + review_context},
            {"role": "user", "content": context},
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
        logger.debug(f"[Design Agent] raw response: {content[:200]}")

        design_data = extract_json(content)
        design_doc = DesignDocument(**design_data)

        logger.info(
            f"[Design Agent] DesignDocument generated: "
            f"pages={len(design_doc.page_specs)}, "
            f"components={len(design_doc.component_library)}"
        )

        return {
            "design_doc": design_doc,
            "sender": self.name,
            "messages": [
                AIMessage(
                    content=(
                        f"Design Agent 已生成 DesignDocument:\n"
                        f"页面数: {len(design_doc.page_specs)}\n"
                        f"组件库: {len(design_doc.component_library)}\n"
                        f"主色: {design_doc.design_tokens.color_primary}"
                    )
                )
            ],
        }


# ── 模块级节点函数 ─────────────────────────

_design_agent: DesignAgent | None = None


def get_design_agent() -> DesignAgent:
    global _design_agent
    if _design_agent is None:
        _design_agent = DesignAgent()
    return _design_agent


async def design_node(state: AgentState) -> dict:
    return await get_design_agent().run(state)

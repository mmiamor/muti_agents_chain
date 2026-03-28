"""PM Agent — LangGraph 节点函数"""
from __future__ import annotations

import asyncio
import json
import logging
import re

from langchain_core.messages import SystemMessage, AIMessage

from src.config import settings
from src.models.state import AgentState
from src.models.document_models import PRD
from src.services.llm_service import LLMService, _retry_with_backoff
from src.prompts.pm_agent import SYSTEM_PROMPT
from src.utils.json_extract import extract_json

logger = logging.getLogger("pm_node")

_role_map = {"system": "system", "human": "user", "ai": "assistant", "tool": "tool"}


def _create_llm() -> LLMService:
    """延迟创建 LLM 实例"""
    return LLMService(
        api_key=settings.ZAI_API_KEY,
        base_url=settings.OPENAI_BASE_URL,
        default_model=settings.DEFAULT_MODEL,
        max_retries=settings.LLM_RETRY_MAX,
        base_delay=settings.LLM_RETRY_BASE_DELAY,
    )


class PMAgent:
    """PM Agent 实现"""

    name = "pm_agent"
    role = "资深产品经理"

    def __init__(self, llm: LLMService | None = None):
        self.llm = llm
        if self.llm is None:
            self.llm = _create_llm()

    async def run(self, state: AgentState) -> dict:
        """分析需求，生成 PRD"""
        sender = state.get("sender", "N/A")
        logger.info(f"[PM Agent] processing, sender={sender}")

        # 节点间冷却，避免 429
        if settings.NODE_DELAY > 0:
            await asyncio.sleep(settings.NODE_DELAY)

        # 审查反馈上下文
        review_context = ""
        latest_review = state.get("latest_review")
        revision_count = state.get("revision_count", 0)
        if latest_review and latest_review.status == "REJECTED":
            review_context = f"\n\n## ⚠️ 审查员反馈（第 {revision_count} 次修改）\n{latest_review.comments}\n请根据以上反馈修改你的 PRD。"

        # 构建消息
        messages = [{"role": "system", "content": SYSTEM_PROMPT + review_context}]
        # 传递完整上下文
        for m in state.get("messages", []):
            messages.append({"role": _role_map.get(m.type, m.type), "content": m.content})

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
        logger.debug(f"[PM Agent] raw response: {content[:200]}")

        prd_data = extract_json(content)
        prd = PRD(**prd_data)

        logger.info(f"[PM Agent] PRD generated: {prd.vision}")

        return {
            "prd": prd,
            "sender": self.name,
            "messages": [
                AIMessage(content=f"PM Agent 已生成 PRD:\n愿景: {prd.vision}\n核心功能: {', '.join(prd.core_features)}\n用户故事数: {len(prd.user_stories)}")
            ],
        }


# ── 模块级节点函数 ─────────────────────────

_pm_agent: PMAgent | None = None


def get_pm_agent() -> PMAgent:
    global _pm_agent
    if _pm_agent is None:
        _pm_agent = PMAgent()
    return _pm_agent


async def pm_node(state: AgentState) -> dict:
    return await get_pm_agent().run(state)

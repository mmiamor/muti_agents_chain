"""PM Agent — LangGraph 节点函数"""
from __future__ import annotations

import asyncio
import logging

from langchain_core.messages import AIMessage

from src.config import settings
from src.models.state import AgentState
from src.models.document_models import PRD
from src.agents.factory import create_llm, get_revision_count
from src.services.llm_service import _retry_with_backoff
from src.prompts.pm_agent import SYSTEM_PROMPT
from src.utils.json_extract import extract_json
from src.memory.agent_context import prepare_messages_for_llm

logger = logging.getLogger("pm_node")


class PMAgent:
    """PM Agent 实现"""

    name = "pm_agent"
    role = "资深产品经理"

    def __init__(self, llm=None):
        self.llm = llm
        if self.llm is None:
            # 传入 agent_name 以获取专用模型
            self.llm = create_llm(agent_name=self.name)

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
        revision_count = get_revision_count(state, self.name)
        if latest_review and latest_review.status == "REJECTED":
            review_context = f"\n\n## ⚠️ 审查员反馈（第 {revision_count} 次修改）\n{latest_review.comments}\n请根据以上反馈修改你的 PRD。"

        # 使用优化的上下文管理器准备消息
        system_prompt = SYSTEM_PROMPT + review_context
        messages = prepare_messages_for_llm(
            state.get("messages", []),
            system_prompt=system_prompt,
            agent_name=self.name,
        )

        response = await _retry_with_backoff(
            coro_factory=lambda: self.llm.client.chat.completions.create(
                model=self.llm.default_model,  # 使用 Agent 专用模型
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

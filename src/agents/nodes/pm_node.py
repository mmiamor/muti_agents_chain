"""PM Agent — LangGraph 节点函数"""
from __future__ import annotations

import json
import logging

from langchain_core.messages import SystemMessage, AIMessage

from src.config import settings
from src.models.state import AgentState
from src.models.document_models import PRD
from src.services.llm_service import LLMService
from src.prompts.pm_agent import SYSTEM_PROMPT

logger = logging.getLogger("pm_node")


def _create_llm() -> LLMService:
    """延迟创建 LLM 实例（避免模块导入时就需要环境变量）"""
    return LLMService(
        api_key=settings.ZAI_API_KEY,
        base_url=settings.OPENAI_BASE_URL,
        default_model=settings.DEFAULT_MODEL,
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
        logger.info(f"[PM Agent] processing, sender={state.get('sender', 'N/A')}")

        # 如果已有审查反馈且被拒绝，将反馈作为额外上下文
        review_context = ""
        latest_review = state.get("latest_review")
        revision_count = state.get("revision_count", 0)
        if latest_review and latest_review.status == "REJECTED":
            review_context = f"\n\n## ⚠️ 审查员反馈（第 {revision_count} 次修改）\n{latest_review.comments}\n请根据以上反馈修改你的 PRD。"

        # 构建消息
        messages = [SystemMessage(content=SYSTEM_PROMPT + review_context)]
        messages.extend(state.get("messages", []))

        # 调用 LLM
        response = await self.llm.client.chat.completions.create(
            model=settings.DEFAULT_MODEL,
            messages=[{"role": m.type, "content": m.content} for m in messages],
            temperature=0,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content
        logger.debug(f"[PM Agent] raw response: {content[:200]}")

        # 解析 PRD
        prd_data = json.loads(content)
        prd = PRD(**prd_data)

        logger.info(f"[PM Agent] PRD generated: {prd.vision}")

        return {
            "prd": prd,
            "sender": self.name,
            "messages": [
                AIMessage(content=f"PM Agent 已生成 PRD:\n愿景: {prd.vision}\n核心功能: {', '.join(prd.core_features)}\n用户故事数: {len(prd.user_stories)}")
            ],
        }

    async def review(self, state: AgentState) -> bool:
        """自我反思 — 检查 PRD 完整性"""
        prd = state.get("prd")
        if not prd:
            return False
        # 基本完整性检查
        checks = [
            bool(prd.vision),
            bool(prd.target_audience),
            len(prd.user_stories) > 0,
            len(prd.core_features) > 0,
            bool(prd.mermaid_flowchart),
        ]
        result = all(checks)
        if not result:
            logger.warning(f"[PM Agent] self-review failed: {checks}")
        return result


# ── 模块级节点函数（LangGraph 使用）────────────────

_pm_agent: PMAgent | None = None


def get_pm_agent() -> PMAgent:
    """获取或创建 PM Agent 单例（延迟初始化）"""
    global _pm_agent
    if _pm_agent is None:
        _pm_agent = PMAgent()
    return _pm_agent


async def pm_node(state: AgentState) -> dict:
    """LangGraph 节点函数 — PM Agent 入口"""
    return await get_pm_agent().run(state)

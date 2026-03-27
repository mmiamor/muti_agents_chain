"""Multi-Agent 编排器 — LangGraph 图构建与条件路由"""
from __future__ import annotations

import logging

from src.config import settings
from src.models.state import AgentState
from src.models.agent_models import ReviewFeedback

logger = logging.getLogger("orchestrator")


# ── Agent 名称常量 ─────────────────────────────────

class AgentNames:
    """Agent 节点名称常量（全局统一，防止拼写错误）"""
    PM = "pm_agent"
    REVIEWER = "reviewer_agent"
    ARCHITECT = "architect_agent"
    DESIGN = "design_agent"
    FRONTEND_DEV = "frontend_dev_agent"
    BACKEND_DEV = "backend_dev_agent"
    QA = "qa_agent"
    HUMAN = "human_intervention"


# ── 路由函数 ──────────────────────────────────────

def review_router(state: AgentState) -> str:
    """
    Reviewer 节点后的条件路由

    决策逻辑：
    1. 无审查结果 → 打回 PM 重做
    2. APPROVED → 流转下一阶段（架构师）
    3. REJECTED + 超过最大重试次数 → 人工干预
    4. REJECTED + 还有机会 → 打回 PM 重做（revision_count +1）
    """
    latest_review: ReviewFeedback | None = state.get("latest_review")
    revision_count: int = state.get("revision_count", 0)
    max_revisions = getattr(settings, "MAX_REVISION_COUNT", 3)

    if not latest_review:
        logger.warning("[Router] No review result, routing back to PM")
        return AgentNames.PM

    if latest_review.status == "APPROVED":
        logger.info("✅ [Router] Review approved, proceeding to Architect")
        return AgentNames.ARCHITECT

    if revision_count >= max_revisions:
        logger.warning(
            f"🚨 [Router] Max revisions ({revision_count}/{max_revisions}) exceeded, "
            f"triggering human intervention"
        )
        return AgentNames.HUMAN

    logger.info(
        f"❌ [Router] Review rejected ({revision_count}/{max_revisions}): "
        f"{latest_review.comments}"
    )
    return AgentNames.PM


# ── 图构建 ────────────────────────────────────────

def build_graph():
    """
    构建 LangGraph StateGraph

    Phase 2 闭环：
        PM → Reviewer → (APPROVED → Architect | REJECTED → PM)
                              (max revisions → Human → END)

    返回编译后的图实例。
    """
    from langgraph.graph import StateGraph, END
    from langgraph.checkpoint.memory import MemorySaver

    from src.agents.nodes.pm_node import pm_node
    from src.agents.nodes.reviewer_node import reviewer_node

    workflow = StateGraph(AgentState)

    # ── 注册节点 ──
    workflow.add_node(AgentNames.PM, pm_node)
    workflow.add_node(AgentNames.REVIEWER, reviewer_node)

    # 人工干预节点（占位，Phase 2 暂不实现具体逻辑）
    async def human_node(state: AgentState) -> dict:
        logger.warning("[Human] Manual intervention required")
        return {"sender": "human_intervention"}

    workflow.add_node(AgentNames.HUMAN, human_node)

    # ── 设置入口 ──
    workflow.set_entry_point(AgentNames.PM)

    # ── 标准边 ──
    # PM 产出 PRD 后，无条件流转给 Reviewer
    workflow.add_edge(AgentNames.PM, AgentNames.REVIEWER)

    # ── 条件边 ──
    # Reviewer 审查后，根据结果路由
    # Phase 2: APPROVED → END (Phase 3 会改为 → Architect)
    workflow.add_conditional_edges(
        AgentNames.REVIEWER,
        review_router,
        {
            AgentNames.ARCHITECT: END,
            AgentNames.PM: AgentNames.PM,
            AgentNames.HUMAN: AgentNames.HUMAN,
        },
    )

    # 人工干预 → 结束
    workflow.add_edge(AgentNames.HUMAN, END)

    # ── 编译 ──
    memory = MemorySaver()
    graph = workflow.compile(checkpointer=memory)

    logger.info("StateGraph compiled successfully")
    return graph

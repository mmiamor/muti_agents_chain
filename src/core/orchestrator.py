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
    1. 无审查结果 → 打回当前阶段重做
    2. APPROVED → 流转下一阶段
    3. REJECTED + 超过最大重试次数 → 人工干预
    4. REJECTED + 还有机会 → 打回当前阶段重做

    当前阶段根据产出物判断（而非 sender，因为 sender 会被 Reviewer 覆盖）：
    - 有 PRD 但无 TRD → PM 阶段
    - 有 TRD → Architect 阶段
    """
    latest_review: ReviewFeedback | None = state.get("latest_review")
    max_revisions = getattr(settings, "MAX_REVISION_COUNT", 3)

    # 根据「被审查的产出物」判断当前阶段
    has_trd = state.get("trd") is not None
    has_prd = state.get("prd") is not None

    if has_trd:
        # TRD 存在 → 审查的是 Architect 的产出
        current_agent = AgentNames.ARCHITECT
        revision_count = state.get("architect_revision_count", 0)
        next_agent = "__end__"  # Phase 4 会改为 DESIGN
    elif has_prd:
        # 有 PRD 无 TRD → 审查的是 PM 的产出
        current_agent = AgentNames.PM
        revision_count = state.get("revision_count", 0)
        next_agent = AgentNames.ARCHITECT
    else:
        logger.warning("[Router] No artifact found, routing back to PM")
        return AgentNames.PM

    if not latest_review:
        logger.warning("[Router] No review result, routing back to %s", current_agent)
        return current_agent

    if latest_review.status == "APPROVED":
        logger.info(f"✅ [Router] Review approved, proceeding from {current_agent} → {next_agent}")
        # Phase 3: Architect APPROVED → END（下一阶段尚未实现）
        if current_agent == AgentNames.ARCHITECT:
            return "__end__"
        return next_agent

    if revision_count >= max_revisions:
        logger.warning(
            f"🚨 [Router] Max revisions for {current_agent} "
            f"({revision_count}/{max_revisions}) exceeded, triggering human intervention"
        )
        return AgentNames.HUMAN

    logger.info(
        f"❌ [Router] Review rejected for {current_agent} "
        f"({revision_count}/{max_revisions}): {latest_review.comments}"
    )
    return current_agent


# ── 图构建 ────────────────────────────────────────

def build_graph():
    """
    构建 LangGraph StateGraph

    Phase 3 流程：
        PM → Reviewer → (APPROVED → Architect)
                              (REJECTED → PM, max → Human)
        Architect → Reviewer → (APPROVED → END)
                                  (REJECTED → Architect, max → Human)

    返回编译后的图实例。
    """
    from langgraph.graph import StateGraph, END
    from langgraph.checkpoint.memory import MemorySaver

    from src.agents.nodes.pm_node import pm_node
    from src.agents.nodes.reviewer_node import reviewer_node
    from src.agents.nodes.architect_node import architect_node

    workflow = StateGraph(AgentState)

    # ── 注册节点 ──
    workflow.add_node(AgentNames.PM, pm_node)
    workflow.add_node(AgentNames.REVIEWER, reviewer_node)
    workflow.add_node(AgentNames.ARCHITECT, architect_node)

    # 人工干预节点（占位，暂不实现具体逻辑）
    async def human_node(state: AgentState) -> dict:
        logger.warning("[Human] Manual intervention required")
        return {"sender": "human_intervention"}

    workflow.add_node(AgentNames.HUMAN, human_node)

    # ── 设置入口 ──
    workflow.set_entry_point(AgentNames.PM)

    # ── 标准边 ──
    workflow.add_edge(AgentNames.PM, AgentNames.REVIEWER)
    workflow.add_edge(AgentNames.ARCHITECT, AgentNames.REVIEWER)

    # ── 条件边 ──
    workflow.add_conditional_edges(
        AgentNames.REVIEWER,
        review_router,
        {
            AgentNames.PM: AgentNames.PM,
            AgentNames.ARCHITECT: AgentNames.ARCHITECT,
            AgentNames.DESIGN: END,  # Phase 4 尚未实现，先结束
            "__end__": END,
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

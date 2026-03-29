"""Multi-Agent 编排器 — LangGraph 图构建与条件路由"""
from __future__ import annotations

import logging

from src.config import settings
from src.models.state import AgentState
from src.models.agent_models import ReviewFeedback
from src.agents.factory import get_revision_count

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


# ── 阶段注册表 ──────────────────────────────────────
# 每个阶段定义：当前 Agent、审查的产出物字段、被拒后重做的 Agent、通过后下一 Agent
# 路由器按产出物判断当前阶段，查找此表决定去向

class StageRegistry:
    """
    阶段注册表 — 新增 Agent 只需在此注册一行

    每条记录:
      agent:       负责产出的 Agent 名称
      artifact:    产出物在 state 中的 key
      next_agent:  APPROVED 后流转到哪个 Agent（"__end__" 表示结束）
    """
    stages = [
        {
            "agent": AgentNames.PM,
            "artifact": "prd",
            "next_agent": AgentNames.ARCHITECT,
        },
        {
            "agent": AgentNames.ARCHITECT,
            "artifact": "trd",
            "next_agent": AgentNames.DESIGN,
        },
        {
            "agent": AgentNames.DESIGN,
            "artifact": "design_doc",
            "next_agent": "__end__",
        },
    ]

    @classmethod
    def find_stage(cls, state: AgentState) -> dict | None:
        """根据 state 中存在的产出物判断当前阶段（从后往前匹配最新的）"""
        for stage in reversed(cls.stages):
            if state.get(stage["artifact"]) is not None:
                return stage
        return None

    @classmethod
    def find_next_stage(cls, agent_name: str) -> dict | None:
        """查找某 Agent 通过后的下一阶段配置"""
        for i, stage in enumerate(cls.stages):
            if stage["agent"] == agent_name and i + 1 < len(cls.stages):
                return cls.stages[i + 1]
        return None


# ── 路由函数 ──────────────────────────────────────

def review_router(state: AgentState) -> str:
    """
    Reviewer 节点后的条件路由

    决策逻辑：
    1. 找到当前阶段（通过产出物判断）
    2. 无审查结果 → 打回当前 Agent 重做
    3. APPROVED → 流转下一阶段
    4. REJECTED + 超过最大重试次数 → 人工干预
    5. REJECTED + 还有机会 → 打回当前 Agent 重做
    """
    latest_review: ReviewFeedback | None = state.get("latest_review")
    max_revisions = getattr(settings, "MAX_REVISION_COUNT", 3)

    stage = StageRegistry.find_stage(state)

    if not stage:
        logger.warning("[Router] No artifact found, routing back to PM")
        return AgentNames.PM

    current_agent = stage["agent"]
    next_agent = stage["next_agent"]
    revision_count = get_revision_count(state, current_agent)

    if not latest_review:
        logger.warning("[Router] No review result, routing back to %s", current_agent)
        return current_agent

    if latest_review.status == "APPROVED":
        logger.info(f"✅ [Router] Review approved, proceeding from {current_agent} → {next_agent}")
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

    Phase 4 流程：
        PM → Reviewer → Architect → Reviewer → Design → Reviewer → END
        (每个 Agent 后 REJECTED 可循环，超过 max 次进 Human)
    """
    from langgraph.graph import StateGraph, END
    from langgraph.checkpoint.memory import MemorySaver

    from src.agents.nodes.pm_node import pm_node
    from src.agents.nodes.reviewer_node import reviewer_node
    from src.agents.nodes.architect_node import architect_node
    from src.agents.nodes.design_node import design_node

    workflow = StateGraph(AgentState)

    # ── 注册节点 ──
    workflow.add_node(AgentNames.PM, pm_node)
    workflow.add_node(AgentNames.REVIEWER, reviewer_node)
    workflow.add_node(AgentNames.ARCHITECT, architect_node)
    workflow.add_node(AgentNames.DESIGN, design_node)

    # 人工干预节点（占位）
    async def human_node(state: AgentState) -> dict:
        logger.warning("[Human] Manual intervention required")
        return {"sender": "human_intervention"}

    workflow.add_node(AgentNames.HUMAN, human_node)

    # ── 设置入口 ──
    workflow.set_entry_point(AgentNames.PM)

    # ── 标准边：产出 → Reviewer ──
    workflow.add_edge(AgentNames.PM, AgentNames.REVIEWER)
    workflow.add_edge(AgentNames.ARCHITECT, AgentNames.REVIEWER)
    workflow.add_edge(AgentNames.DESIGN, AgentNames.REVIEWER)

    # ── 条件边：Reviewer → 根据 review_router 路由 ──
    workflow.add_conditional_edges(
        AgentNames.REVIEWER,
        review_router,
        {
            AgentNames.PM: AgentNames.PM,
            AgentNames.ARCHITECT: AgentNames.ARCHITECT,
            AgentNames.DESIGN: AgentNames.DESIGN,
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

"""
工作流引擎 - 执行自定义工作流配置
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional

from langchain_core.messages import AIMessage

from src.models.workflow import (
    ExecutionMode,
    WorkflowConfig,
    WorkflowStage,
    AgentNodeConfig,
    ReviewConfig,
)
from src.models.state import AgentState
from src.utils.logger import setup_logger

logger = setup_logger("workflow_engine")


class WorkflowEngine:
    """工作流引擎 - 执行自定义工作流"""

    def __init__(self, workflow_config: WorkflowConfig):
        """
        初始化工作流引擎

        Args:
            workflow_config: 工作流配置
        """
        self.config = workflow_config
        self.current_stage_index = 0
        self.execution_history: List[Dict[str, Any]] = []

        # Agent 导入缓存
        self._agent_cache: Dict[str, Any] = {}

    def _get_agent_instance(self, agent_name: str):
        """获取 Agent 实例（带缓存）"""
        if agent_name not in self._agent_cache:
            # 动态导入 Agent
            agent_map = {
                "pm_agent": ("src.agents.nodes.pm_node", "get_pm_agent"),
                "architect_agent": ("src.agents.nodes.architect_node", "get_architect_agent"),
                "design_agent": ("src.agents.nodes.design_node", "get_design_agent"),
                "backend_dev_agent": ("src.agents.nodes.backend_dev_node", "get_backend_dev_agent"),
                "frontend_dev_agent": ("src.agents.nodes.frontend_dev_node", "get_frontend_dev_agent"),
                "qa_agent": ("src.agents.nodes.qa_node", "get_qa_agent"),
                "reviewer_agent": ("src.agents.nodes.reviewer_node", "get_reviewer_agent"),
            }

            if agent_name not in agent_map:
                raise ValueError(f"Unknown agent: {agent_name}")

            module_path, func_name = agent_map[agent_name]
            module = __import__(module_path, fromlist=[func_name])
            get_agent_func = getattr(module, func_name)
            self._agent_cache[agent_name] = get_agent_func()

        return self._agent_cache[agent_name]

    async def execute_stage(
        self,
        stage: WorkflowStage,
        state: AgentState,
    ) -> AgentState:
        """
        执行单个阶段

        Args:
            stage: 工作流阶段
            state: Agent 状态

        Returns:
            更新后的状态
        """
        logger.info(f"🎯 执行阶段: {stage.name}")
        logger.info(f"   执行模式: {stage.mode.value}")
        logger.info(f"   Agent 数量: {len(stage.agents)}")

        # 过滤跳过的 Agent
        active_agents = [agent for agent in stage.agents if agent.enabled and agent.name not in self.config.skip_agents]

        if not active_agents:
            logger.warning(f"⚠️  阶段 {stage.name} 没有启用的 Agent，跳过")
            return state

        # 根据执行模式执行
        if stage.mode == ExecutionMode.SEQUENTIAL:
            state = await self._execute_sequential(active_agents, state, stage.review)
        elif stage.mode == ExecutionMode.PARALLEL:
            state = await self._execute_parallel(active_agents, state, stage.review)
        elif stage.mode == ExecutionMode.CONDITIONAL:
            state = await self._execute_conditional(stage, state)

        # 记录执行历史
        self.execution_history.append({
            "stage": stage.name,
            "agents": [agent.name for agent in active_agents],
            "mode": stage.mode.value,
            "success": True,
        })

        return state

    async def _execute_sequential(
        self,
        agents: List[AgentNodeConfig],
        state: AgentState,
        review_config: ReviewConfig,
    ) -> AgentState:
        """顺序执行 Agents"""
        for agent_config in agents:
            logger.info(f"   → 执行 Agent: {agent_config.name}")
            state = await self._execute_single_agent(agent_config, state, review_config)

        return state

    async def _execute_parallel(
        self,
        agents: List[AgentNodeConfig],
        state: AgentState,
        review_config: ReviewConfig,
    ) -> AgentState:
        """并行执行 Agents"""
        logger.info(f"   → 并行执行 {len(agents)} 个 Agents")

        # 创建并发任务
        tasks = [
            self._execute_single_agent(agent, state.copy(), review_config)
            for agent in agents
        ]

        # 等待所有任务完成
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 合并结果
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"   ❌ Agent {agents[i].name} 执行失败: {result}")
            elif isinstance(result, dict):
                # 更新状态
                state.update(result)

        return state

    async def _execute_conditional(
        self,
        stage: WorkflowStage,
        state: AgentState,
    ) -> AgentState:
        """条件执行"""
        if not stage.conditions:
            logger.warning("⚠️  条件执行模式但未配置条件规则")
            return state

        for rule in stage.conditions:
            if self._evaluate_condition(rule, state):
                logger.info(f"   ✓ 条件满足，执行 then 分支: {rule.then_branch}")
                for agent_name in rule.then_branch:
                    agent_config = AgentNodeConfig(name=agent_name)
                    state = await self._execute_single_agent(agent_config, state, stage.review)
            else:
                if rule.else_branch:
                    logger.info(f"   ✗ 条件不满足，执行 else 分支: {rule.else_branch}")
                    for agent_name in rule.else_branch:
                        agent_config = AgentNodeConfig(name=agent_name)
                        state = await self._execute_single_agent(agent_config, state, stage.review)

        return state

    async def _execute_single_agent(
        self,
        agent_config: AgentNodeConfig,
        state: AgentState,
        review_config: ReviewConfig,
    ) -> AgentState:
        """执行单个 Agent"""
        try:
            # 获取 Agent 实例
            agent = self._get_agent_instance(agent_config.name)

            # 执行 Agent
            result = await agent.run(state)

            # 如果启用审查
            if review_config.enabled and review_config.strategy != "skip":
                result = await self._review_agent_output(
                    agent_config.name,
                    result,
                    state,
                    review_config,
                )

            return result

        except Exception as e:
            logger.error(f"❌ Agent {agent_config.name} 执行失败: {e}")
            if agent_config.retry_on_failure:
                logger.info(f"🔄 重试 Agent {agent_config.name}")
                # TODO: 实现重试逻辑
            raise

    async def _review_agent_output(
        self,
        agent_name: str,
        result: Dict[str, Any],
        state: AgentState,
        review_config: ReviewConfig,
    ) -> Dict[str, Any]:
        """审查 Agent 输出"""
        logger.info(f"   🔍 审查 {agent_name} 的输出")

        # 获取审查员 Agent
        reviewer_name = review_config.reviewer or "reviewer_agent"
        reviewer = self._get_agent_instance(reviewer_name)

        # 执行审查
        review_result = await reviewer.review(
            agent_name=agent_name,
            artifact=result,
            state=state,
        )

        # 如果审查通过
        if review_result.get("status") == "APPROVED":
            logger.info(f"   ✅ {agent_name} 审查通过")
            return result

        # 如果需要自动修复
        if review_config.auto_fix and review_config.strategy == "auto":
            logger.info(f"   🔧 自动修复 {agent_name} 的输出")

            for attempt in range(review_config.max_fix_attempts):
                # 重新执行 Agent（带有审查反馈）
                agent = self._get_agent_instance(agent_name)
                result = await agent.run_with_feedback(
                    state=state,
                    feedback=review_result.get("comments", ""),
                )

                # 重新审查
                review_result = await reviewer.review(
                    agent_name=agent_name,
                    artifact=result,
                    state=state,
                )

                if review_result.get("status") == "APPROVED":
                    logger.info(f"   ✅ 修复后审查通过（尝试 {attempt + 1} 次）")
                    return result

            logger.warning(f"   ⚠️  达到最大修复次数（{review_config.max_fix_attempts}）")

        return result

    def _evaluate_condition(self, rule, state: AgentState) -> bool:
        """评估条件规则"""
        field_value = state.get(rule.field)

        if rule.operator == "eq":
            return field_value == rule.value
        elif rule.operator == "ne":
            return field_value != rule.value
        elif rule.operator == "gt":
            return isinstance(field_value, (int, float)) and field_value > rule.value
        elif rule.operator == "lt":
            return isinstance(field_value, (int, float)) and field_value < rule.value
        elif rule.operator == "contains":
            return rule.value in str(field_value)
        elif rule.operator == "regex":
            import re
            return bool(re.search(rule.value, str(field_value)))

        return False

    async def execute(
        self,
        initial_state: AgentState,
        stop_at_stage: Optional[str] = None,
    ) -> AgentState:
        """
        执行完整工作流

        Args:
            initial_state: 初始状态
            stop_at_stage: 停止阶段（用于调试）

        Returns:
            最终状态
        """
        logger.info(f"🚀 开始执行工作流: {self.config.name}")
        logger.info(f"   阶段数量: {len(self.config.stages)}")
        logger.info(f"   跳过的 Agents: {self.config.skip_agents}")

        state = initial_state

        for i, stage in enumerate(self.config.stages):
            self.current_stage_index = i

            # 检查是否需要停止
            if stop_at_stage and stage.name == stop_at_stage:
                logger.info(f"⏸️  在阶段 {stage.name} 停止")
                break

            # 执行阶段
            try:
                state = await self.execute_stage(stage, state)
                logger.info(f"✅ 阶段 {stage.name} 完成")
            except Exception as e:
                logger.error(f"❌ 阶段 {stage.name} 失败: {e}")
                raise

        logger.info(f"🎉 工作流执行完成")
        logger.info(f"   执行的阶段数: {len(self.execution_history)}")

        return state

    def get_execution_summary(self) -> Dict[str, Any]:
        """获取执行摘要"""
        return {
            "workflow_name": self.config.name,
            "total_stages": len(self.config.stages),
            "completed_stages": len(self.execution_history),
            "execution_history": self.execution_history,
            "skipped_agents": self.config.skip_agents,
        }


__all__ = ["WorkflowEngine"]

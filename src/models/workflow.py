"""
工作流配置模型 - 支持自定义 Agent 执行链路
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class ExecutionMode(str, Enum):
    """执行模式"""
    SEQUENTIAL = "sequential"  # 顺序执行
    PARALLEL = "parallel"      # 并行执行
    CONDITIONAL = "conditional"  # 条件执行


class AgentNodeConfig(BaseModel):
    """Agent 节点配置"""
    name: str = Field(..., description="Agent 名称")
    enabled: bool = Field(default=True, description="是否启用")
    max_revisions: int = Field(default=3, description="最大修改次数")
    timeout: int = Field(default=300, description="超时时间（秒）")
    retry_on_failure: bool = Field(default=True, description="失败时是否重试")
    custom_prompt: Optional[str] = Field(None, description="自定义提示词")


class ReviewStrategy(str, Enum):
    """审查策略"""
    AUTO = "auto"  # 自动审查
    MANUAL = "manual"  # 人工审查
    SKIP = "skip"  # 跳过审查
    CONDITIONAL = "conditional"  # 条件审查


class ReviewConfig(BaseModel):
    """审查配置"""
    enabled: bool = Field(default=True, description="是否启用审查")
    strategy: ReviewStrategy = Field(default=ReviewStrategy.AUTO, description="审查策略")
    reviewer: Optional[str] = Field(None, description="指定审查员 Agent")
    auto_fix: bool = Field(default=True, description="是否自动修复")
    max_fix_attempts: int = Field(default=3, description="最大修复次数")


class ConditionalRule(BaseModel):
    """条件规则"""
    field: str = Field(..., description="判断字段")
    operator: str = Field(..., description="操作符: eq, ne, gt, lt, contains, regex")
    value: Any = Field(..., description="比较值")
    then_branch: List[str] = Field(..., description="满足条件时执行的 Agent 列表")
    else_branch: List[str] = Field(default_factory=list, description="不满足条件时执行的 Agent 列表")


class WorkflowStage(BaseModel):
    """工作流阶段"""
    name: str = Field(..., description="阶段名称")
    agents: List[AgentNodeConfig] = Field(..., description="Agent 列表")
    mode: ExecutionMode = Field(default=ExecutionMode.SEQUENTIAL, description="执行模式")
    review: ReviewConfig = Field(default_factory=ReviewConfig, description="审查配置")
    conditions: Optional[List[ConditionalRule]] = Field(None, description="条件规则")
    parallel_group: Optional[str] = Field(None, description="并行组名称（用于并行执行）")


class WorkflowConfig(BaseModel):
    """工作流配置"""
    name: str = Field(..., description="工作流名称")
    description: Optional[str] = Field(None, description="工作流描述")
    version: str = Field(default="1.0.0", description="配置版本")
    stages: List[WorkflowStage] = Field(..., description="阶段列表")
    global_settings: Dict[str, Any] = Field(default_factory=dict, description="全局设置")

    # 并行执行配置
    parallel_stages: Optional[Dict[str, List[str]]] = Field(
        None,
        description="并行阶段配置 {group_name: [stage_names]}"
    )

    # 跳过配置
    skip_agents: List[str] = Field(default_factory=list, description="跳过的 Agent 列表")

    # 条件跳过
    skip_conditions: Optional[List[ConditionalRule]] = Field(
        None,
        description="条件跳过规则"
    )


# 预定义工作流模板

class WorkflowTemplates:
    """预定义工作流模板"""

    @staticmethod
    def full_pipeline() -> WorkflowConfig:
        """完整流水线 - 所有 Agent 顺序执行"""
        return WorkflowConfig(
            name="full_pipeline",
            description="完整的软件开发流水线",
            stages=[
                WorkflowStage(
                    name="requirements",
                    agents=[AgentNodeConfig(name="pm_agent")],
                    review=ReviewConfig(strategy=ReviewStrategy.AUTO),
                ),
                WorkflowStage(
                    name="architecture",
                    agents=[AgentNodeConfig(name="architect_agent")],
                    review=ReviewConfig(strategy=ReviewStrategy.AUTO),
                ),
                WorkflowStage(
                    name="design",
                    agents=[AgentNodeConfig(name="design_agent")],
                    review=ReviewConfig(strategy=ReviewStrategy.AUTO),
                ),
                WorkflowStage(
                    name="development",
                    agents=[
                        AgentNodeConfig(name="backend_dev_agent"),
                        AgentNodeConfig(name="frontend_dev_agent"),
                    ],
                    mode=ExecutionMode.PARALLEL,
                    parallel_group="dev_group",
                    review=ReviewConfig(strategy=ReviewStrategy.AUTO),
                ),
                WorkflowStage(
                    name="testing",
                    agents=[AgentNodeConfig(name="qa_agent")],
                    review=ReviewConfig(strategy=ReviewStrategy.AUTO),
                ),
            ],
        )

    @staticmethod
    def rapid_prototype() -> WorkflowConfig:
        """快速原型 - 精简流程"""
        return WorkflowConfig(
            name="rapid_prototype",
            description="快速原型开发流程",
            stages=[
                WorkflowStage(
                    name="quick_design",
                    agents=[
                        AgentNodeConfig(name="pm_agent"),
                        AgentNodeConfig(name="architect_agent"),
                    ],
                    mode=ExecutionMode.SEQUENTIAL,
                    review=ReviewConfig(strategy=ReviewStrategy.SKIP),
                ),
                WorkflowStage(
                    name="quick_dev",
                    agents=[
                        AgentNodeConfig(name="backend_dev_agent"),
                        AgentNodeConfig(name="frontend_dev_agent"),
                    ],
                    mode=ExecutionMode.PARALLEL,
                    review=ReviewConfig(strategy=ReviewStrategy.SKIP),
                ),
            ],
        )

    @staticmethod
    def design_only() -> WorkflowConfig:
        """仅设计 - 只有设计和架构"""
        return WorkflowConfig(
            name="design_only",
            description="仅包含设计阶段的流程",
            stages=[
                WorkflowStage(
                    name="product_design",
                    agents=[AgentNodeConfig(name="pm_agent")],
                    review=ReviewConfig(strategy=ReviewStrategy.AUTO),
                ),
                WorkflowStage(
                    name="technical_design",
                    agents=[AgentNodeConfig(name="architect_agent")],
                    review=ReviewConfig(strategy=ReviewStrategy.AUTO),
                ),
                WorkflowStage(
                    name="ui_design",
                    agents=[AgentNodeConfig(name="design_agent")],
                    review=ReviewConfig(strategy=ReviewStrategy.AUTO),
                ),
            ],
        )

    @staticmethod
    def backend_only() -> WorkflowConfig:
        """仅后端 - 后端开发流程"""
        return WorkflowConfig(
            name="backend_only",
            description="仅后端开发流程",
            stages=[
                WorkflowStage(
                    name="backend_analysis",
                    agents=[AgentNodeConfig(name="pm_agent")],
                    review=ReviewConfig(strategy=ReviewStrategy.AUTO),
                ),
                WorkflowStage(
                    name="backend_arch",
                    agents=[AgentNodeConfig(name="architect_agent")],
                    review=ReviewConfig(strategy=ReviewStrategy.AUTO),
                ),
                WorkflowStage(
                    name="backend_dev",
                    agents=[AgentNodeConfig(name="backend_dev_agent")],
                    review=ReviewConfig(strategy=ReviewStrategy.AUTO),
                ),
            ],
        )

    @staticmethod
    def frontend_only() -> WorkflowConfig:
        """仅前端 - 前端开发流程"""
        return WorkflowConfig(
            name="frontend_only",
            description="仅前端开发流程",
            stages=[
                WorkflowStage(
                    name="frontend_analysis",
                    agents=[AgentNodeConfig(name="pm_agent")],
                    review=ReviewConfig(strategy=ReviewStrategy.AUTO),
                ),
                WorkflowStage(
                    name="ui_design",
                    agents=[AgentNodeConfig(name="design_agent")],
                    review=ReviewConfig(strategy=ReviewStrategy.AUTO),
                ),
                WorkflowStage(
                    name="frontend_dev",
                    agents=[AgentNodeConfig(name="frontend_dev_agent")],
                    review=ReviewConfig(strategy=ReviewStrategy.AUTO),
                ),
            ],
        )

    @staticmethod
    def custom(agents: List[str], parallel: bool = False) -> WorkflowConfig:
        """自定义工作流"""
        agent_configs = [AgentNodeConfig(name=agent) for agent in agents]
        mode = ExecutionMode.PARALLEL if parallel else ExecutionMode.SEQUENTIAL

        return WorkflowConfig(
            name="custom",
            description="自定义工作流",
            stages=[
                WorkflowStage(
                    name="custom_stage",
                    agents=agent_configs,
                    mode=mode,
                    review=ReviewConfig(strategy=ReviewStrategy.AUTO),
                ),
            ],
        )


__all__ = [
    "ExecutionMode",
    "AgentNodeConfig",
    "ReviewStrategy",
    "ReviewConfig",
    "ConditionalRule",
    "WorkflowStage",
    "WorkflowConfig",
    "WorkflowTemplates",
]

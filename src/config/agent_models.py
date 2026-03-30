"""
Agent 模型配置 - 支持不同 Agent 使用不同模型
"""
from __future__ import annotations

from typing import Dict, Optional


class AgentModelConfig:
    """Agent 模型配置管理"""

    # 所有 Agent 列表
    ALL_AGENTS = [
        "pm_agent",
        "architect_agent",
        "design_agent",
        "backend_dev_agent",
        "frontend_dev_agent",
        "qa_agent",
        "reviewer_agent",
    ]

    def __init__(self, model_mapping: Dict[str, str], default_model: str):
        """
        初始化模型配置

        Args:
            model_mapping: Agent 名称到模型名称的映射
            default_model: 默认模型（当 Agent 未配置时使用）
        """
        self.model_mapping = model_mapping
        self.default_model = default_model

    def get_model_for_agent(self, agent_name: str) -> str:
        """
        获取指定 Agent 使用的模型

        Args:
            agent_name: Agent 名称

        Returns:
            模型名称
        """
        return self.model_mapping.get(agent_name, self.default_model)

    def get_all_models(self) -> set[str]:
        """获取所有配置的模型集合"""
        models = set(self.model_mapping.values())
        models.add(self.default_model)
        return models

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "default_model": self.default_model,
            "agent_models": self.model_mapping,
        }


def parse_agent_model_config(
    default_model: str,
    pm_model: Optional[str] = None,
    architect_model: Optional[str] = None,
    design_model: Optional[str] = None,
    backend_dev_model: Optional[str] = None,
    frontend_dev_model: Optional[str] = None,
    qa_model: Optional[str] = None,
    reviewer_model: Optional[str] = None,
) -> AgentModelConfig:
    """
    从环境变量或参数创建 AgentModelConfig

    Args:
        default_model: 默认模型
        pm_model: PM Agent 使用的模型
        architect_model: Architect Agent 使用的模型
        design_model: Design Agent 使用的模型
        backend_dev_model: Backend Dev Agent 使用的模型
        frontend_dev_model: Frontend Dev Agent 使用的模型
        qa_model: QA Agent 使用的模型
        reviewer_model: Reviewer Agent 使用的模型

    Returns:
        AgentModelConfig 实例
    """
    model_mapping = {}

    # 只配置非 None 的值
    if pm_model:
        model_mapping["pm_agent"] = pm_model
    if architect_model:
        model_mapping["architect_agent"] = architect_model
    if design_model:
        model_mapping["design_agent"] = design_model
    if backend_dev_model:
        model_mapping["backend_dev_agent"] = backend_dev_model
    if frontend_dev_model:
        model_mapping["frontend_dev_agent"] = frontend_dev_model
    if qa_model:
        model_mapping["qa_agent"] = qa_model
    if reviewer_model:
        model_mapping["reviewer_agent"] = reviewer_model

    return AgentModelConfig(
        model_mapping=model_mapping,
        default_model=default_model,
    )


__all__ = [
    "AgentModelConfig",
    "parse_agent_model_config",
]

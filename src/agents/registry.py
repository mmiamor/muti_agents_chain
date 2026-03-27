"""Agent 注册表 — 统一管理所有 Agent"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.agents.base import BaseAgent


class AgentRegistry:
    """全局 Agent 注册表"""
    _agents: dict[str, type["BaseAgent"]] = {}

    @classmethod
    def register(cls, agent_class: type["BaseAgent"]) -> None:
        """注册 Agent 类"""
        if not hasattr(agent_class, "name"):
            raise ValueError(f"Agent class {agent_class.__name__} must have a 'name' attribute")
        cls._agents[agent_class.name] = agent_class

    @classmethod
    def get(cls, name: str) -> type["BaseAgent"]:
        """获取已注册的 Agent 类"""
        if name not in cls._agents:
            raise KeyError(
                f"Agent '{name}' not registered. "
                f"Available: {list(cls._agents.keys())}"
            )
        return cls._agents[name]

    @classmethod
    def list_agents(cls) -> list[str]:
        """列出所有已注册的 Agent 名称"""
        return list(cls._agents.keys())

    @classmethod
    def clear(cls) -> None:
        """清空注册表（主要用于测试）"""
        cls._agents.clear()

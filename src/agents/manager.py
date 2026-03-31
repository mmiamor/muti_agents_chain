"""
Agent 单例管理器 - 确保每个 Agent 只创建一次
"""
from __future__ import annotations

from typing import TypeVar, Type, Callable, Any

T = TypeVar('T')


class AgentManager:
    """
    Agent 单例管理器

    确保每个 Agent 只创建一次，避免重复初始化
    """

    _instances: dict[str, Any] = {}
    _factories: dict[str, Callable[[], Any]] = {}

    @classmethod
    def register(cls, name: str, factory: Callable[[], T]) -> None:
        """
        注册 Agent 工厂函数

        Args:
            name: Agent 名称
            factory: 工厂函数
        """
        cls._factories[name] = factory

    @classmethod
    def get(cls, name: str) -> Any:
        """
        获取 Agent 实例（单例）

        Args:
            name: Agent 名称

        Returns:
            Agent 实例
        """
        if name not in cls._instances:
            if name not in cls._factories:
                raise ValueError(f"Agent '{name}' not registered")
            cls._instances[name] = cls._factories[name]()

        return cls._instances[name]

    @classmethod
    def clear(cls) -> None:
        """清除所有实例（主要用于测试）"""
        cls._instances.clear()

    @classmethod
    def create_getter(cls, name: str, agent_class: Type[T]) -> Callable[[], T]:
        """
        创建一个 getter 函数

        Args:
            name: Agent 名称
            agent_class: Agent 类

        Returns:
            返回 Agent 实例的函数
        """
        def getter() -> T:
            return cls.get(name)

        # 注册工厂
        cls.register(name, agent_class)

        return getter


def get_agent_singleton(agent_class: Type[T], instance_var_name: str) -> Callable[[], T]:
    """
    创建单例获取函数的便捷方法

    Args:
        agent_class: Agent 类
        instance_var_name: 实例变量名（用于缓存）

    Returns:
        返回单例的函数
    """
    _instance = None

    def get_instance() -> T:
        nonlocal _instance
        if _instance is None:
            _instance = agent_class()
        return _instance

    return get_instance


__all__ = ["AgentManager", "get_agent_singleton"]

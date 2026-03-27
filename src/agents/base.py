"""Agent 基类 — 所有 Agent 必须继承"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.models.state import AgentState


class BaseAgent(ABC):
    """
    Agent 基类

    每个 Agent 必须：
    1. 声明 name 和 role
    2. 实现 run() — 核心执行逻辑，返回 State 更新字典
    3. 实现 review() — 自我反思，检查输出质量
    """
    name: str
    role: str
    description: str = ""

    @abstractmethod
    async def run(self, state: "AgentState") -> dict:
        """
        核心执行方法

        接收当前 State，返回需要更新的 State 字典。
        LangGraph 会自动将返回值 merge 到全局 State。
        """
        ...

    @abstractmethod
    async def review(self, state: "AgentState") -> bool:
        """
        自我反思 — 检查上一次 run 的输出质量

        Returns:
            True 表示通过，False 表示需要重做
        """
        ...

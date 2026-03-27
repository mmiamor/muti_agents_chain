"""Agent 上下文对象 — 封装依赖注入"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from src.services.llm_service import LLMService


@dataclass
class AgentContext:
    """Agent 执行上下文，封装所有外部依赖"""
    llm: "LLMService"
    memory: Optional[Any] = None
    config: dict[str, Any] = field(default_factory=dict)

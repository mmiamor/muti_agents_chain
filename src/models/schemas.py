"""
Pydantic 数据模型
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ChainType(str, Enum):
    """Chain 类型"""
    SIMPLE = "simple"           # 单步调用
    SEQUENTIAL = "sequential"   # 顺序链
    PARALLEL = "parallel"       # 并行链
    CONDITIONAL = "conditional" # 条件链
    LOOP = "loop"               # 循环链


class MessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class ChatMessage(BaseModel):
    """聊天消息"""
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class LLMRequest(BaseModel):
    """LLM 请求"""
    model: str = "glm-5"
    messages: list[ChatMessage] = Field(default_factory=list)
    temperature: float = Field(default=0.7, ge=0, le=2)
    max_tokens: Optional[int] = None
    stream: bool = False
    tools: Optional[list[dict[str, Any]]] = None          # OpenAI 格式工具列表
    tool_choice: Optional[str | dict[str, Any]] = None    # "auto" / "none" / specific function


class LLMResponse(BaseModel):
    """LLM 响应"""
    content: str
    model: str
    usage: dict[str, int] = Field(default_factory=dict)
    finish_reason: str = "stop"
    latency_ms: float = 0.0


class TaskResult(BaseModel):
    """任务结果"""
    task_id: str
    status: TaskStatus
    result: Any = None
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    finished_at: Optional[datetime] = None


class ChainConfig(BaseModel):
    """Chain 配置"""
    name: str
    chain_type: ChainType = ChainType.SEQUENTIAL
    steps: list[dict[str, Any]] = Field(default_factory=list)
    retry_count: int = Field(default=3, ge=0)
    timeout: float = Field(default=60.0, gt=0)

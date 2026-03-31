"""
优化的状态定义 - 使用 Pydantic 提高性能和类型安全
"""
from __future__ import annotations

from enum import Enum
from typing import Optional, Any
from datetime import datetime

from pydantic import BaseModel, Field, field_validator
from langchain_core.messages import BaseMessage

from src.models.document_models import PRD, TRD, DesignDocument, BackendCodeSpec, FrontendCodeSpec, QAReport
from src.models.agent_models import ReviewFeedback


class AgentPhase(str, Enum):
    """开发阶段"""
    REQUIREMENT_GATHERING = "requirement_gathering"
    ARCHITECTURE_DESIGN = "architecture_design"
    UI_DESIGN = "ui_design"
    CODING = "coding"
    TESTING = "testing"
    FINISHED = "finished"


class ArtifactMetadata(BaseModel):
    """
    产出物元数据

    跟踪产出物的创建和修改历史
    """
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    revision_count: int = 0
    created_by: str = ""
    version: str = "1.0"

    def touch(self, agent_name: str) -> None:
        """更新元数据"""
        self.updated_at = datetime.now()
        self.revision_count += 1
        self.created_by = agent_name


class OptimizedAgentState(BaseModel):
    """
    优化的 Agent 状态模型

    使用 Pydantic 提供:
    - 更好的类型安全
    - 更快的访问速度
    - 自动验证
    - 内置序列化
    """
    # 消息历史（注意：BaseMessage 不是 Pydantic 模型，使用 Any）
    messages: list[BaseMessage] = Field(default_factory=list)

    # 当前阶段
    current_phase: AgentPhase = AgentPhase.REQUIREMENT_GATHERING

    # 上一个发送消息的 Agent 名称
    sender: str = "user"

    # 核心产出物（使用 Optional 避免内存浪费）
    prd: Optional[PRD] = None
    trd: Optional[TRD] = None
    design_doc: Optional[DesignDocument] = None
    backend_code: Optional[BackendCodeSpec] = None
    frontend_code: Optional[FrontendCodeSpec] = None
    qa_report: Optional[QAReport] = None

    # 产出物元数据
    prd_metadata: Optional[ArtifactMetadata] = None
    trd_metadata: Optional[ArtifactMetadata] = None
    design_doc_metadata: Optional[ArtifactMetadata] = None
    backend_code_metadata: Optional[ArtifactMetadata] = None
    frontend_code_metadata: Optional[ArtifactMetadata] = None
    qa_report_metadata: Optional[ArtifactMetadata] = None

    # 审查状态
    latest_review: Optional[ReviewFeedback] = None
    revision_counts: dict[str, int] = Field(default_factory=dict)

    # 性能统计
    total_tokens_used: int = 0
    total_llm_calls: int = 0
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None

    class Config:
        """Pydantic 配置"""
        arbitrary_types_allowed = True  # 允许 BaseMessage 类型
        use_enum_values = True

    def get_artifact(self, artifact_key: str) -> Optional[Any]:
        """
        获取产出物

        Args:
            artifact_key: 产出物键名（如 "prd", "trd"）

        Returns:
            产出物对象或 None
        """
        return getattr(self, artifact_key, None)

    def set_artifact(self, artifact_key: str, artifact: Any, agent_name: str) -> None:
        """
        设置产出物

        Args:
            artifact_key: 产出物键名
            artifact: 产出物对象
            agent_name: 设置的 Agent 名称
        """
        setattr(self, artifact_key, artifact)

        # 更新元数据
        metadata_key = f"{artifact_key}_metadata"
        metadata = getattr(self, metadata_key, None)
        if metadata is None:
            metadata = ArtifactMetadata(created_by=agent_name)
            setattr(self, metadata_key, metadata)
        else:
            metadata.touch(agent_name)

    def get_artifact_metadata(self, artifact_key: str) -> Optional[ArtifactMetadata]:
        """获取产出物元数据"""
        metadata_key = f"{artifact_key}_metadata"
        return getattr(self, metadata_key, None)

    def increment_revision_count(self, agent_name: str) -> int:
        """
        增加 Agent 的修订计数

        Args:
            agent_name: Agent 名称

        Returns:
            新的修订计数
        """
        self.revision_counts[agent_name] = self.revision_counts.get(agent_name, 0) + 1
        return self.revision_counts[agent_name]

    def get_revision_count(self, agent_name: str) -> int:
        """获取 Agent 的修订计数"""
        return self.revision_counts.get(agent_name, 0)

    def add_tokens(self, token_count: int) -> None:
        """添加 token 使用量"""
        self.total_tokens_used += token_count

    def increment_llm_calls(self) -> None:
        """增加 LLM 调用次数"""
        self.total_llm_calls += 1

    def mark_finished(self) -> None:
        """标记流程完成"""
        self.end_time = datetime.now()
        self.current_phase = AgentPhase.FINISHED

    def get_duration_seconds(self) -> float:
        """获取流程持续时间（秒）"""
        end = self.end_time or datetime.now()
        return (end - self.start_time).total_seconds()

    def to_dict(self) -> dict[str, Any]:
        """
        转换为字典（用于序列化）

        Returns:
            dict: 状态字典
        """
        return self.model_dump(exclude_none=True)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OptimizedAgentState":
        """
        从字典创建实例（用于反序列化）

        Args:
            data: 状态字典

        Returns:
            OptimizedAgentState 实例
        """
        return cls(**data)


# 为了向后兼容，保留旧的 TypedDict 版本
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages


class AgentState(TypedDict, total=False):
    """
    Legacy Agent State - 保持向后兼容

    新代码应使用 OptimizedAgentState
    """
    messages: list[BaseMessage]  # 注意：旧版本没有使用 reducer
    current_phase: AgentPhase
    sender: str
    prd: Optional[PRD]
    trd: Optional[TRD]
    design_doc: Optional[DesignDocument]
    backend_code: Optional[BackendCodeSpec]
    frontend_code: Optional[FrontendCodeSpec]
    qa_report: Optional[QAReport]
    latest_review: Optional[ReviewFeedback]
    revision_counts: dict[str, int]


__all__ = [
    "AgentPhase",
    "ArtifactMetadata",
    "OptimizedAgentState",
    "AgentState",
]

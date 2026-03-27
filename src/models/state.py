"""全局状态定义 — LangGraph StateGraph 共享黑板"""
from __future__ import annotations

from typing import Annotated, Optional
from enum import Enum
from typing_extensions import TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

from src.models.document_models import PRD, TRD
from src.models.agent_models import ReviewFeedback


class AgentPhase(str, Enum):
    """开发阶段"""
    REQUIREMENT_GATHERING = "requirement_gathering"
    ARCHITECTURE_DESIGN = "architecture_design"
    UI_DESIGN = "ui_design"
    CODING = "coding"
    TESTING = "testing"
    FINISHED = "finished"


class AgentState(TypedDict, total=False):
    """
    Multi-Agent 系统全局状态黑板

    - messages: 使用 add_messages reducer，新消息追加而非覆盖
    - artifacts: 独立于 messages，下游 Agent 直接读取结构化数据
    - review: 控制流转的「红绿灯」
    - revision_count: 防止死循环的「安全阀」
    """
    # 消息历史（追加式）
    messages: Annotated[list[BaseMessage], add_messages]

    # 当前阶段
    current_phase: AgentPhase

    # 上一个发送消息的 Agent 名称（用于路由判断）
    sender: str

    # 核心产出物
    prd: Optional[PRD]
    trd: Optional[TRD]

    # 审查状态
    latest_review: Optional[ReviewFeedback]
    revision_count: int

"""Agent 相关模型 — Review / Registry"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ReviewFeedback(BaseModel):
    """审查反馈"""
    status: Literal["APPROVED", "REJECTED"] = Field(description="审查结果")
    comments: str = Field(description="审查意见与修改建议")


class AgentInfo(BaseModel):
    """Agent 注册信息"""
    name: str = Field(description="Agent 标识名")
    role: str = Field(description="角色描述")
    description: str = Field(description="能力描述")
    input_schema: str = Field(description="输入模型类名")
    output_schema: str = Field(description="输出模型类名")

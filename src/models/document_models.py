"""核心交付物数据模型 — PRD / TRD"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


# ── PRD 相关 ─────────────────────────────────────────

class UserStory(BaseModel):
    """用户故事：作为...我想...以便..."""
    role: str = Field(description="用户角色，例如：普通用户、管理员")
    action: str = Field(description="想要执行的动作")
    benefit: str = Field(description="带来的核心价值")


class PRD(BaseModel):
    """产品需求文档"""
    vision: str = Field(description="产品核心愿景与一句话定位")
    target_audience: list[str] = Field(description="目标用户群体描述")
    user_stories: list[UserStory] = Field(description="核心用户故事列表")
    core_features: list[str] = Field(description="核心功能模块列表")
    non_functional: str = Field(description="非功能性需求（性能、可用性等）")
    mermaid_flowchart: str = Field(description="业务流程图的 Mermaid 语法代码")


# ── TRD 相关 ─────────────────────────────────────────

class TechStack(BaseModel):
    """技术栈选型"""
    frontend: str = Field(description="前端框架及核心库")
    backend: str = Field(description="后端框架及核心语言")
    database: str = Field(description="主数据库及缓存选型")
    infrastructure: str = Field(description="部署与运维设施")


class APIEndpoint(BaseModel):
    """API 接口定义"""
    path: str = Field(description="API 路径，例如：/api/v1/users")
    method: Literal["GET", "POST", "PUT", "DELETE", "PATCH"] = Field(description="HTTP 方法")
    description: str = Field(description="接口功能描述")


class TRD(BaseModel):
    """技术设计文档"""
    tech_stack: TechStack = Field(description="系统技术栈选型")
    architecture_overview: str = Field(description="高层架构设计说明")
    mermaid_er_diagram: str = Field(description="数据库 ER 图的 Mermaid 语法代码")
    api_endpoints: list[APIEndpoint] = Field(description="核心 API 接口列表")

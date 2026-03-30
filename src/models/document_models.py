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


# ── Design Doc 相关 ─────────────────────────────────

class DesignTokens(BaseModel):
    """设计 Token — 配色、字体、间距"""
    color_primary: str = Field(description="主色值，例如 #2563EB")
    color_secondary: str = Field(description="辅助色值，例如 #6366F1")
    font_family: str = Field(description="字体族，例如 Inter, system-ui")
    border_radius: str = Field(description="圆角，例如 8px")
    spacing_unit: str = Field(description="基础间距单位，例如 4px")


class PageSpec(BaseModel):
    """页面/组件规格"""
    page_name: str = Field(description="页面名称，例如：首页、个人中心")
    components: list[str] = Field(description="该页面包含的 UI 组件列表")
    description: str = Field(description="页面功能描述")
    mermaid_wireframe: str = Field(default="", description="页面线框图的 Mermaid flowchart 语法")


class DesignDocument(BaseModel):
    """UI/UX 设计文档"""
    page_specs: list[PageSpec] = Field(description="核心页面规格列表")
    user_journey: str = Field(description="用户旅程图的 Mermaid flowchart 语法")
    design_tokens: DesignTokens = Field(description="设计 Token")
    responsive_strategy: str = Field(description="响应式设计策略说明")
    component_library: list[str] = Field(description="复用组件清单")


# ── Code 相关 ────────────────────────────────────────

class CodeFile(BaseModel):
    """单个代码文件"""
    path: str = Field(description="文件相对路径，例如 src/models/user.py")
    description: str = Field(description="文件功能描述")
    content: str = Field(description="文件完整代码内容")


class BackendCodeSpec(BaseModel):
    """后端代码规格"""
    project_structure: str = Field(description="项目目录树（文本格式）")
    files: list[CodeFile] = Field(description="核心代码文件列表（5-10 个）")
    setup_commands: list[str] = Field(description="项目启动命令，例如 pip install -r requirements.txt")
    dependencies: str = Field(description="核心依赖说明")


class FrontendCodeSpec(BaseModel):
    """前端代码规格"""
    project_structure: str = Field(description="项目目录树（文本格式）")
    files: list[CodeFile] = Field(description="核心代码文件列表（5-10 个）")
    setup_commands: list[str] = Field(description="项目启动命令，例如 npm install && npm run dev")
    dependencies: str = Field(description="核心依赖说明")


# ── QA 报告相关 ──────────────────────────────────

class QATestCase(BaseModel):
    """测试用例"""
    test_name: str = Field(description="测试名称")
    test_type: Literal["unit", "integration", "e2e"] = Field(description="测试类型")
    scope: Literal["backend", "frontend", "full_stack"] = Field(description="测试范围")
    description: str = Field(description="测试描述")
    steps: list[str] = Field(description="测试步骤")
    expected_result: str = Field(description="预期结果")


class QualityBreakdown(BaseModel):
    """质量评分细项"""
    completeness: int = Field(description="完整性评分（1-10）")
    consistency: int = Field(description="一致性评分（1-10）")
    security: int = Field(description="安全性评分（1-10）")
    maintainability: int = Field(description="可维护性评分（1-10）")
    error_handling: int = Field(description="错误处理评分（1-10）")


class PotentialIssue(BaseModel):
    """潜在问题"""
    severity: Literal["high", "medium", "low"] = Field(description="严重程度")
    category: Literal["security", "performance", "logic", "compatibility"] = Field(description="问题类别")
    description: str = Field(description="问题描述")
    recommendation: str = Field(description="修复建议")


class QAReport(BaseModel):
    """QA 质量保障报告"""
    test_plan: list[QATestCase] = Field(description="测试计划用例列表")
    quality_score: int = Field(description="整体质量评分（1-10）")
    quality_breakdown: QualityBreakdown = Field(description="质量评分细项")
    potential_issues: list[PotentialIssue] = Field(description="潜在问题列表")
    summary: str = Field(description="整体质量评估总结")

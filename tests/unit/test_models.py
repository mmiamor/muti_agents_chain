"""数据模型单元测试"""
import pytest
from pydantic import ValidationError

from src.models.document_models import (
    UserStory,
    PRD,
    TechStack,
    APIEndpoint,
    TRD,
    DesignTokens,
    PageSpec,
    DesignDocument,
    CodeFile,
    BackendCodeSpec,
    FrontendCodeSpec,
)
from src.models.agent_models import ReviewFeedback


class TestPRD:
    def test_valid_prd(self):
        prd = PRD(
            vision="做最便捷的遛狗平台",
            target_audience=["城市养宠人群"],
            user_stories=[UserStory(role="用户", action="找遛狗师", benefit="省心")],
            core_features=["发布需求", "匹配遛狗师"],
            non_functional="响应时间<2s",
            mermaid_flowchart="graph LR\nA[发布需求]-->B[匹配]",
        )
        assert prd.vision == "做最便捷的遛狗平台"
        assert len(prd.user_stories) == 1
        assert prd.user_stories[0].role == "用户"

    def test_prd_missing_required_fields(self):
        with pytest.raises(ValidationError):
            PRD(vision="test")  # 缺少必填字段

    def test_prd_serialization(self):
        prd = PRD(
            vision="测试",
            target_audience=["测试用户"],
            user_stories=[],
            core_features=["功能1"],
            non_functional="无",
            mermaid_flowchart="graph LR",
        )
        data = prd.model_dump()
        assert isinstance(data["user_stories"], list)
        assert "vision" in data

    def test_user_story_validation(self):
        story = UserStory(role="管理员", action="管理用户", benefit="提升效率")
        assert story.role == "管理员"


class TestTRD:
    def test_valid_trd(self):
        trd = TRD(
            tech_stack=TechStack(
                frontend="React + Tailwind",
                backend="FastAPI + Python",
                database="PostgreSQL + Redis",
                infrastructure="Docker + AWS",
            ),
            architecture_overview="微服务架构",
            mermaid_er_diagram="erDiagram\nUSER ||--o{ ORDER",
            api_endpoints=[
                APIEndpoint(path="/api/v1/users", method="GET", description="获取用户列表")
            ],
        )
        assert trd.tech_stack.frontend == "React + Tailwind"
        assert len(trd.api_endpoints) == 1
        assert trd.api_endpoints[0].method == "GET"

    def test_trd_invalid_http_method(self):
        with pytest.raises(ValidationError):
            APIEndpoint(path="/test", method="INVALID", description="bad")


class TestReviewFeedback:
    def test_approved(self):
        fb = ReviewFeedback(status="APPROVED", comments="很好")
        assert fb.status == "APPROVED"

    def test_rejected(self):
        fb = ReviewFeedback(status="REJECTED", comments="缺少用户故事")
        assert fb.status == "REJECTED"

    def test_invalid_status(self):
        with pytest.raises(ValidationError):
            ReviewFeedback(status="MAYBE", comments="不支持")


class TestDesignDocument:
    def test_valid_design_doc(self):
        doc = DesignDocument(
            page_specs=[
                PageSpec(
                    page_name="首页",
                    components=["搜索栏", "列表"],
                    description="核心浏览页",
                    mermaid_wireframe="graph TD\nA-->B",
                )
            ],
            user_journey="graph LR\nA-->B-->C",
            design_tokens=DesignTokens(
                color_primary="#2563EB",
                color_secondary="#6366F1",
                font_family="Inter",
                border_radius="8px",
                spacing_unit="4px",
            ),
            responsive_strategy="移动优先",
            component_library=["按钮", "输入框"],
        )
        assert len(doc.page_specs) == 1
        assert doc.design_tokens.color_primary == "#2563EB"
        assert doc.design_tokens.border_radius == "8px"

    def test_design_tokens_required_fields(self):
        with pytest.raises(ValidationError):
            DesignTokens(color_primary="#fff")

    def test_page_spec_optional_wireframe(self):
        ps = PageSpec(page_name="关于", components=[], description="关于页")
        assert ps.mermaid_wireframe == ""


class TestCodeSpec:
    def test_code_file(self):
        f = CodeFile(path="src/main.py", description="入口", content="print('hi')")
        assert f.path == "src/main.py"

    def test_backend_code_spec(self):
        spec = BackendCodeSpec(
            project_structure="src/",
            files=[CodeFile(path="main.py", description="入口", content="code")],
            setup_commands=["pip install -r req.txt"],
            dependencies="fastapi",
        )
        assert len(spec.files) == 1
        assert spec.setup_commands == ["pip install -r req.txt"]

    def test_frontend_code_spec(self):
        spec = FrontendCodeSpec(
            project_structure="src/",
            files=[CodeFile(path="App.tsx", description="根组件", content="code")],
            setup_commands=["npm install"],
            dependencies="react",
        )
        assert len(spec.files) == 1

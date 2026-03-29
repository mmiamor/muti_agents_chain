"""编排器与路由逻辑单元测试"""
import pytest

from src.models.state import AgentState, AgentPhase
from src.models.document_models import PRD, TRD, DesignDocument, TechStack, UserStory, APIEndpoint, PageSpec, DesignTokens
from src.models.agent_models import ReviewFeedback
from src.core.orchestrator import review_router, AgentNames, StageRegistry


SAMPLE_PRD = PRD(
    vision="测试APP",
    target_audience=["用户"],
    user_stories=[UserStory(role="用户", action="测试", benefit="好")],
    core_features=["功能1"],
    non_functional="无",
    mermaid_flowchart="graph LR",
)

SAMPLE_TRD = TRD(
    tech_stack=TechStack(frontend="React", backend="FastAPI", database="PG", infrastructure="Docker"),
    architecture_overview="前后端分离",
    mermaid_er_diagram="erDiagram",
    api_endpoints=[APIEndpoint(path="/api/v1/t", method="GET", description="测试")],
)

SAMPLE_DESIGN = DesignDocument(
    page_specs=[PageSpec(page_name="首页", components=["导航"], description="测试页")],
    user_journey="graph LR",
    design_tokens=DesignTokens(
        color_primary="#2563EB",
        color_secondary="#6366F1",
        font_family="Inter",
        border_radius="8px",
        spacing_unit="4px",
    ),
    responsive_strategy="移动优先",
    component_library=["按钮"],
)


def _make_state(
    prd=None,
    trd=None,
    design_doc=None,
    review=None,
    revision_counts=None,
) -> AgentState:
    """构建测试状态"""
    return AgentState(
        messages=[],
        current_phase=AgentPhase.REQUIREMENT_GATHERING,
        sender="reviewer_agent",
        prd=prd,
        trd=trd,
        design_doc=design_doc,
        latest_review=review,
        revision_counts=revision_counts or {},
    )


class TestStageRegistry:
    """阶段注册表测试"""

    def test_find_stage_pm(self):
        state = _make_state(prd=SAMPLE_PRD)
        stage = StageRegistry.find_stage(state)
        assert stage is not None
        assert stage["agent"] == AgentNames.PM

    def test_find_stage_architect(self):
        state = _make_state(prd=SAMPLE_PRD, trd=SAMPLE_TRD)
        stage = StageRegistry.find_stage(state)
        assert stage is not None
        assert stage["agent"] == AgentNames.ARCHITECT

    def test_find_stage_design(self):
        state = _make_state(prd=SAMPLE_PRD, trd=SAMPLE_TRD, design_doc=SAMPLE_DESIGN)
        stage = StageRegistry.find_stage(state)
        assert stage is not None
        assert stage["agent"] == AgentNames.DESIGN

    def test_find_stage_no_artifact(self):
        state = _make_state()
        assert StageRegistry.find_stage(state) is None

    def test_find_next_stage(self):
        nxt = StageRegistry.find_next_stage(AgentNames.PM)
        assert nxt is not None
        assert nxt["agent"] == AgentNames.ARCHITECT

    def test_find_next_stage_design(self):
        """Design 是最后一个阶段，没有下一阶段"""
        assert StageRegistry.find_next_stage(AgentNames.DESIGN) is None


class TestReviewRouterPMPhase:
    """PM 阶段路由测试（有 PRD 无 TRD）"""

    def test_approved_goes_to_architect(self):
        state = _make_state(prd=SAMPLE_PRD, review=ReviewFeedback(status="APPROVED", comments="OK"))
        assert review_router(state) == AgentNames.ARCHITECT

    def test_rejected_goes_back_to_pm(self):
        state = _make_state(prd=SAMPLE_PRD, review=ReviewFeedback(status="REJECTED", comments="缺少用户故事"))
        assert review_router(state) == AgentNames.PM

    def test_max_revision_triggers_human(self):
        state = _make_state(
            prd=SAMPLE_PRD,
            review=ReviewFeedback(status="REJECTED", comments="还是不行"),
            revision_counts={"pm_agent": 3},
        )
        assert review_router(state) == AgentNames.HUMAN

    def test_no_review_goes_back_to_pm(self):
        state = _make_state(prd=SAMPLE_PRD, review=None)
        assert review_router(state) == AgentNames.PM

    def test_exactly_max_minus_one_still_goes_to_pm(self):
        state = _make_state(
            prd=SAMPLE_PRD,
            review=ReviewFeedback(status="REJECTED", comments="再改改"),
            revision_counts={"pm_agent": 2},
        )
        assert review_router(state) == AgentNames.PM

    def test_approved_ignores_revision_count(self):
        state = _make_state(
            prd=SAMPLE_PRD,
            review=ReviewFeedback(status="APPROVED", comments="终于好了"),
            revision_counts={"pm_agent": 5},
        )
        assert review_router(state) == AgentNames.ARCHITECT


class TestReviewRouterArchitectPhase:
    """Architect 阶段路由测试（有 TRD）"""

    def test_architect_approved_goes_to_design(self):
        state = _make_state(
            prd=SAMPLE_PRD, trd=SAMPLE_TRD,
            review=ReviewFeedback(status="APPROVED", comments="TRD 完整"),
        )
        assert review_router(state) == AgentNames.DESIGN

    def test_architect_rejected_goes_back_to_architect(self):
        state = _make_state(
            prd=SAMPLE_PRD, trd=SAMPLE_TRD,
            review=ReviewFeedback(status="REJECTED", comments="API 不规范"),
        )
        assert review_router(state) == AgentNames.ARCHITECT

    def test_architect_max_revision_triggers_human(self):
        state = _make_state(
            prd=SAMPLE_PRD, trd=SAMPLE_TRD,
            review=ReviewFeedback(status="REJECTED", comments="还是不行"),
            revision_counts={"architect_agent": 3},
        )
        assert review_router(state) == AgentNames.HUMAN

    def test_architect_revision_count_independent(self):
        """Architect revision_count 超高不影响 PM 阶段的判断"""
        state = _make_state(
            prd=SAMPLE_PRD,
            review=ReviewFeedback(status="REJECTED", comments="再改"),
            revision_counts={"pm_agent": 1, "architect_agent": 5},
        )
        assert review_router(state) == AgentNames.PM


class TestReviewRouterDesignPhase:
    """Design 阶段路由测试（有 design_doc）"""

    def test_design_approved_goes_to_end(self):
        state = _make_state(
            prd=SAMPLE_PRD, trd=SAMPLE_TRD, design_doc=SAMPLE_DESIGN,
            review=ReviewFeedback(status="APPROVED", comments="设计完整"),
        )
        assert review_router(state) == "__end__"

    def test_design_rejected_goes_back_to_design(self):
        state = _make_state(
            prd=SAMPLE_PRD, trd=SAMPLE_TRD, design_doc=SAMPLE_DESIGN,
            review=ReviewFeedback(status="REJECTED", comments="页面缺失"),
        )
        assert review_router(state) == AgentNames.DESIGN

    def test_design_max_revision_triggers_human(self):
        state = _make_state(
            prd=SAMPLE_PRD, trd=SAMPLE_TRD, design_doc=SAMPLE_DESIGN,
            review=ReviewFeedback(status="REJECTED", comments="还是不行"),
            revision_counts={"design_agent": 3},
        )
        assert review_router(state) == AgentNames.HUMAN


class TestReviewRouterEdgeCases:
    """边界情况"""

    def test_no_artifact_routes_to_pm(self):
        state = _make_state(review=ReviewFeedback(status="REJECTED", comments="无"))
        assert review_router(state) == AgentNames.PM

    def test_no_review_with_artifact(self):
        """有产出物但无审查结果 → 打回当前 Agent"""
        state = _make_state(prd=SAMPLE_PRD, review=None)
        assert review_router(state) == AgentNames.PM


class TestAgentNames:
    def test_all_constants_defined(self):
        assert AgentNames.PM == "pm_agent"
        assert AgentNames.REVIEWER == "reviewer_agent"
        assert AgentNames.ARCHITECT == "architect_agent"
        assert AgentNames.DESIGN == "design_agent"
        assert AgentNames.HUMAN == "human_intervention"

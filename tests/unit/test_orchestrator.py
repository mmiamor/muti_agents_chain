"""编排器与路由逻辑单元测试"""
import pytest

from src.models.state import AgentState, AgentPhase
from src.models.document_models import PRD, TRD, TechStack, UserStory, APIEndpoint
from src.models.agent_models import ReviewFeedback
from src.core.orchestrator import review_router, AgentNames


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


def _make_state(
    prd=None,
    trd=None,
    review=None,
    revision_count=0,
    architect_revision_count=0,
) -> AgentState:
    """构建测试状态。路由器根据 prd/trd 产出物判断当前阶段"""
    return AgentState(
        messages=[],
        current_phase=AgentPhase.REQUIREMENT_GATHERING,
        sender="reviewer_agent",  # Reviewer 节点之后的典型 sender
        prd=prd,
        trd=trd,
        latest_review=review,
        revision_count=revision_count,
        architect_revision_count=architect_revision_count,
    )


class TestReviewRouterPMPhase:
    """PM 阶段路由测试（有 PRD 无 TRD）"""

    def test_approved_goes_to_architect(self):
        state = _make_state(
            prd=SAMPLE_PRD,
            review=ReviewFeedback(status="APPROVED", comments="OK"),
        )
        assert review_router(state) == AgentNames.ARCHITECT

    def test_rejected_goes_back_to_pm(self):
        state = _make_state(
            prd=SAMPLE_PRD,
            review=ReviewFeedback(status="REJECTED", comments="缺少用户故事"),
        )
        assert review_router(state) == AgentNames.PM

    def test_max_revision_triggers_human(self):
        state = _make_state(
            prd=SAMPLE_PRD,
            review=ReviewFeedback(status="REJECTED", comments="还是不行"),
            revision_count=3,
        )
        assert review_router(state) == AgentNames.HUMAN

    def test_no_review_goes_back_to_pm(self):
        state = _make_state(prd=SAMPLE_PRD, review=None)
        assert review_router(state) == AgentNames.PM

    def test_exactly_max_minus_one_still_goes_to_pm(self):
        state = _make_state(
            prd=SAMPLE_PRD,
            review=ReviewFeedback(status="REJECTED", comments="再改改"),
            revision_count=2,
        )
        assert review_router(state) == AgentNames.PM

    def test_approved_ignores_revision_count(self):
        state = _make_state(
            prd=SAMPLE_PRD,
            review=ReviewFeedback(status="APPROVED", comments="终于好了"),
            revision_count=5,
        )
        assert review_router(state) == AgentNames.ARCHITECT


class TestReviewRouterArchitectPhase:
    """Architect 阶段路由测试（有 TRD）"""

    def test_architect_approved_goes_to_end(self):
        state = _make_state(
            prd=SAMPLE_PRD,
            trd=SAMPLE_TRD,
            review=ReviewFeedback(status="APPROVED", comments="TRD 完整"),
        )
        assert review_router(state) == "__end__"

    def test_architect_rejected_goes_back_to_architect(self):
        state = _make_state(
            prd=SAMPLE_PRD,
            trd=SAMPLE_TRD,
            review=ReviewFeedback(status="REJECTED", comments="API 不规范"),
        )
        assert review_router(state) == AgentNames.ARCHITECT

    def test_architect_max_revision_triggers_human(self):
        state = _make_state(
            prd=SAMPLE_PRD,
            trd=SAMPLE_TRD,
            review=ReviewFeedback(status="REJECTED", comments="还是不行"),
            architect_revision_count=3,
        )
        assert review_router(state) == AgentNames.HUMAN

    def test_architect_revision_count_independent(self):
        """Architect revision_count 超高不影响 PM 阶段的判断"""
        state = _make_state(
            prd=SAMPLE_PRD,
            review=ReviewFeedback(status="REJECTED", comments="再改"),
            revision_count=1,
            architect_revision_count=5,
        )
        # 没有 TRD → 判断为 PM 阶段
        assert review_router(state) == AgentNames.PM

    def test_no_artifact_routes_to_pm(self):
        """没有任何产出物 → 打回 PM"""
        state = _make_state(
            review=ReviewFeedback(status="REJECTED", comments="无"),
        )
        assert review_router(state) == AgentNames.PM


class TestAgentNames:
    def test_all_constants_defined(self):
        assert AgentNames.PM == "pm_agent"
        assert AgentNames.REVIEWER == "reviewer_agent"
        assert AgentNames.ARCHITECT == "architect_agent"
        assert AgentNames.HUMAN == "human_intervention"

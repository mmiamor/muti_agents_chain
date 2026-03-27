"""编排器与路由逻辑单元测试"""
import pytest

from src.models.state import AgentState, AgentPhase
from src.models.agent_models import ReviewFeedback
from src.core.orchestrator import review_router, AgentNames


def _make_state(sender="reviewer_agent", review=None, revision_count=0) -> AgentState:
    return AgentState(
        messages=[],
        current_phase=AgentPhase.REQUIREMENT_GATHERING,
        sender=sender,
        prd=None,
        trd=None,
        latest_review=review,
        revision_count=revision_count,
    )


class TestReviewRouter:
    def test_approved_goes_to_architect(self):
        """审查通过 → 流转架构师"""
        state = _make_state(review=ReviewFeedback(status="APPROVED", comments="OK"))
        assert review_router(state) == AgentNames.ARCHITECT

    def test_rejected_goes_back_to_pm(self):
        """审查拒绝 → 打回 PM"""
        state = _make_state(review=ReviewFeedback(status="REJECTED", comments="缺少用户故事"))
        assert review_router(state) == AgentNames.PM

    def test_max_revision_triggers_human(self):
        """超过最大重试次数 → 人工干预"""
        state = _make_state(
            review=ReviewFeedback(status="REJECTED", comments="还是不行"),
            revision_count=3,
        )
        assert review_router(state) == AgentNames.HUMAN

    def test_no_review_goes_back_to_pm(self):
        """无审查结果 → 打回 PM"""
        state = _make_state(review=None)
        assert review_router(state) == AgentNames.PM

    def test_exactly_max_minus_one_still_goes_to_pm(self):
        """revision_count = 2 (max=3) → 还有机会，打回 PM"""
        state = _make_state(
            review=ReviewFeedback(status="REJECTED", comments="再改改"),
            revision_count=2,
        )
        assert review_router(state) == AgentNames.PM

    def test_approved_ignores_revision_count(self):
        """即使 revision_count 很高，APPROVED 也应该继续"""
        state = _make_state(
            review=ReviewFeedback(status="APPROVED", comments="终于好了"),
            revision_count=5,
        )
        assert review_router(state) == AgentNames.ARCHITECT


class TestAgentNames:
    def test_all_constants_defined(self):
        assert AgentNames.PM == "pm_agent"
        assert AgentNames.REVIEWER == "reviewer_agent"
        assert AgentNames.ARCHITECT == "architect_agent"
        assert AgentNames.HUMAN == "human_intervention"

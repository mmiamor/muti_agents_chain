"""Reviewer Agent 节点单元测试"""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from langchain_core.messages import HumanMessage

from src.agents.nodes.reviewer_node import ReviewerAgent, reviewer_node
from src.models.state import AgentState, AgentPhase
from src.models.document_models import PRD, UserStory
from src.models.agent_models import ReviewFeedback

APPROVED_JSON = json.dumps({"status": "APPROVED", "comments": "PRD 完整，通过。"})
REJECTED_JSON = json.dumps({"status": "REJECTED", "comments": "缺少非功能需求。"})


def _mock_llm_response(content: str):
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = content
    return mock_response


@pytest.fixture
def state_with_prd():
    return AgentState(
        messages=[HumanMessage(content="做一个遛狗APP")],
        current_phase=AgentPhase.REQUIREMENT_GATHERING,
        sender="pm_agent",
        prd=PRD(
            vision="遛狗平台",
            target_audience=["养宠人群"],
            user_stories=[UserStory(role="用户", action="找遛狗师", benefit="省心")],
            core_features=["发布需求", "匹配遛狗师"],
            non_functional="响应<2s",
            mermaid_flowchart="graph LR\nA-->B",
        ),
        trd=None,
        latest_review=None,
        revision_count=0,
    )


@pytest.fixture
def state_no_target():
    return AgentState(
        messages=[],
        current_phase=AgentPhase.REQUIREMENT_GATHERING,
        sender="unknown_agent",
        prd=None,
        trd=None,
        latest_review=None,
        revision_count=0,
    )


class TestReviewerAgent:
    def test_agent_info(self):
        agent = ReviewerAgent(llm=MagicMock())
        assert agent.name == "reviewer_agent"
        assert agent.role == "审查专家"

    @pytest.mark.asyncio
    async def test_approved_review(self, state_with_prd):
        mock_llm = MagicMock()
        mock_llm.client.chat.completions.create = AsyncMock(
            return_value=_mock_llm_response(APPROVED_JSON)
        )
        agent = ReviewerAgent(llm=mock_llm)
        result = await agent.run(state_with_prd)

        assert "latest_review" in result
        assert result["latest_review"].status == "APPROVED"
        assert result["sender"] == "reviewer_agent"

    @pytest.mark.asyncio
    async def test_rejected_review(self, state_with_prd):
        mock_llm = MagicMock()
        mock_llm.client.chat.completions.create = AsyncMock(
            return_value=_mock_llm_response(REJECTED_JSON)
        )
        agent = ReviewerAgent(llm=mock_llm)
        result = await agent.run(state_with_prd)

        assert result["latest_review"].status == "REJECTED"
        assert "非功能需求" in result["latest_review"].comments

    @pytest.mark.asyncio
    async def test_no_review_target(self, state_no_target):
        """无审查目标时应返回 REJECTED 而非崩溃"""
        agent = ReviewerAgent(llm=MagicMock())
        result = await agent.run(state_no_target)

        assert result["latest_review"].status == "REJECTED"
        assert "无法识别" in result["latest_review"].comments

    @pytest.mark.asyncio
    async def test_review_passes_with_feedback(self, state_with_prd):
        state = {**state_with_prd, "latest_review": ReviewFeedback(status="APPROVED", comments="OK")}
        agent = ReviewerAgent(llm=MagicMock())
        assert await agent.review(state) is True

    @pytest.mark.asyncio
    async def test_review_fails_without_feedback(self, state_with_prd):
        agent = ReviewerAgent(llm=MagicMock())
        assert await agent.review(state_with_prd) is False

    @pytest.mark.asyncio
    async def test_reviewer_node_function(self, state_with_prd):
        mock_llm = MagicMock()
        mock_llm.client.chat.completions.create = AsyncMock(
            return_value=_mock_llm_response(APPROVED_JSON)
        )
        with patch("src.agents.nodes.reviewer_node._create_llm", return_value=mock_llm):
            result = await reviewer_node(state_with_prd)
            assert "latest_review" in result

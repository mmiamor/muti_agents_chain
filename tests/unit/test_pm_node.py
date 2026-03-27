"""PM Agent 节点单元测试"""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from langchain_core.messages import HumanMessage, AIMessage

from src.agents.nodes.pm_node import PMAgent, pm_node
from src.models.state import AgentState, AgentPhase
from src.models.document_models import PRD, UserStory
from src.models.agent_models import ReviewFeedback


MOCK_PRD_JSON = json.dumps({
    "vision": "遛狗平台",
    "target_audience": ["城市养宠人群"],
    "user_stories": [
        {"role": "用户", "action": "找遛狗师", "benefit": "省心"}
    ],
    "core_features": ["发布需求", "匹配遛狗师"],
    "non_functional": "响应时间<2s",
    "mermaid_flowchart": "graph LR\nA-->B",
})


def _mock_llm_response(content: str):
    """构造 mock LLM 响应"""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = content
    return mock_response


@pytest.fixture
def base_state():
    return AgentState(
        messages=[HumanMessage(content="我想做一个遛狗APP")],
        current_phase=AgentPhase.REQUIREMENT_GATHERING,
        sender="user",
        prd=None,
        trd=None,
        latest_review=None,
        revision_count=0,
    )


@pytest.fixture
def rejected_state():
    return AgentState(
        messages=[HumanMessage(content="我想做一个遛狗APP")],
        current_phase=AgentPhase.REQUIREMENT_GATHERING,
        sender="reviewer_agent",
        prd=None,
        trd=None,
        latest_review=ReviewFeedback(status="REJECTED", comments="缺少用户故事"),
        revision_count=1,
    )


class TestPMAgent:
    def test_agent_info(self):
        agent = PMAgent(llm=MagicMock())
        assert agent.name == "pm_agent"
        assert agent.role == "资深产品经理"

    @pytest.mark.asyncio
    async def test_run_returns_prd(self, base_state):
        """PM Agent 应该返回包含 PRD 的状态更新"""
        mock_llm = MagicMock()
        mock_llm.client.chat.completions.create = AsyncMock(
            return_value=_mock_llm_response(MOCK_PRD_JSON)
        )
        agent = PMAgent(llm=mock_llm)

        result = await agent.run(base_state)

        assert "prd" in result
        assert result["prd"].vision == "遛狗平台"
        assert result["sender"] == "pm_agent"
        assert len(result["messages"]) == 1

    @pytest.mark.asyncio
    async def test_run_with_rejection_context(self, rejected_state):
        """被拒绝后应该包含审查反馈上下文"""
        mock_llm = MagicMock()
        mock_llm.client.chat.completions.create = AsyncMock(
            return_value=_mock_llm_response(MOCK_PRD_JSON)
        )
        agent = PMAgent(llm=mock_llm)

        result = await agent.run(rejected_state)

        assert result["prd"].vision == "遛狗平台"
        # 验证传给 LLM 的消息中包含审查反馈
        call_args = mock_llm.client.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]
        system_msg = messages[0]["content"]
        assert "审查员反馈" in system_msg

    @pytest.mark.asyncio
    async def test_review_passes_for_valid_prd(self, base_state):
        """完整 PRD 自我反思应该通过"""
        prd = PRD(
            vision="测试",
            target_audience=["用户"],
            user_stories=[UserStory(role="用户", action="测试", benefit="好")],
            core_features=["功能1"],
            non_functional="无",
            mermaid_flowchart="graph LR",
        )
        state = {**base_state, "prd": prd}
        agent = PMAgent(llm=MagicMock())
        assert await agent.review(state) is True

    @pytest.mark.asyncio
    async def test_review_fails_for_incomplete_prd(self, base_state):
        """不完整 PRD 自我反思应该失败"""
        state = base_state  # prd=None
        agent = PMAgent(llm=MagicMock())
        assert await agent.review(state) is False

    @pytest.mark.asyncio
    async def test_pm_node_function(self, base_state):
        """pm_node 函数应该正常调用"""
        mock_llm = MagicMock()
        mock_llm.client.chat.completions.create = AsyncMock(
            return_value=_mock_llm_response(MOCK_PRD_JSON)
        )
        with patch("src.agents.nodes.pm_node._create_llm", return_value=mock_llm):
            result = await pm_node(base_state)
            assert "prd" in result

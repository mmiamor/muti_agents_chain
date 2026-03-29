"""Architect Agent 节点单元测试"""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from langchain_core.messages import HumanMessage, AIMessage

from src.agents.nodes.architect_node import ArchitectAgent, architect_node
from src.models.state import AgentState, AgentPhase
from src.models.document_models import PRD, TRD, TechStack, APIEndpoint, UserStory
from src.models.agent_models import ReviewFeedback


MOCK_TRD_JSON = json.dumps({
    "tech_stack": {
        "frontend": "React + TypeScript",
        "backend": "FastAPI (Python 3.12)",
        "database": "PostgreSQL + Redis",
        "infrastructure": "Docker + K8s",
    },
    "architecture_overview": "前后端分离架构，前端 React SPA，后端 FastAPI RESTful API。",
    "mermaid_er_diagram": "erDiagram\nUSERS ||--o{ ORDERS : places",
    "api_endpoints": [
        {"path": "/api/v1/users", "method": "GET", "description": "获取用户列表"},
        {"path": "/api/v1/users", "method": "POST", "description": "创建用户"},
    ],
})

SAMPLE_PRD = PRD(
    vision="遛狗平台",
    target_audience=["城市养宠人群"],
    user_stories=[UserStory(role="用户", action="找遛狗师", benefit="省心")],
    core_features=["发布需求", "匹配遛狗师"],
    non_functional="响应时间<2s",
    mermaid_flowchart="graph LR\nA-->B",
)


def _mock_llm_response(content: str):
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = content
    return mock_response


@pytest.fixture
def base_state():
    return AgentState(
        messages=[HumanMessage(content="我想做一个遛狗APP")],
        current_phase=AgentPhase.ARCHITECTURE_DESIGN,
        sender="pm_agent",
        prd=SAMPLE_PRD,
        trd=None,
        latest_review=ReviewFeedback(status="APPROVED", comments="PRD 通过"),
        revision_counts={},
    )


@pytest.fixture
def no_prd_state():
    return AgentState(
        messages=[HumanMessage(content="没有PRD")],
        current_phase=AgentPhase.ARCHITECTURE_DESIGN,
        sender="pm_agent",
        prd=None,
        trd=None,
        latest_review=None,
        revision_counts={},
    )


@pytest.fixture
def rejected_trd_state():
    return AgentState(
        messages=[HumanMessage(content="我想做一个遛狗APP")],
        current_phase=AgentPhase.ARCHITECTURE_DESIGN,
        sender="reviewer_agent",
        prd=SAMPLE_PRD,
        trd=None,
        latest_review=ReviewFeedback(status="REJECTED", comments="API 设计不够 RESTful"),
        revision_counts={"architect_agent": 1},
    )


class TestArchitectAgent:
    def test_agent_info(self):
        agent = ArchitectAgent(llm=MagicMock())
        assert agent.name == "architect_agent"
        assert agent.role == "资深架构师"

    @pytest.mark.asyncio
    async def test_run_returns_trd(self, base_state):
        """Architect Agent 应该返回包含 TRD 的状态更新"""
        mock_llm = MagicMock()
        mock_llm.client.chat.completions.create = AsyncMock(
            return_value=_mock_llm_response(MOCK_TRD_JSON)
        )
        agent = ArchitectAgent(llm=mock_llm)

        result = await agent.run(base_state)

        assert "trd" in result
        assert result["trd"].tech_stack.backend == "FastAPI (Python 3.12)"
        assert result["sender"] == "architect_agent"
        assert len(result["trd"].api_endpoints) == 2

    @pytest.mark.asyncio
    async def test_run_without_prd_returns_error(self, no_prd_state):
        """没有 PRD 时应该返回错误消息"""
        agent = ArchitectAgent(llm=MagicMock())
        result = await agent.run(no_prd_state)

        assert "trd" not in result
        assert result["sender"] == "architect_agent"

    @pytest.mark.asyncio
    async def test_run_with_rejection_context(self, rejected_trd_state):
        """TRD 被拒绝后应该包含审查反馈上下文"""
        mock_llm = MagicMock()
        mock_llm.client.chat.completions.create = AsyncMock(
            return_value=_mock_llm_response(MOCK_TRD_JSON)
        )
        agent = ArchitectAgent(llm=mock_llm)

        result = await agent.run(rejected_trd_state)

        assert result["trd"].tech_stack.backend == "FastAPI (Python 3.12)"
        call_args = mock_llm.client.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]
        system_msg = messages[0]["content"]
        assert "审查员反馈" in system_msg

    @pytest.mark.asyncio
    async def test_architect_node_function(self, base_state):
        """architect_node 函数应该正常调用"""
        import src.agents.nodes.architect_node as arch_mod
        arch_mod._architect_agent = None

        mock_llm = MagicMock()
        mock_llm.client.chat.completions.create = AsyncMock(
            return_value=_mock_llm_response(MOCK_TRD_JSON)
        )
        with patch("src.agents.nodes.architect_node.create_llm", return_value=mock_llm):
            result = await architect_node(base_state)
            assert "trd" in result

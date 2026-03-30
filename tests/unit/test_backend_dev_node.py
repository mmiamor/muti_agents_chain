"""Backend Dev Agent 节点单元测试"""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from langchain_core.messages import HumanMessage

from src.agents.nodes.backend_dev_node import BackendDevAgent, backend_dev_node
from src.models.state import AgentState, AgentPhase
from src.models.document_models import TRD, TechStack, APIEndpoint
from src.models.agent_models import ReviewFeedback


MOCK_BACKEND_JSON = json.dumps({
    "project_structure": "project/\n├── src/\n│   ├── main.py\n│   ├── models/\n│   │   └── user.py\n│   ├── routes/\n│   │   └── users.py\n│   └── config.py\n├── requirements.txt\n└── README.md",
    "files": [
        {
            "path": "src/main.py",
            "description": "FastAPI 应用入口",
            "content": "from fastapi import FastAPI\n\napp = FastAPI(title=\"DogWalk API\")\n\n@app.get(\"/health\")\ndef health():\n    return {\"status\": \"ok\"}",
        },
        {
            "path": "requirements.txt",
            "description": "Python 依赖",
            "content": "fastapi>=0.100\nuvicorn\nsqlalchemy\npydantic",
        },
    ],
    "setup_commands": ["pip install -r requirements.txt", "uvicorn src.main:app --reload"],
    "dependencies": "fastapi>=0.100, uvicorn, sqlalchemy, pydantic",
})

SAMPLE_TRD = TRD(
    tech_stack=TechStack(frontend="React", backend="FastAPI", database="PG", infrastructure="Docker"),
    architecture_overview="前后端分离",
    mermaid_er_diagram="erDiagram",
    api_endpoints=[APIEndpoint(path="/api/v1/t", method="GET", description="测试")],
)


def _mock_llm_response(content: str):
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = content
    return mock_response


@pytest.fixture
def base_state():
    return AgentState(
        messages=[HumanMessage(content="做APP")],
        current_phase=AgentPhase.CODING,
        sender="design_agent",
        trd=SAMPLE_TRD,
        latest_review=ReviewFeedback(status="APPROVED", comments="Design 通过"),
        revision_counts={},
    )


@pytest.fixture
def missing_trd_state():
    return AgentState(
        messages=[],
        current_phase=AgentPhase.CODING,
        sender="design_agent",
        trd=None,
        latest_review=None,
        revision_counts={},
    )


@pytest.fixture
def rejected_state():
    return AgentState(
        messages=[],
        current_phase=AgentPhase.CODING,
        sender="reviewer_agent",
        trd=SAMPLE_TRD,
        latest_review=ReviewFeedback(status="REJECTED", comments="API 路径不对"),
        revision_counts={"backend_dev_agent": 1},
    )


class TestBackendDevAgent:
    def test_agent_info(self):
        agent = BackendDevAgent(llm=MagicMock())
        assert agent.name == "backend_dev_agent"
        assert agent.role == "后端开发工程师"

    @pytest.mark.asyncio
    async def test_run_returns_backend_code(self, base_state):
        mock_llm = MagicMock()
        mock_llm.client.chat.completions.create = AsyncMock(
            return_value=_mock_llm_response(MOCK_BACKEND_JSON)
        )
        agent = BackendDevAgent(llm=mock_llm)
        result = await agent.run(base_state)

        assert "backend_code" in result
        assert result["sender"] == "backend_dev_agent"
        assert len(result["backend_code"].files) == 2
        assert result["backend_code"].files[0].path == "src/main.py"

    @pytest.mark.asyncio
    async def test_run_without_trd_returns_error(self, missing_trd_state):
        agent = BackendDevAgent(llm=MagicMock())
        result = await agent.run(missing_trd_state)
        assert "backend_code" not in result

    @pytest.mark.asyncio
    async def test_run_with_rejection_context(self, rejected_state):
        mock_llm = MagicMock()
        mock_llm.client.chat.completions.create = AsyncMock(
            return_value=_mock_llm_response(MOCK_BACKEND_JSON)
        )
        agent = BackendDevAgent(llm=mock_llm)
        result = await agent.run(rejected_state)
        assert result["backend_code"] is not None
        call_args = mock_llm.client.chat.completions.create.call_args
        assert "审查员反馈" in call_args.kwargs["messages"][0]["content"]

    @pytest.mark.asyncio
    async def test_backend_dev_node_function(self, base_state):
        import src.agents.nodes.backend_dev_node as mod
        mod._backend_dev_agent = None
        mock_llm = MagicMock()
        mock_llm.client.chat.completions.create = AsyncMock(
            return_value=_mock_llm_response(MOCK_BACKEND_JSON)
        )
        with patch("src.agents.nodes.backend_dev_node.create_llm", return_value=mock_llm):
            result = await backend_dev_node(base_state)
            assert "backend_code" in result

"""Frontend Dev Agent 节点单元测试"""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from langchain_core.messages import HumanMessage

from src.agents.nodes.frontend_dev_node import FrontendDevAgent, frontend_dev_node
from src.models.state import AgentState, AgentPhase
from src.models.document_models import (
    TRD, TechStack, APIEndpoint, DesignDocument, PageSpec, DesignTokens,
)
from src.models.agent_models import ReviewFeedback


MOCK_FRONTEND_JSON = json.dumps({
    "project_structure": "project/\n├── src/\n│   ├── App.tsx\n│   ├── pages/\n│   │   └── Home.tsx\n│   ├── components/\n│   │   └── Button.tsx\n│   └── api/\n│       └── client.ts\n├── package.json\n└── tsconfig.json",
    "files": [
        {
            "path": "src/App.tsx",
            "description": "应用根组件",
            "content": "import React from 'react';\n\nfunction App() {\n  return <div>Hello</div>;\n}\n\nexport default App;",
        },
        {
            "path": "package.json",
            "description": "依赖声明",
            "content": '{\n  "name": "dogwalk-app",\n  "dependencies": {\n    "react": "^18",\n    "react-dom": "^18"\n  }\n}',
        },
    ],
    "setup_commands": ["npm install", "npm run dev"],
    "dependencies": "react, react-dom, typescript, axios",
})

SAMPLE_TRD = TRD(
    tech_stack=TechStack(frontend="React", backend="FastAPI", database="PG", infrastructure="Docker"),
    architecture_overview="前后端分离",
    mermaid_er_diagram="erDiagram",
    api_endpoints=[APIEndpoint(path="/api/v1/t", method="GET", description="测试")],
)

SAMPLE_DESIGN = DesignDocument(
    page_specs=[PageSpec(page_name="首页", components=["按钮"], description="测试")],
    user_journey="graph LR",
    design_tokens=DesignTokens(
        color_primary="#2563EB", color_secondary="#6366F1",
        font_family="Inter", border_radius="8px", spacing_unit="4px",
    ),
    responsive_strategy="移动优先",
    component_library=["按钮"],
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
        sender="backend_dev_agent",
        trd=SAMPLE_TRD,
        design_doc=SAMPLE_DESIGN,
        latest_review=ReviewFeedback(status="APPROVED", comments="Backend 通过"),
        revision_counts={},
    )


@pytest.fixture
def missing_input_state():
    return AgentState(
        messages=[],
        current_phase=AgentPhase.CODING,
        sender="backend_dev_agent",
        trd=None,
        design_doc=None,
        latest_review=None,
        revision_counts={},
    )


class TestFrontendDevAgent:
    def test_agent_info(self):
        agent = FrontendDevAgent(llm=MagicMock())
        assert agent.name == "frontend_dev_agent"
        assert agent.role == "前端开发工程师"

    @pytest.mark.asyncio
    async def test_run_returns_frontend_code(self, base_state):
        mock_llm = MagicMock()
        mock_llm.client.chat.completions.create = AsyncMock(
            return_value=_mock_llm_response(MOCK_FRONTEND_JSON)
        )
        agent = FrontendDevAgent(llm=mock_llm)
        result = await agent.run(base_state)

        assert "frontend_code" in result
        assert result["sender"] == "frontend_dev_agent"
        assert len(result["frontend_code"].files) == 2

    @pytest.mark.asyncio
    async def test_run_without_trd_design_returns_error(self, missing_input_state):
        agent = FrontendDevAgent(llm=MagicMock())
        result = await agent.run(missing_input_state)
        assert "frontend_code" not in result

    @pytest.mark.asyncio
    async def test_frontend_dev_node_function(self, base_state):
        import src.agents.nodes.frontend_dev_node as mod
        mod._frontend_dev_agent = None
        mock_llm = MagicMock()
        mock_llm.client.chat.completions.create = AsyncMock(
            return_value=_mock_llm_response(MOCK_FRONTEND_JSON)
        )
        with patch("src.agents.nodes.frontend_dev_node.create_llm", return_value=mock_llm):
            result = await frontend_dev_node(base_state)
            assert "frontend_code" in result

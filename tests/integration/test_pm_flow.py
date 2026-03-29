"""PM → Architect 全流程集成测试（mock LLM，不调用真实 API）"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from langchain_core.messages import HumanMessage

from src.models.state import AgentState, AgentPhase
from src.models.document_models import (
    PRD, TRD, DesignDocument, TechStack, UserStory, APIEndpoint,
    PageSpec, DesignTokens,
)
from src.models.agent_models import ReviewFeedback


SAMPLE_PRD_JSON = """{"vision":"遛狗平台","target_audience":["养宠人群"],"user_stories":[{"role":"用户","action":"找遛狗师","benefit":"省心"}],"core_features":["发布需求","匹配遛狗师"],"non_functional":"响应<2s","mermaid_flowchart":"graph LR\\nA-->B"}"""

SAMPLE_TRD_JSON = """{"tech_stack":{"frontend":"React","backend":"FastAPI","database":"PG","infrastructure":"Docker"},"architecture_overview":"前后端分离","mermaid_er_diagram":"erDiagram","api_endpoints":[{"path":"/api/v1/t","method":"GET","description":"测试"}]}"""

SAMPLE_DESIGN_JSON = """{"page_specs":[{"page_name":"首页","components":["搜索栏"],"description":"测试","mermaid_wireframe":"graph TD\\nA-->B"}],"user_journey":"graph LR\\nA-->B","design_tokens":{"color_primary":"#2563EB","color_secondary":"#6366F1","font_family":"Inter","border_radius":"8px","spacing_unit":"4px"},"responsive_strategy":"移动优先","component_library":["按钮"]}"""

APPROVED_JSON = '{"status":"APPROVED","comments":"OK"}'


def _mock_llm(content: str):
    mock_llm = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = content
    mock_llm.client.chat.completions.create = AsyncMock(return_value=mock_response)
    return mock_llm


@pytest.fixture
def initial_state():
    return {
        "messages": [HumanMessage(content="做遛狗APP")],
        "current_phase": AgentPhase.REQUIREMENT_GATHERING,
        "sender": "user",
    }


class TestPMFlow:
    """PM 阶段集成（mock）"""

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_pm_reviewer_architect_design_pipeline(self, initial_state):
        """模拟完整流水线：PM → Reviewer → Architect → Reviewer → Design → Reviewer"""
        from src.agents.nodes.pm_node import PMAgent
        from src.agents.nodes.reviewer_node import ReviewerAgent
        from src.agents.nodes.architect_node import ArchitectAgent
        from src.agents.nodes.design_node import DesignAgent

        # 按顺序模拟每个 Agent 的调用
        pm_llm = _mock_llm(SAMPLE_PRD_JSON)
        reviewer_llm = _mock_llm(APPROVED_JSON)
        architect_llm = _mock_llm(SAMPLE_TRD_JSON)
        design_llm = _mock_llm(SAMPLE_DESIGN_JSON)

        pm = PMAgent(llm=pm_llm)
        reviewer = ReviewerAgent(llm=reviewer_llm)
        architect = ArchitectAgent(llm=architect_llm)
        designer = DesignAgent(llm=design_llm)

        # Step 1: PM
        state = dict(initial_state)
        state.update(await pm.run(state))
        assert state["prd"] is not None

        # Step 2: Review PRD
        state["sender"] = "pm_agent"
        state.update(await reviewer.run(state))
        assert state["latest_review"].status == "APPROVED"

        # Step 3: Architect
        state["sender"] = "reviewer_agent"
        state.update(await architect.run(state))
        assert state["trd"] is not None

        # Step 4: Review TRD
        state["sender"] = "architect_agent"
        state.update(await reviewer.run(state))
        assert state["latest_review"].status == "APPROVED"

        # Step 5: Design
        state["sender"] = "reviewer_agent"
        state.update(await designer.run(state))
        assert state["design_doc"] is not None
        assert len(state["design_doc"].page_specs) > 0

        # Step 6: Review Design
        state["sender"] = "design_agent"
        state.update(await reviewer.run(state))
        assert state["latest_review"].status == "APPROVED"

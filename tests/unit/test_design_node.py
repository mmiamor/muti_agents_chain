"""Design Agent 节点单元测试"""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from langchain_core.messages import HumanMessage

from src.agents.nodes.design_node import DesignAgent, design_node
from src.models.state import AgentState, AgentPhase
from src.models.document_models import PRD, TRD, TechStack, UserStory, APIEndpoint
from src.models.agent_models import ReviewFeedback


MOCK_DESIGN_JSON = json.dumps({
    "page_specs": [
        {
            "page_name": "首页",
            "components": ["搜索栏", "推荐列表", "底部导航"],
            "description": "核心浏览入口",
            "mermaid_wireframe": "graph TD\nA[顶部搜索]-->B[内容列表]\nB-->C[底部Tab]",
        },
        {
            "page_name": "个人中心",
            "components": ["头像", "订单列表", "设置入口"],
            "description": "用户个人信息与管理",
            "mermaid_wireframe": "graph TD\nA[头像区]-->B[功能列表]",
        },
    ],
    "user_journey": "graph LR\nA[打开APP]-->B[浏览首页]\nB-->C[搜索服务]\nC-->D[下单]",
    "design_tokens": {
        "color_primary": "#2563EB",
        "color_secondary": "#6366F1",
        "font_family": "Inter, system-ui",
        "border_radius": "8px",
        "spacing_unit": "4px",
    },
    "responsive_strategy": "移动优先，断点 768px/1024px/1440px",
    "component_library": ["按钮", "输入框", "卡片", "列表项", "模态框", "底部导航"],
})


SAMPLE_PRD = PRD(
    vision="遛狗平台",
    target_audience=["城市养宠人群"],
    user_stories=[UserStory(role="用户", action="找遛狗师", benefit="省心")],
    core_features=["发布需求", "匹配遛狗师"],
    non_functional="响应时间<2s",
    mermaid_flowchart="graph LR\nA-->B",
)

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
        messages=[HumanMessage(content="做遛狗APP")],
        current_phase=AgentPhase.UI_DESIGN,
        sender="architect_agent",
        prd=SAMPLE_PRD,
        trd=SAMPLE_TRD,
        latest_review=ReviewFeedback(status="APPROVED", comments="TRD 通过"),
        revision_counts={},
    )


@pytest.fixture
def missing_input_state():
    return AgentState(
        messages=[HumanMessage(content="没有PRD")],
        current_phase=AgentPhase.UI_DESIGN,
        sender="architect_agent",
        prd=None,
        trd=None,
        latest_review=None,
        revision_counts={},
    )


@pytest.fixture
def rejected_state():
    return AgentState(
        messages=[HumanMessage(content="做遛狗APP")],
        current_phase=AgentPhase.UI_DESIGN,
        sender="reviewer_agent",
        prd=SAMPLE_PRD,
        trd=SAMPLE_TRD,
        latest_review=ReviewFeedback(status="REJECTED", comments="缺少个人中心页面"),
        revision_counts={"design_agent": 1},
    )


class TestDesignAgent:
    def test_agent_info(self):
        agent = DesignAgent(llm=MagicMock())
        assert agent.name == "design_agent"
        assert agent.role == "资深 UI/UX 设计师"

    @pytest.mark.asyncio
    async def test_run_returns_design_doc(self, base_state):
        """Design Agent 应返回包含 DesignDocument 的状态更新"""
        mock_llm = MagicMock()
        mock_llm.client.chat.completions.create = AsyncMock(
            return_value=_mock_llm_response(MOCK_DESIGN_JSON)
        )
        agent = DesignAgent(llm=mock_llm)

        result = await agent.run(base_state)

        assert "design_doc" in result
        assert result["sender"] == "design_agent"
        assert len(result["design_doc"].page_specs) == 2
        assert result["design_doc"].design_tokens.color_primary == "#2563EB"

    @pytest.mark.asyncio
    async def test_run_without_prd_trd_returns_error(self, missing_input_state):
        """缺少 PRD 或 TRD 时应返回错误消息"""
        agent = DesignAgent(llm=MagicMock())
        result = await agent.run(missing_input_state)

        assert "design_doc" not in result
        assert result["sender"] == "design_agent"

    @pytest.mark.asyncio
    async def test_run_with_rejection_context(self, rejected_state):
        """被拒绝后应包含审查反馈上下文"""
        mock_llm = MagicMock()
        mock_llm.client.chat.completions.create = AsyncMock(
            return_value=_mock_llm_response(MOCK_DESIGN_JSON)
        )
        agent = DesignAgent(llm=mock_llm)

        result = await agent.run(rejected_state)

        assert result["design_doc"] is not None
        call_args = mock_llm.client.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]
        system_msg = messages[0]["content"]
        assert "审查员反馈" in system_msg

    @pytest.mark.asyncio
    async def test_design_node_function(self, base_state):
        """design_node 函数应正常调用"""
        import src.agents.nodes.design_node as design_mod
        design_mod._design_agent = None

        mock_llm = MagicMock()
        mock_llm.client.chat.completions.create = AsyncMock(
            return_value=_mock_llm_response(MOCK_DESIGN_JSON)
        )
        with patch("src.agents.nodes.design_node.create_llm", return_value=mock_llm):
            result = await design_node(base_state)
            assert "design_doc" in result

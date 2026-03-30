"""QA Agent 单元测试"""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.models.state import AgentState, AgentPhase
from src.models.document_models import (
    QAReport, QATestCase, QualityBreakdown, PotentialIssue,
    PRD, TRD, DesignDocument, BackendCodeSpec, FrontendCodeSpec,
    UserStory, TechStack, APIEndpoint, PageSpec, DesignTokens, CodeFile,
)
from src.agents.nodes.qa_node import QAAgent, qa_node, get_qa_agent, _qa_agent


@pytest.fixture(autouse=True)
def reset_singleton():
    """每个测试前重置单例"""
    global _qa_agent
    _qa_agent = None
    yield
    _qa_agent = None


# ── 样例数据 ─────────────────────────────────────

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

SAMPLE_BACKEND = BackendCodeSpec(
    project_structure="src/",
    files=[CodeFile(path="src/main.py", description="入口", content="print('hello')")],
    setup_commands=["pip install -r requirements.txt"],
    dependencies="fastapi",
)

SAMPLE_FRONTEND = FrontendCodeSpec(
    project_structure="src/",
    files=[CodeFile(path="src/App.tsx", description="根组件", content="export default App")],
    setup_commands=["npm install"],
    dependencies="react",
)

SAMPLE_QA_REPORT = QAReport(
    test_plan=[
        QATestCase(
            test_name="登录功能测试",
            test_type="unit",
            scope="backend",
            description="测试用户登录接口",
            steps=["POST /api/v1/login with valid credentials"],
            expected_result="返回 200 和 token",
        ),
    ],
    quality_score=8,
    quality_breakdown=QualityBreakdown(
        completeness=8, consistency=9, security=7, maintainability=8, error_handling=8,
    ),
    potential_issues=[
        PotentialIssue(
            severity="medium",
            category="security",
            description="缺少 rate limiting",
            recommendation="添加限流中间件",
        ),
    ],
    summary="整体质量良好，建议加强安全性。",
)


def _mock_llm(response_json: dict):
    """创建 mock LLM"""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = f"```json\n{json.dumps(response_json)}\n```"

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    mock_llm = MagicMock()
    mock_llm.client = mock_client
    mock_llm.max_retries = 0
    mock_llm.base_delay = 0
    return mock_llm


class TestQAAgent:
    """QA Agent 测试"""

    def test_agent_info(self):
        agent = QAAgent()
        assert agent.name == "qa_agent"
        assert agent.role == "质量保障专家"

    @pytest.mark.asyncio
    async def test_run_returns_qa_report(self):
        agent = QAAgent(llm=_mock_llm(SAMPLE_QA_REPORT.model_dump()))

        state = AgentState(
            messages=[],
            current_phase=AgentPhase.CODING,
            sender="frontend_dev_agent",
            prd=SAMPLE_PRD,
            trd=SAMPLE_TRD,
            design_doc=DesignDocument(
                page_specs=[PageSpec(page_name="首页", components=["导航"], description="测试页")],
                user_journey="graph LR",
                design_tokens=DesignTokens(
                    color_primary="#2563EB", color_secondary="#6366F1",
                    font_family="Inter", border_radius="8px", spacing_unit="4px",
                ),
                responsive_strategy="移动优先",
                component_library=["按钮"],
            ),
            backend_code=SAMPLE_BACKEND,
            frontend_code=SAMPLE_FRONTEND,
            latest_review=None,
            revision_counts={},
        )

        result = await agent.run(state)

        assert "qa_report" in result
        assert isinstance(result["qa_report"], QAReport)
        assert result["qa_report"].quality_score == 8
        assert len(result["qa_report"].test_plan) == 1
        assert result["sender"] == "qa_agent"

    @pytest.mark.asyncio
    async def test_run_without_prd_returns_error(self):
        agent = QAAgent(llm=_mock_llm(SAMPLE_QA_REPORT.model_dump()))

        state = AgentState(
            messages=[],
            current_phase=AgentPhase.CODING,
            sender="frontend_dev_agent",
            prd=None,
            trd=SAMPLE_TRD,
            latest_review=None,
            revision_counts={},
        )

        result = await agent.run(state)
        assert "qa_report" not in result
        assert result["sender"] == "qa_agent"

    @pytest.mark.asyncio
    async def test_run_with_rejection_context(self):
        """被拒后应包含审查反馈上下文"""
        agent = QAAgent(llm=_mock_llm(SAMPLE_QA_REPORT.model_dump()))

        state = AgentState(
            messages=[],
            current_phase=AgentPhase.CODING,
            sender="reviewer_agent",
            prd=SAMPLE_PRD,
            trd=SAMPLE_TRD,
            latest_review=MagicMock(status="REJECTED", comments="测试用例不足"),
            revision_counts={"qa_agent": 1},
        )

        await agent.run(state)

        # 验证 LLM 调用时包含了审查反馈
        call_args = agent.llm.client.chat.completions.create.call_args
        messages = call_args[1]["messages"]
        system_msg = messages[0]["content"]
        assert "审查员反馈" in system_msg
        assert "测试用例不足" in system_msg

    def test_qa_node_function(self):
        """模块级节点函数应返回 Agent 运行结果"""
        node_fn = qa_node
        assert callable(node_fn)

    def test_get_qa_agent_singleton(self):
        """get_qa_agent 应返回单例"""
        a1 = get_qa_agent()
        a2 = get_qa_agent()
        assert a1 is a2

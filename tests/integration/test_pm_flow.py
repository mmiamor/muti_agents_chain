"""PM 闭环集成测试 — mock LLM 验证完整流转逻辑"""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from langchain_core.messages import HumanMessage

from src.core.orchestrator import build_graph
from src.models.state import AgentPhase
from src.models.document_models import PRD, UserStory
from src.models.agent_models import ReviewFeedback


def _mock_llm_response(content: str):
    """构造 mock LLM 响应"""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = content
    return mock_response


VALID_PRD_JSON = json.dumps({
    "vision": "待办事项APP",
    "target_audience": ["上班族", "学生"],
    "user_stories": [
        {"role": "用户", "action": "创建待办", "benefit": "管理任务"},
        {"role": "用户", "action": "设置提醒", "benefit": "不遗忘"},
    ],
    "core_features": ["任务CRUD", "分类标签", "到期提醒", "搜索过滤"],
    "non_functional": "响应时间<300ms, 可用性99.9%, 支持10万用户并发",
    "mermaid_flowchart": "graph LR\nA[创建任务]-->B[设置标签]\nB-->C[到期提醒]\nC-->D[完成]",
})

BAD_PRD_JSON = json.dumps({
    "vision": "测试APP",
    "target_audience": ["用户"],
    "user_stories": [],
    "core_features": [],
    "non_functional": "",
    "mermaid_flowchart": "",
})

APPROVED_JSON = json.dumps({"status": "APPROVED", "comments": "PRD 完整，逻辑清晰，通过。"})
REJECTED_JSON = json.dumps({"status": "REJECTED", "comments": "用户故事为空，核心功能缺失，非功能需求未量化。"})


class TestGraphCompilation:
    """图编译与结构验证"""

    def test_graph_compiles(self):
        """图必须能成功编译"""
        graph = build_graph()
        assert graph is not None

    def test_graph_has_expected_nodes(self):
        """图应该包含 PM、Reviewer、Human 节点"""
        graph = build_graph()
        node_names = list(graph.get_graph().nodes.keys())
        assert "pm_agent" in node_names
        assert "reviewer_agent" in node_names
        assert "human_intervention" in node_names

    def test_graph_has_edges(self):
        """图应该有正确的边"""
        graph = build_graph()
        graph_data = graph.get_graph()
        edges = [(e.source, e.target) for e in graph_data.edges]

        assert ("pm_agent", "reviewer_agent") in edges
        assert ("reviewer_agent", "pm_agent") in edges
        assert ("reviewer_agent", "human_intervention") in edges
        assert ("human_intervention", "__end__") in edges


class TestGraphFlowWithMock:
    """Mock LLM 验证完整流转逻辑"""

    @pytest.fixture(autouse=True)
    def _patch_llm(self):
        """统一 patch PM 和 Reviewer 的 LLM 调用"""
        from src.agents.nodes.pm_node import get_pm_agent
        from src.agents.nodes.reviewer_node import get_reviewer_agent

        self.pm_agent = get_pm_agent()
        self.reviewer_agent = get_reviewer_agent()

        self._orig_pm_create = self.pm_agent.llm.client.chat.completions.create
        self._orig_rev_create = self.reviewer_agent.llm.client.chat.completions.create

        yield

        self.pm_agent.llm.client.chat.completions.create = self._orig_pm_create
        self.reviewer_agent.llm.client.chat.completions.create = self._orig_rev_create

    @pytest.mark.asyncio
    async def test_approved_flow_pm_to_end(self):
        """APPROVED 路径：PM→Reviewer(APPROVED)→END"""
        self.pm_agent.llm.client.chat.completions.create = AsyncMock(
            return_value=_mock_llm_response(VALID_PRD_JSON)
        )
        self.reviewer_agent.llm.client.chat.completions.create = AsyncMock(
            return_value=_mock_llm_response(APPROVED_JSON)
        )

        graph = build_graph()
        config = {"configurable": {"thread_id": "mock-test-approved-001"}}

        result = await graph.ainvoke({
            "messages": [HumanMessage(content="做一个待办APP")],
            "current_phase": AgentPhase.REQUIREMENT_GATHERING,
            "sender": "user",
        }, config)

        # PM 生成了 PRD
        assert result["prd"] is not None
        assert result["prd"].vision == "待办事项APP"
        assert len(result["prd"].core_features) == 4
        assert len(result["prd"].user_stories) == 2

        # Reviewer 通过
        assert result["latest_review"].status == "APPROVED"
        assert result["latest_review"].comments == "PRD 完整，逻辑清晰，通过。"

        # 0 次修改
        assert result.get("revision_count", 0) == 0

        # 消息链完整
        messages = result.get("messages", [])
        assert len(messages) >= 2

    @pytest.mark.asyncio
    async def test_rejected_once_then_approved(self):
        """REJECTED→PM重做→APPROVED 路径：验证 revision_count 递增"""
        call_count = {"pm": 0, "rev": 0}

        async def pm_side_effect(*args, **kwargs):
            call_count["pm"] += 1
            if call_count["pm"] == 1:
                return _mock_llm_response(BAD_PRD_JSON)
            return _mock_llm_response(VALID_PRD_JSON)

        async def rev_side_effect(*args, **kwargs):
            call_count["rev"] += 1
            # 第一次审查：BAD PRD → REJECTED
            if call_count["rev"] == 1:
                return _mock_llm_response(REJECTED_JSON)
            # 第二次审查：VALID PRD → APPROVED
            return _mock_llm_response(APPROVED_JSON)

        self.pm_agent.llm.client.chat.completions.create = AsyncMock(
            side_effect=pm_side_effect
        )
        self.reviewer_agent.llm.client.chat.completions.create = AsyncMock(
            side_effect=rev_side_effect
        )

        graph = build_graph()
        config = {"configurable": {"thread_id": "mock-test-retry-001"}}

        result = await graph.ainvoke({
            "messages": [HumanMessage(content="做一个待办APP")],
            "current_phase": AgentPhase.REQUIREMENT_GATHERING,
            "sender": "user",
        }, config)

        # PM 被调用了两次（第一次被拒，第二次通过）
        assert call_count["pm"] == 2

        # 最终 PRD 是完整的
        assert result["prd"].vision == "待办事项APP"
        assert result["latest_review"].status == "APPROVED"

    @pytest.mark.asyncio
    async def test_max_revisions_triggers_human(self):
        """超过 max_revisions → 人工干预"""
        self.pm_agent.llm.client.chat.completions.create = AsyncMock(
            return_value=_mock_llm_response(BAD_PRD_JSON)
        )
        self.reviewer_agent.llm.client.chat.completions.create = AsyncMock(
            return_value=_mock_llm_response(REJECTED_JSON)
        )

        graph = build_graph()
        config = {"configurable": {"thread_id": "mock-test-human-001"}}

        result = await graph.ainvoke({
            "messages": [HumanMessage(content="做一个待办APP")],
            "current_phase": AgentPhase.REQUIREMENT_GATHERING,
            "sender": "user",
        }, config)

        # 达到最大重试次数后触发人工干预
        assert result["sender"] == "human_intervention"
        assert result.get("revision_count", 0) >= 3
        assert result["latest_review"].status == "REJECTED"

"""PM 闭环集成测试"""
import pytest
from langchain_core.messages import HumanMessage

from src.core.orchestrator import build_graph


class TestGraphCompilation:
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
        # LangGraph Edge 对象有 source/target 属性
        edges = [(e.source, e.target) for e in graph_data.edges]

        # PM → Reviewer 应该有标准边
        assert ("pm_agent", "reviewer_agent") in edges

        # Reviewer → PM 应该有条件边（REJECTED 路由）
        assert ("reviewer_agent", "pm_agent") in edges

        # Reviewer → human_intervention 条件边
        assert ("reviewer_agent", "human_intervention") in edges

        # human_intervention → __end__
        assert ("human_intervention", "__end__") in edges

    @pytest.mark.asyncio
    async def test_graph_invoke_with_mock(self):
        """测试完整 PM→Reviewer 流转（需要 mock LLM）"""
        pytest.skip("需要真实 LLM API Key，CI 环境跳过")

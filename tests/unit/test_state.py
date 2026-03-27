"""全局状态单元测试"""
import pytest

from src.models.state import AgentState, AgentPhase


class TestAgentState:
    def test_default_state_construction(self):
        """AgentState 使用 TypedDict，可以构建空字典或部分填充"""
        state: AgentState = {
            "messages": [],
            "current_phase": AgentPhase.REQUIREMENT_GATHERING,
            "sender": "user",
            "prd": None,
            "trd": None,
            "latest_review": None,
            "revision_count": 0,
        }
        assert state["current_phase"] == AgentPhase.REQUIREMENT_GATHERING
        assert state["revision_count"] == 0
        assert state["prd"] is None

    def test_phase_enum_values(self):
        """AgentPhase 枚举值验证"""
        assert AgentPhase.REQUIREMENT_GATHERING == "requirement_gathering"
        assert AgentPhase.ARCHITECTURE_DESIGN == "architecture_design"
        assert AgentPhase.UI_DESIGN == "ui_design"
        assert AgentPhase.CODING == "coding"
        assert AgentPhase.TESTING == "testing"
        assert AgentPhase.FINISHED == "finished"

    def test_phase_transition(self):
        """阶段流转"""
        state: AgentState = {
            "messages": [],
            "current_phase": AgentPhase.REQUIREMENT_GATHERING,
            "sender": "user",
            "prd": None,
            "trd": None,
            "latest_review": None,
            "revision_count": 0,
        }
        state["current_phase"] = AgentPhase.ARCHITECTURE_DESIGN
        assert state["current_phase"] == "architecture_design"

    def test_messages_reducer_import(self):
        """验证 add_messages reducer 可以正常导入"""
        from langgraph.graph.message import add_messages
        assert callable(add_messages)

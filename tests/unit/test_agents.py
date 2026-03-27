"""Agent 基类与注册表单元测试"""
import pytest

from src.agents.base import BaseAgent
from src.agents.registry import AgentRegistry
from src.models.state import AgentState


class MockAgent(BaseAgent):
    name = "mock_agent"
    role = "测试 Agent"

    async def run(self, state: AgentState) -> dict:
        return {"sender": self.name}

    async def review(self, state: AgentState) -> bool:
        return True


class IncompleteAgent(BaseAgent):
    """缺少 name 属性的 Agent，用于测试注册校验"""
    role = "不完整的 Agent"

    async def run(self, state: AgentState) -> dict:
        return {}

    async def review(self, state: AgentState) -> bool:
        return False


class TestBaseAgent:
    def test_agent_info(self):
        agent = MockAgent()
        assert agent.name == "mock_agent"
        assert agent.role == "测试 Agent"

    @pytest.mark.asyncio
    async def test_agent_run(self):
        agent = MockAgent()
        result = await agent.run({})
        assert result == {"sender": "mock_agent"}

    @pytest.mark.asyncio
    async def test_agent_review(self):
        agent = MockAgent()
        assert await agent.review({}) is True

    def test_cannot_instantiate_abstract(self):
        """BaseAgent 是抽象类，不能直接实例化"""
        with pytest.raises(TypeError):
            BaseAgent()  # type: ignore


class TestAgentRegistry:
    def setup_method(self):
        AgentRegistry.clear()

    def teardown_method(self):
        AgentRegistry.clear()

    def test_register_and_get(self):
        AgentRegistry.register(MockAgent)
        assert AgentRegistry.get("mock_agent") == MockAgent

    def test_list_agents(self):
        AgentRegistry.register(MockAgent)
        assert "mock_agent" in AgentRegistry.list_agents()

    def test_get_nonexistent_raises(self):
        with pytest.raises(KeyError, match="not registered"):
            AgentRegistry.get("nonexistent")

    def test_register_without_name_raises(self):
        with pytest.raises(ValueError, match="must have a 'name' attribute"):
            AgentRegistry.register(IncompleteAgent)

    def test_clear(self):
        AgentRegistry.register(MockAgent)
        AgentRegistry.clear()
        assert AgentRegistry.list_agents() == []

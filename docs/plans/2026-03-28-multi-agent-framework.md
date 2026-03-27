# LLMChain Multi-Agent Framework 实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 基于三份飞书文档（需求文档 v1.0 + Agent 工作规范 + 8 个核心 Agent），将现有 llmchain 项目重构为 LangGraph 驱动的 Multi-Agent 应用开发框架。

**Architecture:** 采用 LangGraph StateGraph 构建状态机驱动的多 Agent 协作系统。全局 State（TypedDict）作为共享黑板，Agent 通过结构化 Pydantic 输入/输出进行通信，条件路由控制流转，Reviewer 防止质量退化，revision_count 防止死循环。分 4 个 Phase 逐步落地：Phase 1 骨架+状态，Phase 2 PM闭环，Phase 3 全链路，Phase 4 扩展。

**Tech Stack:** Python 3.13 / LangGraph / LangChain Core / Pydantic v2 / FastAPI / OpenAI SDK (智谱兼容) / Redis (缓存) / aiosqlite (持久化)

---

## Phase 0: 项目重构与依赖准备

> 目标：清理旧代码结构，安装新依赖，建立新目录骨架。

### Task 0.1: 安装新依赖

**Files:**
- Modify: `requirements.txt`

**Step 1: 更新 requirements.txt**

```
# ── Web Framework ──
fastapi>=0.115.0
uvicorn[standard]>=0.32.0

# ── LLM & Agent ──
langchain>=0.3.0
langchain-core>=0.3.0
langchain-openai>=0.3.0
langgraph>=0.2.0
openai>=1.60.0

# ── Data & Validation ──
pydantic>=2.10.0
pyyaml>=6.0.0

# ── Infrastructure ──
python-dotenv>=1.0.1
httpx>=0.28.0
aiosqlite>=0.20.0
redis>=5.2.0

# ── Dev ──
pytest>=8.0.0
pytest-asyncio>=0.24.0
```

**Step 2: 安装依赖**

```bash
cd D:\CODES\llmchain
pip install -r requirements.txt
```

Expected: 所有包安装成功，无报错

**Step 3: Commit**

```bash
git add requirements.txt
git commit -m "chore: update deps for langgraph multi-agent framework"
```

---

### Task 0.2: 建立新目录结构

**Files:**
- Create: `src/agents/__init__.py`
- Create: `src/agents/base.py`
- Create: `src/agents/context.py`
- Create: `src/agents/registry.py`
- Create: `src/agents/nodes/__init__.py`
- Create: `src/memory/__init__.py`
- Create: `src/memory/base.py`
- Create: `src/memory/factory.py`
- Create: `src/models/agent_models.py`
- Create: `src/models/document_models.py`
- Create: `src/models/state.py`
- Create: `src/prompts/__init__.py`
- Create: `src/utils/validators.py`
- Create: `src/api/streaming.py`
- Create: `docs/plans/.gitkeep`
- Create: `tests/fixtures/.gitkeep`

**Step 1: 创建目录骨架**

```bash
cd D:\CODES\llmchain
# 新目录
New-Item -ItemType Directory -Path src/agents/nodes -Force
New-Item -ItemType Directory -Path src/memory -Force
New-Item -ItemType Directory -Path src/prompts -Force
New-Item -ItemType Directory -Path tests/fixtures -Force

# __init__.py 文件
"" | Set-Content src/agents/__init__.py
"" | Set-Content src/agents/nodes/__init__.py
"" | Set-Content src/memory/__init__.py
"" | Set-Content src/prompts/__init__.py
"" | Set-Content tests/fixtures/__init__.py
"" | Set-Content tests/fixtures/.gitkeep
"" | Set-Content docs/plans/.gitkeep
```

**Step 2: 验证目录结构**

```bash
Get-ChildItem -Path src -Recurse -Name -Directory
```

Expected: `agents`, `agents/nodes`, `api`, `config`, `core`, `memory`, `models`, `prompts`, `services`, `utils`

**Step 3: Commit**

```bash
git add -A
git commit -m "chore: scaffold new directory structure for multi-agent framework"
```

---

### Task 0.3: 更新 .env.example

**Files:**
- Modify: `.env.example`

**Step 1: 更新环境变量模板**

```env
# ── LLM API (智谱 GLM) ──
ZAI_API_KEY=sk-your-key-here
OPENAI_API_KEY=sk-your-key-here
OPENAI_BASE_URL=https://open.bigmodel.cn/api/paas/v4/
DEFAULT_MODEL=glm-5

# ── 服务配置 ──
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=true
LOG_LEVEL=INFO

# ── Redis ──
REDIS_URL=redis://localhost:6379/0

# ── 数据库 ──
DATABASE_URL=sqlite+aiosqlite:///./data/app.db

# ── Agent 配置 ──
MAX_REVISION_COUNT=3
RECURSION_LIMIT=30
STREAM_ENABLED=true
```

**Step 2: Commit**

```bash
git add .env.example
git commit -m "chore: update env template for multi-agent config"
```

---

## Phase 1: 状态定义与核心骨架

> 目标：定义全局 State、数据模型、Agent 基类，搭建 LangGraph StateGraph 骨架。

### Task 1.1: 定义 Pydantic 数据模型

**Files:**
- Create: `src/models/document_models.py`
- Create: `src/models/agent_models.py`
- Test: `tests/unit/test_models.py`

**Step 1: 写失败测试**

```python
# tests/unit/test_models.py
"""数据模型单元测试"""
import pytest
from pydantic import ValidationError
from src.models.document_models import (
    UserStory, PRD, TechStack, APIEndpoint, TRD
)
from src.models.agent_models import ReviewFeedback


class TestPRD:
    def test_valid_prd(self):
        prd = PRD(
            vision="做最便捷的遛狗平台",
            target_audience=["城市养宠人群"],
            user_stories=[UserStory(role="用户", action="找遛狗师", benefit="省心")],
            core_features=["发布需求", "匹配遛狗师"],
            non_functional="响应时间<2s",
            mermaid_flowchart="graph LR\nA[发布需求]-->B[匹配]",
        )
        assert prd.vision == "做最便捷的遛狗平台"
        assert len(prd.user_stories) == 1

    def test_prd_missing_required_fields(self):
        with pytest.raises(ValidationError):
            PRD(vision="test")  # 缺少必填字段


class TestTRD:
    def test_valid_trd(self):
        trd = TRD(
            tech_stack=TechStack(
                frontend="React + Tailwind",
                backend="FastAPI + Python",
                database="PostgreSQL + Redis",
                infrastructure="Docker + AWS",
            ),
            architecture_overview="微服务架构",
            mermaid_er_diagram="erDiagram\nUSER ||--o{ ORDER",
            api_endpoints=[
                APIEndpoint(path="/api/v1/users", method="GET", description="获取用户列表")
            ],
        )
        assert len(trd.api_endpoints) == 1


class TestReviewFeedback:
    def test_approved(self):
        fb = ReviewFeedback(status="APPROVED", comments="很好")
        assert fb.status == "APPROVED"

    def test_invalid_status(self):
        with pytest.raises(ValidationError):
            ReviewFeedback(status="MAYBE", comments="不支持")
```

**Step 2: 运行测试确认失败**

```bash
cd D:\CODES\llmchain
pytest tests/unit/test_models.py -v
```

Expected: FAIL — ModuleNotFoundError: No module named 'src.models.document_models'

**Step 3: 实现 document_models.py**

```python
# src/models/document_models.py
"""核心交付物数据模型 — PRD / TRD"""
from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field


# ── PRD 相关 ─────────────────────────────────────────

class UserStory(BaseModel):
    """用户故事：作为...我想...以便..."""
    role: str = Field(description="用户角色，例如：普通用户、管理员")
    action: str = Field(description="想要执行的动作")
    benefit: str = Field(description="带来的核心价值")


class PRD(BaseModel):
    """产品需求文档"""
    vision: str = Field(description="产品核心愿景与一句话定位")
    target_audience: list[str] = Field(description="目标用户群体描述")
    user_stories: list[UserStory] = Field(description="核心用户故事列表")
    core_features: list[str] = Field(description="核心功能模块列表")
    non_functional: str = Field(description="非功能性需求（性能、可用性等）")
    mermaid_flowchart: str = Field(description="业务流程图的 Mermaid 语法代码")


# ── TRD 相关 ─────────────────────────────────────────

class TechStack(BaseModel):
    """技术栈选型"""
    frontend: str = Field(description="前端框架及核心库")
    backend: str = Field(description="后端框架及核心语言")
    database: str = Field(description="主数据库及缓存选型")
    infrastructure: str = Field(description="部署与运维设施")


class APIEndpoint(BaseModel):
    """API 接口定义"""
    path: str = Field(description="API 路径，例如：/api/v1/users")
    method: Literal["GET", "POST", "PUT", "DELETE", "PATCH"] = Field(description="HTTP 方法")
    description: str = Field(description="接口功能描述")


class TRD(BaseModel):
    """技术设计文档"""
    tech_stack: TechStack = Field(description="系统技术栈选型")
    architecture_overview: str = Field(description="高层架构设计说明")
    mermaid_er_diagram: str = Field(description="数据库 ER 图的 Mermaid 语法代码")
    api_endpoints: list[APIEndpoint] = Field(description="核心 API 接口列表")
```

**Step 4: 实现 agent_models.py**

```python
# src/models/agent_models.py
"""Agent 相关模型 — Review / Registry"""
from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field


class ReviewFeedback(BaseModel):
    """审查反馈"""
    status: Literal["APPROVED", "REJECTED"] = Field(description="审查结果")
    comments: str = Field(description="审查意见与修改建议")


class AgentInfo(BaseModel):
    """Agent 注册信息"""
    name: str = Field(description="Agent 标识名")
    role: str = Field(description="角色描述")
    description: str = Field(description="能力描述")
    input_schema: str = Field(description="输入模型类名")
    output_schema: str = Field(description="输出模型类名")
```

**Step 5: 运行测试确认通过**

```bash
pytest tests/unit/test_models.py -v
```

Expected: 4 tests PASSED

**Step 6: Commit**

```bash
git add src/models/document_models.py src/models/agent_models.py tests/unit/test_models.py
git commit -m "feat: add Pydantic data models for PRD, TRD, ReviewFeedback"
```

---

### Task 1.2: 定义全局 State

**Files:**
- Create: `src/models/state.py`
- Test: `tests/unit/test_state.py`

**Step 1: 写失败测试**

```python
# tests/unit/test_state.py
"""全局状态单元测试"""
from src.models.state import AgentState, AgentPhase


class TestAgentState:
    def test_default_state(self):
        state = AgentState()
        assert state.current_phase == AgentPhase.REQUIREMENT_GATHERING
        assert state.revision_count == 0
        assert state.prd is None
        assert state.trd is None
        assert state.latest_review is None
        assert state.messages == []

    def test_phase_transition(self):
        state = AgentState()
        state.current_phase = AgentPhase.ARCHITECTURE_DESIGN
        assert state.current_phase == "architecture_design"
```

**Step 2: 运行测试确认失败**

```bash
pytest tests/unit/test_state.py -v
```

**Step 3: 实现 state.py**

```python
# src/models/state.py
"""全局状态定义 — LangGraph StateGraph 共享黑板"""
from __future__ import annotations

from typing import Annotated, Optional
from enum import Enum
from typing_extensions import TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

from src.models.document_models import PRD, TRD
from src.models.agent_models import ReviewFeedback


class AgentPhase(str, Enum):
    """开发阶段"""
    REQUIREMENT_GATHERING = "requirement_gathering"
    ARCHITECTURE_DESIGN = "architecture_design"
    UI_DESIGN = "ui_design"
    CODING = "coding"
    TESTING = "testing"
    FINISHED = "finished"


class AgentState(TypedDict):
    """
    Multi-Agent 系统全局状态黑板

    - messages: 使用 add_messages reducer，新消息追加而非覆盖
    - artifacts: 独立于 messages，下游 Agent 直接读取结构化数据
    - review: 控制流转的「红绿灯」
    - revision_count: 防止死循环的「安全阀」
    """
    # 消息历史（追加式）
    messages: Annotated[list[BaseMessage], add_messages]

    # 当前阶段
    current_phase: AgentPhase

    # 上一个发送消息的 Agent 名称（用于路由判断）
    sender: str

    # 核心产出物
    prd: Optional[PRD]
    trd: Optional[TRD]

    # 审查状态
    latest_review: Optional[ReviewFeedback]
    revision_count: int
```

**Step 4: 运行测试确认通过**

```bash
pytest tests/unit/test_state.py -v
```

Expected: 2 tests PASSED

**Step 5: Commit**

```bash
git add src/models/state.py tests/unit/test_state.py
git commit -m "feat: define global AgentState with LangGraph TypedDict"
```

---

### Task 1.3: 定义 Agent 基类与注册表

**Files:**
- Create: `src/agents/base.py`
- Create: `src/agents/registry.py`
- Create: `src/agents/context.py`
- Test: `tests/unit/test_agents.py`

**Step 1: 写失败测试**

```python
# tests/unit/test_agents.py
"""Agent 基类与注册表单元测试"""
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


class TestBaseAgent:
    def test_agent_info(self):
        agent = MockAgent()
        assert agent.name == "mock_agent"
        assert agent.role == "测试 Agent"


class TestAgentRegistry:
    def setup_method(self):
        AgentRegistry._agents.clear()

    def test_register_and_get(self):
        AgentRegistry.register(MockAgent)
        assert AgentRegistry.get("mock_agent") == MockAgent

    def test_list_agents(self):
        AgentRegistry.register(MockAgent)
        assert "mock_agent" in AgentRegistry.list_agents()

    def test_get_nonexistent_raises(self):
        with pytest.raises(KeyError):
            AgentRegistry.get("nonexistent")
```

**Step 2: 运行测试确认失败**

```bash
pytest tests/unit/test_agents.py -v
```

**Step 3: 实现 context.py**

```python
# src/agents/context.py
"""Agent 上下文对象 — 封装依赖注入"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from src.services.llm_service import LLMService
from src.memory.base import MemoryBackend


@dataclass
class AgentContext:
    """Agent 执行上下文，封装所有外部依赖"""
    llm: LLMService
    memory: Optional[MemoryBackend] = None
    config: dict[str, Any] = field(default_factory=dict)
```

**Step 4: 实现 base.py**

```python
# src/agents/base.py
"""Agent 基类 — 所有 Agent 必须继承"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.models.state import AgentState
    from src.agents.context import AgentContext


class BaseAgent(ABC):
    """
    Agent 基类

    每个 Agent 必须：
    1. 声明 name 和 role
    2. 实现 run() — 核心执行逻辑，返回 State 更新字典
    3. 实现 review() — 自我反思，检查输出质量
    """
    name: str
    role: str
    description: str = ""

    @abstractmethod
    async def run(self, state: "AgentState") -> dict:
        """
        核心执行方法

        接收当前 State，返回需要更新的 State 字典。
        LangGraph 会自动将返回值 merge 到全局 State。
        """
        ...

    @abstractmethod
    async def review(self, state: "AgentState") -> bool:
        """
        自我反思 — 检查上一次 run 的输出质量

        Returns:
            True 表示通过，False 表示需要重做
        """
        ...
```

**Step 5: 实现 registry.py**

```python
# src/agents/registry.py
"""Agent 注册表 — 统一管理所有 Agent"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.agents.base import BaseAgent


class AgentRegistry:
    """全局 Agent 注册表"""
    _agents: dict[str, type["BaseAgent"]] = {}

    @classmethod
    def register(cls, agent_class: type["BaseAgent"]) -> None:
        cls._agents[agent_class.name] = agent_class

    @classmethod
    def get(cls, name: str) -> type["BaseAgent"]:
        if name not in cls._agents:
            raise KeyError(f"Agent '{name}' not registered. Available: {list(cls._agents.keys())}")
        return cls._agents[name]

    @classmethod
    def list_agents(cls) -> list[str]:
        return list(cls._agents.keys())

    @classmethod
    def clear(cls) -> None:
        cls._agents.clear()
```

**Step 6: 运行测试确认通过**

```bash
pytest tests/unit/test_agents.py -v
```

Expected: 4 tests PASSED

**Step 7: Commit**

```bash
git add src/agents/ src/tests/unit/test_agents.py
git commit -m "feat: add BaseAgent, AgentRegistry, AgentContext"
```

---

### Task 1.4: 更新 settings.py 支持新配置

**Files:**
- Modify: `src/config/settings.py`

**Step 1: 追加新配置项**

在 `Settings` 类末尾追加：

```python
    # ── Agent 配置 ──
    MAX_REVISION_COUNT: int = int(os.getenv("MAX_REVISION_COUNT", "3"))
    RECURSION_LIMIT: int = int(os.getenv("RECURSION_LIMIT", "30"))
    STREAM_ENABLED: bool = os.getenv("STREAM_ENABLED", "true").lower() in ("1", "true", "yes")

    # ── Storage ──
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/app.db")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
```

**Step 2: 验证导入无报错**

```bash
python -c "from src.config.settings import settings; print(settings.MAX_REVISION_COUNT)"
```

Expected: `3`

**Step 3: Commit**

```bash
git add src/config/settings.py
git commit -m "feat: add agent and storage config to settings"
```

---

## Phase 2: PM Agent 闭环（需求 → 审查 → 通过/打回）

> 目标：实现 PM Agent + Reviewer Agent + 条件路由，完成需求阶段的完整闭环。

### Task 2.1: PM Agent System Prompt

**Files:**
- Create: `src/prompts/pm_agent.py`

**Step 1: 创建 PM Prompt**

```python
# src/prompts/pm_agent.py
"""PM Agent 系统提示词"""
SYSTEM_PROMPT = """你是一位拥有 10 年经验的资深产品经理。

## 你的职责
1. 与用户对话，挖掘真实需求，澄清产品边界
2. 进行竞品与市场分析
3. 生成结构化的产品需求文档（PRD）

## 工作原则
- 主动提问，不要假设用户已经想清楚了所有细节
- 聚焦核心价值，砍掉不必要的需求
- 用「作为...我想...以便...」的格式书写用户故事
- 非功能需求必须量化（响应时间、并发量、可用性等）
- 业务流程图使用 Mermaid 语法，格式必须正确

## 禁止事项
- 禁止编造不存在的竞品或市场数据
- 禁止输出纯文本形式的 PRD，必须严格按照 JSON Schema 输出
- 禁止超出用户描述范围添加功能

## 当前阶段
你需要根据用户的想法，输出一份完整的 PRD 文档。如果信息不足，先提出 3-5 个关键问题。
"""
```

**Step 2: Commit**

```bash
git add src/prompts/pm_agent.py
git commit -m "feat: add PM Agent system prompt"
```

---

### Task 2.2: Reviewer Agent System Prompt

**Files:**
- Create: `src/prompts/reviewer_agent.py`

**Step 1: 创建 Reviewer Prompt**

```python
# src/prompts/reviewer_agent.py
"""Reviewer Agent 系统提示词"""
SYSTEM_PROMPT = """你是一位严谨的代码与文档审查专家。

## 你的职责
交叉检查产出物是否满足上游需求，决定是否通过或打回重做。

## 审查维度
1. **完整性**：是否有遗漏的功能点或非功能需求？
2. **一致性**：产出物是否与上游文档（如 PRD → TRD）严格对齐？
3. **可行性**：技术方案是否合理？是否有明显的技术风险？
4. **格式规范**：Mermaid 语法是否正确？JSON 结构是否完整？

## 输出规范
- status: "APPROVED" 或 "REJECTED"
- comments: 具体的修改建议（如果 REJECTED）

## 原则
- 如果只是微小格式问题，优先 APPROVED 并在 comments 中建议改进
- 只有在核心逻辑缺失或明显错误时才 REJECTED
- 不要因为风格偏好而 REJECTED
"""
```

**Step 2: Commit**

```bash
git add src/prompts/reviewer_agent.py
git commit -m "feat: add Reviewer Agent system prompt"
```

---

### Task 2.3: 实现 PM Agent 节点

**Files:**
- Create: `src/agents/nodes/pm_node.py`
- Modify: `src/agents/nodes/__init__.py`
- Test: `tests/unit/test_pm_node.py`

**Step 1: 写失败测试**

```python
# tests/unit/test_pm_node.py
"""PM Agent 节点单元测试"""
import pytest
from unittest.mock import AsyncMock, patch
from langchain_core.messages import HumanMessage, AIMessage

from src.agents.nodes.pm_node import pm_node
from src.models.state import AgentState, AgentPhase


@pytest.fixture
def base_state():
    return AgentState(
        messages=[HumanMessage(content="我想做一个遛狗APP")],
        current_phase=AgentPhase.REQUIREMENT_GATHERING,
        sender="user",
        prd=None,
        trd=None,
        latest_review=None,
        revision_count=0,
    )


class TestPMNode:
    @pytest.mark.asyncio
    async def test_pm_node_returns_prd(self, base_state):
        """PM Agent 应该返回包含 PRD 的状态更新"""
        with patch("src.agents.nodes.pm_node.pm_agent") as mock_agent:
            from src.models.document_models import PRD, UserStory
            mock_prd = PRD(
                vision="遛狗平台",
                target_audience=["养宠人群"],
                user_stories=[UserStory(role="用户", action="找遛狗师", benefit="省心")],
                core_features=["发布需求"],
                non_functional="响应<2s",
                mermaid_flowchart="graph LR",
            )
            mock_agent.run.return_value = {
                "prd": mock_prd,
                "sender": "pm_agent",
            }

            result = await pm_node(base_state)
            assert "prd" in result
            assert result["prd"].vision == "遛狗平台"
            assert result["sender"] == "pm_agent"
```

**Step 2: 运行测试确认失败**

```bash
pytest tests/unit/test_pm_node.py -v
```

**Step 3: 实现 pm_node.py**

```python
# src/agents/nodes/pm_node.py
"""PM Agent — LangGraph 节点函数"""
from __future__ import annotations

from langchain_core.messages import SystemMessage, AIMessage

from src.config import settings
from src.models.state import AgentState
from src.models.document_models import PRD
from src.services.llm_service import LLMService
from src.prompts.pm_agent import SYSTEM_PROMPT


# 初始化 LLM 服务
_llm = LLMService(
    api_key=settings.ZAI_API_KEY,
    base_url=settings.OPENAI_BASE_URL,
    default_model=settings.DEFAULT_MODEL,
)


class PMAgent:
    """PM Agent 实现"""

    name = "pm_agent"
    role = "资深产品经理"

    def __init__(self, llm: LLMService):
        self.llm = llm

    async def run(self, state: AgentState) -> dict:
        """分析需求，生成 PRD"""
        # 构建消息
        messages = [SystemMessage(content=SYSTEM_PROMPT)]
        messages.extend(state["messages"])

        # 调用 LLM 并强制结构化输出
        structured_llm = self.llm.client.chat.completions
        response = await structured_llm.create(
            model=settings.DEFAULT_MODEL,
            messages=[{"role": m.type, "content": m.content} for m in messages],
            temperature=0,
            response_format={"type": "json_object"},
        )

        import json
        content = response.choices[0].message.content
        prd_data = json.loads(content)

        prd = PRD(**prd_data)

        return {
            "prd": prd,
            "sender": self.name,
            "messages": [AIMessage(content=f"PM Agent 已生成 PRD:\n{prd.vision}")],
        }

    async def review(self, state: AgentState) -> bool:
        """自我反思"""
        prd = state.get("prd")
        if not prd:
            return False
        # 基本完整性检查
        return bool(prd.vision and prd.user_stories and prd.core_features)


pm_agent = PMAgent(_llm)


async def pm_node(state: AgentState) -> dict:
    """LangGraph 节点函数 — PM Agent 入口"""
    return await pm_agent.run(state)
```

**Step 4: 运行测试确认通过**

```bash
pytest tests/unit/test_pm_node.py -v
```

Expected: PASSED

**Step 5: Commit**

```bash
git add src/agents/nodes/pm_node.py src/agents/nodes/__init__.py tests/unit/test_pm_node.py
git commit -m "feat: implement PM Agent node with structured PRD output"
```

---

### Task 2.4: 实现 Reviewer Agent 节点

**Files:**
- Create: `src/agents/nodes/reviewer_node.py`
- Test: `tests/unit/test_reviewer_node.py`

**Step 1: 写失败测试**

```python
# tests/unit/test_reviewer_node.py
"""Reviewer Agent 节点单元测试"""
import pytest
from unittest.mock import AsyncMock, patch
from langchain_core.messages import HumanMessage

from src.agents.nodes.reviewer_node import reviewer_node
from src.models.state import AgentState, AgentPhase
from src.models.document_models import PRD, UserStory
from src.models.agent_models import ReviewFeedback


@pytest.fixture
def state_with_prd():
    return AgentState(
        messages=[HumanMessage(content="做一个遛狗APP")],
        current_phase=AgentPhase.REQUIREMENT_GATHERING,
        sender="pm_agent",
        prd=PRD(
            vision="遛狗平台",
            target_audience=["养宠人群"],
            user_stories=[UserStory(role="用户", action="找遛狗师", benefit="省心")],
            core_features=["发布需求", "匹配遛狗师"],
            non_functional="响应<2s",
            mermaid_flowchart="graph LR\nA-->B",
        ),
        trd=None,
        latest_review=None,
        revision_count=0,
    )


class TestReviewerNode:
    @pytest.mark.asyncio
    async def test_reviewer_returns_feedback(self, state_with_prd):
        """Reviewer 应该返回 ReviewFeedback"""
        with patch("src.agents.nodes.reviewer_node.reviewer_agent") as mock:
            mock.run.return_value = {
                "latest_review": ReviewFeedback(
                    status="APPROVED", comments="PRD 完整，通过"
                ),
                "sender": "reviewer_agent",
            }

            result = await reviewer_node(state_with_prd)
            assert "latest_review" in result
            assert result["latest_review"].status == "APPROVED"
```

**Step 2: 运行测试确认失败**

```bash
pytest tests/unit/test_reviewer_node.py -v
```

**Step 3: 实现 reviewer_node.py**

```python
# src/agents/nodes/reviewer_node.py
"""Reviewer Agent — LangGraph 节点函数"""
from __future__ import annotations

import json

from langchain_core.messages import SystemMessage, AIMessage

from src.config import settings
from src.models.state import AgentState
from src.models.agent_models import ReviewFeedback
from src.services.llm_service import LLMService
from src.prompts.reviewer_agent import SYSTEM_PROMPT


_llm = LLMService(
    api_key=settings.ZAI_API_KEY,
    base_url=settings.OPENAI_BASE_URL,
    default_model=settings.DEFAULT_MODEL,
)


class ReviewerAgent:
    """Reviewer Agent 实现"""

    name = "reviewer_agent"
    role = "审查专家"

    def __init__(self, llm: LLMService):
        self.llm = llm

    async def run(self, state: AgentState) -> dict:
        """审查产出物，返回 APPROVED 或 REJECTED"""
        sender = state.get("sender", "")

        # 确定审查目标
        review_target = ""
        if sender == "pm_agent" and state.get("prd"):
            review_target = f"请审查以下 PRD：\n{state['prd'].model_dump_json(indent=2)}"

        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            {"role": "user", "content": review_target},
        ]

        response = await self.llm.client.chat.completions.create(
            model=settings.DEFAULT_MODEL,
            messages=messages,
            temperature=0,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content
        feedback_data = json.loads(content)
        feedback = ReviewFeedback(**feedback_data)

        return {
            "latest_review": feedback,
            "sender": self.name,
            "messages": [AIMessage(content=f"Reviewer: {feedback.status} — {feedback.comments}")],
        }

    async def review(self, state: AgentState) -> bool:
        return state.get("latest_review", None) is not None


reviewer_agent = ReviewerAgent(_llm)


async def reviewer_node(state: AgentState) -> dict:
    """LangGraph 节点函数 — Reviewer Agent 入口"""
    return await reviewer_agent.run(state)
```

**Step 4: 运行测试确认通过**

```bash
pytest tests/unit/test_reviewer_node.py -v
```

**Step 5: Commit**

```bash
git add src/agents/nodes/reviewer_node.py tests/unit/test_reviewer_node.py
git commit -m "feat: implement Reviewer Agent node with approve/reject logic"
```

---

### Task 2.5: 实现条件路由

**Files:**
- Create: `src/core/orchestrator.py`
- Test: `tests/unit/test_orchestrator.py`

**Step 1: 写失败测试**

```python
# tests/unit/test_orchestrator.py
"""编排器与路由逻辑单元测试"""
from src.models.state import AgentState, AgentPhase
from src.models.agent_models import ReviewFeedback
from src.core.orchestrator import review_router


class TestReviewRouter:
    def test_approved_goes_to_architect(self):
        state = AgentState(
            messages=[],
            current_phase=AgentPhase.REQUIREMENT_GATHERING,
            sender="reviewer_agent",
            prd=None,
            trd=None,
            latest_review=ReviewFeedback(status="APPROVED", comments="OK"),
            revision_count=0,
        )
        assert review_router(state) == "architect_agent"

    def test_rejected_goes_back_to_pm(self):
        state = AgentState(
            messages=[],
            current_phase=AgentPhase.REQUIREMENT_GATHERING,
            sender="reviewer_agent",
            prd=None,
            trd=None,
            latest_review=ReviewFeedback(status="REJECTED", comments="缺少用户故事"),
            revision_count=0,
        )
        assert review_router(state) == "pm_agent"

    def test_max_revision_triggers_human(self):
        state = AgentState(
            messages=[],
            current_phase=AgentPhase.REQUIREMENT_GATHERING,
            sender="reviewer_agent",
            prd=None,
            trd=None,
            latest_review=ReviewFeedback(status="REJECTED", comments="还是不行"),
            revision_count=3,
        )
        assert review_router(state) == "human_intervention"

    def test_no_review_goes_back_to_pm(self):
        state = AgentState(
            messages=[],
            current_phase=AgentPhase.REQUIREMENT_GATHERING,
            sender="reviewer_agent",
            prd=None,
            trd=None,
            latest_review=None,
            revision_count=0,
        )
        assert review_router(state) == "pm_agent"
```

**Step 2: 运行测试确认失败**

```bash
pytest tests/unit/test_orchestrator.py -v
```

**Step 3: 实现 orchestrator.py**

```python
# src/core/orchestrator.py
"""Multi-Agent 编排器 — LangGraph 图构建与条件路由"""
from __future__ import annotations

from src.config import settings
from src.models.state import AgentState
from src.models.agent_models import ReviewFeedback
from src.utils.logger import setup_logger

logger = setup_logger("orchestrator")

# ── Agent 名称常量 ─────────────────────────────────

class AgentNames:
    PM = "pm_agent"
    REVIEWER = "reviewer_agent"
    ARCHITECT = "architect_agent"
    DESIGN = "design_agent"
    FRONTEND_DEV = "frontend_dev_agent"
    BACKEND_DEV = "backend_dev_agent"
    QA = "qa_agent"
    HUMAN = "human_intervention"


# ── 路由函数 ──────────────────────────────────────

def review_router(state: AgentState) -> str:
    """
    Reviewer 节点后的条件路由

    决策逻辑：
    1. 无审查结果 → 打回 PM 重做
    2. APPROVED → 流转下一阶段（架构师）
    3. REJECTED + 超过最大重试次数 → 人工干预
    4. REJECTED + 还有机会 → 打回 PM 重做
    """
    latest_review: ReviewFeedback | None = state.get("latest_review")
    revision_count: int = state.get("revision_count", 0)
    max_revisions = settings.MAX_REVISION_COUNT

    if not latest_review:
        logger.warning("No review result, routing back to PM")
        return AgentNames.PM

    if latest_review.status == "APPROVED":
        logger.info("✅ Review approved, proceeding to Architect")
        return AgentNames.ARCHITECT

    if revision_count >= max_revisions:
        logger.warning(
            f"🚨 Max revisions ({revision_count}) exceeded, triggering human intervention"
        )
        return AgentNames.HUMAN

    logger.info(
        f"❌ Review rejected ({revision_count}/{max_revisions}): {latest_review.comments}"
    )
    return AgentNames.PM


# ── 图构建 ────────────────────────────────────────

def build_graph():
    """
    构建 LangGraph StateGraph

    Phase 2 闭环：PM → Reviewer → (APPROVED: Architect | REJECTED: PM)
    """
    from langgraph.graph import StateGraph, END

    from src.agents.nodes.pm_node import pm_node
    from src.agents.nodes.reviewer_node import reviewer_node

    workflow = StateGraph(AgentState)

    # 注册节点
    workflow.add_node(AgentNames.PM, pm_node)
    workflow.add_node(AgentNames.REVIEWER, reviewer_node)

    # 人工干预节点（Phase 2 暂为占位）
    async def human_node(state: AgentState) -> dict:
        return {"sender": "human_intervention"}
    workflow.add_node(AgentNames.HUMAN, human_node)

    # 设置入口
    workflow.set_entry_point(AgentNames.PM)

    # 标准边：PM → Reviewer
    workflow.add_edge(AgentNames.PM, AgentNames.REVIEWER)

    # 条件边：Reviewer → ?
    workflow.add_conditional_edges(
        AgentNames.REVIEWER,
        review_router,
        {
            AgentNames.ARCHITECT: AgentNames.ARCHITECT,
            AgentNames.PM: AgentNames.PM,
            AgentNames.HUMAN: AgentNames.HUMAN,
        },
    )

    # 人工干预 → 结束
    workflow.add_edge(AgentNames.HUMAN, END)

    # 编译图
    from langgraph.checkpoint.memory import MemorySaver
    memory = MemorySaver()

    return workflow.compile(
        checkpointer=memory,
    )
```

**Step 4: 运行测试确认通过**

```bash
pytest tests/unit/test_orchestrator.py -v
```

Expected: 4 tests PASSED

**Step 5: Commit**

```bash
git add src/core/orchestrator.py tests/unit/test_orchestrator.py
git commit -m "feat: implement orchestrator with conditional routing (PM review loop)"
```

---

### Task 2.6: 集成测试 — PM 闭环

**Files:**
- Create: `tests/integration/test_pm_flow.py`

**Step 1: 写集成测试**

```python
# tests/integration/test_pm_flow.py
"""PM Agent 完整闭环集成测试"""
import pytest
from langchain_core.messages import HumanMessage

from src.core.orchestrator import build_graph
from src.models.state import AgentState


class TestPMFlow:
    @pytest.mark.asyncio
    async def test_graph_compiles(self):
        """图必须能成功编译"""
        graph = build_graph()
        assert graph is not None

    @pytest.mark.asyncio
    async def test_pm_to_reviewer_flow(self):
        """测试 PM → Reviewer 的基本流转"""
        graph = build_graph()
        config = {"configurable": {"thread_id": "test-pm-flow"}}

        # 注意：此测试需要真实 LLM API，标记为 slow
        pytest.skip("需要真实 LLM API Key，CI 环境跳过")
```

**Step 2: 验证图编译**

```bash
pytest tests/integration/test_pm_flow.py::TestPMFlow::test_graph_compiles -v
```

Expected: PASSED

**Step 3: Commit**

```bash
git add tests/integration/test_pm_flow.py
git commit -m "test: add PM flow integration test skeleton"
```

---

### Task 2.7: 更新 API 路由

**Files:**
- Modify: `src/api/routes.py`

**Step 1: 添加 Pipeline 端点**

在 `routes.py` 中追加：

```python
from src.core.orchestrator import build_graph

# ── Pipeline 端点 ──

@router.post("/pipeline/run")
async def run_pipeline(prompt: str, thread_id: str = "default"):
    """运行完整流水线（PM → Reviewer → ...）"""
    try:
        graph = build_graph()
        config = {"configurable": {"thread_id": thread_id}}

        initial_state = {
            "messages": [HumanMessage(content=prompt)],
            "current_phase": "requirement_gathering",
            "sender": "user",
            "prd": None,
            "trd": None,
            "latest_review": None,
            "revision_count": 0,
        }

        result = await graph.ainvoke(initial_state, config)
        return {
            "status": "completed",
            "prd": result.get("prd").model_dump() if result.get("prd") else None,
            "review": result.get("latest_review").model_dump() if result.get("latest_review") else None,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

**Step 2: 验证导入无报错**

```bash
python -c "from src.api.routes import router; print('OK')"
```

**Step 3: Commit**

```bash
git add src/api/routes.py
git commit -m "feat: add /pipeline/run API endpoint"
```

---

## Phase 3: 全链路（Architect + Design + Dev + QA）

> 目标：扩展到 8 个 Agent，完成完整的 SDLC 闭环。

### Task 3.1: Architect Agent

**Files:**
- Create: `src/prompts/arch_agent.py`
- Create: `src/agents/nodes/arch_node.py`
- Test: `tests/unit/test_arch_node.py`

**Step 1: 实现 Arch Prompt + Agent 节点**

参照 Task 2.3 的模式，实现：
- `src/prompts/arch_agent.py` — 架构师系统提示词（强调技术栈选型、ER 图、API 设计）
- `src/agents/nodes/arch_node.py` — 读取 State 中的 PRD，调用 LLM 生成 TRD

**Step 2: 写测试并验证**

```bash
pytest tests/unit/test_arch_node.py -v
```

**Step 3: Commit**

```bash
git add src/prompts/arch_agent.py src/agents/nodes/arch_node.py tests/unit/test_arch_node.py
git commit -m "feat: implement Architect Agent node with TRD output"
```

---

### Task 3.2: Design Agent

**Files:**
- Create: `src/prompts/design_agent.py`
- Create: `src/agents/nodes/design_node.py`
- Create: `src/models/document_models.py` (追加 ComponentTree 模型)

**Step 1: 追加 Design 产出模型**

在 `document_models.py` 末尾追加：

```python
class ComponentNode(BaseModel):
    """UI 组件节点"""
    name: str = Field(description="组件名称")
    type: str = Field(description="组件类型（Page/Layout/Widget）")
    children: list[str] = Field(default_factory=list, description="子组件 ID")
    props: dict[str, str] = Field(default_factory=dict, description="组件属性")

class ComponentTree(BaseModel):
    """前端组件树"""
    pages: list[ComponentNode] = Field(description="页面列表")
    shared_components: list[ComponentNode] = Field(description="公共组件")
    route_structure: str = Field(description="页面路由结构的 Mermaid 图")
```

**Step 2: 实现 Design Agent**

参照 PM Agent 模式，读取 PRD 生成 ComponentTree

**Step 3: Commit**

```bash
git commit -m "feat: implement Design Agent with component tree output"
```

---

### Task 3.3: Frontend Dev + Backend Dev Agent

**Files:**
- Create: `src/prompts/frontend_dev_agent.py`
- Create: `src/prompts/backend_dev_agent.py`
- Create: `src/agents/nodes/frontend_node.py`
- Create: `src/agents/nodes/backend_node.py`
- Test: `tests/unit/test_dev_nodes.py`

**实现要点：**
- Frontend Dev：读取 ComponentTree + API 端点 → 输出前端代码（字符串存储）
- Backend Dev：读取 TRD + ER 图 → 输出后端代码 + SQL 脚本
- 均使用 `response_format={"type": "json_object"}` 强制结构化输出

---

### Task 3.4: QA Agent

**Files:**
- Create: `src/prompts/qa_agent.py`
- Create: `src/agents/nodes/qa_node.py`

**实现要点：**
- 读取 PRD + TRD + 前后端代码
- 生成测试用例 + 自动化测试脚本
- 输出测试报告（通过率、Bug 列表）

---

### Task 3.5: 扩展图 — 完整 SDLC 链路

**Files:**
- Modify: `src/core/orchestrator.py`

**Step 1: 扩展 build_graph**

```
PM → Reviewer → (APPROVED)
  → Architect + Design (并行) → Reviewer → (APPROVED)
  → Frontend Dev + Backend Dev (并行) → QA → Reviewer → (APPROVED)
  → FINISHED
```

**Step 2: 添加更多路由函数**

- `arch_review_router` — 架构审查后路由
- `dev_review_router` — 代码审查后路由
- `qa_review_router` — 测试审查后路由

**Step 3: 集成测试**

```bash
pytest tests/integration/test_full_pipeline.py -v
```

---

### Task 3.6: Orchestrator Agent（敏捷大管家）

**Files:**
- Create: `src/agents/nodes/orchestrator_node.py`

**实现要点：**
- 接收用户输入，决定触发哪个阶段的 Agent
- 管理全局状态和进度
- 支持「从某个阶段重新开始」的指令

---

## Phase 4: 质量保障与可观测

> 目标：格式校验、流式输出、日志增强、安全防护。

### Task 4.1: Mermaid 语法校验器

**Files:**
- Create: `src/utils/validators.py`
- Test: `tests/unit/test_validators.py`

**实现：**
- `validate_mermaid(code: str) -> ValidationResult` — 正则 + 结构校验
- `auto_fix(llm, broken_output, schema) -> BaseModel` — 失败自动重试 ≤ 3 次
- 集成到各 Agent 的 run() 方法中

---

### Task 4.2: SSE 流式输出

**Files:**
- Create: `src/api/streaming.py`
- Modify: `src/api/routes.py`

**实现：**
- `POST /pipeline/run?stream=true` → SSE 事件流
- 事件类型：`thinking` / `progress` / `artifact` / `result` / `[DONE]`

---

### Task 4.3: 结构化日志增强

**Files:**
- Modify: `src/utils/logger.py`

**实现：**
- JSON 格式日志输出
- 自动注入 request_id / thread_id
- LLM 调用耗时、token 用量自动记录

---

### Task 4.4: 更新 README.md

**Files:**
- Modify: `README.md`

**更新内容：**
- 新项目结构说明
- Multi-Agent 架构图
- 快速启动命令
- API 端点列表
- 环境变量说明

---

## 里程碑检查

| Phase | 核心交付 | 验证标准 |
|-------|---------|---------|
| Phase 0 | 依赖安装 + 目录结构 | `pip install` 成功，目录完整 |
| Phase 1 | State + Models + BaseAgent | 单元测试全部通过 |
| Phase 2 | PM 闭环（需求→审查→通过/打回） | 集成测试通过，API 可调用 |
| Phase 3 | 全链路 8 Agent | 端到端流水线可运行 |
| Phase 4 | 校验 + 流式 + 日志 | Mermaid 校验、SSE 输出正常 |

---

## 注意事项

1. **先跑通再扩展** — 每个 Phase 都必须是可独立运行的
2. **Mock 优先** — 单元测试用 mock LLM，集成测试才用真实 API
3. **小步提交** — 每个 Task 完成就 commit
4. **需求文档为准** — 如果实现与文档冲突，以飞书文档为准

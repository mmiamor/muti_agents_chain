# Multi-Agent Chain 项目标准 v3.0

> 基于 LangGraph 的 Multi-Agent 应用开发框架，实现从需求到代码的全流程自动化。

---

## 📋 目录

1. [架构标准](#1-架构标准)
2. [项目结构标准](#2-项目结构标准)
3. [编码标准](#3-编码标准)
4. [记忆系统标准](#4-记忆系统标准)
5. [API 标准化](#5-api-标准化)
6. [测试标准](#6-测试标准)
7. [格式校验标准](#7-格式校验标准)
8. [性能与监控](#8-性能与监控)
9. [版本管理](#9-版本管理)

---

## 1. 架构标准

### 1.1 核心架构：LangGraph + Multi-Agent Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                    Multi-Agent Chain Framework                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────┐    ┌──────────────┐    ┌──────────────────┐      │
│  │ API Layer│───▶│ Orchestrator │───▶│  Agent Pipeline   │      │
│  │ (FastAPI)│◀───│  (LangGraph)  │◀───│                  │      │
│  └──────────┘    └──────┬───────┘    └────────┬─────────┘      │
│                         │                     │                 │
│                         ▼                     ▼                 │
│                  ┌──────────────┐    ┌──────────────────┐      │
│                  │  Context Mgr │    │   Agent Nodes     │      │
│                  │ (智能上下文)  │    │ PM→Arch→Design    │      │
│                  └──────────────┘    │ →Dev→QA→Review    │      │
│                                      └──────────────────┘      │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│  Services: LLM │ Memory │ Chain │ Utils │ Config              │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Agent Pipeline 流程

```
User Input
    │
    ▼
┌─────────────┐      ┌──────────────┐
│   PM Agent  │─────▶│   Reviewer   │──REJECTED──▶ retry
│ (需求分析)  │      │   (评审)     │
└─────────────┘      └──────┬───────┘
                            │ APPROVED
                            ▼
                    ┌──────────────┐
                    │Architect Agent│      ┌──────────────┐
                    │  (架构设计)   │─────▶│   Reviewer   │
                    └──────────────┘      │   (评审)     │
                            │             └──────┬───────┘
                            ▼                     │
                    ┌──────────────┐              │
                    │ Design Agent  │              │
                    │  (UI设计)     │              │
                    └──────────────┘              │
                            │                     │
                            ▼                     │
                    ┌──────────────┐              │
                    │ Backend Dev  │              │
                    │ Frontend Dev │              │
                    └──────────────┘              │
                            │                     │
                            ▼                     │
                    ┌──────────────┐              │
                    │   QA Agent   │              │
                    │  (质量保障)   │              │
                    └──────────────┘              │
                            │                     │
                            └─────────────────────┘
                                    │
                                    ▼
                            Final Output
```

### 1.3 Agent 定义标准

每个 Agent 必须实现 `BaseAgent` 接口：

```python
class BaseAgent(ABC):
    """
    Agent 基类 — 所有 Agent 必须继承此类

    每个 Agent 必须：
    1. 声明 name 和 role
    2. 实现 run() — 核心执行逻辑，返回 State 更新字典
    3. 实现 review() — 自我反思，检查输出质量
    """
    name: str                    # Agent 标识名
    role: str                    # 角色描述
    description: str = ""        # 详细描述

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

### 1.4 LangGraph State 标准

```python
class AgentState(TypedDict, total=False):
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
    design_doc: Optional[DesignDocument]
    backend_code: Optional[BackendCodeSpec]
    frontend_code: Optional[FrontendCodeSpec]
    qa_report: Optional[QAReport]

    # 审查状态
    latest_review: Optional[ReviewFeedback]
    revision_counts: dict[str, int]  # agent_name → revision 次数
```

---

## 2. 项目结构标准

```
muti_agents_chain/
├── src/
│   ├── main.py                      # 应用入口
│   │
│   ├── config/                      # 配置管理
│   │   ├── __init__.py
│   │   ├── settings.py              # 环境配置
│   │   └── context_config.py        # ⭐ 上下文管理配置
│   │
│   ├── core/                        # 核心引擎
│   │   ├── __init__.py
│   │   ├── engine.py                # 主引擎
│   │   ├── orchestrator.py          # ⭐ LangGraph 编排器
│   │   ├── pipeline.py              # 处理管道
│   │   └── scheduler.py             # 任务调度器
│   │
│   ├── agents/                      # ⭐ Agent 体系
│   │   ├── __init__.py
│   │   ├── base.py                  # Agent 基类
│   │   ├── context.py               # Agent 上下文对象
│   │   ├── factory.py               # Agent 工厂
│   │   ├── registry.py              # Agent 注册表
│   │   └── nodes/                   # Agent 节点实现
│   │       ├── __init__.py
│   │       ├── pm_node.py           # PM Agent
│   │       ├── architect_node.py    # Architect Agent
│   │       ├── design_node.py       # Design Agent
│   │       ├── backend_dev_node.py  # Backend Dev Agent
│   │       ├── frontend_dev_node.py # Frontend Dev Agent
│   │       ├── qa_node.py           # QA Agent
│   │       └── reviewer_node.py     # Reviewer Agent
│   │
│   ├── memory/                      # ⭐ 记忆系统
│   │   ├── __init__.py
│   │   ├── context_manager.py       # ⭐ 智能上下文管理
│   │   └── agent_context.py         # Agent 上下文工具
│   │
│   ├── services/                    # 基础服务
│   │   ├── __init__.py
│   │   ├── llm_service.py           # LLM 调用服务（GLM）
│   │   ├── chain_service.py         # Chain 编排服务
│   │   └── memory_service.py        # 记忆管理服务
│   │
│   ├── models/                      # 数据模型
│   │   ├── __init__.py
│   │   ├── schemas.py               # 通用模型
│   │   ├── agent_models.py          # Agent 相关模型
│   │   ├── state.py                 # ⭐ LangGraph State
│   │   └── document_models.py       # 文档模型（PRD/TRD等）
│   │
│   ├── prompts/                     # ⭐ Agent Prompts
│   │   ├── __init__.py
│   │   ├── pm_agent.py              # PM Agent Prompt
│   │   ├── architect_agent.py       # Architect Agent Prompt
│   │   ├── design_agent.py          # Design Agent Prompt
│   │   ├── backend_dev_agent.py     # Backend Dev Agent Prompt
│   │   ├── frontend_dev_agent.py    # Frontend Dev Agent Prompt
│   │   ├── qa_agent.py              # QA Agent Prompt
│   │   └── reviewer_agent.py        # Reviewer Agent Prompt
│   │
│   ├── api/                         # API 层
│   │   ├── __init__.py
│   │   ├── server.py                # FastAPI 服务器
│   │   └── routes.py                # 路由定义
│   │
│   ├── utils/                       # 工具函数
│   │   ├── __init__.py
│   │   ├── logger.py                # 日志工具
│   │   ├── helpers.py               # 辅助函数
│   │   └── json_extract.py          # JSON 提取工具
│   │
│   └── __init__.py
│
├── tests/
│   ├── unit/                        # 单元测试
│   │   └── (测试文件)
│   ├── integration/                 # 集成测试
│   │   └── (测试文件)
│   ├── e2e_pm_reviewer.py          # ⭐ E2E 测试示例
│   └── fixtures/                    # 测试数据
│
├── docs/                           # 项目文档
│   ├── PROJECT_STANDARDS.md        # 本文件
│   ├── CONTEXT_MANAGEMENT.md       # ⭐ 上下文管理文档
│   └── README.md                   # 项目说明
│
├── data/                           # 数据目录
├── logs/                           # 日志目录
├── scripts/                        # 运维脚本
├── .env.example                    # 环境变量示例
├── .env                            # 环境变量（本地）
├── requirements.txt                # Python 依赖
├── pyproject.toml                  # 项目配置
└── README.md                       # 项目说明
```

---

## 3. 编码标准

### 3.1 Python 规范

| 规则 | 标准 |
|------|------|
| Python 版本 | >= 3.12 |
| 类型注解 | 所有函数签名必须有类型注解（return type 也不能省） |
| 异步优先 | I/O 操作必须使用 async/await |
| Docstring | 所有公开类和方法必须有 docstring |
| 错误处理 | 不允许裸 `except`，必须指定具体异常类型 |
| 日志级别 | DEBUG（数据细节）、INFO（流程节点）、WARNING（重试/降级）、ERROR（失败） |
| 命名 | 类 PascalCase，函数 snake_case，常量 UPPER_SNAKE_CASE，私有属性 _前缀 |

### 3.2 Agent 节点编码规范

```python
# ✅ 正确的 Agent 节点实现
class PMAgent(BaseAgent):
    """PM Agent 实现"""

    name = "pm_agent"
    role = "资深产品经理"

    def __init__(self, llm=None):
        self.llm = llm
        if self.llm is None:
            self.llm = create_llm()

    async def run(self, state: AgentState) -> dict:
        """分析需求，生成 PRD"""
        # 1. 获取审查反馈
        review_context = self._build_review_context(state)

        # 2. 准备优化的上下文
        messages = prepare_messages_for_llm(
            state.get("messages", []),
            system_prompt=SYSTEM_PROMPT + review_context,
            agent_name=self.name,
        )

        # 3. 调用 LLM
        response = await self.llm.client.chat.completions.create(
            model=settings.DEFAULT_MODEL,
            messages=messages,
            temperature=0,
        )

        # 4. 解析结果
        prd_data = extract_json(response.choices[0].message.content)
        prd = PRD(**prd_data)

        # 5. 返回 State 更新
        return {
            "prd": prd,
            "sender": self.name,
            "messages": [AIMessage(content=f"PM Agent 已生成 PRD...")],
        }

    async def review(self, state: AgentState) -> bool:
        """自我反思 — 检查 PRD 完整性"""
        prd = state.get("prd")
        if not prd:
            return False

        # 检查必需字段
        return bool(
            prd.vision and
            prd.target_audience and
            prd.core_features and
            prd.user_stories
        )
```

### 3.3 上下文优化标准

```python
# ✅ 使用优化的上下文管理
from src.memory.agent_context import prepare_messages_for_llm

# 在 Agent 节点中
messages = prepare_messages_for_llm(
    state["messages"],
    system_prompt=SYSTEM_PROMPT,
    agent_name="pm_agent"
)

# 自动处理：
# 1. 上下文压缩（超过阈值时）
# 2. 系统提示添加
# 3. Token 限制裁剪
# 4. 关键信息保留
```

### 3.4 模型定义规范

- 所有 Agent 输出必须定义为 Pydantic Model
- Model 必须包含字段描述
- 枚举类型使用 `str, Enum`
- 嵌套模型禁止循环引用

```python
class PRD(BaseModel):
    """产品需求文档"""

    vision: str = Field(..., description="产品愿景")
    target_audience: str = Field(..., description="目标用户群体")
    core_features: list[str] = Field(..., description="核心功能列表")
    user_stories: list[UserStory] = Field(..., description="用户故事列表")
    mermaid_flowchart: str = Field(..., description="业务流程图（Mermaid格式）")
    non_functional: dict[str, str] = Field(..., description="非功能性需求")
```

---

## 4. 记忆系统标准

### 4.1 智能上下文管理

| 功能 | 说明 | 实现 |
|------|------|------|
| 自动检测 | 监控消息数量和 token 估算 | `ContextManager.should_compact()` |
| 智能压缩 | 保留关键信息，压缩中间内容 | `ContextManager.compact_messages()` |
| 滑动窗口 | 保留最近 N 条消息 | `ContextConfig.keep_last_n` |
| 语义摘要 | 生成中间内容摘要 | `ContextManager._generate_summary()` |

### 4.2 上下文配置

```python
from src.memory.context_manager import ContextConfig

config = ContextConfig(
    max_messages=100,              # 最大消息数量
    max_tokens=8000,               # 最大 token 估算
    compact_threshold=0.8,         # 触发压缩阈值（80%）
    keep_first_n=5,                # 保留前 5 条关键消息
    keep_last_n=20,                # 保留最近 20 条消息
    enable_semantic_compact=True,  # 启用语义压缩
)
```

### 4.3 使用示例

```python
from src.memory.agent_context import prepare_messages_for_llm, get_context_stats

# 准备优化的消息
messages = prepare_messages_for_llm(
    state_messages,
    system_prompt=SYSTEM_PROMPT,
    agent_name="pm_agent",
)

# 获取统计信息
stats = get_context_stats()
print(f"压缩次数: {stats['compression_count']}")
print(f"压缩率: {stats['last_compaction_ratio']:.1%}")
```

---

## 5. API 标准化

### 5.1 RESTful 端点设计

```
POST   /api/v1/run                    # 运行完整 Pipeline
GET    /api/v1/status/{thread_id}     # 查询任务状态
GET    /api/v1/result/{thread_id}     # 获取任务结果
DELETE /api/v1/session/{thread_id}    # 清除会话
GET    /api/v1/health                 # 健康检查
```

### 5.2 请求/响应格式

**请求格式：**
```json
{
  "message": "我想做一个遛狗APP",
  "stream": false
}
```

**响应格式：**
```json
{
  "thread_id": "thread_xxx",
  "status": "completed",
  "result": {
    "prd": {...},
    "trd": {...},
    "design_doc": {...}
  }
}
```

### 5.3 流式响应

支持 SSE (Server-Sent Events) 流式输出：

```
POST /api/v1/run?stream=true
Content-Type: text/event-stream

data: {"type": "phase", "phase": "PM Agent", "status": "running"}

data: {"type": "progress", "step": "analyzing", "percent": 30}

data: {"type": "artifact", "name": "prd", "data": {...}}

data: {"type": "result", "status": "completed"}

data: [DONE]
```

---

## 6. 测试标准

### 6.1 测试金字塔

| 层级 | 覆盖范围 | 工具 | 要求 |
|------|----------|------|------|
| 单元测试 | Agent 逻辑、工具函数 | pytest + pytest-asyncio | 覆盖率 >= 80% |
| 集成测试 | Agent 间协作、完整流水线 | pytest | 核心流程全覆盖 |
| E2E 测试 | API 端到端 | 真实 LLM | 关键路径全覆盖 |

### 6.2 测试文件命名

```
tests/unit/test_pm_agent.py
tests/unit/test_architect_agent.py
tests/unit/test_context_manager.py
tests/integration/test_full_pipeline.py
tests/e2e_pm_reviewer.py
tests/fixtures/sample_input.json
```

### 6.3 E2E 测试示例

```python
async def test_pm_to_reviewer_flow():
    """测试 PM -> Reviewer 完整流程"""
    graph = build_graph()
    config = {"configurable": {"thread_id": "test-001"}}

    initial_state = {
        "messages": [HumanMessage(content="我想做一个遛狗APP")],
        "current_phase": AgentPhase.REQUIREMENT_GATHERING,
        "sender": "user",
    }

    result = await graph.ainvoke(initial_state, config)

    # 验证结果
    assert result.get("prd") is not None
    assert result.get("latest_review") is not None
```

---

## 7. 格式校验标准

### 7.1 输出验证

所有 Agent 输出必须符合预定义的 Schema：

```python
from src.utils.json_extract import extract_json

# 在 Agent 节点中
content = response.choices[0].message.content
prd_data = extract_json(content)  # 自动提取和验证 JSON
prd = PRD(**prd_data)             # Pydantic 验证
```

### 7.2 错误处理

- JSON 提取失败：自动重试最多 3 次
- Schema 验证失败：返回详细错误信息
- 超时处理：指数退避重试

---

## 8. 性能与监控

### 8.1 性能指标

| 指标 | 目标 | 监控方式 |
|------|------|----------|
| 首字响应时间 | < 2 秒 | 流式输出时打印日志 |
| Agent 执行时间 | 视 Agent 复杂度 | `time.perf_counter()` |
| Token 使用量 | 记录每次调用 | LLM Service 日志 |
| 上下文压缩率 | 30-60% | Context Manager 统计 |

### 8.2 日志标准

```python
from src.utils.logger import setup_logger

logger = setup_logger("pm_agent")

# 不同级别的日志
logger.debug("详细数据")    # 数据细节
logger.info("流程节点")     # 关键节点
logger.warning("重试/降级")  # 非致命错误
logger.error("失败")        # 致命错误
```

### 8.3 监控指标

- LLM 调用次数和延迟
- Token 使用量（prompt + completion）
- 上下文压缩统计
- Agent 执行成功率
- 错误率和重试次数

---

## 9. 版本管理

### 9.1 版本历史

| 版本 | 日期         | 主要变更 |
|------|------------|----------|
| v3.0 | 2026-03-30 | 添加智能上下文管理系统，优化记忆处理 |
| v2.0 | 2026-03-28 | 基于 LangGraph 重构，实现 Multi-Agent Pipeline |
| v1.0 | 2026-03-15 | 初始版本（基础 LLM Chain 框架） |

### 9.2 兼容性

- Python: >= 3.12
- LangGraph: >= 0.3.0
- FastAPI: >= 0.115.0
- OpenAI SDK: >= 1.60.0

---

## 10. 最佳实践

### 10.1 Agent 开发

1. **单一职责**: 每个 Agent 专注于一个特定任务
2. **幂等性**: Agent 的 `run()` 方法应该是幂等的
3. **错误处理**: 使用重试机制处理暂时性错误
4. **上下文优化**: 使用 `prepare_messages_for_llm()` 优化上下文

### 10.2 性能优化

1. **异步优先**: 所有 I/O 操作使用 async/await
2. **连接池**: 复用 HTTP 连接
3. **缓存**: 合理使用缓存减少重复计算
4. **批处理**: 合并多个小请求

### 10.3 可维护性

1. **文档**: 保持代码和文档同步更新
2. **测试**: 编写全面的测试用例
3. **日志**: 记录关键操作和错误
4. **监控**: 建立完善的监控体系

---

## 附录

### A. 相关文档

- [上下文管理指南](CONTEXT_MANAGEMENT.md)
- [README](README.md)
- [API 文档](docs/API_REFERENCE.md)

### B. 工具和资源

- [LangGraph 文档](https://langchain-ai.github.io/langgraph/)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [Pydantic 文档](https://docs.pydantic.dev/)

### C. 贡献指南

1. Fork 项目
2. 创建特性分支
3. 提交变更
4. 推送到分支
5. 创建 Pull Request

---

**文档版本**: v3.0
**最后更新**: 2026-03-30
**维护者**: Multi-Agent Chain Team

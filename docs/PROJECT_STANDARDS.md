# LLMChain 项目标准 v2.0

> 基于「应用开发体系 Agent 需求文档」重构，构建 Multi-Agent 应用开发框架。

---

## 1. 架构标准

### 1.1 核心架构：Multi-Agent + Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                      LLMChain Framework                       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │ API Layer│───▶│ Orchestrator │───▶│ Agent System  │       │
│  │ (FastAPI)│◀───│   (编排器)    │◀───│  (Agent 体系) │       │
│  └──────────┘    └──────┬───────┘    └──────┬───────┘       │
│                         │                     │               │
│                         ▼                     ▼               │
│                  ┌──────────────┐    ┌──────────────┐       │
│                  │   Memory     │    │   Reviewer   │       │
│                  │  (记忆系统)   │    │ (评审/反思)   │       │
│                  └──────────────┘    └──────────────┘       │
│                                                               │
├─────────────────────────────────────────────────────────────┤
│  Infrastructure: Config │ Logger │ Scheduler │ Storage        │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Agent 定义标准

每个 Agent 必须实现 `BaseAgent` 接口：

```python
class BaseAgent(ABC):
    """Agent 基类 — 所有 Agent 必须继承此类"""
    
    name: str                    # Agent 标识名
    role: str                    # 角色描述（PM/Architect/Reviewer...）
    system_prompt: str           # 系统提示词
    input_schema: type[BaseModel]   # 输入格式（Pydantic Model）
    output_schema: type[BaseModel]  # 输出格式（Pydantic Model）
    
    @abstractmethod
    async def run(self, input_data: BaseModel) -> BaseModel:
        """核心执行方法"""
        ...
    
    @abstractmethod
    async def review(self, input_data: BaseModel, output: BaseModel) -> ReviewResult:
        """自我反思 — 检查输出质量"""
        ...
```

### 1.3 Agent 间通信标准

- **输入/输出格式**：所有 Agent 的输入和输出必须是 Pydantic Model（JSON 序列化）
- **上下文传递**：通过 `AgentContext` 对象传递，包含 session_id、history、artifacts
- **状态管理**：每个 Agent 步骤记录到 Memory，支持回溯

---

## 2. 项目结构标准

```
llmchain/
├── src/
│   ├── main.py                    # 应用入口
│   │
│   ├── config/                    # 配置管理
│   │   ├── settings.py            # 环境配置
│   │   └── prompts/               # ⭐ System Prompts 目录
│   │       ├── pm_agent.md        # PM-Agent 提示词
│   │       ├── arch_agent.md      # Arch-Agent 提示词
│   │       └── reviewer.md        # Reviewer 提示词
│   │
│   ├── core/                      # 核心引擎
│   │   ├── engine.py              # 主引擎
│   │   ├── orchestrator.py        # ⭐ 多 Agent 编排器
│   │   ├── pipeline.py            # 处理管道
│   │   └── scheduler.py           # 任务调度器
│   │
│   ├── agents/                    # ⭐ Agent 体系
│   │   ├── base.py                # Agent 基类
│   │   ├── context.py             # Agent 上下文对象
│   │   ├── pm_agent.py            # PM-Agent（需求分析）
│   │   ├── arch_agent.py          # Arch-Agent（技术设计）
│   │   ├── reviewer_agent.py      # Reviewer Agent（评审）
│   │   └── registry.py            # Agent 注册表
│   │
│   ├── memory/                    # ⭐ 记忆系统（独立模块）
│   │   ├── base.py                # 存储后端抽象接口
│   │   ├── short_term.py          # 短期记忆（会话上下文）
│   │   ├── long_term.py           # 长期记忆（持久化）
│   │   └── factory.py             # 存储后端工厂
│   │
│   ├── services/                  # 基础服务
│   │   ├── llm_service.py         # LLM 调用服务
│   │   ├── chain_service.py       # Chain 编排服务
│   │   └── memory_service.py      # 记忆管理（兼容层）
│   │
│   ├── models/                    # 数据模型
│   │   ├── schemas.py             # 通用模型
│   │   ├── agent_models.py        # ⭐ Agent 相关模型
│   │   └── document_models.py     # ⭐ 文档模型（PRD/TRD）
│   │
│   ├── api/                       # API 层
│   │   ├── server.py              # HTTP 服务
│   │   ├── routes.py              # 路由定义
│   │   └── streaming.py           # ⭐ 流式输出支持
│   │
│   ├── utils/                     # 工具函数
│   │   ├── logger.py
│   │   ├── helpers.py
│   │   └── validators.py          # ⭐ 格式校验器
│   │
│   └── plugins/                   # ⭐ 插件系统（可扩展）
│       ├── base.py                # 插件基类
│       └── search.py              # 搜索/RAG 插件
│
├── prompts/                       # ⭐ 外部 Prompt 文件（版本管理）
│   ├── pm_agent_v1.md
│   ├── arch_agent_v1.md
│   └── reviewer_v1.md
│
├── tests/
│   ├── unit/
│   │   ├── test_engine.py
│   │   ├── test_agents.py         # ⭐ Agent 单元测试
│   │   └── test_validators.py
│   ├── integration/
│   │   └── test_full_flow.py      # ⭐ 端到端流程测试
│   └── fixtures/                  # 测试数据
│       ├── sample_prd.json
│       └── sample_trd.json
│
├── docs/                          # 项目文档
│   ├── PROJECT_STANDARDS.md       # 本文件
│   ├── AGENT_DESIGN.md            # Agent 设计文档
│   └── API_REFERENCE.md           # API 参考
│
├── scripts/                       # 运维脚本
├── logs/                          # 日志目录
├── data/                          # 数据目录
├── .python-version
├── requirements.txt
└── .env.example
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

### 3.2 Agent 编码规范

```python
# ✅ 正确的 Agent 实现
class PMAgent(BaseAgent):
    name = "pm_agent"
    role = "资深产品经理"
    input_schema = UserIdea
    output_schema = PRDDocument
    
    def __init__(self, llm_service: LLMService, memory: MemoryStore):
        self.llm = llm_service
        self.memory = memory
    
    async def run(self, input_data: UserIdea) -> PRDDocument:
        """分析用户想法，生成 PRD"""
        context = self._build_context(input_data)
        
        # Step 1: 需求澄清
        questions = await self._elicit_requirements(input_data)
        
        # Step 2: 竞品分析
        market = await self._analyze_market(input_data)
        
        # Step 3: 生成 PRD
        prd = await self._generate_prd(context, questions, market)
        
        return prd
    
    async def review(self, input_data: UserIdea, output: PRDDocument) -> ReviewResult:
        """自我反思 — 检查 PRD 完整性"""
        ...
```

### 3.3 模型定义规范

- 所有 Agent 输入/输出必须定义为 Pydantic Model
- Model 必须包含 `model_config` 配置 `json_schema_extra` 示例
- 枚举类型使用 `str, Enum`
- 嵌套模型禁止循环引用

```python
class PRDDocument(BaseModel):
    """产品需求文档"""
    product_vision: str = Field(..., description="产品愿景")
    target_users: list[UserPersona] = Field(..., description="目标用户群")
    user_stories: list[UserStory] = Field(..., description="用户故事列表")
    core_features: list[Feature] = Field(..., description="核心功能列表")
    business_flow: str = Field(..., description="业务流程图（Mermaid）")
    nfr: NonFunctionalRequirements = Field(..., description="非功能需求")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "product_vision": "打造最便捷的遛狗服务平台...",
            }
        }
    )
```

---

## 4. 记忆系统标准

### 4.1 分层记忆

| 层级 | 用途 | 存储 | 生命周期 |
|------|------|------|----------|
| 工作记忆 | 当前 Agent 执行中的临时数据 | 内存 | 单次 run |
| 短期记忆 | 会话对话历史 | 内存/Redis | 会话级 |
| 长期记忆 | 跨会话的文档、决策 | SQLite/文件 | 持久化 |

### 4.2 记忆接口标准

```python
class MemoryBackend(ABC):
    @abstractmethod
    async def save(self, key: str, value: Any, ttl: int | None = None) -> None: ...
    
    @abstractmethod
    async def load(self, key: str) -> Any | None: ...
    
    @abstractmethod
    async def search(self, query: str, top_k: int = 5) -> list[MemoryEntry]: ...
    
    @abstractmethod
    async def delete(self, key: str) -> bool: ...
```

---

## 5. API 标准化

### 5.1 RESTful 端点设计

```
POST   /api/v1/agent/pm/run          # 运行 PM-Agent
POST   /api/v1/agent/arch/run         # 运行 Arch-Agent
POST   /api/v1/agent/reviewer/run     # 运行 Reviewer

POST   /api/v1/pipeline/run           # 运行完整流水线（PM → Review → Arch → Review）
GET    /api/v1/pipeline/{task_id}/status  # 查询流水线状态
GET    /api/v1/pipeline/{task_id}/result  # 获取流水线结果

GET    /api/v1/session/{id}/context   # 获取会话上下文
DELETE /api/v1/session/{id}           # 清除会话

POST   /api/v1/chat                   # 通用聊天（兼容）
GET    /api/v1/health                 # 健康检查
```

### 5.2 流式响应标准

所有生成类接口必须支持 SSE (Server-Sent Events) 流式输出：

```
POST /api/v1/agent/pm/run?stream=true
Content-Type: text/event-stream

data: {"type": "thinking", "content": "正在分析用户需求..."}

data: {"type": "progress", "step": "requirement_elicitation", "percent": 30}

data: {"type": "artifact", "name": "questions", "data": [...]}

data: {"type": "result", "document": {...}}

data: [DONE]
```

---

## 6. 测试标准

### 6.1 测试金字塔

| 层级 | 覆盖范围 | 工具 | 要求 |
|------|----------|------|------|
| 单元测试 | Agent 逻辑、工具函数 | pytest + pytest-asyncio | 覆盖率 >= 80% |
| 集成测试 | Agent 间协作、完整流水线 | pytest + httpx | 核心流程全覆盖 |
| E2E 测试 | API 端到端 | httpx / curl | 关键路径全覆盖 |

### 6.2 测试文件命名

```
tests/unit/test_engine.py
tests/unit/test_pm_agent.py
tests/unit/test_arch_agent.py
tests/unit/test_validators.py
tests/integration/test_full_pipeline.py
tests/fixtures/sample_input.json
```

---

## 7. 格式校验标准

需求文档要求：生成的代码（Mermaid、JSON）必须符合语法规范，失败自动重试 <= 3 次。

```python
class OutputValidator:
    """输出格式校验器"""
    
    @staticmethod
    def validate_mermaid(code: str) -> ValidationResult:
        """校验 Mermaid 图表语法"""
        ...
    
    @staticmethod
    def validate_json_schema(data: dict, schema: dict) -> ValidationResult:
        """校验 JSON 是否符合 Schema"""
        ...
    
    @staticmethod
    async def auto_fix(llm: LLMService, broken_output: str, schema: type[BaseModel]) -> BaseModel:
        """自动修复不合规输出（重试 <= 3 次）"""
        ...
```

---

## 8. 扩展性标准

### 8.1 插件系统

后续 Agent（UI/UX Agent、Coding Agent）通过插件方式接入：

```python
class Plugin(ABC):
    name: str
    version: str
    
    @abstractmethod
    def register(self, registry: AgentRegistry) -> None:
        """将 Agent 注册到系统"""
        ...
```

### 8.2 Agent 注册表

```python
class AgentRegistry:
    _agents: dict[str, type[BaseAgent]] = {}
    
    @classmethod
    def register(cls, agent_class: type[BaseAgent]) -> None:
        cls._agents[agent_class.name] = agent_class
    
    @classmethod
    def get(cls, name: str) -> type[BaseAgent]:
        return cls._agents[name]
    
    @classmethod
    def list_agents(cls) -> list[str]:
        return list(cls._agents.keys())
```

---

## 9. 非功能需求检查清单

- [x] 可扩展：模块间使用标准 JSON/Markdown 进行输入输出
- [x] 准确性：引入格式校验器，失败自动重试不超过 3 次
- [x] 响应时效：首字响应时间 < 2 秒（流式输出）
- [x] 安全性：提示词层限制不输出敏感数据，支持本地化部署
- [x] 可观测：结构化日志 + 关键指标（latency、token usage）

---

## 10. 版本管理

| 版本 | 日期 | 变更 |
|------|------|------|
| v2.0 | 2026-03-28 | 基于 Multi-Agent 需求文档重构标准 |
| v1.0 | 2026-03 | 初始版本（基础 LLM Chain 框架） |

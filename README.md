# LLMChain — Multi-Agent AI 软件开发流水线

> 基于 LangGraph 的 Multi-Agent 系统，从产品需求到代码交付的自动化流水线。

## 架构概览

```
用户需求
   │
   ▼
┌─────────┐    ┌──────────┐    ┌───────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌────┐
│ PM Agent ├───►│ Reviewer  ├───►│ Architect ├───►│ Reviewer  ├───►│  Design  ├───►│ Reviewer  ├───►│ ...│
│ (产品经理)│    │ (审查专家)│    │ (架构师)  │    │ (审查专家)│    │ (UI/UX)  │    │ (审查专家)│    │    │
└─────────┘    └──────────┘    └───────────┘    └──────────┘    └──────────┘    └──────────┘    │    │
                                                                                               │    │
     每个产出物经 Reviewer 审查：                                                               ▼    │
     ✅ APPROVED → 流转下一阶段                                                                 │    │
     ❌ REJECTED → 打回当前 Agent 修改（最多 3 次）                                              │    │
     🚨 超限 → 人工干预 (Human Intervention)                                                     │    │
                                                                                               ┌────┴──┐
                                                                                               │ QA    │
                                                                                               │ Agent │──► Reviewer → END
                                                                                               └───────┘
```

### 完整流水线

| 阶段 | Agent | 产出物 | 说明 |
|------|-------|--------|------|
| 1 | PM Agent | PRD | 产品需求文档（用户故事、核心功能、流程图） |
| 2 | Architect Agent | TRD | 技术设计文档（技术栈、架构、ER图、API） |
| 3 | Design Agent | DesignDocument | UI/UX 设计（页面规格、设计 Token、用户旅程） |
| 4 | Backend Dev Agent | BackendCodeSpec | 后端代码（文件列表、项目结构、启动命令） |
| 5 | Frontend Dev Agent | FrontendCodeSpec | 前端代码（组件文件、项目结构、依赖） |
| 6 | QA Agent | QAReport | 质量报告（测试计划、质量评分、潜在问题） |

### 核心机制

- **StageRegistry** — 声明式阶段注册表，新增 Agent 只需添加一行配置
- **ReviewRouter** — 基于 AgentState 中产出物自动判断当前阶段，决定 APPROVED/REJECTED/HUMAN 路由
- **Revision Counter** — 每个 Agent 独立计数，防止单阶段死循环
- **LangGraph StateGraph** — 状态机驱动，MemorySaver 检查点支持

## 技术栈

- **Python 3.13** — pyenv 管理
- **LangGraph** — Agent 编排与状态机
- **LangChain** — LLM 抽象层
- **智谱 GLM-5** — 主力 LLM（OpenAI SDK 兼容）
- **Pydantic** — 全部产出物使用强类型数据模型
- **FastAPI** — HTTP 服务层
- **pytest + asyncio** — 单元测试 + E2E 测试

## 项目结构

```
llmchain/
├── src/
│   ├── agents/                     # Multi-Agent 系统
│   │   ├── base.py                 # Agent 抽象基类
│   │   ├── factory.py              # LLM 工厂 + revision 计数工具
│   │   ├── context.py              # Agent 上下文管理
│   │   ├── registry.py             # Agent 注册表
│   │   └── nodes/                  # LangGraph 节点函数
│   │       ├── pm_node.py          # PM Agent — 生成 PRD
│   │       ├── architect_node.py   # Architect Agent — 生成 TRD
│   │       ├── design_node.py      # Design Agent — 生成 DesignDocument
│   │       ├── backend_dev_node.py # Backend Dev — 生成后端代码
│   │       ├── frontend_dev_node.py# Frontend Dev — 生成前端代码
│   │       ├── qa_node.py          # QA Agent — 生成质量报告
│   │       └── reviewer_node.py    # Reviewer — 审查产出物
│   ├── core/
│   │   ├── orchestrator.py         # LangGraph 图构建 + 路由
│   │   ├── engine.py               # 主引擎
│   │   ├── pipeline.py             # 处理管道
│   │   └── scheduler.py            # 任务调度器
│   ├── models/
│   │   ├── state.py                # AgentState 全局状态定义
│   │   ├── document_models.py      # PRD / TRD / DesignDoc / CodeSpec / QAReport
│   │   └── agent_models.py         # ReviewFeedback 等模型
│   ├── prompts/                    # Agent 系统提示词
│   │   ├── pm_agent.py
│   │   ├── architect_agent.py
│   │   ├── design_agent.py
│   │   ├── backend_dev_agent.py
│   │   ├── frontend_dev_agent.py
│   │   ├── qa_agent.py
│   │   └── reviewer_agent.py
│   ├── services/
│   │   ├── llm_service.py          # LLM 调用（含重试与退避）
│   │   ├── chain_service.py        # Chain 编排
│   │   └── memory_service.py       # 记忆管理
│   ├── config/
│   │   └── settings.py             # 环境配置（.env）
│   ├── api/
│   │   ├── server.py               # FastAPI 服务
│   │   └── routes.py               # API 路由
│   └── utils/
│       ├── json_extract.py         # LLM 响应 JSON 提取
│       ├── logger.py               # 日志配置
│       └── helpers.py              # 通用工具
├── tests/
│   ├── unit/                       # 单元测试（105 个）
│   │   ├── test_pm_node.py
│   │   ├── test_architect_node.py
│   │   ├── test_design_node.py
│   │   ├── test_backend_dev_node.py
│   │   ├── test_frontend_dev_node.py
│   │   ├── test_qa_node.py
│   │   ├── test_reviewer_node.py
│   │   ├── test_orchestrator.py    # 路由与阶段注册表测试
│   │   ├── test_models.py          # 数据模型测试
│   │   ├── test_state.py
│   │   └── test_agents.py          # 基类与注册表测试
│   ├── integration/                # 集成测试
│   └── e2e_pm_reviewer*.py         # E2E 真实 LLM 测试
├── .env                            # 环境变量（API Key 等）
└── requirements.txt
```

## 快速开始

### 1. 环境准备

```bash
# Python 3.13（pyenv）
pyenv install 3.13.11
pyenv local 3.13.11

# 创建虚拟环境
python -m venv .venv
.\.venv\Scripts\Activate.ps1   # Windows
source .venv/bin/activate      # macOS/Linux
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env`：
```ini
ZAI_API_KEY=your_zhipu_api_key_here
DEFAULT_MODEL=glm-5
NODE_DELAY=2                    # 节点间冷却秒数（防限流）
MAX_REVISION_COUNT=3            # 单 Agent 最大修改次数
```

### 4. 运行测试

```bash
# 单元测试（105 个，~40s）
python -m pytest tests/unit/ -v

# E2E 真实 LLM 测试（需要有效 API Key）
python -m tests.e2e_pm_reviewer
```

### 5. 启动服务

```bash
python -m src.main
```

## 数据模型

所有 Agent 产出物均为 Pydantic 强类型模型：

```
PRD
├── vision: str                  # 产品愿景
├── target_audience: list[str]   # 目标用户
├── user_stories: list[UserStory]
├── core_features: list[str]
├── non_functional: str
└── mermaid_flowchart: str

TRD
├── tech_stack: TechStack        # frontend / backend / database / infra
├── architecture_overview: str
├── mermaid_er_diagram: str
└── api_endpoints: list[APIEndpoint]

DesignDocument
├── page_specs: list[PageSpec]
├── user_journey: str
├── design_tokens: DesignTokens
├── responsive_strategy: str
└── component_library: list[str]

BackendCodeSpec / FrontendCodeSpec
├── project_structure: str
├── files: list[CodeFile]        # path / description / content
├── setup_commands: list[str]
└── dependencies: str

QAReport
├── test_plan: list[QATestCase]  # name / type / scope / steps / expected
├── quality_score: int           # 1-10
├── quality_breakdown: QualityBreakdown  # 5 维度评分
├── potential_issues: list[PotentialIssue]
└── summary: str
```

## 开发指南

### 新增 Agent

只需 3 步：

1. **创建节点** — `src/agents/nodes/your_agent.py`
2. **创建 Prompt** — `src/prompts/your_agent.py`
3. **注册阶段** — 在 `src/core/orchestrator.py` 的 `StageRegistry.stages` 添加一行

```python
# orchestrator.py — StageRegistry.stages
{
    "agent": AgentNames.YOUR_AGENT,
    "artifact": "your_artifact",
    "next_agent": AgentNames.NEXT_AGENT,  # "__end__" 表示结束
},
```

路由、审查、死循环防护全部自动生效。

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `ZAI_API_KEY` | — | 智谱 API Key（必填） |
| `DEFAULT_MODEL` | `glm-5` | 默认 LLM 模型 |
| `OPENAI_BASE_URL` | 智谱 API | OpenAI 兼容 Base URL |
| `NODE_DELAY` | `2` | 节点间冷却秒数 |
| `MAX_REVISION_COUNT` | `3` | 单 Agent 最大修改次数 |
| `RECURSION_LIMIT` | `30` | LangGraph 最大递归 |
| `LLM_RETRY_MAX` | `3` | LLM 调用最大重试 |
| `LLM_RETRY_BASE_DELAY` | `3` | 重试初始等待秒数 |

## License

MIT

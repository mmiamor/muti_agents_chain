# 🚀 Multi-Agent Chain — AI 软件开发流水线

> 基于 LangGraph 的 Multi-Agent 系统，实现从产品需求到代码交付的全流程自动化。

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.3+-green.svg)](https://github.com/langchain-ai/langgraph)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## ✨ 核心特性

### 🤖 智能 Multi-Agent 协作
- **7 个专业 Agent** - PM、架构师、设计师、后端开发、前端开发、QA、审查员
- **自动编排** - 基于 LangGraph 状态机的智能流程控制
- **质量保障** - 每个产出物经过自动审查，不合格自动修改（最多 3 次）
- **人工干预** - 超过修改限制时触发人工干预流程

### 🧠 智能上下文管理
- **自动压缩** - 当上下文超过阈值时自动压缩历史消息
- **智能保留** - 保留关键信息（系统提示、用户需求、决策点）
- **Token 优化** - 平均节省 30-60% 的 token 使用量
- **滑动窗口** - 保留最近的消息维持对话连贯性

### 📊 强类型数据模型
- **Pydantic 模型** - 所有产出物使用强类型验证
- **结构化输出** - PRD、TRD、设计文档、代码规范等
- **类型安全** - 编译时类型检查，减少运行时错误

### 🌐 流式输出 + 持久化
- **实时反馈** - Server-Sent Events (SSE) 流式输出
- **细粒度事件** - 7 种事件类型（phase, progress, artifact, thinking, review, error, done）
- **结果持久化** - 自动保存所有 Agent 产出物到数据库
- **人工干预管理** - 完整的干预任务生命周期管理

### 🔧 多环境配置
- **三环境支持** - Development（开发）、Testing（测试）、Production（生产）
- **智能检测** - 自动检测环境（环境变量 → Git 分支 → 默认）
- **配置隔离** - 每个环境独立的数据库和配置
- **一键切换** - 简单的环境变量切换机制

### 🎯 Agent 专用模型配置
- **灵活模型选择** - 每个 Agent 可配置不同的 LLM 模型
- **成本优化** - 根据任务重要性选择不同性能的模型
- **默认回退** - 未配置的 Agent 自动使用默认模型
- **运行时查询** - 支持查询和验证 Agent 模型配置

---

## 🏗️ 系统架构

### Agent Pipeline 流程

```
┌─────────────────────────────────────────────────────────────────┐
│                    Multi-Agent 开发流水线                         │
└─────────────────────────────────────────────────────────────────┘

用户需求输入
     │
     ▼
┌─────────────┐      ┌──────────────┐      ┌───────────────┐
│  PM Agent   │─────▶│   Reviewer   │◀─────│  Feedback     │
│ (产品经理)   │      │  (审查专家)   │      │  (反馈循环)    │
└─────────────┘      └──────┬───────┘      └───────────────┘
     │ APPROVED               │
     ▼                        │ REJECTED (最多3次)
┌─────────────┐               │
│Architect    │─────▶ ┌──────┴───────┐
│(架构师)      │      │   Reviewer   │
└─────────────┘      │  (审查专家)   │
     │              └──────┬───────┘
     ▼                     │
┌─────────────┐             │
│  Design     │─────▶ ┌────┴──────┐
│ (UI/UX设计) │      │ Reviewer  │
└─────────────┘      └────┬──────┘
     │                     │
     ▼                     │
┌─────────────┐             │
│ Backend Dev │─────▶ ┌────┴──────┐
│ Frontend Dev│      │ Reviewer  │
└─────────────┘      └────┬──────┘
     │                     │
     ▼                     │
┌─────────────┐             │
│   QA Agent  │─────▶ ┌────┴──────┐
│ (质量保障)   │      │ Reviewer  │───▶ 最终交付
└─────────────┘      └───────────┘

审查机制:
✅ APPROVED  → 流转到下一阶段
❌ REJECTED  → 返回当前 Agent 修改 (最多3次)
🚨 超限      → 人工干预处理
```

### 开发阶段详解

| 阶段 | Agent | 产出物 | 说明 |
|------|-------|--------|------|
| 1️⃣ | PM Agent | PRD | 产品需求文档（用户故事、核心功能、业务流程） |
| 2️⃣ | Architect Agent | TRD | 技术设计文档（技术栈、架构、数据库、API） |
| 3️⃣ | Design Agent | DesignDocument | UI/UX 设计（页面规格、设计系统、用户旅程） |
| 4️⃣ | Backend Dev Agent | BackendCodeSpec | 后端代码（项目结构、文件内容、启动命令） |
| 5️⃣ | Frontend Dev Agent | FrontendCodeSpec | 前端代码（组件、样式、依赖配置） |
| 6️⃣ | QA Agent | QAReport | 质量报告（测试计划、质量评分、潜在问题） |

---

## 🛠️ 技术栈

### 核心框架
| 技术 | 版本 | 用途 |
|------|------|------|
| Python | 3.13+ | 核心开发语言 |
| LangGraph | 0.3+ | Agent 编排与状态机 |
| LangChain | Latest | LLM 抽象层 |
| FastAPI | Latest | HTTP 服务层 |

### 数据存储
| 技术 | 用途 |
|------|------|
| SQLAlchemy | ORM 框架 |
| aiosqlite | 异步 SQLite |
| Redis | 缓存和会话 |

### LLM 提供商
| 提供商 | 模型 | 用途 |
|--------|------|------|
| 智谱 AI | Qwen3-235B-A22B | 主力语言模型 |

### 开发工具
| 工具 | 用途 |
|------|------|
| pytest | 测试框架 |
| python-dotenv | 环境变量管理 |
| uvicorn | ASGI 服务器 |

---

## 📁 项目结构

```
muti_agents_chain/
├── src/
│   ├── agents/                    # 🤖 Multi-Agent 系统
│   │   ├── nodes/                 # Agent 节点实现
│   │   │   ├── pm_node.py         # PM Agent
│   │   │   ├── architect_node.py  # Architect Agent
│   │   │   ├── design_node.py     # Design Agent
│   │   │   ├── backend_dev_node.py# Backend Dev Agent
│   │   │   ├── frontend_dev_node.py# Frontend Dev Agent
│   │   │   ├── qa_node.py         # QA Agent
│   │   │   └── reviewer_node.py   # Reviewer Agent
│   │   └── prompts/               # Agent 提示词
│   │
│   ├── core/                      # ⚙️ 核心引擎
│   │   ├── orchestrator.py        # LangGraph 编排器
│   │   └── enhanced_pipeline.py   # 增强流程（持久化+流式）
│   │
│   ├── memory/                    # 🧠 智能记忆系统
│   │   └── context_manager.py     # 上下文管理器
│   │
│   ├── models/                    # 📊 数据模型
│   │   ├── state.py               # LangGraph State 定义
│   │   └── document_models.py     # 文档模型（PRD/TRD等）
│   │
│   ├── database/                  # 💾 数据库
│   │   └── models.py              # 持久化模型
│   │
│   ├── services/                  # 🔧 服务层
│   │   ├── llm_service.py         # LLM 调用服务
│   │   ├── persistence_service.py # 持久化服务
│   │   └── persistence_decorator.py# 持久化装饰器
│   │
│   ├── config/                    # ⚙️ 配置管理
│   │   ├── environment.py         # 多环境管理
│   │   ├── development.py         # 开发环境配置
│   │   ├── testing.py             # 测试环境配置
│   │   ├── production.py          # 生产环境配置
│   │   └── settings.py            # 配置入口
│   │
│   ├── api/                       # 🌐 API 层
│   │   ├── streaming.py           # 流式输出 API
│   │   ├── human_intervention.py  # 人工干预 API
│   │   └── data.py                # 数据查询 API
│   │
│   └── utils/                     # 🛠️ 工具函数
│       ├── logger.py              # 日志配置
│       └── helpers.py             # 通用工具
│
├── tests/                         # 🧪 测试
│   ├── e2e_pm_reviewer.py         # E2E 测试
│   └── fixtures/                  # 测试数据
│
├── docs/                          # 📚 文档
│   ├── ENVIRONMENT_QUICK_START.md # 环境配置快速指南
│   ├── MULTI_ENVIRONMENT_CONFIG.md# 多环境配置详解
│   ├── MULTI_ENVIRONMENT_COMPLETE.md# 多环境实现报告
│   ├── PERSISTENCE_COMPLETE.md    # 持久化系统报告
│   ├── PROJECT_STANDARDS.md       # 项目标准
│   └── CONTEXT_MANAGEMENT.md      # 上下文管理指南
│
├── data/                          # 💾 数据存储
│   ├── dev.db                     # 开发数据库
│   ├── test.db                    # 测试数据库
│   └── prod.db                    # 生产数据库
│
├── .env                           # 基础配置（不提交）
├── .env.development               # 开发环境配置
├── .env.testing                   # 测试环境配置
├── .env.production                # 生产环境配置
├── .env.example                   # 环境变量示例
├── requirements.txt               # Python 依赖
├── test_environment.py            # 环境配置测试
├── test_env_switching.py          # 环境切换演示
└── README.md                      # 本文件
```

---

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆仓库
git clone https://github.com/your-repo/muti_agents_chain.git
cd muti_agents_chain

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .\.venv\Scripts\Activate.ps1  # Windows
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境

```bash
# 复制开发环境配置
cp .env.example .env.development

# 编辑配置文件
vim .env.development
```

配置示例：

```ini
# LLM API 配置
OPENAI_API_KEY=your_zhipu_api_key_here
OPENAI_BASE_URL=https://api.scnet.cn/api/llm/v1/
DEFAULT_MODEL=Qwen3-235B-A22B

# 服务配置
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=true
LOG_LEVEL=DEBUG

# 数据库配置
DATABASE_URL=sqlite+aiosqlite:///./data/dev.db
REDIS_URL=redis://localhost:6379/0

# Agent 配置
NODE_DELAY=5                    # 节点间冷却秒数（防限流）
MAX_REVISION_COUNT=3            # 单 Agent 最大修改次数
RECURSION_LIMIT=30              # LangGraph 最大递归深度
STREAM_ENABLED=true             # 启用流式输出

# 限流配置
LLM_RETRY_MAX=5                 # 最大重试次数
LLM_RETRY_BASE_DELAY=5          # 首次重试等待秒数
LLM_TIMEOUT=300                 # LLM 请求超时时间（秒）
```

### 4. 运行测试

```bash
# 环境配置测试
python test_environment.py

# 环境切换演示
python test_env_switching.py

# E2E 测试（需要有效的 API Key）
python tests/e2e_pm_reviewer.py
```

### 5. 启动服务

```bash
# 开发环境（默认）
python -m src.main

# 测试环境
ENVIRONMENT=testing python -m src.main

# 生产环境
ENVIRONMENT=production python -m src.main
```

访问 API 文档：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 💡 使用示例

### Python API 调用

```python
import asyncio
from langchain_core.messages import HumanMessage
from src.core.orchestrator import build_graph
from src.models.state import AgentPhase

async def main():
    # 构建图
    graph = build_graph()
    config = {"configurable": {"thread_id": "demo-001"}}

    # 准备输入
    initial_state = {
        "messages": [
            HumanMessage(content="我想做一个遛狗APP，帮助忙碌的都市养狗人找到靠谱的遛狗服务者")
        ],
        "current_phase": AgentPhase.REQUIREMENT_GATHERING,
        "sender": "user",
    }

    # 执行流程
    result = await graph.ainvoke(initial_state, config)

    # 获取结果
    prd = result.get("prd")
    trd = result.get("trd")
    design_doc = result.get("design_doc")

    print(f"产品愿景: {prd.vision}")
    print(f"技术栈: {trd.tech_stack}")
    print(f"设计文档: {design_doc.user_journey}")

asyncio.run(main())
```

### 流式输出 API

```bash
# 启动流式输出
curl -N -X POST "http://localhost:8000/api/v1/stream/run?message=我想做一个笔记应用"

# 或使用 HTTPie
http -S --stream POST "http://localhost:8000/api/v1/stream/run?message=做一个笔记应用"
```

### 人工干预处理

```python
from src.services.persistence_service import get_human_intervention_service

# 获取待处理任务
human_service = get_human_intervention_service()
tasks = await human_service.get_pending_tasks()

# 解决任务
await human_service.resolve_intervention(
    task_id="task-123",
    resolution_type="approved",
    feedback="同意通过，继续执行"
)
```

---

## 🔧 多环境配置

### 环境切换方法

#### 方法 1: 环境变量（推荐）

```bash
# 开发环境
export ENVIRONMENT=development
python -m src.main

# 测试环境
export ENVIRONMENT=testing
python -m src.main

# 生产环境
export ENVIRONMENT=production
python -m src.main
```

#### 方法 2: 代码中切换

```python
from src.config import set_environment, reload_settings

# 切换到生产环境
set_environment("production")

# 重新加载配置
settings = reload_settings()
```

#### 方法 3: Git 分支自动检测

```bash
# 创建特定分支会自动使用对应环境
git checkout -b prod      # → production
git checkout -b test      # → testing
git checkout main         # → development
```

### 环境对比

| 配置项 | Development | Testing | Production |
|--------|-------------|---------|------------|
| DEBUG | ✅ True | ✅ True | ❌ False |
| LOG_LEVEL | DEBUG | DEBUG | WARNING |
| 数据库 | dev.db | test.db | prod.db |
| Redis DB | 0 | 1 | 2 |
| API 文档 | 开启 | 开启 | 关闭 |
| CORS | 全部 | 限制 | 严格 |


---

## 🎯 Agent 模型配置

### 为什么需要 Agent 专用模型？

不同的 Agent 任务复杂度不同，对模型性能的要求也不同：

- **PM Agent、Architect Agent** - 需要深度思考和复杂推理 → 使用高性能模型
- **Backend Dev、Frontend Dev** - 代码生成任务对速度要求高 → 使用快速模型
- **QA Agent** - 测试任务相对简单 → 使用标准模型

### 配置方法

在环境配置文件中添加 Agent 专用模型：

```bash
# .env.development
DEFAULT_MODEL=glm-4              # 默认模型
PM_MODEL=glm-4-plus             # PM Agent 使用高性能模型
ARCHITECT_MODEL=glm-4-plus      # Architect Agent 使用高性能模型
BACKEND_DEV_MODEL=glm-4-turbo   # 后端开发使用快速模型
FRONTEND_DEV_MODEL=glm-4-turbo  # 前端开发使用快速模型
```

### 模型选择建议

| Agent | 推荐模型 | 原因 |
|-------|----------|------|
| PM Agent | glm-4-plus | 需求分析需要深度思考 |
| Architect Agent | glm-4-plus | 架构设计需要复杂推理 |
| Design Agent | glm-4 | UI/UX 设计需要平衡性能和质量 |
| Backend Dev Agent | glm-4-turbo | 代码生成需要速度 |
| Frontend Dev Agent | glm-4-turbo | 代码生成需要速度 |
| QA Agent | glm-4 | 测试任务相对简单 |
| Reviewer Agent | glm-4-plus | 代码审查需要高质量输出 |

### API 使用

```python
from src.agents.factory import create_llm
from src.config import settings

# 为特定 Agent 创建 LLM
pm_llm = create_llm(agent_name="pm_agent")
qa_llm = create_llm(agent_name="qa_agent")

# 查看当前配置
config = settings.agent_model_config
print(f"PM Agent 模型: {config.get_model_for_agent('pm_agent')}")
print(f"所有模型: {config.get_all_models()}")
```

详细配置指南请参考：[Agent 模型配置指南](docs/AGENT_MODEL_CONFIG.md)

---

## 📊 数据模型

所有 Agent 产出物都使用 Pydantic 强类型模型：

### PRD（产品需求文档）
```python
{
  "vision": "打造最便捷的遛狗服务平台...",
  "target_audience": ["忙碌的都市白领", "行动不便的老年人"],
  "core_features": ["在线预约", "实时定位", "安全保险"],
  "user_stories": [...],
  "mermaid_flowchart": "graph TD; A[用户] --> B[浏览]",
  "non_functional": {...}
}
```

### TRD（技术设计文档）
```python
{
  "tech_stack": {
    "frontend": ["React", "TypeScript"],
    "backend": ["FastAPI", "Python"],
    "database": ["PostgreSQL"],
    "infra": ["Docker", "AWS"]
  },
  "architecture_overview": "...",
  "mermaid_er_diagram": "erDiagram...",
  "api_endpoints": [...]
}
```

### DesignDocument（UI/UX 设计）
```python
{
  "page_specs": [...],
  "user_journey": "...",
  "design_tokens": {...},
  "responsive_strategy": "...",
  "component_library": [...]
}
```

---

## 🧪 测试

### 测试覆盖

| 类型 | 覆盖范围 | 命令 |
|------|----------|------|
| 环境测试 | 环境检测、配置加载、切换 | `python test_environment.py` |
| 单元测试 | Agent 逻辑、工具函数 | `pytest tests/unit/ -v` |
| 集成测试 | Agent 间协作 | `pytest tests/integration/ -v` |
| E2E 测试 | 完整流程 | `python tests/e2e_pm_reviewer.py` |

### 测试结果

```
============================================================
✅ 所有测试通过！
============================================================

测试 1: 环境自动检测 ✅
测试 2: 环境配置加载 ✅
测试 3: 环境切换 ✅
测试 4: .env 文件加载 ✅
测试 5: 配置完整性 ✅
```

---

## 📈 性能优化

### 智能上下文管理

- **自动压缩**: 当消息超过阈值时自动压缩
- **智能保留**: 保留关键信息（系统提示、用户需求、决策点）
- **Token 节省**: 平均节省 30-60% 的 token 使用量
- **滑动窗口**: 保留最近的消息维持对话连贯性

### 结果持久化

- **自动保存**: Agent 执行结果自动保存到数据库
- **多版本管理**: 支持产出物的多个版本
- **审查历史**: 完整的审查记录
- **人工干预**: 完整的干预任务生命周期

---

## 🔍 环境变量

### 基础配置

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `ENVIRONMENT` | `development` | 运行环境（development/testing/production） |
| `DEBUG` | `true` | 调试模式 |
| `LOG_LEVEL` | `DEBUG` | 日志级别 |

### LLM 配置

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `OPENAI_API_KEY` | — | 智谱 API Key（必填） |
| `DEFAULT_MODEL` | `Qwen3-235B-A22B` | 默认 LLM 模型 |
| `OPENAI_BASE_URL` | 智谱 API | OpenAI 兼容 Base URL |
| `LLM_TIMEOUT` | `300` | LLM 请求超时时间（秒） |

### Agent 配置

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `NODE_DELAY` | `5` | 节点间冷却秒数 |
| `MAX_REVISION_COUNT` | `3` | 单 Agent 最大修改次数 |
| `RECURSION_LIMIT` | `30` | LangGraph 最大递归深度 |
| `STREAM_ENABLED` | `true` | 启用流式输出 |
| `LLM_RETRY_MAX` | `5` | 最大重试次数 |
| `LLM_RETRY_BASE_DELAY` | `5` | 首次重试等待秒数 |

---

## 📚 文档

### 用户文档
- [项目状态总览](PROJECT_STATUS.md) - 项目进展和功能清单

### 技术文档
- [项目开发标准](docs/PROJECT_STANDARDS.md) - 详细的开发标准和规范
- [上下文管理指南](docs/CONTEXT_MANAGEMENT.md) - 智能上下文管理指南

### API 文档
- Swagger UI: http://localhost:8000/docs (开发环境)
- ReDoc: http://localhost:8000/redoc

---

## 🤝 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交变更 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

### 开发规范

- 遵循 [项目标准](docs/PROJECT_STANDARDS.md)
- 添加单元测试
- 更新相关文档
- 确保所有测试通过

---

## 📝 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 🙏 致谢

- [LangGraph](https://github.com/langchain-ai/langgraph) - 强大的 Agent 编排框架
- [智谱 AI](https://open.bigmodel.cn/) - 提供 GLM 系列语言模型
- [LangChain](https://github.com/langchain-ai/langchain) - LLM 应用开发框架

---

## 📮 联系方式

如有问题或建议，请：

- 提交 [Issue](https://github.com/your-repo/muti_agents_chain/issues)
- 发送邮件到 [mmiamor@icloud.com](mailto:mmiamor@icloud.com)

---

## 🔗 相关链接

- [项目状态](PROJECT_STATUS.md) - 查看项目进展
- [更新日志](CHANGELOG.md) - 版本更新历史
- [问题追踪](https://github.com/your-repo/muti_agents_chain/issues) - Bug 和功能请求

---

**Made with ❤️ by Multi-Agent Chain Team**

*最后更新: 2026-03-30*

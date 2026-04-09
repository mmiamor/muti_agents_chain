# 🚀 Omni Agent Graph

<div align="center">

**全能型智能体编排系统 — 从需求到代码的全流程自动化**

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.3+-green.svg)](https://github.com/langchain-ai/langgraph)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

[功能特性](#-核心特性) • [快速开始](#-快速开始) • [系统架构](#-系统架构) • [使用指南](#-使用指南) • [API 文档](#-api-文档)

</div>

---

## 📖 项目简介

**Omni Agent Graph** 是一个基于 LangGraph 的 Multi-Agent 智能编排系统，通过 **7 个专业 AI Agent** 的协作，实现从产品需求到代码交付的全流程自动化。

### 🎯 核心价值

- **全流程自动化** - 从需求分析到代码生成，无需人工介入
- **质量保障** - 自动审查机制，确保每个产出物符合标准
- **灵活可扩展** - 支持自定义工作流、模型配置和技术栈
- **生产就绪** - 完整的持久化、监控和人工干预支持

### ✨ 应用场景

```
📱 产品原型 → 快速生成 PRD/TRD/设计文档
💻 代码开发 → 自动生成前后端代码
🧪 质量保障 → 自动测试和质量报告
🔄 迭代优化 → 基于反馈持续改进
```

---

## ✨ 核心特性

### 🤖 智能 Multi-Agent 协作

| Agent | 职责 | 产出物 |
|-------|------|--------|
| **PM Agent** | 产品需求分析 | PRD 文档 |
| **Architect Agent** | 技术架构设计 | TRD 文档 |
| **Design Agent** | UI/UX 设计 | 设计文档 |
| **Backend Dev Agent** | 后端代码开发 | 后端代码规范 |
| **Frontend Dev Agent** | 前端代码开发 | 前端代码规范 |
| **QA Agent** | 质量测试 | QA 报告 |
| **Reviewer Agent** | 质量审查 | 审查意见 |

### 🧠 RAG 增强的知识复用

- **智能检索** - 自动从历史 PRD 库中检索相似项目经验
- **语义匹配** - 基于向量相似度的精准知识匹配
- **持续学习** - 每个批准的 PRD 自动纳入知识库
- **上下文增强** - 检索结果作为参考信息提升生成质量

### 🎯 精确代码生成

- **前后端分离** - 独立的后端和前端代码生成器
- **路径精确定位** - 根据文件角色自动确定准确路径
- **多技术栈支持** - FastAPI、NestJS、React、Vue 等
- **职责清晰** - model/service/component 分层明确

### 🔧 智能上下文管理

- **自动压缩** - 当上下文超过阈值时自动压缩历史消息
- **智能保留** - 保留关键信息（系统提示、用户需求、决策点）
- **Token 优化** - 平均节省 30-60% 的 token 使用量

### 🌐 流式输出 + 持久化

- **实时反馈** - Server-Sent Events (SSE) 流式输出
- **细粒度事件** - 7 种事件类型（phase、progress、artifact、thinking、review、error、done）
- **结果持久化** - 自动保存所有 Agent 产出物到数据库
- **人工干预** - 完整的干预任务生命周期管理

### 🔗 自定义工作流

- **灵活执行** - 支持顺序、并行、条件执行
- **Agent 跳过** - 可跳过不需要的 Agent
- **自定义审查** - 自动、人工、跳过、条件审查
- **YAML 配置** - 文件化的配置管理

---

## 🏗️ 系统架构

### Agent Pipeline 流程

```
┌─────────────────────────────────────────────────────────────────┐
│                  Omni Agent Graph 开发流水线                      │
└─────────────────────────────────────────────────────────────────┘

用户需求输入
     │
     ▼
┌─────────────┐      ┌──────────────┐      ┌───────────────┐
│  PM Agent   │─────▶│   Reviewer   │◀─────│  Feedback     │
│  📋 PRD     │      │  ✅ 审查专家  │      │  🔄 反馈循环  │
└─────────────┘      └──────┬───────┘      └───────────────┘
     │ APPROVED               │
     ▼                        │ REJECTED (最多3次)
┌─────────────┐               │
│Architect    │─────▶ ┌──────┴───────┐
│ 🏗️ TRD      │      │   Reviewer   │
└─────────────┘      │  (审查专家)   │
     │              └──────┬───────┘
     ▼                     │
┌─────────────┐             │
│  Design     │─────▶ ┌────┴──────┐
│  🎨 Design  │      │ Reviewer  │
└─────────────┘      └────┬──────┘
     │                     │
     ▼                     │
┌─────────────┐             │
│ Backend Dev │─────▶ ┌────┴──────┐
│ Frontend Dev│      │ Reviewer  │
│ 💻 Code     │      └────┬──────┘
└─────────────┘             │
     │                     │
     ▼                     │
┌─────────────┐             │
│   QA Agent  │─────▶ ┌────┴──────┐
│  🧪 QA      │      │ Reviewer  │───▶ 最终交付
└─────────────┘      └───────────┘

审查机制:
✅ APPROVED  → 流转到下一阶段
❌ REJECTED  → 返回当前 Agent 修改 (最多3次)
🚨 超限      → 人工干预处理
```

### 技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                      Omni Agent Graph                         │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Multi-Agent │  │ RAG Knowledge│  │ Code Gen     │     │
│  │   System     │  │    Base      │  │   System     │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                  │                  │             │
│         └──────────────────┼──────────────────┘             │
│                            │                                │
│         ┌──────────────────┴──────────────────┐             │
│         │       LangGraph Orchestrator        │             │
│         └──────────────────┬──────────────────┘             │
│                            │                                │
│         ┌──────────────────┴──────────────────┐             │
│         │        Context Manager              │             │
│         │    (Smart Compression & Retention)  │             │
│         └──────────────────┬──────────────────┘             │
│                            │                                │
│  ┌─────────────────────────┼─────────────────────────┐     │
│  │                         │                         │     │
│  ▼                         ▼                         ▼     │
│ ┌─────────┐           ┌─────────┐            ┌─────────┐  │
│ │   LLM   │           │Database │            │  Redis  │  │
│ │ Service │           │Storage  │            │  Cache  │  │
│ └─────────┘           └─────────┘            └─────────┘  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛠️ 技术栈

### 核心框架

| 技术 | 版本 | 用途 |
|------|------|------|
| ![Python](https://img.shields.io/badge/Python-3.13+-blue) | 3.13+ | 核心开发语言 |
| ![LangGraph](https://img.shields.io/badge/LangGraph-0.3+-green) | 0.3+ | Agent 编排与状态机 |
| ![LangChain](https://img.shields.io/badge/LangChain-Latest-orange) | Latest | LLM 抽象层 |
| ![FastAPI](https://img.shields.io/badge/FastAPI-Latest-teal) | Latest | HTTP 服务层 |

### 数据存储

| 技术 | 用途 |
|------|------|
| ![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-ORM-red) | ORM 框架 |
| ![aiosqlite](https://img.shields.io/badge/aiosqlite-Async-blue) | 异步 SQLite |
| ![Redis](https://img.sh.shields.io/badge/Redis-Cache-red) | 缓存和会话 |

### LLM 提供商

| 提供商 | 模型      | 用途 |
|--------|---------|------|
| ![智谱 AI](https://img.shields.io/badge/智谱AI-Qwen3-purple) | GLM-4.7 | 主力语言模型 |
| ![OpenAI Compatible](https://img.shields.io/badge/OpenAI-Compatible-green) | Any     | 支持兼容接口 |

---

## 📁 项目结构

```
omni_agent_graph/
├── 📂 src/
│   ├── 🤂 agents/                    # Multi-Agent 系统
│   │   ├── nodes/                   # Agent 节点实现
│   │   └── prompts/                 # Agent 提示词
│   │
│   ├── ⚙️ core/                      # 核心引擎
│   │   ├── orchestrator.py          # LangGraph 编排器
│   │   └── enhanced_pipeline.py     # 增强流程
│   │
│   ├── 🧠 memory/                    # 智能记忆系统
│   │   └── context_manager.py       # 上下文管理器
│   │
│   ├── 📊 models/                    # 数据模型
│   │   ├── state.py                 # LangGraph State
│   │   └── document_models.py       # 文档模型
│   │
│   ├── 💾 database/                  # 数据库
│   │   └── models.py                # 持久化模型
│   │
│   ├── 🔧 services/                  # 服务层
│   │   ├── llm_service.py           # LLM 调用
│   │   ├── rag_service.py           # RAG 检索 ⭐
│   │   ├── backend_codegen_service.py# 后端代码生成 ⭐
│   │   ├── frontend_codegen_service.py# 前端代码生成 ⭐
│   │   └── code_locator_service.py  # 代码定位 ⭐
│   │
│   ├── ⚙️ config/                    # 配置管理
│   │   ├── environment.py           # 多环境管理
│   │   ├── development.py           # 开发环境
│   │   ├── testing.py               # 测试环境
│   │   └── production.py            # 生产环境
│   │
│   └── 🌐 api/                       # API 层
│       ├── streaming.py             # 流式输出
│       ├── human_intervention.py    # 人工干预
│       └── data.py                  # 数据查询
│
├── 📂 docs/                          # 📚 文档
│   ├── PM_RAG_INTEGRATION.md        # RAG 集成指南 ⭐
│   ├── CODE_GENERATION_SYSTEM.md    # 代码生成系统 ⭐
│   └── ...                          # 更多文档
│
├── 📂 workflows/                     # 工作流配置
│   ├── full_pipeline.yaml           # 完整流水线
│   ├── rapid_prototype.yaml         # 快速原型
│   └── ...                          # 更多模板
│
├── 📂 tests/                         # 测试
├── 📂 data/                          # 数据存储
├── .env                             # 环境配置
├── requirements.txt                 # Python 依赖
└── README.md                        # 本文件
```

---

## 🚀 快速开始

### 1️⃣ 环境准备

```bash
# 克隆仓库
git clone https://github.com/mmiamor/omni_agent_graph.git
cd omni_agent_graph

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .\.venv\Scripts\Activate.ps1  # Windows
```

### 2️⃣ 安装依赖

```bash
pip install -r requirements.txt
```

### 3️⃣ 配置环境

```bash
# 复制开发环境配置
cp .env.example .env.development

# 编辑配置文件
vim .env.development
```

**配置示例：**

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
NODE_DELAY=5                    # 节点间冷却秒数
MAX_REVISION_COUNT=3            # 最大修改次数
RECURSION_LIMIT=30              # 最大递归深度
STREAM_ENABLED=true             # 启用流式输出

# RAG 配置 ⭐
ENABLE_RAG_FOR_PM=true          # 启用 PM Agent RAG
RAG_TOP_K=3                     # 检索结果数量
RAG_SCORE_THRESHOLD=0.6         # 相似度阈值
```

### 4️⃣ 启动服务

```bash
# 开发环境（默认）
python -m src.main

# 测试环境
ENVIRONMENT=testing python -m src.main

# 生产环境
ENVIRONMENT=production python -m src.main
```

**访问 API 文档：**
- 📖 Swagger UI: http://localhost:8000/docs
- 📕 ReDoc: http://localhost:8000/redoc

---

## 💡 使用指南

### Python API 调用

```python
import asyncio
from langchain_core.messages import HumanMessage
from src.core.orchestrator import build_graph

async def main():
    # 构建图
    graph = build_graph()
    config = {"configurable": {"thread_id": "demo-001"}}

    # 准备输入
    initial_state = {
        "messages": [
            HumanMessage(content="我想做一个遛狗APP，帮助忙碌的都市养狗人找到靠谱的遛狗服务者")
        ],
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
# 使用 curl
curl -N -X POST "http://localhost:8000/api/v1/stream/run?message=我想做一个笔记应用"

# 使用 HTTPie
http -S --stream POST "http://localhost:8000/api/v1/stream/run?message=做一个笔记应用"
```

### 自定义工作流

```python
from src.core.workflow_loader import WorkflowLoader

# 加载预定义模板
loader = WorkflowLoader()
workflow = loader.load_template("rapid_prototype")

# 可用模板:
# - full_pipeline: 完整流水线
# - rapid_prototype: 快速原型
# - backend_only: 仅后端
# - frontend_only: 仅前端
```

---

## 🎯 核心功能

### RAG 增强的 PM Agent

```python
from src.services.rag_service import retrieve_similar_prds

# 自动检索相似 PRD
context = await retrieve_similar_prds(
    query="在线教育平台需求",
    top_k=3,
    score_threshold=0.6
)

# 检索结果会自动添加到 PM Agent 的上下文中
```

**优势：**
- 📚 自动学习历史项目经验
- 🎯 语义相似度精准匹配
- 🔄 知识库持续积累

### 精确代码生成

```python
from src.services.backend_codegen_service import BackendCodeGenerator
from src.services.frontend_codegen_service import FrontendCodeGenerator

# 后端代码生成
backend_gen = BackendCodeGenerator()
backend_code = backend_gen.generate_from_trd(trd, output_dir="./output")

# 前端代码生成
frontend_gen = FrontendCodeGenerator()
frontend_code = frontend_gen.generate_from_design(design, trd, output_dir="./output")
```

**特性：**
- 🎯 文件路径精确定位
- 📦 标准项目结构
- 🔧 多技术栈支持

### 智能上下文管理

```python
from src.memory.context_manager import prepare_messages_for_llm

# 自动压缩和优化上下文
messages = prepare_messages_for_llm(
    history_messages=long_history,
    system_prompt=system_prompt,
    agent_name="pm_agent"
)
```

**优势：**
- 💰 节省 30-60% Token
- 🧠 保留关键信息
- 🔄 自动压缩

---

## 📊 数据模型

### PRD（产品需求文档）

```json
{
  "vision": "打造最便捷的遛狗服务平台...",
  "target_audience": ["忙碌的都市白领", "行动不便的老年人"],
  "core_features": ["在线预约", "实时定位", "安全保险"],
  "user_stories": [
    {
      "role": "狗主人",
      "action": "预约遛狗服务",
      "benefit": "节省时间，保障宠物安全"
    }
  ],
  "mermaid_flowchart": "graph TD; A[用户] --> B[浏览]",
  "non_functional": "响应时间 < 2s，可用性 99.9%"
}
```

### TRD（技术设计文档）

```json
{
  "tech_stack": {
    "frontend": "React + TypeScript",
    "backend": "FastAPI + Python",
    "database": "PostgreSQL",
    "infra": "Docker + AWS"
  },
  "architecture_overview": "微服务架构，前后端分离",
  "mermaid_er_diagram": "erDiagram...",
  "api_endpoints": [
    {
      "path": "/api/v1/users",
      "method": "GET",
      "description": "获取用户列表"
    }
  ]
}
```

---

## 🧪 测试

### 测试覆盖

| 类型 | 覆盖范围 | 命令 |
|------|----------|------|
| 环境测试 | 环境检测、配置加载 | `python test_environment.py` |
| 单元测试 | Agent 逻辑、工具函数 | `pytest tests/unit/ -v` |
| 集成测试 | Agent 间协作 | `pytest tests/integration/ -v` |
| E2E 测试 | 完整流程 | `python tests/e2e_pm_reviewer.py` |

---

## 🔧 高级配置

### Agent 专用模型配置

```bash
# .env.development
DEFAULT_MODEL=glm-4              # 默认模型
PM_MODEL=glm-4-plus             # PM Agent 使用高性能模型
ARCHITECT_MODEL=glm-4-plus      # Architect Agent 使用高性能模型
BACKEND_DEV_MODEL=glm-4-turbo   # 后端开发使用快速模型
FRONTEND_DEV_MODEL=glm-4-turbo  # 前端开发使用快速模型
```

### 多环境配置

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

---

## 📚 文档

### 用户文档
- [项目标准](docs/PROJECT_STANDARDS.md) - 详细的开发标准和规范
- [上下文管理](docs/CONTEXT_MANAGEMENT.md) - 智能上下文管理指南
- [RAG 集成](docs/PM_RAG_INTEGRATION.md) - RAG 系统使用指南 ⭐
- [代码生成系统](docs/CODE_GENERATION_SYSTEM.md) - 代码生成详解 ⭐

### 技术文档
- [多环境配置](docs/MULTI_ENVIRONMENT_CONFIG.md) - 多环境配置详解
- [工作流 API](docs/WORKFLOW_API_AND_MONITORING.md) - 工作流 API 和监控
- [Agent 模型配置](docs/AGENT_MODEL_CONFIG.md) - Agent 模型配置指南

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

- 提交 [Issue](https://github.com/mmiamor/omni_agent_graph/issues)
- 发送邮件到 [mmiamor@icloud.com](mailto:mmiamor@icloud.com)

---

<div align="center">

**Made with ❤️ by Omni Agent Graph Team**

*最后更新: 2026-04-09*

[⬆ 返回顶部](#-omni-agent-graph)

</div>

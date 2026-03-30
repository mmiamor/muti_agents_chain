# 🚀 Multi-Agent Chain — AI 软件开发流水线

> 基于 LangGraph 的 Multi-Agent 系统，实现从产品需求到代码交付的全流程自动化。

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.3+-green.svg)](https://github.com/langchain-ai/langgraph)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## ✨ 特性

- 🤖 **Multi-Agent 协作** - 7 个专业 Agent 自动协作完成软件开发全流程
- 🔄 **智能审查机制** - 每个产出物经过自动审查，不合格自动修改
- 🧠 **智能上下文管理** - 自动压缩和优化对话上下文，节省 30-60% token
- 📊 **强类型数据模型** - 所有产出物使用 Pydantic 模型，确保数据质量
- 🎯 **LangGraph 编排** - 基于状态机的流程控制，支持检查点和回滚
- 🚦 **自动路由决策** - 智能判断下一步操作，无需人工干预
- 📈 **可观测性** - 完善的日志和监控，实时追踪执行状态

---

## 🏗️ 架构概览

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

### 完整开发阶段

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

| 类别 | 技术 | 用途 |
|------|------|------|
| **语言** | Python 3.13+ | 核心开发语言 |
| **框架** | LangGraph 0.3+ | Agent 编排与状态机 |
| **LLM** | 智谱 GLM-5 | 主力语言模型 |
| **API** | FastAPI | HTTP 服务层 |
| **数据** | Pydantic | 强类型数据验证 |
| **测试** | pytest + pytest-asyncio | 单元测试和 E2E 测试 |

---

## 📁 项目结构

```
muti_agents_chain/
├── src/
│   ├── agents/                    # 🤖 Multi-Agent 系统
│   │   ├── base.py                # Agent 基类
│   │   ├── factory.py             # Agent 工厂
│   │   ├── registry.py            # Agent 注册表
│   │   └── nodes/                 # Agent 节点实现
│   │       ├── pm_node.py         # PM Agent
│   │       ├── architect_node.py  # Architect Agent
│   │       ├── design_node.py     # Design Agent
│   │       ├── backend_dev_node.py# Backend Dev Agent
│   │       ├── frontend_dev_node.py# Frontend Dev Agent
│   │       ├── qa_node.py         # QA Agent
│   │       └── reviewer_node.py   # Reviewer Agent
│   │
│   ├── core/                      # ⚙️ 核心引擎
│   │   ├── orchestrator.py        # LangGraph 编排器
│   │   ├── engine.py              # 主引擎
│   │   ├── pipeline.py            # 处理管道
│   │   └── scheduler.py           # 任务调度器
│   │
│   ├── memory/                    # 🧠 智能记忆系统
│   │   ├── context_manager.py     # 上下文管理器
│   │   └── agent_context.py       # Agent 上下文工具
│   │
│   ├── models/                    # 📊 数据模型
│   │   ├── state.py               # LangGraph State 定义
│   │   ├── document_models.py     # 文档模型（PRD/TRD等）
│   │   └── agent_models.py        # Agent 相关模型
│   │
│   ├── prompts/                   # 💬 Agent 提示词
│   │   ├── pm_agent.py
│   │   ├── architect_agent.py
│   │   ├── design_agent.py
│   │   ├── backend_dev_agent.py
│   │   ├── frontend_dev_agent.py
│   │   ├── qa_agent.py
│   │   └── reviewer_agent.py
│   │
│   ├── services/                  # 🔧 基础服务
│   │   ├── llm_service.py         # LLM 调用服务
│   │   ├── chain_service.py       # Chain 编排服务
│   │   └── memory_service.py      # 记忆管理服务
│   │
│   ├── config/                    # ⚙️ 配置管理
│   │   ├── settings.py            # 环境配置
│   │   └── context_config.py      # 上下文配置
│   │
│   ├── api/                       # 🌐 API 层
│   │   ├── server.py              # FastAPI 服务器
│   │   └── routes.py              # API 路由
│   │
│   └── utils/                     # 🛠️ 工具函数
│       ├── logger.py              # 日志配置
│       ├── json_extract.py        # JSON 提取工具
│       └── helpers.py             # 通用工具
│
├── tests/                         # 🧪 测试
│   ├── unit/                      # 单元测试
│   ├── integration/               # 集成测试
│   └── e2e_pm_reviewer.py         # E2E 测试
│
├── docs/                          # 📚 文档
│   ├── PROJECT_STANDARDS.md       # 项目标准
│   ├── CONTEXT_MANAGEMENT.md      # 上下文管理指南
│   └── README.md                  # 本文件
│
├── .env.example                   # 环境变量示例
├── requirements.txt               # Python 依赖
└── README.md                      # 项目说明
```

---

## 🚀 快速开始

### 1. 环境准备

```bash
# 安装 Python 3.13（使用 pyenv）
pyenv install 3.13.11
pyenv local 3.13.11

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .\.venv\Scripts\Activate.ps1  # Windows
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```ini
# LLM API 配置
ZAI_API_KEY=your_zhipu_api_key_here
OPENAI_API_KEY=your_zhipu_api_key_here
OPENAI_BASE_URL=https://open.bigmodel.cn/api/paas/v4/
DEFAULT_MODEL=glm-5

# 服务配置
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=true
LOG_LEVEL=INFO

# Agent 配置
NODE_DELAY=2                    # 节点间冷却秒数（防限流）
MAX_REVISION_COUNT=3            # 单 Agent 最大修改次数
RECURSION_LIMIT=30              # LangGraph 最大递归深度
STREAM_ENABLED=true             # 启用流式输出

# 上下文管理配置
MAX_CONTEXT_MESSAGES=100        # 最大上下文消息数
MAX_CONTEXT_TOKENS=8000         # 最大上下文 tokens
COMPACT_THRESHOLD=0.8           # 触发压缩的阈值
```

### 4. 运行测试

```bash
# 单元测试
python -m pytest tests/unit/ -v

# E2E 测试（需要有效的 API Key）
python tests/e2e_pm_reviewer.py
```

### 5. 启动服务

```bash
# 启动 FastAPI 服务
python -m src.main

# 或使用 uvicorn 直接启动
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

访问 http://localhost:8000 查看 API 文档。

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

### HTTP API 调用

```bash
# 启动完整流水线
curl -X POST http://localhost:8000/api/v1/run \
  -H "Content-Type: application/json" \
  -d '{
    "message": "我想做一个遛狗APP"
  }'

# 查询任务状态
curl http://localhost:8000/api/v1/status/{thread_id}

# 获取任务结果
curl http://localhost:8000/api/v1/result/{thread_id}
```

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

## 🔧 开发指南

### 新增 Agent

只需 3 步即可添加新的 Agent：

1. **创建节点** - `src/agents/nodes/your_agent.py`
```python
class YourAgent(BaseAgent):
    name = "your_agent"
    role = "您的角色"

    async def run(self, state: AgentState) -> dict:
        # 实现逻辑
        return {"artifact": ...}

    async def review(self, state: AgentState) -> bool:
        # 自我审查
        return True
```

2. **创建 Prompt** - `src/prompts/your_agent.py`
```python
SYSTEM_PROMPT = """
您是一位专业的{角色}...
"""
```

3. **注册阶段** - 在 `src/core/orchestrator.py` 添加配置
```python
StageRegistry.stages = [
    # ... 其他阶段
    {
        "agent": AgentNames.YOUR_AGENT,
        "artifact": "your_artifact",
        "next_agent": AgentNames.NEXT_AGENT,
    },
]
```

### 上下文优化使用

```python
from src.memory.agent_context import prepare_messages_for_llm

# 在 Agent 中使用优化的上下文
messages = prepare_messages_for_llm(
    state["messages"],
    system_prompt=SYSTEM_PROMPT,
    agent_name="your_agent",
)

# 自动处理：
# ✅ 上下文压缩
# ✅ 系统提示添加
# ✅ Token 限制裁剪
# ✅ 关键信息保留
```

---

## 📈 性能优化

### 智能上下文管理

- **自动压缩**: 当消息超过阈值时自动压缩
- **智能保留**: 保留关键信息（系统提示、用户需求、决策点）
- **Token 节省**: 平均节省 30-60% 的 token 使用量
- **滑动窗口**: 保留最近的消息维持对话连贯性

### 配置优化

```python
from src.config.context_config import get_balanced_config

# 选择预设配置
config = get_balanced_config()  # 轻量/平衡/全面

# 或自定义配置
from src.memory.context_manager import ContextConfig

config = ContextConfig(
    max_messages=100,
    max_tokens=8000,
    compact_threshold=0.8,
)
```

---

## 🧪 测试

### 测试覆盖

| 类型 | 覆盖范围 | 命令 |
|------|----------|------|
| 单元测试 | Agent 逻辑、工具函数 | `pytest tests/unit/ -v` |
| 集成测试 | Agent 间协作 | `pytest tests/integration/ -v` |
| E2E 测试 | 完整流程 | `python tests/e2e_pm_reviewer.py` |

### 测试数据

测试数据位于 `tests/fixtures/` 目录，包含：
- 示例 PRD
- 示例 TRD
- 示例设计文档

---

## 📚 文档

- [项目标准](docs/PROJECT_STANDARDS.md) - 详细的开发标准和规范
- [上下文管理](docs/CONTEXT_MANAGEMENT.md) - 智能上下文管理指南
- [API 文档](http://localhost:8000/docs) - FastAPI 自动生成的 API 文档

---

## 🔍 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `ZAI_API_KEY` | — | 智谱 API Key（必填） |
| `DEFAULT_MODEL` | `glm-5` | 默认 LLM 模型 |
| `OPENAI_BASE_URL` | 智谱 API | OpenAI 兼容 Base URL |
| `NODE_DELAY` | `2` | 节点间冷却秒数 |
| `MAX_REVISION_COUNT` | `3` | 单 Agent 最大修改次数 |
| `RECURSION_LIMIT` | `30` | LangGraph 最大递归深度 |
| `STREAM_ENABLED` | `true` | 启用流式输出 |

---

## 🤝 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交变更 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

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
- 发送邮件到 [mmiamor@icloud.com](mmiamor@icloud.com)

---

**Made with ❤️ by Multi-Agent Chain Team**

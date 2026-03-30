# Agent 模型配置指南

## 概述

Multi-Agent Chain 现在支持为不同的 Agent 配置不同的 LLM 模型。这允许您根据每个 Agent 的特定需求选择最合适的模型，在性能、成本和质量之间取得最佳平衡。

## 支持的 Agent

系统支持以下 7 个 Agent 的独立模型配置：

1. **PM Agent** (`pm_agent`) - 产品经理 Agent
2. **Architect Agent** (`architect_agent`) - 架构师 Agent
3. **Design Agent** (`design_agent`) - 设计师 Agent
4. **Backend Dev Agent** (`backend_dev_agent`) - 后端开发 Agent
5. **Frontend Dev Agent** (`frontend_dev_agent`) - 前端开发 Agent
6. **QA Agent** (`qa_agent`) - 测试 Agent
7. **Reviewer Agent** (`reviewer_agent`) - 审查员 Agent

## 配置方法

### 方法 1: 环境变量配置

在环境配置文件（`.env.development`、`.env.testing`、`.env.production`）中添加：

```bash
# 默认模型（所有未配置的 Agent 使用）
DEFAULT_MODEL=glm-4

# Agent 专用模型
PM_MODEL=glm-4-plus
ARCHITECT_MODEL=glm-4-plus
BACKEND_DEV_MODEL=glm-4-turbo
FRONTEND_DEV_MODEL=glm-4-turbo
```

### 方法 2: 代码中配置

```python
from src.config import parse_agent_model_config, settings

# 创建自定义配置
config = parse_agent_model_config(
    default_model="glm-4",
    pm_model="glm-4-plus",
    architect_model="glm-4-plus",
    backend_dev_model="glm-4-turbo",
)

# 使用配置
model = config.get_model_for_agent("pm_agent")
print(f"PM Agent 使用模型: {model}")
```

## 模型选择建议

### 高性能模型（如 glm-4-plus）

**适合**:
- PM Agent - 需求分析和产品规划
- Architect Agent - 系统架构设计
- Reviewer Agent - 代码审查

**原因**: 这些任务需要深度思考和复杂推理

### 标准模型（如 glm-4）

**适合**:
- Design Agent - UI/UX 设计
- QA Agent - 测试用例生成

**原因**: 这些任务需要平衡性能和质量

### 快速模型（如 glm-4-turbo）

**适合**:
- Backend Dev Agent - 后端代码生成
- Frontend Dev Agent - 前端代码生成

**原因**: 代码生成任务对速度要求较高，且可以通过审查机制保证质量

## 配置示例

### 开发环境配置

```bash
# .env.development
DEFAULT_MODEL=glm-4
PM_MODEL=glm-4
ARCHITECT_MODEL=glm-4
BACKEND_DEV_MODEL=glm-4-turbo
FRONTEND_DEV_MODEL=glm-4-turbo
```

### 生产环境配置

```bash
# .env.production
DEFAULT_MODEL=glm-4-plus
PM_MODEL=glm-4-plus
ARCHITECT_MODEL=glm-4-plus
BACKEND_DEV_MODEL=glm-4-plus
FRONTEND_DEV_MODEL=glm-4-plus
QA_MODEL=glm-4-plus
REVIEWER_MODEL=glm-4-plus
```

### 测试环境配置

```bash
# .env.testing
DEFAULT_MODEL=glm-4-flash
# 所有 Agent 使用快速模型以加快测试
```

## API 使用

### 创建 Agent 实例

```python
from src.agents.factory import create_llm

# 为特定 Agent 创建 LLM
pm_llm = create_llm(agent_name="pm_agent")
qa_llm = create_llm(agent_name="qa_agent")

# 创建默认 LLM
default_llm = create_llm()
```

### 检查模型配置

```python
from src.config import settings

# 获取 Agent 模型配置
config = settings.agent_model_config

# 获取特定 Agent 的模型
pm_model = config.get_model_for_agent("pm_agent")

# 获取所有使用的模型
all_models = config.get_all_models()

# 查看完整配置
config_dict = config.to_dict()
```

## 成本优化策略

### 1. 混合策略

为关键 Agent 使用高性能模型，为其他 Agent 使用标准模型：

```bash
DEFAULT_MODEL=glm-4
PM_MODEL=glm-4-plus      # 关键
ARCHITECT_MODEL=glm-4-plus  # 关键
REVIEWER_MODEL=glm-4-plus   # 关键
```

### 2. 开发/生产分离

- 开发环境：使用快速模型
- 生产环境：使用高性能模型

### 3. 任务特定优化

- 代码生成：使用快速模型 + 自动审查
- 决策类任务：使用高性能模型

## 监控和调优

### 查看模型使用情况

```python
from src.config import settings

config = settings.agent_model_config
print("当前模型配置:")
print(f"默认模型: {config.default_model}")
print(f"Agent 模型映射: {config.model_mapping}")
print(f"所有使用的模型: {config.get_all_models()}")
```

### 性能监控

系统会记录每个 Agent 的执行时间、Token 使用量等指标，可以据此优化模型选择。

## 故障排除

### Agent 未使用配置的模型

1. 检查环境变量是否正确设置
2. 确认已重新加载配置
3. 验证 Agent 名称是否正确

### 配置未生效

```python
# 强制重新加载配置
from src.config import reload_settings
settings = reload_settings()
```

## 最佳实践

1. **从小开始**: 先使用默认模型，再根据需要优化
2. **监控成本**: 关注不同模型的使用成本
3. **质量优先**: 关键路径使用更好的模型
4. **测试验证**: 在测试环境验证配置效果
5. **文档记录**: 记录不同配置的效果和成本

## 更新日志

- **v0.1.1** - 新增 Agent 专用模型配置功能
- 支持为每个 Agent 配置独立模型
- 提供默认模型回退机制
- 支持运行时配置查询

# 自定义工作流配置指南

## 概述

Multi-Agent Chain 现在支持完全自定义的工作流配置。您可以：

- 🔧 **自定义 Agent 执行顺序**
- ⚡ **并行执行多个 Agent**
- 🎯 **跳过不需要的 Agent**
- 🔀 **条件分支执行**
- ⚙️ **灵活的审查策略**

## 快速开始

### 方式 1: 使用预定义模板

```python
from src.core.workflow_loader import WorkflowLoader

loader = WorkflowLoader()

# 加载快速原型模板
workflow = loader.load_template("rapid_prototype")

# 可用模板:
# - full_pipeline: 完整流水线
# - rapid_prototype: 快速原型
# - design_only: 仅设计
# - backend_only: 仅后端
# - frontend_only: 仅前端
```

### 方式 2: 从文件加载

```python
# 加载 YAML 配置
workflow = loader.load_from_file("workflows/my_workflow.yaml")

# 加载 JSON 配置
workflow = loader.load_from_file("workflows/my_workflow.json")
```

### 方式 3: 动态创建

```python
# 创建自定义工作流
workflow = loader.create_custom_workflow(
    name="my_workflow",
    agents=["pm_agent", "backend_dev_agent"],
    parallel=False,
    skip_review=True,
)
```

## 配置文件格式

### YAML 格式

```yaml
name: my_custom_workflow
description: 我的自定义工作流
version: "1.0.0"

stages:
  - name: stage1
    agents:
      - name: pm_agent
        enabled: true
        max_revisions: 3
    mode: sequential
    review:
      enabled: true
      strategy: auto
      auto_fix: true
      max_fix_attempts: 3

global_settings:
  timeout: 300
  retry_on_failure: true
```

### JSON 格式

```json
{
  "name": "my_custom_workflow",
  "description": "我的自定义工作流",
  "version": "1.0.0",
  "stages": [
    {
      "name": "stage1",
      "agents": [
        {
          "name": "pm_agent",
          "enabled": true,
          "max_revisions": 3
        }
      ],
      "mode": "sequential",
      "review": {
        "enabled": true,
        "strategy": "auto"
      }
    }
  ]
}
```

## 配置选项详解

### 阶段 (Stage) 配置

| 字段 | 类型 | 说明 |
|------|------|------|
| `name` | string | 阶段名称 |
| `agents` | list | Agent 列表 |
| `mode` | string | 执行模式: `sequential`, `parallel`, `conditional` |
| `review` | object | 审查配置 |
| `conditions` | list | 条件规则（conditional 模式） |
| `parallel_group` | string | 并行组名称 |

### Agent 配置

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `name` | string | 必填 | Agent 名称 |
| `enabled` | boolean | true | 是否启用 |
| `max_revisions` | int | 3 | 最大修改次数 |
| `timeout` | int | 300 | 超时时间（秒） |
| `retry_on_failure` | boolean | true | 失败时重试 |
| `custom_prompt` | string | null | 自定义提示词 |

### 执行模式 (Execution Mode)

#### Sequential - 顺序执行

```yaml
stages:
  - name: sequential_stage
    agents:
      - name: pm_agent
      - name: architect_agent
    mode: sequential  # 按 pm → architect 顺序执行
```

#### Parallel - 并行执行

```yaml
stages:
  - name: parallel_stage
    agents:
      - name: backend_dev_agent
      - name: frontend_dev_agent
    mode: parallel  # 同时执行后端和前端
    parallel_group: dev_group
```

#### Conditional - 条件执行

```yaml
stages:
  - name: conditional_stage
    agents: []
    mode: conditional
    conditions:
      - field: project_type
        operator: eq
        value: web
        then_branch:
          - frontend_dev_agent
          - backend_dev_agent
        else_branch:
          - backend_dev_agent
```

### 审查配置 (Review Config)

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `enabled` | boolean | true | 是否启用审查 |
| `strategy` | string | auto | 审查策略: `auto`, `manual`, `skip`, `conditional` |
| `reviewer` | string | null | 指定审查员 Agent |
| `auto_fix` | boolean | true | 是否自动修复 |
| `max_fix_attempts` | int | 3 | 最大修复次数 |

## 使用场景

### 场景 1: 快速原型开发

```yaml
name: rapid_prototype
description: 快速原型，跳过审查
stages:
  - name: quick_design
    agents:
      - name: pm_agent
      - name: architect_agent
    mode: sequential
    review:
      enabled: false  # 跳过审查

  - name: quick_dev
    agents:
      - name: backend_dev_agent
      - name: frontend_dev_agent
    mode: parallel
    review:
      enabled: false  # 跳过审查
```

### 场景 2: 仅后端开发

```yaml
name: backend_only
description: 只包含后端开发
stages:
  - name: analysis
    agents:
      - name: pm_agent
    mode: sequential

  - name: architecture
    agents:
      - name: architect_agent
    mode: sequential

  - name: development
    agents:
      - name: backend_dev_agent
    mode: sequential
```

### 场景 3: 并行开发

```yaml
name: parallel_dev
description: 前后端并行开发
stages:
  - name: planning
    agents:
      - name: pm_agent
      - name: architect_agent
    mode: sequential

  - name: parallel_development
    agents:
      - name: backend_dev_agent
      - name: frontend_dev_agent
    mode: parallel  # 并行执行
    parallel_group: dev_team

  - name: testing
    agents:
      - name: qa_agent
    mode: sequential
```

### 场景 4: 跳过特定阶段

```python
# 加载完整流水线
workflow = loader.load_template("full_pipeline")

# 跳过设计阶段
workflow.skip_agents = ["design_agent"]

# 执行时会自动跳过 design_agent
```

## 执行工作流

```python
from src.core.workflow_engine import WorkflowEngine
from src.models.state import AgentState

# 创建工作流引擎
engine = WorkflowEngine(workflow)

# 准备初始状态
initial_state = AgentState(
    messages=[{"role": "user", "content": "创建一个 TODO 应用"}],
    sender="user",
)

# 执行工作流
final_state = await engine.execute(initial_state)

# 获取执行摘要
summary = engine.get_execution_summary()
print(summary)
```

## 高级功能

### 1. 自定义 Agent 提示词

```yaml
stages:
  - name: custom_prompt_stage
    agents:
      - name: pm_agent
        custom_prompt: |
          你是一位专注于移动应用的产品经理。
          请特别关注用户体验和性能优化。
```

### 2. 条件跳过

```yaml
name: conditional_skip
skip_conditions:
  - field: complexity
    operator: lt
    value: 5
    then_branch:
      - pm_agent
      - backend_dev_agent
    else_branch:
      - pm_agent
      - architect_agent
      - backend_dev_agent
```

### 3. 全局设置

```yaml
global_settings:
  timeout: 300              # 默认超时时间
  retry_on_failure: true    # 失败重试
  save_intermediate_results: true  # 保存中间结果
  enable_logging: true      # 启用详细日志
```

## API 参考

### WorkflowLoader

```python
class WorkflowLoader:
    def __init__(self, config_dir: Optional[Path] = None)

    def load_template(self, template_name: str) -> WorkflowConfig
    def load_from_file(self, file_path: Union[str, Path]) -> WorkflowConfig
    def load_from_dict(self, data: Dict) -> WorkflowConfig
    def save_to_file(self, config: WorkflowConfig, file_path: Union[str, Path], format: str = "yaml")
    def list_available_workflows(self) -> List[str]
    def create_custom_workflow(self, name: str, agents: List[str], parallel: bool = False, skip_review: bool = False) -> WorkflowConfig
```

### WorkflowEngine

```python
class WorkflowEngine:
    def __init__(self, workflow_config: WorkflowConfig)

    async def execute_stage(self, stage: WorkflowStage, state: AgentState) -> AgentState
    async def execute(self, initial_state: AgentState, stop_at_stage: Optional[str] = None) -> AgentState
    def get_execution_summary(self) -> Dict[str, Any]
```

## 最佳实践

1. **从模板开始** - 先使用预定义模板，再根据需求调整
2. **模块化设计** - 将复杂流程分解为多个简单阶段
3. **合理使用并行** - 只在独立任务间使用并行执行
4. **审查策略** - 开发时跳过审查，生产时启用
5. **测试配置** - 使用模拟状态测试工作流配置

## 故障排除

### 问题: Agent 执行失败

**解决方案**:
- 检查 Agent 名称是否正确
- 验证 Agent 配置参数
- 查看日志了解详细错误

### 问题: 并行执行结果不符合预期

**解决方案**:
- 确保 Agents 之间没有依赖关系
- 检查状态更新逻辑
- 考虑改用顺序执行

### 问题: 配置文件加载失败

**解决方案**:
- 验证 YAML/JSON 格式
- 检查必需字段是否完整
- 查看验证错误信息

## 示例配置

### 完整示例

查看 `workflows/` 目录获取更多示例：

- `full_pipeline.yaml` - 完整开发流水线
- `rapid_prototype.yaml` - 快速原型
- `backend_only.yaml` - 仅后端
- `frontend_only.yaml` - 仅前端

### 代码示例

查看 `examples/custom_workflow_example.py` 获取完整使用示例。

---

**更新**: 2026-03-30
**版本**: 1.0.0

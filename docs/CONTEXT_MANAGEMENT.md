# 上下文记忆管理系统

## 概述

本项目实现了智能上下文管理系统，能够自动检测、压缩和优化对话历史，有效控制 token 使用量，同时保留关键信息。

## 核心功能

### 1. 自动检测
- **消息数量监控**: 当消息数达到阈值时触发压缩
- **Token 估算**: 基于字符数智能估算 token 使用量
- **实时统计**: 提供详细的上下文统计信息

### 2. 智能压缩
- **保留关键消息**: 系统提示、用户需求、决策点
- **滑动窗口**: 保留最近的消息维持对话连贯性
- **语义摘要**: 压缩中间内容为简洁摘要

### 3. 灵活配置
- 支持多种预设配置（轻量/平衡/全面）
- 可自定义压缩阈值和保留策略
- 支持动态调整配置

## 使用方法

### 基础使用

```python
from src.memory.agent_context import prepare_messages_for_llm

# 在 Agent 节点中
messages = prepare_messages_for_llm(
    state["messages"],
    system_prompt=SYSTEM_PROMPT,
    agent_name="pm_agent"
)

response = await client.chat.completions.create(
    messages=messages,
    model="glm-5"
)
```

### 高级配置

```python
from src.config.context_config import setup_context_management

# 在项目启动时配置
context_manager = setup_context_management()

# 或使用预设配置
from src.config.context_config import get_balanced_config
context_manager = get_context_manager(get_balanced_config())
```

### 直接使用 ContextManager

```python
from src.memory.context_manager import get_context_manager

manager = get_context_manager()

# 检查是否需要压缩
if manager.should_compact(messages):
    messages = manager.compact_messages(messages)

# 获取统计信息
stats = manager.get_stats()
print(f"压缩次数: {stats['compression_count']}")
print(f"压缩率: {stats['last_compaction_ratio']:.1%}")
```

## 配置说明

### ContextConfig 参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `max_messages` | 100 | 最大消息数量 |
| `max_tokens` | 8000 | 最大 token 估算 |
| `compact_threshold` | 0.8 | 触发压缩的阈值（80%） |
| `keep_first_n` | 5 | 保留前 N 条关键消息 |
| `keep_last_n` | 20 | 保留最近 N 条消息 |
| `enable_semantic_compact` | True | 是否启用语义压缩 |

### 预设配置

#### 轻量级配置 (get_lightweight_config)
- 适合快速迭代、简单任务
- 消息数量: 50
- Token 限制: 4000
- 禁用语义压缩

#### 平衡配置 (get_balanced_config)
- 适合大多数场景
- 消息数量: 100
- Token 限制: 8000
- 启用语义压缩

#### 全面配置 (get_comprehensive_config)
- 适合复杂、长期项目
- 消息数量: 200
- Token 限制: 16000
- 启用语义压缩

## 性能优化

### Token 节省
- 自动压缩可节省 30-60% 的 token 使用
- 智能保留关键信息，不影响对话质量
- 减少无效信息的传递

### 速度提升
- 减少 LLM 处理时间
- 降低网络传输延迟
- 提升整体响应速度

### 成本控制
- 减少不必要的 token 消耗
- 优化 API 调用成本
- 提高资源利用率

## 监控与调试

### 获取统计信息

```python
from src.memory.agent_context import get_context_stats

stats = get_context_stats()
print(f"总消息数: {stats['total_messages']}")
print(f"估算 tokens: {stats['estimated_tokens']}")
print(f"压缩次数: {stats['compression_count']}")
```

### 日志输出

系统会自动记录以下关键事件：
- 上下文压缩触发
- 压缩执行详情
- Agent 上下文准备
- Token 使用统计

## 最佳实践

1. **项目启动时配置**: 在 `src/config/__init__.py` 中调用 `setup_context_management()`
2. **监控统计**: 定期检查 `get_context_stats()` 了解压缩效果
3. **调整阈值**: 根据实际使用情况调整 `compact_threshold`
4. **保留关键信息**: 确保 `keep_first_n` 足够大以保留初始需求
5. **测试验证**: 在不同场景下测试压缩后的上下文质量

## 注意事项

1. **系统提示**: 系统提示始终保留，不会被压缩
2. **用户消息**: 用户消息优先级较高，尽量保留
3. **压缩时机**: 默认在 80% 阈值时触发，可根据需求调整
4. **语义摘要**: 语义摘要会增加少量处理时间，但能更好地保留上下文

## 扩展性

系统设计支持以下扩展：
- 集成 Redis 进行持久化存储
- 使用向量数据库进行语义检索
- 实现更复杂的压缩策略
- 添加上下文质量评估机制

## 故障排除

### 压缩过于频繁
- 增加 `max_messages` 或 `max_tokens`
- 提高 `compact_threshold`

### 上下文信息丢失
- 增加 `keep_first_n` 和 `keep_last_n`
- 启用 `enable_semantic_compact`

### 性能问题
- 使用轻量级配置
- 禁用语义压缩

## 相关文件

- `src/memory/context_manager.py` - 核心上下文管理器
- `src/memory/agent_context.py` - Agent 工具函数
- `src/services/memory_service.py` - 集成记忆服务
- `src/config/context_config.py` - 配置管理

# 智谱 API 优化配置指南

## 📋 当前问题

从 E2E 测试日志可以看到，系统遇到以下 API 限制问题：

1. **Rate Limiting (429)** - API 限频
2. **Timeout** - 请求超时
3. **长时间等待** - 每次请求需要等待较长时间

## 🔧 已优化的配置

### 1. 超时和重试配置

```python
# src/config/settings.py
LLM_RETRY_MAX: int = 5              # 最大重试次数（3 → 5）
LLM_RETRY_BASE_DELAY: float = 5.0   # 重试基础延迟（3 → 5秒）
NODE_DELAY: float = 5.0              # 节点间延迟（2 → 5秒）
LLM_TIMEOUT: int = 300               # LLM 请求超时（新增，5分钟）
```

### 2. LLM 服务配置

```python
# src/services/llm_service.py
self.client = AsyncOpenAI(
    api_key=api_key,
    base_url=base_url,
    timeout=300.0,          # 增加到 5 分钟
    max_retries=0,          # 我们自己控制重试
)
```

## 💡 建议的 .env 配置

根据当前智谱 API 的限制情况，建议在 `.env` 文件中设置：

```ini
# ── LLM API 配置 ──
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://open.bigmodel.cn/api/paas/v4/
DEFAULT_MODEL=glm-5

# ── 性能优化配置 ──
NODE_DELAY=8                    # 节点间冷却秒数（建议 5-10）
LLM_RETRY_MAX=5                 # 最大重试次数
LLM_RETRY_BASE_DELAY=8          # 重试基础延迟秒数
LLM_TIMEOUT=300                 # LLM 超时时间（秒）

# ── Agent 配置 ──
MAX_REVISION_COUNT=3            # 单 Agent 最大修改次数
RECURSION_LIMIT=30              # LangGraph 最大递归深度
STREAM_ENABLED=true             # 启用流式输出

# ── 上下文管理 ──
MAX_CONTEXT_MESSAGES=100        # 最大上下文消息数
MAX_CONTEXT_TOKENS=8000         # 最大上下文 tokens
COMPACT_THRESHOLD=0.8           # 触发压缩的阈值
```

## 🚀 分阶段测试策略

由于 API 限制，建议采用分阶段测试：

### 阶段 1: PM Agent 单独测试

```python
# 只测试 PM Agent 生成 PRD
initial_state = {
    "messages": [HumanMessage(content="简单需求")],
    "current_phase": AgentPhase.REQUIREMENT_GATHERING,
    "sender": "user",
}

# 设置较小的递归限制
config = {
    "configurable": {
        "thread_id": "test-pm-only",
        "recursion_limit": 10  # 限制深度
    }
}
```

### 阶段 2: PM → Reviewer 测试

测试 PM 和 Reviewer 之间的交互，确保审查机制正常工作。

### 阶段 3: 完整流程测试

只有在阶段 1 和 2 稳定后才进行完整流程测试。

## 📊 监控和诊断

### 1. 使用增强的 E2E 测试

新的 E2E 测试提供了详细的日志输出：

```bash
python tests/e2e_pm_reviewer.py
```

输出包含：
- ⏱️ 详细的执行时间
- 📊 消息统计
- 🔄 重试次数
- 🧠 上下文压缩统计
- 💾 结果保存为 JSON

### 2. 查看保存的结果

测试完成后会保存结果文件：

```bash
# 查看最新的测试结果
ls -la test_output_*.json | tail -1

# 分析结果
cat test_output_e2e-test-*.json | jq '.context_stats'
```

## 🛠️ 故障排除

### 问题 1: 频繁的 429 错误

**解决方案：**
1. 增加 `NODE_DELAY` 到 10 秒
2. 减少 `MAX_REVISION_COUNT` 到 2
3. 考虑使用更快的模型（如 `glm-4`）

### 问题 2: 持续超时

**解决方案：**
1. 检查网络连接
2. 增加 `LLM_TIMEOUT` 到 600 秒
3. 检查智谱 API 状态

### 问题 3: 上下文过大

**解决方案：**
1. 降低 `MAX_CONTEXT_TOKENS` 到 4000
2. 降低 `COMPACT_THRESHOLD` 到 0.7
3. 启用更激进的压缩策略

## 📈 性能优化建议

### 1. 使用智能上下文管理

```python
from src.memory.agent_context import prepare_messages_for_llm

# 在所有 Agent 中使用优化的上下文
messages = prepare_messages_for_llm(
    state["messages"],
    system_prompt=SYSTEM_PROMPT,
    agent_name="your_agent",
)
```

### 2. 实施请求缓存

对于相同的输入，考虑缓存结果：

```python
import hashlib
import json

def cache_key(messages, system_prompt):
    content = json.dumps(messages + [system_prompt])
    return hashlib.md5(content.encode()).hexdigest()
```

### 3. 使用流式输出

启用流式输出可以提供更好的用户体验：

```python
response = await llm.client.chat.completions.create(
    messages=messages,
    model=settings.DEFAULT_MODEL,
    stream=True,  # 启用流式输出
)

async for chunk in response:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

## 🔮 未来改进

1. **并行处理**: 考虑将独立的 Agent 并行执行
2. **批处理**: 合并多个小请求
3. **缓存层**: 实现 Redis 缓存
4. **降级策略**: API 不可用时的备用方案

---

**最后更新**: 2026-03-30
**相关文档**:
- [项目标准](PROJECT_STANDARDS.md)
- [上下文管理](CONTEXT_MANAGEMENT.md)

# 流式输出 API 文档

## 📋 概述

Multi-Agent Chain 提供基于 Server-Sent Events (SSE) 的流式输出 API，允许客户端实时接收 Agent 执行过程中的事件。

## 🚀 特性

- ✅ **实时事件推送** - Agent 执行过程中的每个阶段都会推送事件
- ✅ **标准化格式** - 统一的事件格式，易于解析
- ✅ **多模式支持** - 支持完整 Pipeline 和单 Agent 执行
- ✅ **错误处理** - 完善的错误处理和重试机制
- ✅ **会话管理** - 支持 ThreadID 进行会话管理

## 🔌 端点

### 1. 完整 Pipeline 流式执行

**端点**: `POST /api/v1/stream/run`

**参数**:
- `message` (string, 必需): 用户需求描述
- `thread_id` (string, 可选): 会话线程ID

**示例**:
```bash
curl -N -X POST "http://localhost:8000/api/v1/stream/run?message=做一个番茄钟应用"
```

**JavaScript 示例**:
```javascript
const url = '/api/v1/stream/run';
const params = new URLSearchParams({
    message: '做一个番茄钟应用',
    thread_id: 'my-thread-123'  // 可选
});

const response = await fetch(`${url}?${params}`, {
    method: 'POST',
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value);
    // 处理事件...
}
```

### 2. 单 Agent 流式执行

**端点**: `POST /api/v1/stream/agent/{agent_name}`

**支持的 Agent**:
- `pm_agent` - 产品经理
- `architect_agent` - 架构师
- `design_agent` - 设计师
- `backend_dev_agent` - 后端开发
- `frontend_dev_agent` - 前端开发
- `qa_agent` - 质量保障

**参数**:
- `message` (string, 必需): 用户需求描述
- `thread_id` (string, 可选): 会话线程ID

**示例**:
```bash
curl -N -X POST "http://localhost:8000/api/v1/stream/agent/pm_agent?message=做一个待办事项应用"
```

## 📊 事件格式

所有事件都采用以下格式：

```json
{
  "type": "事件类型",
  "timestamp": "2024-03-30T10:30:45.123Z",
  "data": {
    // 事件数据
  }
}
```

### 事件类型

#### 1. phase - 阶段事件

```json
{
  "type": "phase",
  "timestamp": "2024-03-30T10:30:45.123Z",
  "data": {
    "agent": "pm_agent",
    "phase": "start",
    "status": "running"
  }
}
```

#### 2. progress - 进度事件

```json
{
  "type": "progress",
  "timestamp": "2024-03-30T10:30:50.123Z",
  "data": {
    "agent": "pm_agent",
    "step": "analyzing_requirements",
    "percent": 50,
    "message": "正在分析用户需求"
  }
}
```

#### 3. artifact - 产出物事件

```json
{
  "type": "artifact",
  "timestamp": "2024-03-30T10:31:00.123Z",
  "data": {
    "agent": "pm_agent",
    "artifact_type": "prd",
    "content": {
      "vision": "打造最便捷的番茄钟应用",
      "target_audience": "需要时间管理的用户",
      "core_features": ["计时器", "休息提醒", "统计分析"]
    }
  }
}
```

#### 4. thinking - 思考过程事件

```json
{
  "type": "thinking",
  "timestamp": "2024-03-30T10:30:55.123Z",
  "data": {
    "agent": "pm_agent",
    "content": "正在分析用户的核心需求..."
  }
}
```

#### 5. review - 审查事件

```json
{
  "type": "review",
  "timestamp": "2024-03-30T10:31:30.123Z",
  "data": {
    "status": "APPROVED",
    "comments": "PRD 完整性良好，核心功能明确"
  }
}
```

#### 6. error - 错误事件

```json
{
  "type": "error",
  "timestamp": "2024-03-30T10:32:00.123Z",
  "data": {
    "error_type": "APITimeoutError",
    "message": "Request timed out",
    "details": "执行失败: thread-123"
  }
}
```

#### 7. done - 完成事件

```json
{
  "type": "done",
  "timestamp": "2024-03-30T10:32:30.123Z",
  "data": {
    "thread_id": "thread-123",
    "duration": 120.5,
    "sender": "reviewer_agent",
    "revision_counts": {
      "pm_agent": 0,
      "architect_agent": 1
    },
    "has_prd": true,
    "has_trd": true,
    "has_design": false,
    "final_status": "completed"
  }
}
```

## 💻 使用示例

### Python 客户端

```python
import asyncio
import json
import httpx

async def stream_pipeline():
    url = "http://localhost:8000/api/v1/stream/run"
    params = {"message": "做一个番茄钟应用"}

    async with httpx.AsyncClient() as client:
        async with client.stream("POST", url, params=params) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    event = json.loads(line[6:])
                    print(f"Event: {event['type']}")
                    print(f"Data: {event['data']}\n")

asyncio.run(stream_pipeline())
```

### JavaScript 客户端

```javascript
async function streamPipeline() {
    const url = '/api/v1/stream/run';
    const params = new URLSearchParams({
        message: '做一个番茄钟应用'
    });

    const response = await fetch(`${url}?${params}`, {
        method: 'POST',
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
            if (line.startsWith('data: ')) {
                const event = JSON.parse(line.slice(6));
                console.log('Event:', event.type, event.data);
            }
        }
    }
}

streamPipeline();
```

### cURL 示例

```bash
# 完整 Pipeline
curl -N -X POST "http://localhost:8000/api/v1/stream/run?message=做一个番茄钟应用"

# 单 Agent
curl -N -X POST "http://localhost:8000/api/v1/stream/agent/pm_agent?message=做一个待办事项应用"

# 带 ThreadID
curl -N -X POST "http://localhost:8000/api/v1/stream/run?message=做一个笔记应用&thread_id=my-thread-123"
```

## 🎨 前端集成

### HTML + JavaScript

参考 `examples/stream_client.html` 获取完整的前端示例。

关键代码：

```javascript
// 创建 EventSource (SSE)
const eventSource = new EventSource('/api/v1/stream/run?message=...');

eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    // 处理事件
    console.log(data);
};

// 或使用 Fetch API
fetch('/api/v1/stream/run?message=...', { method: 'POST' })
    .then(response => {
        const reader = response.body.getReader();
        // 处理流式数据
    });
```

### React 示例

```javascript
import { useState, useEffect } from 'react';

function StreamingAgent() {
    const [events, setEvents] = useState([]);
    const [isRunning, setIsRunning] = useState(false);

    const runPipeline = async (message) => {
        setIsRunning(true);
        const response = await fetch(`/api/v1/stream/run?message=${message}`);
        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        while (true) {
            const { done, value } = await reader.read();
            if (done) {
                setIsRunning(false);
                break;
            }

            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const event = JSON.parse(line.slice(6));
                    setEvents(prev => [...prev, event]);
                }
            }
        }
    };

    return (
        <div>
            <button onClick={() => runPipeline('做一个应用')}>
                {isRunning ? '运行中...' : '开始执行'}
            </button>
            <ul>
                {events.map((event, i) => (
                    <li key={i}>
                        {event.type}: {JSON.stringify(event.data)}
                    </li>
                ))}
            </ul>
        </div>
    );
}
```

## 🔧 配置选项

### 服务器端配置

在 `.env` 文件中：

```ini
# 启用流式输出
STREAM_ENABLED=true

# 超时设置
LLM_TIMEOUT=300  # 5分钟

# 节点延迟
NODE_DELAY=5
```

### 客户端配置

建议的客户端设置：

```javascript
const options = {
    timeout: 300000,  // 5分钟超时
    headers: {
        'Accept': 'text/event-stream',
        'Cache-Control': 'no-cache'
    }
};
```

## 📈 性能考虑

1. **连接管理**: 使用合适的超时设置
2. **重连机制**: 实现自动重连逻辑
3. **事件过滤**: 客户端可以根据需要过滤事件
4. **缓冲控制**: 服务器端已禁用 Nginx 缓冲

## 🛠️ 故障排除

### 连接中断

**问题**: 连接在执行过程中断开

**解决方案**:
1. 增加客户端超时时间
2. 检查网络连接
3. 实现重连机制

### 事件丢失

**问题**: 部分事件没有接收到

**解决方案**:
1. 检查服务器日志
2. 确认事件格式正确
3. 实现事件确认机制

### 性能问题

**问题**: 事件推送延迟

**解决方案**:
1. 减少事件频率
2. 使用事件批处理
3. 优化网络配置

---

**最后更新**: 2026-03-30
**相关文档**:
- [API 文档](API_REFERENCE.md)
- [测试指南](TESTING_GUIDE.md)

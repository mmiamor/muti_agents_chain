# 工作流 API 和监控指南

## 概述

Omni Agent Graph 提供完整的工作流管理 API 和监控系统，支持动态创建和执行工作流，并实时监控系统性能。

## 🚀 工作流 API

### 基础信息

**Base URL**: `http://localhost:8000`
**API 前缀**: `/api/v1/workflows`

### API 端点

#### 1. 列出所有工作流

```http
GET /api/v1/workflows
```

**响应示例**:
```json
["full_pipeline", "rapid_prototype", "design_only", "backend_only", "frontend_only"]
```

#### 2. 获取工作流详情

```http
GET /api/v1/workflows/{workflow_name}
```

**示例**:
```bash
curl http://localhost:8000/api/v1/workflows/rapid_prototype
```

**响应**:
```json
{
  "name": "rapid_prototype",
  "description": "快速原型开发（无审查）",
  "version": "1.0.0",
  "stage_count": 2,
  "agents": ["pm_agent", "architect_agent", "backend_dev_agent", "frontend_dev_agent"],
  "execution_modes": ["sequential", "parallel"]
}
```

#### 3. 创建自定义工作流

```http
POST /api/v1/workflows
```

**请求体**:
```json
{
  "name": "my_workflow",
  "description": "我的自定义工作流",
  "agents": ["pm_agent", "backend_dev_agent"],
  "parallel": false,
  "skip_review": false,
  "save_as_file": true
}
```

**示例**:
```bash
curl -X POST http://localhost:8000/api/v1/workflows \
  -H "Content-Type: application/json" \
  -d '{
    "name": "backend_workflow",
    "agents": ["pm_agent", "architect_agent", "backend_dev_agent"],
    "parallel": false
  }'
```

#### 4. 执行工作流

```http
POST /api/v1/workflows/{workflow_name}/execute
```

**请求体**:
```json
{
  "message": "创建一个笔记应用",
  "stop_at_stage": null,
  "parameters": {}
}
```

**示例**:
```bash
curl -X POST http://localhost:8000/api/v1/workflows/rapid_prototype/execute \
  -H "Content-Type: application/json" \
  -d '{
    "message": "创建一个简单的 TODO 应用"
  }'
```

**响应**:
```json
{
  "workflow_name": "rapid_prototype",
  "execution_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "current_stage": null,
  "completed_stages": 0,
  "total_stages": 2,
  "started_at": "2026-03-31T10:00:00",
  "completed_at": null,
  "error": null
}
```

#### 5. 查询执行状态

```http
GET /api/v1/workflows/{workflow_name}/status/{execution_id}
```

**示例**:
```bash
curl http://localhost:8000/api/v1/workflows/rapid_prototype/status/550e8400-e29b-41d4-a716-446655440000
```

**响应**:
```json
{
  "workflow_name": "rapid_prototype",
  "execution_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "current_stage": "quick_dev",
  "completed_stages": 2,
  "total_stages": 2,
  "started_at": "2026-03-31T10:00:00",
  "completed_at": "2026-03-31T10:05:30",
  "error": null
}
```

#### 6. 删除工作流

```http
DELETE /api/v1/workflows/{workflow_name}
```

**注意**: 只能删除自定义工作流，不能删除预定义模板。

## 📊 监控 API

### 基础信息

**Base URL**: `http://localhost:8000`
**API 前缀**: `/api/v1/monitoring`

### API 端点

#### 1. 获取监控摘要

```http
GET /api/v1/monitoring/summary
```

**响应**:
```json
{
  "total_metrics": 1234,
  "total_errors": 5,
  "active_traces": 2,
  "total_alerts": 3,
  "aggregates": {
    "execution_time": {
      "count": 100,
      "sum": 50000,
      "avg": 500,
      "min": 100,
      "max": 2000
    }
  }
}
```

#### 2. 获取性能指标

```http
GET /api/v1/monitoring/metrics?workflow_name={name}&execution_id={id}&limit={limit}
```

**查询参数**:
- `workflow_name` (可选): 工作流名称过滤
- `execution_id` (可选): 执行 ID 过滤
- `limit` (可选): 限制数量，默认 100

**示例**:
```bash
curl "http://localhost:8000/api/v1/monitoring/metrics?workflow_name=rapid_prototype&limit=50"
```

**响应**:
```json
[
  {
    "id": "metric-id",
    "timestamp": "2026-03-31T10:00:00",
    "workflow_name": "rapid_prototype",
    "execution_id": "exec-id",
    "stage_name": "quick_design",
    "agent_name": "pm_agent",
    "metric_name": "execution_time",
    "value": 1234.56,
    "unit": "ms",
    "labels": {}
  }
]
```

#### 3. 获取错误记录

```http
GET /api/v1/monitoring/errors?workflow_name={name}&severity={severity}&limit={limit}
```

**查询参数**:
- `workflow_name` (可选): 工作流名称过滤
- `severity` (可选): 严重程度 (error, warning, critical)
- `limit` (可选): 限制数量，默认 100

**示例**:
```bash
curl "http://localhost:8000/api/v1/monitoring/errors?severity=critical"
```

#### 4. 获取执行追踪

```http
GET /api/v1/monitoring/traces/{execution_id}
```

**响应**:
```json
{
  "id": "trace-id",
  "execution_id": "exec-id",
  "workflow_name": "rapid_prototype",
  "started_at": "2026-03-31T10:00:00",
  "completed_at": "2026-03-31T10:05:30",
  "status": "completed",
  "total_duration": 330.5,
  "stages_completed": 2,
  "total_stages": 2,
  "input_summary": "创建一个 TODO 应用",
  "output_summary": "已完成开发"
}
```

#### 5. 获取告警

```http
GET /api/v1/monitoring/alerts?severity={severity}&resolved={bool}&limit={limit}
```

**查询参数**:
- `severity` (可选): 严重程度 (info, warning, critical)
- `resolved` (可选): 是否已解决
- `limit` (可选): 限制数量，默认 100

**示例**:
```bash
curl "http://localhost:8000/api/v1/monitoring/alerts?resolved=false"
```

#### 6. 创建告警规则

```http
POST /api/v1/monitoring/alerts/rules
```

**请求体**:
```json
{
  "name": "执行时间过长告警",
  "metric_name": "execution_time",
  "condition": "gt",
  "threshold": 5000,
  "severity": "warning",
  "description": "当 Agent 执行时间超过 5 秒时触发"
}
```

**条件操作符**:
- `gt` - 大于
- `lt` - 小于
- `eq` - 等于
- `ne` - 不等于

**示例**:
```bash
curl -X POST http://localhost:8000/api/v1/monitoring/alerts/rules \
  -H "Content-Type: application/json" \
  -d '{
    "name": "超时告警",
    "metric_name": "execution_time",
    "condition": "gt",
    "threshold": 10000,
    "severity": "critical"
  }'
```

#### 7. 获取仪表板数据

```http
GET /api/v1/monitoring/dashboard
```

**响应**:
```json
{
  "summary": {
    "total_metrics": 1234,
    "total_errors": 5,
    "active_traces": 2,
    "total_alerts": 3
  },
  "recent_metrics": [...],
  "recent_errors": [...],
  "active_alerts": [...],
  "execution_stats": {
    "total_executions": 50,
    "completed": 45,
    "failed": 3,
    "running": 2,
    "success_rate": 0.9,
    "avg_duration_seconds": 120.5
  }
}
```

## 🎛️ 监控仪表板

### 访问仪表板

```
http://localhost:8000/monitoring
```

### 功能

1. **实时监控**
   - 自动刷新每 10 秒
   - 显示系统状态摘要
   - 执行统计信息

2. **统计卡片**
   - 总指标数
   - 总错误数
   - 活跃追踪数
   - 活跃告警数

3. **执行统计**
   - 总执行数
   - 成功/失败/运行中
   - 成功率
   - 平均执行时间

4. **活跃告警**
   - 按严重程度分类显示
   - 实时更新
   - 告警详情

5. **最近错误**
   - 时间戳
   - 错误类型
   - 错误消息
   - Agent 信息

6. **最近指标**
   - 执行时间
   - Token 使用
   - 其他性能指标

## 🔧 使用示例

### Python 示例

```python
import httpx
import asyncio

async def execute_workflow_and_monitor():
    """执行工作流并监控"""

    async with httpx.AsyncClient() as client:
        # 1. 执行工作流
        response = await client.post(
            "http://localhost:8000/api/v1/workflows/rapid_prototype/execute",
            json={"message": "创建一个 TODO 应用"}
        )
        execution = response.json()
        execution_id = execution["execution_id"]

        print(f"工作流开始执行: {execution_id}")

        # 2. 轮询状态
        while True:
            response = await client.get(
                f"http://localhost:8000/api/v1/workflows/rapid_prototype/status/{execution_id}"
            )
            status = response.json()

            print(f"状态: {status['status']}, 阶段: {status['completed_stages']}/{status['total_stages']}")

            if status["status"] in ["completed", "failed"]:
                break

            await asyncio.sleep(5)

        # 3. 查看监控数据
        response = await client.get("http://localhost:8000/api/v1/monitoring/summary")
        summary = response.json()

        print(f"监控摘要: {summary}")

asyncio.run(execute_workflow_and_monitor())
```

### cURL 示例

```bash
# 执行工作流
EXECUTION=$(curl -X POST http://localhost:8000/api/v1/workflows/rapid_prototype/execute \
  -H "Content-Type: application/json" \
  -d '{"message": "创建一个 TODO 应用"}' \
  | jq -r '.execution_id')

echo "执行 ID: $EXECUTION"

# 检查状态
curl http://localhost:8000/api/v1/workflows/rapid_prototype/status/$EXECUTION | jq

# 查看监控摘要
curl http://localhost:8000/api/v1/monitoring/summary | jq
```

## 📈 监控最佳实践

### 1. 关键指标

- **执行时间** - Agent 执行耗时
- **Token 使用** - LLM Token 消耗
- **成功率** - 工作流完成率
- **错误率** - 错误发生频率

### 2. 告警配置

推荐配置的告警规则：

```json
{
  "执行时间过长": {
    "metric_name": "execution_time",
    "condition": "gt",
    "threshold": 10000,
    "severity": "warning"
  },
  "高错误率": {
    "metric_name": "error_count",
    "condition": "gt",
    "threshold": 5,
    "severity": "critical"
  },
  "低成功率": {
    "metric_name": "success_rate",
    "condition": "lt",
    "threshold": 0.8,
    "severity": "warning"
  }
}
```

### 3. 监控仪表板

- 定期查看仪表板
- 关注活跃告警
- 分析执行统计
- 检查错误记录

### 4. 性能优化

- 分析执行时间指标
- 识别性能瓶颈
- 优化 Agent 配置
- 调整工作流流程

## 🔍 故障排除

### 问题: 工作流执行失败

**检查步骤**:
1. 查看执行状态 API
2. 检查错误记录 API
3. 查看执行追踪
4. 检查 Agent 日志

### 问题: 告警未触发

**检查步骤**:
1. 验证告警规则配置
2. 检查指标是否正常记录
3. 验证阈值设置
4. 检查条件操作符

### 问题: 仪表板数据不更新

**检查步骤**:
1. 刷新浏览器页面
2. 检查 API 是否正常运行
3. 查看浏览器控制台错误
4. 重启服务器

## 📚 相关资源

- [API 文档](http://localhost:8000/docs) - Swagger UI
- [工作流配置指南](CUSTOM_WORKFLOW.md) - 工作流配置
- [使用示例](../examples/workflow_api_example.py) - 代码示例

---

**更新**: 2026-03-31
**版本**: 1.0.0

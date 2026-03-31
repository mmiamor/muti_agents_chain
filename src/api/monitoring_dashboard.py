"""
监控仪表板 - 提供实时监控数据可视化
"""
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/monitoring", tags=["monitoring-dashboard"])


@router.get("/", response_class=HTMLResponse)
async def monitoring_dashboard():
    """监控仪表板页面"""
    return """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Multi-Agent Chain - 监控仪表板</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .dashboard {
            max-width: 1400px;
            margin: 0 auto;
        }

        .header {
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }

        .header h1 {
            color: #667eea;
            font-size: 28px;
            margin-bottom: 10px;
        }

        .header p {
            color: #666;
            font-size: 14px;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }

        .stat-card {
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            transition: transform 0.2s;
        }

        .stat-card:hover {
            transform: translateY(-5px);
        }

        .stat-card h3 {
            color: #666;
            font-size: 14px;
            margin-bottom: 10px;
            text-transform: uppercase;
        }

        .stat-card .value {
            font-size: 36px;
            font-weight: bold;
            color: #667eea;
        }

        .stat-card .label {
            font-size: 12px;
            color: #999;
            margin-top: 5px;
        }

        .section {
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }

        .section h2 {
            color: #667eea;
            font-size: 20px;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #f0f0f0;
        }

        .alert-item {
            padding: 12px;
            border-radius: 6px;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .alert-item.critical {
            background: #fee;
            border-left: 4px solid #e74c3c;
        }

        .alert-item.warning {
            background: #fef9e7;
            border-left: 4px solid #f39c12;
        }

        .alert-item.info {
            background: #e8f4f8;
            border-left: 4px solid #3498db;
        }

        .alert-icon {
            font-size: 20px;
        }

        .alert-content {
            flex: 1;
        }

        .alert-content .title {
            font-weight: 600;
            margin-bottom: 4px;
        }

        .alert-content .message {
            font-size: 14px;
            color: #666;
        }

        .error-item {
            padding: 12px;
            border-radius: 6px;
            margin-bottom: 10px;
            background: #f8f9fa;
            border-left: 4px solid #e74c3c;
        }

        .error-item .error-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }

        .error-item .error-type {
            font-weight: 600;
            color: #e74c3c;
        }

        .error-item .error-time {
            font-size: 12px;
            color: #999;
        }

        .error-item .error-message {
            font-size: 14px;
            color: #666;
        }

        .metric-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px;
            border-bottom: 1px solid #f0f0f0;
        }

        .metric-item:last-child {
            border-bottom: none;
        }

        .metric-name {
            font-size: 14px;
            color: #666;
        }

        .metric-value {
            font-weight: 600;
            color: #667eea;
        }

        .loading {
            text-align: center;
            padding: 40px;
            color: #999;
        }

        .loading::after {
            content: "...";
            animation: dots 1.5s steps(4, end) infinite;
        }

        @keyframes dots {
            0%, 20% { content: "."; }
            40% { content: ".."; }
            60%, 100% { content: "..."; }
        }

        .refresh-button {
            background: #667eea;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            transition: background 0.2s;
        }

        .refresh-button:hover {
            background: #5568d3;
        }

        .badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
        }

        .badge.success { background: #d4edda; color: #155724; }
        .badge.warning { background: #fff3cd; color: #856404; }
        .badge.error { background: #f8d7da; color: #721c24; }
        .badge.info { background: #d1ecf1; color: #0c5460; }
    </style>
</head>
<body>
    <div class="dashboard">
        <div class="header">
            <h1>🚀 Multi-Agent Chain 监控仪表板</h1>
            <p>实时监控系统性能、工作流执行和告警信息</p>
            <button class="refresh-button" onclick="loadDashboard()">🔄 刷新数据</button>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <h3>总指标数</h3>
                <div class="value" id="totalMetrics">-</div>
                <div class="label">性能指标记录</div>
            </div>
            <div class="stat-card">
                <h3>总错误数</h3>
                <div class="value" id="totalErrors" style="color: #e74c3c;">-</div>
                <div class="label">错误记录</div>
            </div>
            <div class="stat-card">
                <h3>活跃追踪</h3>
                <div class="value" id="activeTraces" style="color: #27ae60;">-</div>
                <div class="label">正在执行的工作流</div>
            </div>
            <div class="stat-card">
                <h3>活跃告警</h3>
                <div class="value" id="activeAlerts" style="color: #f39c12;">-</div>
                <div class="label">未解决的告警</div>
            </div>
        </div>

        <div class="section">
            <h2>📊 执行统计</h2>
            <div id="executionStats" class="loading">加载中</div>
        </div>

        <div class="section">
            <h2>🚨 活跃告警</h2>
            <div id="alertsContainer" class="loading">加载中</div>
        </div>

        <div class="section">
            <h2>❌ 最近错误</h2>
            <div id="errorsContainer" class="loading">加载中</div>
        </div>

        <div class="section">
            <h2>📈 最近指标</h2>
            <div id="metricsContainer" class="loading">加载中</div>
        </div>
    </div>

    <script>
        const API_BASE = '/api/v1/monitoring';

        async function loadDashboard() {
            try {
                // 加载摘要数据
                const summary = await fetch(`${API_BASE}/summary`).then(r => r.json());
                document.getElementById('totalMetrics').textContent = summary.total_metrics;
                document.getElementById('totalErrors').textContent = summary.total_errors;
                document.getElementById('activeTraces').textContent = summary.active_traces;
                document.getElementById('activeAlerts').textContent = summary.total_alerts;

                // 加载仪表板数据
                const dashboard = await fetch(`${API_BASE}/dashboard`).then(r => r.json());

                // 显示执行统计
                displayExecutionStats(dashboard.execution_stats);

                // 显示告警
                displayAlerts(dashboard.active_alerts);

                // 显示错误
                displayErrors(dashboard.recent_errors);

                // 显示指标
                displayMetrics(dashboard.recent_metrics);

            } catch (error) {
                console.error('加载仪表板数据失败:', error);
            }
        }

        function displayExecutionStats(stats) {
            const container = document.getElementById('executionStats');
            container.innerHTML = `
                <div class="stats-grid" style="grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));">
                    <div class="metric-item">
                        <span class="metric-name">总执行数</span>
                        <span class="metric-value">${stats.total_executions}</span>
                    </div>
                    <div class="metric-item">
                        <span class="metric-name">已完成</span>
                        <span class="metric-value">${stats.completed}</span>
                    </div>
                    <div class="metric-item">
                        <span class="metric-name">失败</span>
                        <span class="metric-value">${stats.failed}</span>
                    </div>
                    <div class="metric-item">
                        <span class="metric-name">成功率</span>
                        <span class="metric-value">${(stats.success_rate * 100).toFixed(1)}%</span>
                    </div>
                    <div class="metric-item">
                        <span class="metric-name">平均耗时</span>
                        <span class="metric-value">${stats.avg_duration_seconds.toFixed(1)}s</span>
                    </div>
                </div>
            `;
        }

        function displayAlerts(alerts) {
            const container = document.getElementById('alertsContainer');

            if (alerts.length === 0) {
                container.innerHTML = '<p style="color: #999; text-align: center; padding: 20px;">✅ 没有活跃告警</p>';
                return;
            }

            container.innerHTML = alerts.map(alert => `
                <div class="alert-item ${alert.severity}">
                    <span class="alert-icon">${alert.severity === 'critical' ? '🔴' : alert.severity === 'warning' ? '⚠️' : 'ℹ️'}</span>
                    <div class="alert-content">
                        <div class="title">${alert.rule_name}</div>
                        <div class="message">${alert.message}</div>
                    </div>
                </div>
            `).join('');
        }

        function displayErrors(errors) {
            const container = document.getElementById('errorsContainer');

            if (errors.length === 0) {
                container.innerHTML = '<p style="color: #999; text-align: center; padding: 20px;">✅ 没有错误记录</p>';
                return;
            }

            container.innerHTML = errors.map(error => `
                <div class="error-item">
                    <div class="error-header">
                        <span class="error-type">${error.error_type}</span>
                        <span class="error-time">${new Date(error.timestamp).toLocaleString()}</span>
                    </div>
                    <div class="error-message">${error.error_message}</div>
                    ${error.agent_name ? `<div style="font-size: 12px; color: #999; margin-top: 4px;">Agent: ${error.agent_name}</div>` : ''}
                </div>
            `).join('');
        }

        function displayMetrics(metrics) {
            const container = document.getElementById('metricsContainer');

            if (metrics.length === 0) {
                container.innerHTML = '<p style="color: #999; text-align: center; padding: 20px;">暂无指标数据</p>';
                return;
            }

            container.innerHTML = metrics.slice(0, 10).map(metric => `
                <div class="metric-item">
                    <span class="metric-name">${metric.metric_name} (${metric.agent_name})</span>
                    <span class="metric-value">${metric.value.toFixed(2)} ${metric.unit}</span>
                </div>
            `).join('');
        }

        // 自动刷新
        loadDashboard();
        setInterval(loadDashboard, 10000); // 每 10 秒刷新一次
    </script>
</body>
</html>
    """

#!/usr/bin/env python3
"""
工作流 API 和监控使用示例

展示如何使用工作流管理 API 和监控系统
"""
import asyncio
import httpx
from datetime import datetime

BASE_URL = "http://localhost:8000"


async def example_1_list_workflows():
    """示例 1: 列出所有工作流"""
    print("=" * 60)
    print("示例 1: 列出所有工作流")
    print("=" * 60)

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/v1/workflows")
        workflows = response.json()

        print(f"\n📋 可用工作流 ({len(workflows)}):")
        for workflow in workflows:
            print(f"   - {workflow}")


async def example_2_get_workflow_details():
    """示例 2: 获取工作流详情"""
    print("\n" + "=" * 60)
    print("示例 2: 获取工作流详情")
    print("=" * 60)

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/v1/workflows/rapid_prototype")
        workflow = response.json()

        print(f"\n📋 工作流详情:")
        print(f"   名称: {workflow['name']}")
        print(f"   描述: {workflow['description']}")
        print(f"   阶段数: {workflow['stage_count']}")
        print(f"   Agents: {', '.join(workflow['agents'])}")
        print(f"   执行模式: {', '.join(workflow['execution_modes'])}")


async def example_3_create_custom_workflow():
    """示例 3: 创建自定义工作流"""
    print("\n" + "=" * 60)
    print("示例 3: 创建自定义工作流")
    print("=" * 60)

    async with httpx.AsyncClient() as client:
        workflow_data = {
            "name": "my_custom_workflow",
            "description": "我的自定义工作流",
            "agents": ["pm_agent", "backend_dev_agent"],
            "parallel": False,
            "skip_review": False,
            "save_as_file": True,
        }

        response = await client.post(
            f"{BASE_URL}/api/v1/workflows",
            json=workflow_data
        )
        workflow = response.json()

        print(f"\n✅ 工作流创建成功:")
        print(f"   名称: {workflow['name']}")
        print(f"   Agents: {', '.join(workflow['agents'])}")
        print(f"   执行模式: {', '.join(workflow['execution_modes'])}")


async def example_4_execute_workflow():
    """示例 4: 执行工作流"""
    print("\n" + "=" * 60)
    print("示例 4: 执行工作流")
    print("=" * 60)

    async with httpx.AsyncClient() as client:
        execute_data = {
            "message": "创建一个简单的笔记应用",
            "parameters": {
                "user_id": "test_user",
            }
        }

        response = await client.post(
            f"{BASE_URL}/api/v1/workflows/rapid_prototype/execute",
            json=execute_data
        )
        status = response.json()

        print(f"\n🚀 工作流开始执行:")
        print(f"   执行 ID: {status['execution_id']}")
        print(f"   状态: {status['status']}")
        print(f"   总阶段数: {status['total_stages']}")

        return status['execution_id']


async def example_5_check_execution_status(execution_id: str):
    """示例 5: 检查执行状态"""
    print("\n" + "=" * 60)
    print("示例 5: 检查执行状态")
    print("=" * 60)

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/api/v1/workflows/rapid_prototype/status/{execution_id}"
        )
        status = response.json()

        print(f"\n📊 执行状态:")
        print(f"   状态: {status['status']}")
        print(f"   当前阶段: {status['current_stage'] or '未开始'}")
        print(f"   已完成: {status['completed_stages']}/{status['total_stages']}")
        if status['error']:
            print(f"   错误: {status['error']}")


async def example_6_monitoring_summary():
    """示例 6: 获取监控摘要"""
    print("\n" + "=" * 60)
    print("示例 6: 获取监控摘要")
    print("=" * 60)

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/v1/monitoring/summary")
        summary = response.json()

        print(f"\n📊 监控摘要:")
        print(f"   总指标数: {summary['total_metrics']}")
        print(f"   总错误数: {summary['total_errors']}")
        print(f"   活跃追踪: {summary['active_traces']}")
        print(f"   总告警数: {summary['total_alerts']}")


async def example_7_get_recent_errors():
    """示例 7: 获取最近的错误"""
    print("\n" + "=" * 60)
    print("示例 7: 获取最近的错误")
    print("=" * 60)

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/api/v1/monitoring/errors",
            params={"limit": 10}
        )
        errors = response.json()

        print(f"\n❌ 最近的错误 ({len(errors)}):")
        if not errors:
            print("   ✅ 没有错误记录")
        else:
            for error in errors[:5]:
                timestamp = datetime.fromisoformat(error['timestamp']).strftime("%H:%M:%S")
                print(f"   [{timestamp}] {error['error_type']}: {error['error_message']}")


async def example_8_get_active_alerts():
    """示例 8: 获取活跃告警"""
    print("\n" + "=" * 60)
    print("示例 8: 获取活跃告警")
    print("=" * 60)

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/api/v1/monitoring/alerts",
            params={"resolved": False, "limit": 10}
        )
        alerts = response.json()

        print(f"\n🚨 活跃告警 ({len(alerts)}):")
        if not alerts:
            print("   ✅ 没有活跃告警")
        else:
            for alert in alerts[:5]:
                timestamp = datetime.fromisoformat(alert['timestamp']).strftime("%H:%M:%S")
                print(f"   [{timestamp}] [{alert['severity'].upper()}] {alert['message']}")


async def example_9_create_alert_rule():
    """示例 9: 创建告警规则"""
    print("\n" + "=" * 60)
    print("示例 9: 创建告警规则")
    print("=" * 60)

    async with httpx.AsyncClient() as client:
        rule_data = {
            "name": "执行时间过长告警",
            "metric_name": "execution_time",
            "condition": "gt",
            "threshold": 5000,
            "severity": "warning",
            "description": "当 Agent 执行时间超过 5 秒时触发",
        }

        response = await client.post(
            f"{BASE_URL}/api/v1/monitoring/alerts/rules",
            json=rule_data
        )
        rule = response.json()

        print(f"\n✅ 告警规则创建成功:")
        print(f"   名称: {rule['name']}")
        print(f"   指标: {rule['metric_name']}")
        print(f"   条件: {rule['condition']} {rule['threshold']}")
        print(f"   严重程度: {rule['severity']}")


async def example_10_get_dashboard_data():
    """示例 10: 获取仪表板数据"""
    print("\n" + "=" * 60)
    print("示例 10: 获取仪表板数据")
    print("=" * 60)

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/v1/monitoring/dashboard")
        dashboard = response.json()

        print(f"\n📊 仪表板数据:")

        # 摘要
        summary = dashboard['summary']
        print(f"   总指标: {summary['total_metrics']}")
        print(f"   总错误: {summary['total_errors']}")

        # 执行统计
        stats = dashboard['execution_stats']
        print(f"   执行统计:")
        print(f"     总执行数: {stats['total_executions']}")
        print(f"     成功: {stats['completed']}")
        print(f"     失败: {stats['failed']}")
        print(f"     成功率: {stats['success_rate']*100:.1f}%")

        # 告警
        print(f"   活跃告警: {len(dashboard['active_alerts'])}")
        print(f"   最近错误: {len(dashboard['recent_errors'])}")


async def main():
    """运行所有示例"""
    print("\n" + "=" * 60)
    print("🎯 工作流 API 和监控使用示例")
    print("=" * 60)

    try:
        # 运行所有示例
        await example_1_list_workflows()
        await example_2_get_workflow_details()
        await example_3_create_custom_workflow()

        # 执行工作流并检查状态
        execution_id = await example_4_execute_workflow()
        await asyncio.sleep(2)  # 等待一下
        await example_5_check_execution_status(execution_id)

        # 监控相关示例
        await example_6_monitoring_summary()
        await example_7_get_recent_errors()
        await example_8_get_active_alerts()
        await example_9_create_alert_rule()
        await example_10_get_dashboard_data()

        print("\n" + "=" * 60)
        print("🎉 所有示例运行完成！")
        print("=" * 60)

        print("\n📚 更多信息:")
        print("  - 工作流 API: /api/v1/workflows")
        print("  - 监控 API: /api/v1/monitoring")
        print("  - 监控仪表板: http://localhost:8000/monitoring")
        print("  - API 文档: http://localhost:8000/docs")

        return True

    except Exception as e:
        print(f"\n❌ 示例运行失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)

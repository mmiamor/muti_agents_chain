#!/usr/bin/env python3
"""
快速启动脚本 - 流式输出演示
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from examples.stream_client import StreamClient, format_event


async def demo_full_pipeline():
    """演示完整 Pipeline 流程"""
    print("="*60)
    print("🚀 Multi-Agent Chain 流式输出演示")
    print("="*60)
    print()

    client = StreamClient()

    # 示例需求
    examples = [
        "做一个简单的番茄钟应用，包含计时器和休息提醒功能",
        "我想做一个待办事项应用，支持任务分类和提醒",
        "做一个天气查询应用，显示未来一周的天气预报",
    ]

    print("请选择示例需求:")
    for i, example in enumerate(examples, 1):
        print(f"{i}. {example}")
    print("0. 自定义输入")

    choice = input("\n请输入选择 (0-3): ").strip()

    if choice == "0":
        message = input("请输入您的需求: ").strip()
    elif choice in ["1", "2", "3"]:
        message = examples[int(choice) - 1]
    else:
        print("无效选择，使用默认示例")
        message = examples[0]

    print(f"\n📝 需求: {message}")
    print("开始执行...\n")

    try:
        event_count = 0
        start_time = asyncio.get_event_loop().time()

        async for event in client.run_full_pipeline(message):
            print(format_event(event))
            event_count += 1

            # 显示详细产出物信息
            if event.get("type") == "artifact":
                data = event.get("data", {})
                artifact_type = data.get("artifact_type")

                if artifact_type == "prd":
                    content = data.get("content", {})
                    print(f"    ✓ 愿景: {content.get('vision', '')}")
                    features = content.get('core_features', [])
                    if features:
                        print(f"    ✓ 功能: {', '.join(features[:3])}")

                elif artifact_type == "trd":
                    content = data.get("content", {})
                    tech_stack = content.get('tech_stack', {})
                    print(f"    ✓ 前端: {tech_stack.get('frontend', '')}")
                    print(f"    ✓ 后端: {tech_stack.get('backend', '')}")

                elif artifact_type == "design_doc":
                    content = data.get("content", {})
                    pages_count = content.get('pages_count', 0)
                    print(f"    ✓ 页面数: {pages_count}")

        end_time = asyncio.get_event_loop().time()
        duration = end_time - start_time

        print(f"\n📊 统计:")
        print(f"  总事件数: {event_count}")
        print(f"  总耗时: {duration:.1f} 秒")
        print(f"\n✅ 演示完成!")

    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断")
    except Exception as e:
        print(f"\n\n❌ 错误: {type(e).__name__}: {str(e)}")


async def demo_single_agent():
    """演示单 Agent 流程"""
    print("="*60)
    print("🤖 单 Agent 流式输出演示")
    print("="*60)
    print()

    agents = [
        ("pm_agent", "产品经理 - 分析需求生成PRD"),
        ("architect_agent", "架构师 - 技术设计生成TRD"),
        ("design_agent", "设计师 - UI/UX设计"),
    ]

    print("可用的 Agent:")
    for i, (name, description) in enumerate(agents, 1):
        print(f"{i}. {name} - {description}")

    choice = input(f"\n请选择 Agent (1-{len(agents)}): ").strip()

    if choice.isdigit() and 1 <= int(choice) <= len(agents):
        agent_name, description = agents[int(choice) - 1]
    else:
        print("无效选择，使用 PM Agent")
        agent_name, description = agents[0]

    message = input("\n请输入需求描述: ").strip()
    if not message:
        message = "我想做一个简单的待办事项应用"

    print(f"\n📝 Agent: {agent_name}")
    print(f"📝 描述: {description}")
    print(f"📝 需求: {message}")
    print("\n开始执行...\n")

    try:
        client = StreamClient()
        event_count = 0

        async for event in client.run_single_agent(agent_name, message):
            print(format_event(event))
            event_count += 1

        print(f"\n📊 总事件数: {event_count}")
        print(f"\n✅ 演示完成!")

    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断")
    except Exception as e:
        print(f"\n\n❌ 错误: {type(e).__name__}: {str(e)}")


def main():
    """主函数"""
    if len(sys.argv) > 1 and sys.argv[1] == "single":
        asyncio.run(demo_single_agent())
    else:
        asyncio.run(demo_full_pipeline())


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 再见!")

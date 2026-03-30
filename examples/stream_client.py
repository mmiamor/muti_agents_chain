"""
流式 API 客户端示例 — 演示如何使用 SSE 流式输出
"""
import asyncio
import json
from typing import AsyncIterator

import httpx


class StreamClient:
    """流式 API 客户端"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url

    async def run_full_pipeline(
        self,
        message: str,
        thread_id: str | None = None,
    ) -> AsyncIterator[dict]:
        """
        执行完整 Pipeline 并接收流式事件

        Args:
            message: 用户消息
            thread_id: 会话线程ID（可选）

        Yields:
            事件字典
        """
        url = f"{self.base_url}/api/v1/stream/run"
        params = {"message": message}
        if thread_id:
            params["thread_id"] = thread_id

        async with httpx.AsyncClient(timeout=300.0) as client:
            async with client.stream("POST", url, params=params) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]  # 移除 "data: " 前缀
                        try:
                            event = json.loads(data)
                            yield event
                        except json.JSONDecodeError:
                            continue

    async def run_single_agent(
        self,
        agent_name: str,
        message: str,
        thread_id: str | None = None,
    ) -> AsyncIterator[dict]:
        """
        执行单个 Agent 并接收流式事件

        Args:
            agent_name: Agent 名称
            message: 用户消息
            thread_id: 会话线程ID（可选）

        Yields:
            事件字典
        """
        url = f"{self.base_url}/api/v1/stream/agent/{agent_name}"
        params = {"message": message}
        if thread_id:
            params["thread_id"] = thread_id

        async with httpx.AsyncClient(timeout=300.0) as client:
            async with client.stream("POST", url, params=params) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        try:
                            event = json.loads(data)
                            yield event
                        except json.JSONDecodeError:
                            continue


def format_event(event: dict) -> str:
    """格式化事件用于显示"""
    event_type = event.get("type", "unknown")
    timestamp = event.get("timestamp", "")[:19]  # 只显示到秒
    data = event.get("data", {})

    if event_type == "phase":
        return f"[{timestamp}] 🔄 阶段: {data.get('agent')} - {data.get('phase')} ({data.get('status')})"

    elif event_type == "progress":
        percent = data.get("percent", 0)
        bar = "█" * (percent // 5) + "░" * (20 - percent // 5)
        return f"[{timestamp}] 📊 进度: {bar} {percent}% - {data.get('step')}"

    elif event_type == "artifact":
        agent = data.get("agent", "unknown")
        artifact_type = data.get("artifact_type", "unknown")
        return f"[{timestamp}] 📦 产出物: {agent} 生成 {artifact_type}"

    elif event_type == "thinking":
        agent = data.get("agent", "unknown")
        content = data.get("content", "")
        return f"[{timestamp}] 💭 {agent}: {content}"

    elif event_type == "review":
        status = data.get("status", "unknown")
        emoji = "✅" if status == "APPROVED" else "❌"
        return f"[{timestamp}] {emoji} 审查: {status}"

    elif event_type == "error":
        error_type = data.get("error_type", "Unknown")
        message = data.get("message", "")
        return f"[{timestamp}] ⚠️ 错误: {error_type} - {message}"

    elif event_type == "done":
        thread_id = data.get("thread_id", "unknown")
        duration = data.get("duration", 0)
        return f"[{timestamp}] ✅ 完成: {thread_id} (耗时: {duration:.1f}s)"

    else:
        return f"[{timestamp}] ❓ 未知事件: {event_type}"


async def main_full_pipeline():
    """完整 Pipeline 示例"""
    print("="*60)
    print("🚀 完整 Pipeline 流式输出示例")
    print("="*60)

    client = StreamClient()

    message = "我想做一个番茄钟应用，包含计时器和休息提醒功能"

    print(f"\n📝 用户需求: {message}\n")
    print("开始执行...\n")

    try:
        event_count = 0
        async for event in client.run_full_pipeline(message):
            print(format_event(event))
            event_count += 1

            # 显示详细产出物信息
            if event.get("type") == "artifact":
                data = event.get("data", {})
                artifact_type = data.get("artifact_type")

                if artifact_type == "prd":
                    content = data.get("content", {})
                    print(f"    愿景: {content.get('vision', '')}")
                    print(f"    功能: {', '.join(content.get('core_features', []))}")

                elif artifact_type == "trd":
                    content = data.get("content", {})
                    tech_stack = content.get('tech_stack', {})
                    print(f"    前端: {tech_stack.get('frontend', '')}")
                    print(f"    后端: {tech_stack.get('backend', '')}")
                    print(f"    数据库: {tech_stack.get('database', '')}")

        print(f"\n📊 总事件数: {event_count}")

    except Exception as e:
        print(f"\n❌ 错误: {type(e).__name__}: {str(e)}")


async def main_single_agent():
    """单 Agent 示例"""
    print("="*60)
    print("🤖 单 Agent 流式输出示例")
    print("="*60)

    client = StreamClient()

    message = "我想做一个简单的待办事项应用"
    agent_name = "pm_agent"

    print(f"\n📝 Agent: {agent_name}")
    print(f"📝 需求: {message}\n")
    print("开始执行...\n")

    try:
        event_count = 0
        async for event in client.run_single_agent(agent_name, message):
            print(format_event(event))
            event_count += 1

        print(f"\n📊 总事件数: {event_count}")

    except Exception as e:
        print(f"\n❌ 错误: {type(e).__name__}: {str(e)}")


async def main_with_thread_id():
    """使用 thread_id 的示例"""
    print("="*60)
    print("🔗 使用 ThreadID 的流式输出示例")
    print("="*60)

    client = StreamClient()

    message = "我想做一个笔记应用"
    thread_id = "my-custom-thread-123"

    print(f"\n📝 Thread ID: {thread_id}")
    print(f"📝 需求: {message}\n")
    print("开始执行...\n")

    try:
        async for event in client.run_full_pipeline(message, thread_id):
            print(format_event(event))

            # 检查是否完成
            if event.get("type") == "done":
                result_thread_id = event.get("data", {}).get("thread_id")
                print(f"\n✅ 确认 Thread ID: {result_thread_id}")
                break

    except Exception as e:
        print(f"\n❌ 错误: {type(e).__name__}: {str(e)}")


if __name__ == "__main__":
    import sys

    # 选择要运行的示例
    if len(sys.argv) > 1:
        example = sys.argv[1]
        if example == "single":
            asyncio.run(main_single_agent())
        elif example == "thread":
            asyncio.run(main_with_thread_id())
        else:
            print(f"未知示例: {example}")
            print("可用示例: full, single, thread")
    else:
        # 默认运行完整流程
        asyncio.run(main_full_pipeline())

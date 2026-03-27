"""E2E 真实 LLM 测试 — PM → Reviewer 闭环"""
import asyncio
import json

from langchain_core.messages import HumanMessage

from src.core.orchestrator import build_graph
from src.models.state import AgentPhase


async def main():
    graph = build_graph()
    config = {"configurable": {"thread_id": "e2e-test-001"}}

    initial_state = {
        "messages": [HumanMessage(content="我想做一个遛狗APP，帮助忙碌的都市养狗人找到靠谱的遛狗服务者")],
        "current_phase": AgentPhase.REQUIREMENT_GATHERING,
        "sender": "user",
    }

    print("=== Starting PM -> Reviewer flow (real LLM) ===\n")
    result = await graph.ainvoke(initial_state, config)
    print("=== Flow Complete ===\n")

    prd = result.get("prd")
    review = result.get("latest_review")
    sender = result.get("sender")
    messages = result.get("messages", [])
    revision_count = result.get("revision_count", 0)

    print(f"Final sender: {sender}")
    print(f"Revision count: {revision_count}")
    print(f"Messages count: {len(messages)}")
    for m in messages:
        role = getattr(m, "type", "unknown")
        content = getattr(m, "content", "")
        print(f"  [{role}] {content[:200]}")

    if prd:
        print(f"\n=== PRD ===")
        print(f"Vision: {prd.vision}")
        print(f"Target audience: {prd.target_audience}")
        print(f"Core features: {prd.core_features}")
        print(f"User stories: {len(prd.user_stories)}")
        print(f"Non-functional: {prd.non_functional}")
        print(f"Mermaid: {prd.mermaid_flowchart[:100]}...")

    if review:
        print(f"\n=== Review ===")
        print(f"Status: {review.status}")
        print(f"Comments: {review.comments}")

    print("\n=== DONE ===")


if __name__ == "__main__":
    asyncio.run(main())

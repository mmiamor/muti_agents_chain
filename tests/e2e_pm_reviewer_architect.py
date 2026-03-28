"""E2E 真实 LLM 测试 — PM → Reviewer → Architect → Reviewer 全流程"""
import asyncio
import json
import time

from langchain_core.messages import HumanMessage

from src.core.orchestrator import build_graph
from src.models.state import AgentPhase


async def main():
    graph = build_graph()
    config = {"configurable": {"thread_id": "e2e-pm-arch-001"}}

    initial_state = {
        "messages": [HumanMessage(content="我想做一个遛狗APP，帮助忙碌的都市养狗人找到靠谱的遛狗服务者")],
        "current_phase": AgentPhase.REQUIREMENT_GATHERING,
        "sender": "user",
    }

    print("=== Starting PM -> Reviewer -> Architect -> Reviewer flow (real LLM) ===\n")
    start = time.perf_counter()
    result = await graph.ainvoke(initial_state, config)
    elapsed = time.perf_counter() - start
    print(f"\n=== Flow Complete ({elapsed:.1f}s) ===\n")

    prd = result.get("prd")
    trd = result.get("trd")
    review = result.get("latest_review")
    sender = result.get("sender")
    messages = result.get("messages", [])
    revision_count = result.get("revision_count", 0)
    arch_revision_count = result.get("architect_revision_count", 0)

    print(f"Final sender: {sender}")
    print(f"PM revision count: {revision_count}")
    print(f"Architect revision count: {arch_revision_count}")
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

    if trd:
        print(f"\n=== TRD ===")
        print(f"Frontend: {trd.tech_stack.frontend}")
        print(f"Backend: {trd.tech_stack.backend}")
        print(f"Database: {trd.tech_stack.database}")
        print(f"Infrastructure: {trd.tech_stack.infrastructure}")
        print(f"Architecture: {trd.architecture_overview[:200]}")
        print(f"API endpoints: {len(trd.api_endpoints)}")
        for api in trd.api_endpoints:
            print(f"  {api.method} {api.path} — {api.description}")
        print(f"ER diagram: {trd.mermaid_er_diagram[:100]}...")

    if review:
        print(f"\n=== Final Review ===")
        print(f"Status: {review.status}")
        print(f"Comments: {review.comments}")

    print("\n=== DONE ===")


if __name__ == "__main__":
    asyncio.run(main())

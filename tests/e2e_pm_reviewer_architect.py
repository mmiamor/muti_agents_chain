"""E2E 真实 LLM 测试 — PM → Reviewer → Architect → Reviewer → Design → Reviewer 全流程"""
import asyncio
import time

from langchain_core.messages import HumanMessage

from src.core.orchestrator import build_graph
from src.models.state import AgentPhase


async def main():
    graph = build_graph()
    config = {"configurable": {"thread_id": "e2e-pm-arch-design-001"}}

    initial_state = {
        "messages": [HumanMessage(content="我想做一个遛狗APP，帮助忙碌的都市养狗人找到靠谱的遛狗服务者")],
        "current_phase": AgentPhase.REQUIREMENT_GATHERING,
        "sender": "user",
    }

    print("=== Starting PM → Reviewer → Architect → Reviewer → Design → Reviewer flow (real LLM) ===\n")
    start = time.perf_counter()
    result = await graph.ainvoke(initial_state, config)
    elapsed = time.perf_counter() - start
    print(f"\n=== Flow Complete ({elapsed:.1f}s) ===\n")

    prd = result.get("prd")
    trd = result.get("trd")
    design = result.get("design_doc")
    review = result.get("latest_review")
    sender = result.get("sender")
    messages = result.get("messages", [])
    revision_counts = result.get("revision_counts") or {}

    print(f"Final sender: {sender}")
    print(f"Revision counts: {revision_counts}")
    print(f"Messages count: {len(messages)}")
    for m in messages:
        role = getattr(m, "type", "unknown")
        content = getattr(m, "content", "")
        print(f"  [{role}] {content[:200]}")

    if prd:
        print(f"\n=== PRD ===")
        print(f"Vision: {prd.vision}")
        print(f"Features: {prd.core_features}")
        print(f"Stories: {len(prd.user_stories)}")

    if trd:
        print(f"\n=== TRD ===")
        print(f"Backend: {trd.tech_stack.backend}")
        print(f"Database: {trd.tech_stack.database}")
        print(f"APIs: {len(trd.api_endpoints)}")
        for api in trd.api_endpoints:
            print(f"  {api.method} {api.path} — {api.description}")

    if design:
        print(f"\n=== DesignDocument ===")
        print(f"Pages: {len(design.page_specs)}")
        for ps in design.page_specs:
            print(f"  {ps.page_name}: {ps.components}")
        print(f"Tokens: primary={design.design_tokens.color_primary}, font={design.design_tokens.font_family}")
        print(f"Components: {design.component_library}")
        print(f"Responsive: {design.responsive_strategy}")
        print(f"User journey: {design.user_journey[:100]}...")

    if review:
        print(f"\n=== Final Review ===")
        print(f"Status: {review.status}")
        print(f"Comments: {review.comments}")

    print("\n=== DONE ===")


if __name__ == "__main__":
    asyncio.run(main())

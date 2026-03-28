"""PM → Architect 全流程集成测试 — 真实 LLM 验证完整流转"""
import asyncio
import json
import time

import pytest

from langchain_core.messages import HumanMessage

from src.core.orchestrator import build_graph
from src.models.state import AgentPhase


async def _run_flow(thread_id: str, user_message: str):
    """执行完整流程，返回结果"""
    graph = build_graph()
    config = {"configurable": {"thread_id": thread_id}}

    result = await graph.ainvoke(
        {
            "messages": [HumanMessage(content=user_message)],
            "current_phase": AgentPhase.REQUIREMENT_GATHERING,
            "sender": "user",
        },
        config,
    )
    return result


@pytest.mark.asyncio
async def test_pm_architect_full_flow():
    """完整流程：PM→Reviewer→Architect→Reviewer，验证全链路"""
    print("=" * 60)
    print("E2E: PM → Reviewer → Architect → Reviewer (real LLM)")
    print("=" * 60)

    start = time.perf_counter()
    result = await _run_flow(
        "integration-arch-001",
        "我想做一个简单的记账APP，帮助用户记录日常收支",
    )
    elapsed = time.perf_counter() - start

    # ── 验证 PRD ──
    prd = result.get("prd")
    assert prd is not None, "PRD 不应为空"
    assert prd.vision, "PRD vision 不应为空"
    assert len(prd.core_features) > 0, "PRD 应有核心功能"
    assert len(prd.user_stories) > 0, "PRD 应有用户故事"
    print(f"\n[OK] PRD: {prd.vision}")
    print(f"   Features: {prd.core_features}")
    print(f"   Stories: {len(prd.user_stories)}")

    # ── 验证 TRD ──
    trd = result.get("trd")
    assert trd is not None, "TRD 不应为空"
    assert trd.tech_stack.backend, "TRD 后端技术栈不应为空"
    assert trd.tech_stack.database, "TRD 数据库选型不应为空"
    print(f"\n[OK] TRD:")
    print(f"   Backend: {trd.tech_stack.backend}")
    print(f"   Database: {trd.tech_stack.database}")
    print(f"   APIs: {len(trd.api_endpoints)}")
    for api in trd.api_endpoints:
        print(f"     {api.method} {api.path}")

    # ── 验证最终审查结果 ──
    review = result.get("latest_review")
    assert review is not None, "应有审查结果"
    print(f"\n[OK] Final Review: {review.status} — {review.comments}")

    # ── 验证 revision counts ──
    pm_rev = result.get("revision_count", 0)
    arch_rev = result.get("architect_revision_count", 0)
    print(f"\n   PM revisions: {pm_rev}")
    print(f"   Architect revisions: {arch_rev}")

    # ── 验证消息链 ──
    messages = result.get("messages", [])
    assert len(messages) >= 3, f"消息链太短: {len(messages)}"
    print(f"   Messages: {len(messages)}")

    print(f"\n[TIMER] Total time: {elapsed:.1f}s")
    print("=" * 60)
    print("[PASS] ALL CHECKS PASSED")


if __name__ == "__main__":
    asyncio.run(test_pm_architect_full_flow())

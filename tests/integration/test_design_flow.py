"""PM → Architect → Design 全流程集成测试 — 真实 LLM 验证完整流转"""
import asyncio
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
@pytest.mark.e2e
async def test_pm_architect_design_full_flow():
    """完整流程：PM→Reviewer→Architect→Reviewer→Design→Reviewer"""
    print("=" * 60)
    print("E2E: PM → Reviewer → Architect → Reviewer → Design → Reviewer")
    print("=" * 60)

    start = time.perf_counter()
    result = await _run_flow(
        "integration-design-001",
        "我想做一个简单的记账APP，帮助用户记录日常收支",
    )
    elapsed = time.perf_counter() - start

    # ── 验证 PRD ──
    prd = result.get("prd")
    assert prd is not None, "PRD 不应为空"
    assert prd.vision, "PRD vision 不应为空"
    assert len(prd.core_features) > 0, "PRD 应有核心功能"
    print(f"\n[OK] PRD: {prd.vision}")

    # ── 验证 TRD ──
    trd = result.get("trd")
    assert trd is not None, "TRD 不应为空"
    assert trd.tech_stack.backend, "TRD 后端不应为空"
    print(f"[OK] TRD: {trd.tech_stack.backend} / {trd.tech_stack.database}")

    # ── 验证 DesignDocument ──
    design = result.get("design_doc")
    assert design is not None, "DesignDocument 不应为空"
    assert len(design.page_specs) > 0, "应有页面规格"
    assert design.design_tokens.color_primary, "应有主色定义"
    print(f"[OK] Design: {len(design.page_specs)} pages, primary={design.design_tokens.color_primary}")
    for ps in design.page_specs:
        print(f"   {ps.page_name}: {ps.components}")

    # ── 验证最终审查结果 ──
    review = result.get("latest_review")
    assert review is not None, "应有审查结果"
    print(f"\n[OK] Final Review: {review.status} — {review.comments}")

    # ── revision_counts ──
    rev_counts = result.get("revision_counts") or {}
    print(f"   Revision counts: {rev_counts}")

    # ── 消息链 ──
    messages = result.get("messages", [])
    assert len(messages) >= 4, f"消息链太短: {len(messages)}"
    print(f"   Messages: {len(messages)}")

    print(f"\n[TIMER] Total time: {elapsed:.1f}s")
    print("=" * 60)
    print("[PASS] ALL CHECKS PASSED")


if __name__ == "__main__":
    asyncio.run(test_pm_architect_design_full_flow())

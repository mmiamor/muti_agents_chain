"""Agent 公共工厂 — LLM 实例创建、revision 计数工具"""
from __future__ import annotations

from src.config import settings
from src.services.llm_service import LLMService


def create_llm() -> LLMService:
    """创建标准 LLM 实例（所有 Agent 共用）"""
    return LLMService(
        api_key=settings.ZAI_API_KEY,
        base_url=settings.OPENAI_BASE_URL,
        default_model=settings.DEFAULT_MODEL,
        max_retries=settings.LLM_RETRY_MAX,
        base_delay=settings.LLM_RETRY_BASE_DELAY,
    )


# ── revision 计数工具 ────────────────────────────

def get_revision_count(state: dict, agent_name: str) -> int:
    """从 state 中读取指定 agent 的 revision 计数"""
    counts = state.get("revision_counts") or {}
    return counts.get(agent_name, 0)


def next_revision_count(state: dict, agent_name: str) -> dict:
    """返回递增后的 revision_counts 更新字典（merge 用）"""
    counts = dict(state.get("revision_counts") or {})
    counts[agent_name] = counts.get(agent_name, 0) + 1
    return {"revision_counts": counts}

"""Agent 公共工厂 — LLM 实例创建、revision 计数工具"""
from __future__ import annotations

from src.config import settings
from src.services.llm_service import LLMService


def create_llm(agent_name: str | None = None) -> LLMService:
    """
    创建 LLM 实例

    Args:
        agent_name: Agent 名称，用于获取专用模型配置。
                   如果为 None，使用默认模型。

    Returns:
        LLMService 实例
    """
    # 获取 Agent 专用模型
    model = settings.DEFAULT_MODEL
    if agent_name:
        model = settings.agent_model_config.get_model_for_agent(agent_name)

    return LLMService(
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.OPENAI_BASE_URL,
        default_model=model,
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

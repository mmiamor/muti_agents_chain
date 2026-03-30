"""
配置模块
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# 加载 .env 文件（override=True 确保 .env 中的值优先于系统环境变量）
_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(_ROOT / ".env", override=True)


class Settings:
    """应用配置 — 敏感值（如 API Key）从系统环境变量读取"""

    # ── App ──
    APP_NAME: str = "LLMChain AI Backend"
    APP_VERSION: str = "0.1.0"
    APP_HOST: str = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT: int = int(os.getenv("APP_PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() in ("1", "true", "yes")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # ── LLM — 智谱 GLM-5 ──
    ZAI_API_KEY: str = os.getenv("ZAI_API_KEY", "")         # 智谱 API Key
    OPENAI_API_KEY: str = os.getenv("ZAI_API_KEY", "")      # 兼容 LLMService 现有字段
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://open.bigmodel.cn/api/coding/paas/v4/")
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "glm-5")

    # ── Memory ──
    MAX_CONTEXT_LENGTH: int = int(os.getenv("MAX_CONTEXT_LENGTH", "20"))
    MEMORY_TTL: int = int(os.getenv("MEMORY_TTL", "3600"))

    # ── Agent ──
    MAX_REVISION_COUNT: int = int(os.getenv("MAX_REVISION_COUNT", "3"))
    RECURSION_LIMIT: int = int(os.getenv("RECURSION_LIMIT", "30"))
    STREAM_ENABLED: bool = os.getenv("STREAM_ENABLED", "true").lower() in ("1", "true", "yes")

    # ── 限流（适配智谱 GLM）──
    LLM_RETRY_MAX: int = int(os.getenv("LLM_RETRY_MAX", "3"))           # 最大重试次数
    LLM_RETRY_BASE_DELAY: float = float(os.getenv("LLM_RETRY_BASE_DELAY", "3"))  # 首次重试等待秒数
    NODE_DELAY: float = float(os.getenv("NODE_DELAY", "2"))              # 节点间冷却秒数

    # ── Storage ──
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/app.db")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")


settings = Settings()

__all__ = ["settings"]

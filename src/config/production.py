"""
生产环境配置
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# 加载生产环境 .env 文件
_ROOT = Path(__file__).resolve().parent.parent.parent
# 先加载基础配置，再加载环境特定配置（后者覆盖前者）
load_dotenv(_ROOT / ".env", override=False)
load_dotenv(_ROOT / ".env.production", override=True)


class Settings:
    """生产环境配置"""

    # ── App ──
    APP_NAME: str = "LLMChain AI Backend"
    APP_VERSION: str = "0.1.0"
    APP_HOST: str = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT: int = int(os.getenv("APP_PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() in ("1", "true", "yes")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "WARNING")

    # ── LLM ──
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL: str = os.getenv(
        "OPENAI_BASE_URL",
        "https://open.bigmodel.cn/api/coding/paas/v4"
    )
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "glm-4")

    # ── Memory ──
    MAX_CONTEXT_LENGTH: int = int(os.getenv("MAX_CONTEXT_LENGTH", "30"))
    MEMORY_TTL: int = int(os.getenv("MEMORY_TTL", "7200"))

    # ── Agent ──
    MAX_REVISION_COUNT: int = int(os.getenv("MAX_REVISION_COUNT", "3"))
    RECURSION_LIMIT: int = int(os.getenv("RECURSION_LIMIT", "50"))
    STREAM_ENABLED: bool = os.getenv("STREAM_ENABLED", "true").lower() in ("1", "true", "yes")

    # ── 限流（生产环境更宽松）──
    LLM_RETRY_MAX: int = int(os.getenv("LLM_RETRY_MAX", "5"))
    LLM_RETRY_BASE_DELAY: float = float(os.getenv("LLM_RETRY_BASE_DELAY", "8"))
    NODE_DELAY: float = float(os.getenv("NODE_DELAY", "3"))
    LLM_TIMEOUT: int = int(os.getenv("LLM_TIMEOUT", "300"))

    # ── Storage ──
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite+aiosqlite:///./data/prod.db"
    )
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/2")

    # ── 生产环境特有 ──
    ENABLE_PERF_MONITORING: bool = True
    ENABLE_DETAILED_LOGGING: bool = False
    ENABLE_API_DOCS: bool = False
    ENABLE_CORS: bool = True
    CORS_ORIGINS: list[str] = os.getenv("CORS_ORIGINS", "").split(",")


__all__ = ["Settings"]

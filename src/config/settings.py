"""
配置模块
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# 加载 .env 文件（可选，优先使用系统环境变量）
_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(_ROOT / ".env", override=False)


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
    ZAI_API_KEY: str = os.environ["ZAI_API_KEY"]          # 必须，不从 .env fallback
    OPENAI_API_KEY: str = os.environ["ZAI_API_KEY"]        # 兼容 LLMService 现有字段
    OPENAI_BASE_URL: str = "https://open.bigmodel.cn/api/paas/v4/"
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "glm-5")

    # ── Memory ──
    MAX_CONTEXT_LENGTH: int = int(os.getenv("MAX_CONTEXT_LENGTH", "20"))
    MEMORY_TTL: int = int(os.getenv("MEMORY_TTL", "3600"))


settings = Settings()

__all__ = ["settings"]

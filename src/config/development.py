"""
开发环境配置
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

from src.config.agent_models import parse_agent_model_config

# 加载开发环境 .env 文件
_ROOT = Path(__file__).resolve().parent.parent.parent
# 先加载基础配置，再加载环境特定配置（后者覆盖前者）
load_dotenv(_ROOT / ".env", override=False)
load_dotenv(_ROOT / ".env.development", override=True)


class Settings:
    """开发环境配置"""

    # ── App ──
    APP_NAME: str = "LLMChain AI Backend"
    APP_VERSION: str = "0.1.0"
    APP_HOST: str = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT: int = int(os.getenv("APP_PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "true").lower() in ("1", "true", "yes")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "DEBUG")

    # ── LLM ──
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL: str = os.getenv(
        "OPENAI_BASE_URL",
        "https://open.bigmodel.cn/api/coding/paas/v4"
    )
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "glm-4")

    # ── Agent 模型配置 ──
    # 每个Agent可以使用不同的模型，如果未配置则使用 DEFAULT_MODEL
    PM_MODEL: str = os.getenv("PM_MODEL", "")  # PM Agent 专用模型
    ARCHITECT_MODEL: str = os.getenv("ARCHITECT_MODEL", "")  # Architect Agent 专用模型
    DESIGN_MODEL: str = os.getenv("DESIGN_MODEL", "")  # Design Agent 专用模型
    BACKEND_DEV_MODEL: str = os.getenv("BACKEND_DEV_MODEL", "")  # Backend Dev Agent 专用模型
    FRONTEND_DEV_MODEL: str = os.getenv("FRONTEND_DEV_MODEL", "")  # Frontend Dev Agent 专用模型
    QA_MODEL: str = os.getenv("QA_MODEL", "")  # QA Agent 专用模型
    REVIEWER_MODEL: str = os.getenv("REVIEWER_MODEL", "")  # Reviewer Agent 专用模型

    # ── Memory ──
    MAX_CONTEXT_LENGTH: int = int(os.getenv("MAX_CONTEXT_LENGTH", "20"))
    MEMORY_TTL: int = int(os.getenv("MEMORY_TTL", "3600"))

    # ── Agent ──
    MAX_REVISION_COUNT: int = int(os.getenv("MAX_REVISION_COUNT", "3"))
    RECURSION_LIMIT: int = int(os.getenv("RECURSION_LIMIT", "30"))
    STREAM_ENABLED: bool = os.getenv("STREAM_ENABLED", "true").lower() in ("1", "true", "yes")

    # ── 限流 ──
    LLM_RETRY_MAX: int = int(os.getenv("LLM_RETRY_MAX", "5"))
    LLM_RETRY_BASE_DELAY: float = float(os.getenv("LLM_RETRY_BASE_DELAY", "5"))
    NODE_DELAY: float = float(os.getenv("NODE_DELAY", "5"))
    LLM_TIMEOUT: int = int(os.getenv("LLM_TIMEOUT", "300"))

    # ── Storage ──
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite+aiosqlite:///./data/dev.db"
    )
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # ── 开发环境特有 ──
    ENABLE_PERF_MONITORING: bool = True
    ENABLE_DETAILED_LOGGING: bool = True
    ENABLE_API_DOCS: bool = True
    ENABLE_CORS: bool = True
    CORS_ORIGINS: list[str] = ["*"]

    # ── Agent 模型配置实例（在初始化时创建）──
    _agent_model_config = None

    @property
    def agent_model_config(self):
        """获取 Agent 模型配置"""
        if self._agent_model_config is None:
            self._agent_model_config = parse_agent_model_config(
                default_model=self.DEFAULT_MODEL,
                pm_model=self.PM_MODEL if self.PM_MODEL else None,
                architect_model=self.ARCHITECT_MODEL if self.ARCHITECT_MODEL else None,
                design_model=self.DESIGN_MODEL if self.DESIGN_MODEL else None,
                backend_dev_model=self.BACKEND_DEV_MODEL if self.BACKEND_DEV_MODEL else None,
                frontend_dev_model=self.FRONTEND_DEV_MODEL if self.FRONTEND_DEV_MODEL else None,
                qa_model=self.QA_MODEL if self.QA_MODEL else None,
                reviewer_model=self.REVIEWER_MODEL if self.REVIEWER_MODEL else None,
            )
        return self._agent_model_config


__all__ = ["Settings"]

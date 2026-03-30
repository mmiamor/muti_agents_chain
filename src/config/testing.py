"""
测试环境配置
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

from src.config.agent_models import parse_agent_model_config

# 加载测试环境 .env 文件
_ROOT = Path(__file__).resolve().parent.parent.parent
# 先加载基础配置，再加载环境特定配置（后者覆盖前者）
load_dotenv(_ROOT / ".env", override=False)
load_dotenv(_ROOT / ".env.testing", override=True)


class Settings:
    """测试环境配置"""

    # ── App ──
    APP_NAME: str = "LLMChain AI Backend"
    APP_VERSION: str = "0.1.0"
    APP_HOST: str = os.getenv("APP_HOST", "127.0.0.1")
    APP_PORT: int = int(os.getenv("APP_PORT", "8001"))
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
    PM_MODEL: str = os.getenv("PM_MODEL", "")
    ARCHITECT_MODEL: str = os.getenv("ARCHITECT_MODEL", "")
    DESIGN_MODEL: str = os.getenv("DESIGN_MODEL", "")
    BACKEND_DEV_MODEL: str = os.getenv("BACKEND_DEV_MODEL", "")
    FRONTEND_DEV_MODEL: str = os.getenv("FRONTEND_DEV_MODEL", "")
    QA_MODEL: str = os.getenv("QA_MODEL", "")
    REVIEWER_MODEL: str = os.getenv("REVIEWER_MODEL", "")

    # ── Memory ──
    MAX_CONTEXT_LENGTH: int = int(os.getenv("MAX_CONTEXT_LENGTH", "10"))
    MEMORY_TTL: int = int(os.getenv("MEMORY_TTL", "1800"))

    # ── Agent ──
    MAX_REVISION_COUNT: int = int(os.getenv("MAX_REVISION_COUNT", "2"))
    RECURSION_LIMIT: int = int(os.getenv("RECURSION_LIMIT", "20"))
    STREAM_ENABLED: bool = os.getenv("STREAM_ENABLED", "false").lower() in ("1", "true", "yes")

    # ── 限流（测试环境更严格）──
    LLM_RETRY_MAX: int = int(os.getenv("LLM_RETRY_MAX", "3"))
    LLM_RETRY_BASE_DELAY: float = float(os.getenv("LLM_RETRY_BASE_DELAY", "3"))
    NODE_DELAY: float = float(os.getenv("NODE_DELAY", "2"))
    LLM_TIMEOUT: int = int(os.getenv("LLM_TIMEOUT", "180"))

    # ── Storage ──
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite+aiosqlite:///./data/test.db"
    )
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/1")

    # ── 测试环境特有 ──
    ENABLE_PERF_MONITORING: bool = True
    ENABLE_DETAILED_LOGGING: bool = True
    ENABLE_API_DOCS: bool = True
    ENABLE_CORS: bool = True
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # 自动清理测试数据
    AUTO_CLEANUP_TEST_DATA: bool = True

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

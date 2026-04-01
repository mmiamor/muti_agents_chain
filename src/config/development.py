"""
开发环境配置
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

from src.config.base import BaseAppSettings

# 加载开发环境 .env 文件
_ROOT = Path(__file__).resolve().parent.parent.parent
# 先加载基础配置，再加载环境特定配置（后者覆盖前者）
load_dotenv(_ROOT / ".env", override=False)
load_dotenv(_ROOT / ".env.development", override=True)


class Settings(BaseAppSettings):
    """
    开发环境配置

    Omni Agent Graph 开发环境特点:
    - DEBUG 模式开启
    - 详细日志
    - API 文档开启
    - CORS 宽松配置
    - 性能监控开启
    """

    model_config = BaseAppSettings.model_config.copy(
        update={
            "env_file": [".env", ".env.development"],
        }
    )

    # 开发环境默认值
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"

    OPENAI_BASE_URL: str = "https://open.bigmodel.cn/api/paas/v4/"
    DEFAULT_MODEL: str = "glm-4"

    DATABASE_URL: str = "sqlite+aiosqlite:///./data/dev.db"
    REDIS_URL: str = "redis://localhost:6379/0"

    # 开发环境特性
    ENABLE_PERF_MONITORING: bool = True
    ENABLE_DETAILED_LOGGING: bool = True
    ENABLE_API_DOCS: bool = True
    ENABLE_CORS: bool = True

    # 开发环境允许所有源（生产环境应该限制）
    CORS_ORIGINS: list[str] = ["*"]


__all__ = ["Settings"]

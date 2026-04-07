"""
配置基类 - 提供类型安全和验证
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, ClassVar

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.config.agent_models import parse_agent_model_config


class BaseAppSettings(BaseSettings):
    """
    应用配置基类

    提供类型安全的配置管理和验证
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ──
    APP_NAME: str = "Omni Agent Graph"
    APP_VERSION: str = "1.0.0"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # ── LLM ──
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://open.bigmodel.cn/api/paas/v4/"
    DEFAULT_MODEL: str = "glm-4"

    # ── Agent 模型配置 ──
    PM_MODEL: str = ""
    ARCHITECT_MODEL: str = ""
    DESIGN_MODEL: str = ""
    BACKEND_DEV_MODEL: str = ""
    FRONTEND_DEV_MODEL: str = ""
    QA_MODEL: str = ""
    REVIEWER_MODEL: str = ""

    # ── Memory ──
    MAX_CONTEXT_LENGTH: int = 20
    MEMORY_TTL: int = 3600

    # ── Agent ──
    MAX_REVISION_COUNT: int = 3
    RECURSION_LIMIT: int = 30
    STREAM_ENABLED: bool = True

    # ── 限流 ──
    LLM_RETRY_MAX: int = 5
    LLM_RETRY_BASE_DELAY: float = 5.0
    NODE_DELAY: float = 5.0
    LLM_TIMEOUT: int = 300

    # ── Storage ──
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/app.db"
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── 特性开关 ──
    ENABLE_PERF_MONITORING: bool = False
    ENABLE_DETAILED_LOGGING: bool = False
    ENABLE_API_DOCS: bool = True
    ENABLE_CORS: bool = True
    ENABLE_RAG_FOR_PM: bool = True  # 为 PM Agent 启用 RAG

    # ── RAG 配置 ──
    RAG_TOP_K: int = 3  # 检索最相关的 K 个结果
    RAG_SCORE_THRESHOLD: float = 0.6  # 相似度阈值
    RAG_VECTOR_STORE_TYPE: str = "memory"  # memory 或 chroma

    # ── CORS 配置 ──
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # ── 内部状态 ──
    _agent_model_config: Any = None

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """验证日志级别"""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}, got {v}")
        return v.upper()

    @field_validator("APP_PORT")
    @classmethod
    def validate_port(cls, v: int) -> int:
        """验证端口号"""
        if not 1 <= v <= 65535:
            raise ValueError(f"APP_PORT must be between 1 and 65535, got {v}")
        return v

    @field_validator("MAX_REVISION_COUNT", "RECURSION_LIMIT")
    @classmethod
    def validate_positive_int(cls, v: int) -> int:
        """验证正整数"""
        if v < 1:
            raise ValueError(f"Value must be positive, got {v}")
        if v > 100:
            raise ValueError(f"Value too large (>100), got {v}")
        return v

    @model_validator(mode="after")
    def validate_api_key(self) -> "BaseAppSettings":
        """验证必需的 API Key"""
        if not self.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required")
        return self

    @property
    def agent_model_config(self):
        """获取 Agent 模型配置（延迟初始化）"""
        if self._agent_model_config is None:
            self._agent_model_config = parse_agent_model_config(
                default_model=self.DEFAULT_MODEL,
                pm_model=self.PM_MODEL or None,
                architect_model=self.ARCHITECT_MODEL or None,
                design_model=self.DESIGN_MODEL or None,
                backend_dev_model=self.BACKEND_DEV_MODEL or None,
                frontend_dev_model=self.FRONTEND_DEV_MODEL or None,
                qa_model=self.QA_MODEL or None,
                reviewer_model=self.REVIEWER_MODEL or None,
            )
        return self._agent_model_config

    def get_model_for_agent(self, agent_name: str) -> str:
        """
        获取指定 Agent 的模型配置

        Args:
            agent_name: Agent 名称（如 "pm_agent", "architect_agent"）

        Returns:
            str: 模型名称
        """
        return self.agent_model_config.get_model_for_agent(agent_name)

    def get_all_models(self) -> dict[str, str]:
        """
        获取所有 Agent 的模型配置

        Returns:
            dict[str, str]: Agent 名称到模型名称的映射
        """
        return self.agent_model_config.get_all_models()


__all__ = ["BaseAppSettings"]

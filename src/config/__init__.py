"""
环境配置管理
"""
from __future__ import annotations

import os
from pathlib import Path
from dataclasses import dataclass, field
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()


@dataclass
class Settings:
    """应用配置"""
    # App
    APP_HOST: str = field(default_factory=lambda: os.getenv("APP_HOST", "0.0.0.0"))
    APP_PORT: int = field(default_factory=lambda: int(os.getenv("APP_PORT", "8000")))
    DEBUG: bool = field(default_factory=lambda: os.getenv("DEBUG", "true").lower() == "true")
    LOG_LEVEL: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))

    # LLM
    OPENAI_API_KEY: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    OPENAI_BASE_URL: str = field(default_factory=lambda: os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"))
    DEFAULT_MODEL: str = field(default_factory=lambda: os.getenv("DEFAULT_MODEL", "gpt-4o"))

    # Redis
    REDIS_URL: str = field(default_factory=lambda: os.getenv("REDIS_URL", "redis://localhost:6379/0"))

    # Database
    DATABASE_URL: str = field(default_factory=lambda: os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/app.db"))

    # Paths
    BASE_DIR: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent.parent)
    DATA_DIR: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent.parent / "data")
    LOG_DIR: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent.parent / "logs")

    def __post_init__(self):
        """确保目录存在"""
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.LOG_DIR.mkdir(parents=True, exist_ok=True)


# 全局配置单例
settings = Settings()

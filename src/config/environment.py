"""
多环境配置管理 - 支持 development, testing, production 环境
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv

from src.utils.logger import setup_logger

logger = setup_logger("config")


# 环境类型
Environment = Literal["development", "testing", "production"]

# 当前环境（默认为development，后续可自动检测）
_current_env: Environment = "development"

# 项目根目录
_ROOT = Path(__file__).resolve().parent.parent.parent


def get_environment() -> Environment:
    """获取当前环境"""
    global _current_env
    # 每次都重新检测环境变量是否变化
    env_var = os.getenv("ENVIRONMENT")
    if env_var and env_var.lower() in ["development", "testing", "production"]:
        _current_env = env_var.lower()
    return _current_env


def set_environment(env: Environment):
    """设置当前环境"""
    global _current_env
    _current_env = env
    logger.info(f"Environment set to: {env}")


def detect_environment() -> Environment:
    """
    自动检测当前环境

    优先级:
    1. ENVIRONMENT 环境变量
    2. DEBUG 环境变量（DEBUG=true → development）
    3. git branch 检测
    4. 默认 development
    """
    # 1. 检查环境变量
    env_var = os.getenv("ENVIRONMENT")
    if env_var:
        if env_var.lower() in ["development", "testing", "production"]:
            return env_var.lower()

    # 2. 检查 DEBUG 环境变量作为提示
    debug_var = os.getenv("DEBUG", "").lower()
    if debug_var in ["1", "true", "yes"]:
        # DEBUG 模式通常是开发或测试环境
        # 进一步检查 git 分支来区分
        pass

    # 3. 检查git分支（如果适用）
    try:
        import subprocess
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
            cwd=_ROOT,
            timeout=1
        )
        if result.returncode == 0:
            branch = result.stdout.strip().split('/')[-1]
            # 只有明确的 production 分支才使用生产环境
            if branch in ["prod", "production", "release"]:
                return "production"
            elif branch in ["test", "testing", "staging"]:
                return "testing"
            # 其他分支（包括 main）默认为开发环境
            elif branch in ["develop", "dev", "development"]:
                return "development"
    except Exception:
        pass

    # 4. 默认开发环境
    return "development"


def load_env_file(env: Environment | None = None) -> None:
    """
    加载对应环境的 .env 文件

    Args:
        env: 目标环境，如果为None则使用当前环境
    """
    if env is None:
        env = get_environment()

    env_files = {
        "development": ".env.development",
        "testing": ".env.testing",
        "production": ".env.production",
    }

    # 优先加载基础配置
    base_env = _ROOT / ".env"
    if base_env.exists():
        load_dotenv(base_env, override=True)
        logger.debug(f"Loaded base .env file")

    # 加载环境特定配置
    env_file = _ROOT / env_files[env]
    if env_file.exists():
        load_dotenv(env_file, override=True)
        logger.info(f"Loaded environment config: {env_file}")
    else:
        logger.warning(f"Environment file not found: {env_file}, using base config")


def get_settings():
    """
    根据当前环境获取配置

    这应该是获取配置的唯一入口点
    """
    env = get_environment()

    # 先加载环境配置
    load_env_file(env)

    # 根据环境导入不同的配置
    if env == "production":
        from src.config.production import Settings
    elif env == "testing":
        from src.config.testing import Settings
    else:  # development
        from src.config.development import Settings

    return Settings()


# 全局配置实例（延迟加载）
from typing import Optional
_settings: Optional[object] = None
from typing import Any


def settings() -> object:
    """
    获取配置实例（单例模式）

    Returns:
        Settings实例，根据当前环境加载不同配置
    """
    global _settings

    if _settings is None:
        _settings = get_settings()

    return _settings


# 便捷函数
def is_development() -> bool:
    """是否为开发环境"""
    return get_environment() == "development"


def is_testing() -> bool:
    """是否为测试环境"""
    return get_environment() == "testing"


def is_production() -> bool:
    """是否为生产环境"""
    return get_environment() == "production"


def reload_settings():
    """重新加载配置（用于热重载）"""
    global _settings
    _settings = None
    return settings()


__all__ = [
    "Environment",
    "get_environment",
    "set_environment",
    "detect_environment",
    "load_env_file",
    "get_settings",
    "settings",
    "is_development",
    "is_testing",
    "is_production",
    "reload_settings",
]
"""
配置模块 - 多环境配置管理
"""
from __future__ import annotations

# 首先导入环境管理
from src.config.environment import get_environment, detect_environment

# 自动检测环境
_detected_env = detect_environment()

# 根据环境导入对应配置
if _detected_env == "production":
    from src.config.production import Settings
elif _detected_env == "testing":
    from src.config.testing import Settings
else:  # development
    from src.config.development import Settings

# 创建配置实例
settings = Settings()

# 导出环境相关函数和类
__all__ = [
    "settings",
    "Settings",
    "get_environment",
]


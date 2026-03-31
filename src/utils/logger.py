"""
日志配置 - 支持结构化日志和多种输出格式
"""
from __future__ import annotations

import json
import logging
import sys
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


class LogFormat(str, Enum):
    """日志格式类型"""
    TEXT = "text"  # 纯文本格式
    JSON = "json"  # JSON 结构化格式


class StructuredFormatter(logging.Formatter):
    """
    结构化日志格式化器

    输出 JSON 格式的日志，便于日志聚合和分析
    """

    def __init__(self, service_name: str = "llmchain"):
        super().__init__()
        self.service_name = service_name

    def format(self, record: logging.LogRecord) -> str:
        """
        格式化日志记录为 JSON

        Args:
            record: 日志记录

        Returns:
            str: JSON 格式的日志字符串
        """
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "service": self.service_name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # 添加异常信息
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # 添加额外字段
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)

        return json.dumps(log_data, ensure_ascii=False)


class TextFormatter(logging.Formatter):
    """
    文本日志格式化器

    彩色输出（支持终端）和易读的文本格式
    """

    # ANSI 颜色代码
    COLORS = {
        'DEBUG': '\033[36m',      # 青色
        'INFO': '\033[32m',       # 绿色
        'WARNING': '\033[33m',    # 黄色
        'ERROR': '\033[31m',      # 红色
        'CRITICAL': '\033[35m',   # 紫色
    }
    RESET = '\033[0m'

    def __init__(self, use_colors: bool = True):
        super().__init__()
        self.use_colors = use_colors and sys.stderr.isatty()

    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录为文本"""
        levelname = record.levelname

        if self.use_colors:
            color = self.COLORS.get(levelname, '')
            levelname = f"{color}{levelname}{self.RESET}"

        message = record.getMessage()

        # 构建格式化字符串
        formatted = (
            f"{datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')} "
            f"| {levelname:8s} "
            f"| {record.name:20s} "
            f"| {record.module}:{record.funcName}:{record.lineno} "
            f"| {message}"
        )

        # 添加异常信息
        if record.exc_info:
            formatted += f"\n{self.formatException(record.exc_info)}"

        return formatted


def setup_logger(
    name: str = "llmchain",
    level: str = "INFO",
    log_format: LogFormat = LogFormat.TEXT,
    log_file: Path | None = None,
) -> logging.Logger:
    """
    创建并配置 logger

    Args:
        name: Logger 名称
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: 日志格式（text 或 json）
        log_file: 日志文件路径（可选）

    Returns:
        logging.Logger: 配置好的 logger 实例
    """
    logger = logging.getLogger(name)

    # 避免重复添加 handler
    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # 选择格式化器
    if log_format == LogFormat.JSON:
        formatter = StructuredFormatter()
    else:
        formatter = TextFormatter()

    # 控制台输出
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    logger.addHandler(console)

    # 文件输出（如果指定）
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def log_with_extra(
    logger: logging.Logger,
    level: str,
    message: str,
    **extra_fields: Any,
) -> None:
    """
    记录带有额外字段的日志

    Args:
        logger: Logger 实例
        level: 日志级别
        message: 日志消息
        **extra_fields: 额外的结构化字段
    """
    log_method = getattr(logger, level.lower(), logger.info)

    # 创建带有额外字段的日志记录
    old_factory = logging.getLogRecordFactory()

    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        record.extra_fields = extra_fields
        return record

    logging.setLogRecordFactory(record_factory)

    try:
        log_method(message)
    finally:
        logging.setLogRecordFactory(old_factory)


class LoggerContext:
    """
    Logger 上下文管理器

    用法:
        with LoggerContext(logger, "request_id", "12345"):
            logger.info("Processing request")
    """

    def __init__(self, logger: logging.Logger, **context: Any):
        self.logger = logger
        self.context = context
        self.old_factory = None

    def __enter__(self):
        self.old_factory = logging.getLogRecordFactory()

        def record_factory(*args, **kwargs):
            record = self.old_factory(*args, **kwargs)
            if hasattr(record, 'extra_fields'):
                record.extra_fields.update(self.context)
            else:
                record.extra_fields = self.context.copy()
            return record

        logging.setLogRecordFactory(record_factory)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.old_factory:
            logging.setLogRecordFactory(self.old_factory)
        return False


__all__ = [
    "setup_logger",
    "LogFormat",
    "StructuredFormatter",
    "TextFormatter",
    "log_with_extra",
    "LoggerContext",
]


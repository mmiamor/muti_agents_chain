"""
LLMChain AI Backend — 应用入口
"""
from __future__ import annotations

import sys
from pathlib import Path

# 确保项目根目录在 Python 路径中
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import uvicorn

from src.config import settings
from src.utils.logger import setup_logger

logger = setup_logger("main", level=settings.LOG_LEVEL)


def main():
    logger.info(f"🐚 LLMChain AI Backend v0.1.0")
    logger.info(f"   Python: {sys.version.split()[0]}")
    logger.info(f"   Model:  {settings.DEFAULT_MODEL}")
    logger.info(f"   Host:   {settings.APP_HOST}:{settings.APP_PORT}")

    uvicorn.run(
        "src.api.server:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )


if __name__ == "__main__":
    main()

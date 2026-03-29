"""pytest 配置 — 注册自定义 mark"""
import pytest


def pytest_configure(config):
    config.addinivalue_line("markers", "e2e: 需要 LLM API 的端到端测试（默认跳过）")

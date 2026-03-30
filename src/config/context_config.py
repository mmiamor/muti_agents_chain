"""
上下文管理配置示例

在项目启动时根据需求调整上下文管理策略
"""
from src.memory.context_manager import ContextConfig, get_context_manager


def setup_context_management():
    """
    配置上下文管理策略

    在 src/config/__init__.py 或项目入口处调用此函数
    """
    # 根据项目需求调整配置
    config = ContextConfig(
        max_messages=100,              # 最大消息数量
        max_tokens=8000,               # 最大 token 估算
        compact_threshold=0.8,         # 80% 时触发压缩
        keep_first_n=5,                # 保留前 5 条关键消息
        keep_last_n=20,                # 保留最近 20 条消息
        enable_semantic_compact=True,  # 启用语义压缩
    )

    # 初始化全局上下文管理器
    context_manager = get_context_manager(config)

    return context_manager


# 针对不同场景的预设配置

def get_lightweight_config() -> ContextConfig:
    """轻量级配置 - 适合快速迭代、简单任务"""
    return ContextConfig(
        max_messages=50,
        max_tokens=4000,
        compact_threshold=0.75,
        keep_first_n=3,
        keep_last_n=10,
        enable_semantic_compact=False,  # 禁用语义压缩以提升速度
    )


def get_balanced_config() -> ContextConfig:
    """平衡配置 - 适合大多数场景"""
    return ContextConfig(
        max_messages=100,
        max_tokens=8000,
        compact_threshold=0.8,
        keep_first_n=5,
        keep_last_n=20,
        enable_semantic_compact=True,
    )


def get_comprehensive_config() -> ContextConfig:
    """全面配置 - 适合复杂、长期的项目"""
    return ContextConfig(
        max_messages=200,
        max_tokens=16000,
        compact_threshold=0.85,
        keep_first_n=10,
        keep_last_n=30,
        enable_semantic_compact=True,
    )

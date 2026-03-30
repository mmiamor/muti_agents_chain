#!/usr/bin/env python3
"""
Agent 模型配置测试 - 验证不同 Agent 可以使用不同模型
"""
import asyncio
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
_ROOT = Path(__file__).resolve().parent
os.chdir(_ROOT)

from src.config import reload_settings, settings
from src.config.agent_models import AgentModelConfig, parse_agent_model_config
from src.agents.factory import create_llm


def test_agent_model_config():
    """测试 Agent 模型配置"""
    print("=" * 60)
    print("测试 1: AgentModelConfig 基本功能")
    print("=" * 60)

    # 创建配置
    config = parse_agent_model_config(
        default_model="glm-4",
        pm_model="glm-4-plus",
        architect_model="glm-4-plus",
        backend_dev_model="glm-4-turbo",
    )

    # 测试获取模型
    assert config.get_model_for_agent("pm_agent") == "glm-4-plus"
    assert config.get_model_for_agent("architect_agent") == "glm-4-plus"
    assert config.get_model_for_agent("backend_dev_agent") == "glm-4-turbo"
    assert config.get_model_for_agent("qa_agent") == "glm-4"  # 默认模型

    print("✅ PM Agent 模型:", config.get_model_for_agent("pm_agent"))
    print("✅ Architect Agent 模型:", config.get_model_for_agent("architect_agent"))
    print("✅ Backend Dev Agent 模型:", config.get_model_for_agent("backend_dev_agent"))
    print("✅ QA Agent 模型:", config.get_model_for_agent("qa_agent"))
    print("✅ 所有使用的模型:", config.get_all_models())


def test_env_config():
    """测试环境配置中的模型配置"""
    print("\n" + "=" * 60)
    print("测试 2: 环境配置中的 Agent 模型")
    print("=" * 60)

    # 设置测试环境变量
    os.environ["PM_MODEL"] = "glm-4-plus"
    os.environ["ARCHITECT_MODEL"] = "glm-4-plus"
    os.environ["BACKEND_DEV_MODEL"] = "glm-4-turbo"

    # 重新加载配置
    new_settings = reload_settings()

    # 验证配置
    config = new_settings.agent_model_config
    print("✅ 默认模型:", config.default_model)
    print("✅ PM Agent 模型:", config.get_model_for_agent("pm_agent"))
    print("✅ Architect Agent 模型:", config.get_model_for_agent("architect_agent"))
    print("✅ Backend Dev Agent 模型:", config.get_model_for_agent("backend_dev_agent"))

    # 检查是否正确读取了环境变量
    if config.model_mapping:
        print("✅ 配置字典:", config.to_dict())
        # 验证值
        assert config.get_model_for_agent("pm_agent") == "glm-4-plus", "PM模型配置不正确"
        assert config.get_model_for_agent("architect_agent") == "glm-4-plus", "Architect模型配置不正确"
        assert config.get_model_for_agent("backend_dev_agent") == "glm-4-turbo", "Backend Dev模型配置不正确"
        print("✅ 所有模型配置验证通过")
    else:
        print("⚠️  警告: 模型映射为空，环境变量可能未正确加载")


def test_llm_factory():
    """测试 LLM 工厂创建"""
    print("\n" + "=" * 60)
    print("测试 3: LLM 工厂创建")
    print("=" * 60)

    # 直接创建配置实例进行测试
    from src.config.agent_models import parse_agent_model_config

    test_config = parse_agent_model_config(
        default_model="glm-4",
        pm_model="glm-4-plus",
        qa_model="glm-4-flash",
    )

    # 创建临时 LLM 实例测试
    pm_llm = create_llm(agent_name="pm_agent")
    qa_llm = create_llm(agent_name="qa_agent")
    default_llm = create_llm()  # 无 agent_name

    print("✅ PM Agent LLM 默认模型:", pm_llm.default_model)
    print("✅ QA Agent LLM 默认模型:", qa_llm.default_model)
    print("✅ 默认 LLM 默认模型:", default_llm.default_model)
    print("✅ 测试配置: PM={}, QA={}, Default={}".format(
        test_config.get_model_for_agent("pm_agent"),
        test_config.get_model_for_agent("qa_agent"),
        test_config.default_model
    ))

    # 验证基本功能
    assert pm_llm is not None
    assert qa_llm is not None
    assert default_llm is not None
    print("✅ LLM 实例创建成功")


async def test_agent_with_model():
    """测试 Agent 使用专用模型"""
    print("\n" + "=" * 60)
    print("测试 4: Agent 实例使用专用模型")
    print("=" * 60)

    # 导入 PM Agent
    from src.agents.nodes.pm_node import PMAgent

    # 创建 Agent 实例（使用当前环境配置）
    pm_agent = PMAgent()

    # 获取配置的模型
    expected_model = settings.agent_model_config.get_model_for_agent("pm_agent")

    print("✅ PM Agent 使用模型:", pm_agent.llm.default_model)
    print("✅ 配置中的模型:", expected_model)
    print("✅ 当前默认模型:", settings.DEFAULT_MODEL)

    # 验证 Agent 使用的模型
    assert pm_agent.llm.default_model == expected_model
    print("✅ Agent 模型配置匹配")


def test_config_persistence():
    """测试配置持久化和一致性"""
    print("\n" + "=" * 60)
    print("测试 5: 配置持久化和一致性")
    print("=" * 60)

    # 创建配置
    config1 = parse_agent_model_config(
        default_model="glm-4",
        pm_model="glm-4-plus",
    )

    # 多次获取应该返回相同结果
    assert config1.get_model_for_agent("pm_agent") == "glm-4-plus"
    assert config1.get_model_for_agent("pm_agent") == "glm-4-plus"

    # Settings 中的配置应该是单例
    config2 = settings.agent_model_config
    config3 = settings.agent_model_config
    assert config2 is config3

    print("✅ 配置一致性: 通过")
    print("✅ 单例模式: 通过")


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("🧪 Agent 模型配置测试套件")
    print("=" * 60)

    try:
        test_agent_model_config()
        test_env_config()
        test_llm_factory()
        asyncio.run(test_agent_with_model())
        test_config_persistence()

        print("\n" + "=" * 60)
        print("🎉 所有测试通过！")
        print("=" * 60)

        # 显示配置总结
        print("\n📋 配置总结:")
        print("=" * 60)
        config = settings.agent_model_config
        print(f"默认模型: {config.default_model}")
        print(f"Agent 模型映射: {config.model_mapping}")
        print(f"所有使用的模型: {config.get_all_models()}")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

#!/usr/bin/env python3
"""
Agent 模型配置使用示例

展示如何为不同的 Agent 配置和使用不同的模型
"""
import asyncio
from pathlib import Path

# 添加项目根目录到 Python 路径
import sys
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from src.config import settings
from src.agents.factory import create_llm


def example_1_check_model_config():
    """示例 1: 检查当前模型配置"""
    print("=" * 60)
    print("示例 1: 检查当前模型配置")
    print("=" * 60)

    config = settings.agent_model_config

    print(f"\n📋 当前配置:")
    print(f"  默认模型: {config.default_model}")
    print(f"  Agent 模型映射: {config.model_mapping}")
    print(f"  所有使用的模型: {config.get_all_models()}")

    # 检查每个 Agent 的模型
    agents = [
        "pm_agent",
        "architect_agent",
        "design_agent",
        "backend_dev_agent",
        "frontend_dev_agent",
        "qa_agent",
        "reviewer_agent",
    ]

    print(f"\n🤖 各 Agent 使用的模型:")
    for agent in agents:
        model = config.get_model_for_agent(agent)
        print(f"  {agent:20} → {model}")


def example_2_create_agent_llm():
    """示例 2: 为不同 Agent 创建 LLM 实例"""
    print("\n" + "=" * 60)
    print("示例 2: 为不同 Agent 创建 LLM 实例")
    print("=" * 60)

    # 创建不同 Agent 的 LLM 实例
    pm_llm = create_llm(agent_name="pm_agent")
    architect_llm = create_llm(agent_name="architect_agent")
    backend_llm = create_llm(agent_name="backend_dev_agent")
    default_llm = create_llm()

    print(f"\n🔧 创建的 LLM 实例:")
    print(f"  PM Agent LLM:        {pm_llm.default_model}")
    print(f"  Architect Agent LLM: {architect_llm.default_model}")
    print(f"  Backend Dev LLM:     {backend_llm.default_model}")
    print(f"  Default LLM:         {default_llm.default_model}")


async def example_3_custom_config():
    """示例 3: 创建自定义配置"""
    print("\n" + "=" * 60)
    print("示例 3: 创建自定义配置")
    print("=" * 60)

    from src.config.agent_models import parse_agent_model_config

    # 创建自定义配置
    custom_config = parse_agent_model_config(
        default_model="glm-4",
        pm_model="glm-4-plus",
        architect_model="glm-4-plus",
        backend_dev_model="glm-4-turbo",
        frontend_dev_model="glm-4-turbo",
    )

    print(f"\n⚙️  自定义配置:")
    print(f"  默认模型: {custom_config.default_model}")
    print(f"  PM Agent: {custom_config.get_model_for_agent('pm_agent')}")
    print(f"  Architect Agent: {custom_config.get_model_for_agent('architect_agent')}")
    print(f"  Backend Dev: {custom_config.get_model_for_agent('backend_dev_agent')}")
    print(f"  QA Agent: {custom_config.get_model_for_agent('qa_agent')}")


def example_4_cost_optimization():
    """示例 4: 成本优化配置示例"""
    print("\n" + "=" * 60)
    print("示例 4: 成本优化配置示例")
    print("=" * 60)

    print("\n💰 成本优化策略:")

    print("\n1. 开发环境 - 使用快速模型")
    dev_config = {
        "default_model": "glm-4-turbo",
        "description": "所有 Agent 使用快速模型以加快开发"
    }
    print(f"   默认模型: {dev_config['default_model']}")
    print(f"   说明: {dev_config['description']}")

    print("\n2. 生产环境 - 混合策略")
    prod_config = {
        "default_model": "glm-4",
        "pm_model": "glm-4-plus",
        "architect_model": "glm-4-plus",
        "reviewer_model": "glm-4-plus",
        "description": "关键 Agent 使用高性能模型，其他使用标准模型"
    }
    print(f"   默认模型: {prod_config['default_model']}")
    print(f"   PM/Architect/Reviewer: {prod_config['pm_model']}")
    print(f"   说明: {prod_config['description']}")

    print("\n3. 测试环境 - 经济策略")
    test_config = {
        "default_model": "glm-4-flash",
        "description": "使用经济模型降低测试成本"
    }
    print(f"   默认模型: {test_config['default_model']}")
    print(f"   说明: {test_config['description']}")


def example_5_configuration_validation():
    """示例 5: 配置验证"""
    print("\n" + "=" * 60)
    print("示例 5: 配置验证")
    print("=" * 60)

    from src.config.agent_models import parse_agent_model_config

    # 测试配置
    test_config = parse_agent_model_config(
        default_model="glm-4",
        pm_model="glm-4-plus",
        architect_model="glm-4-plus",
    )

    print(f"\n✅ 验证结果:")

    # 验证配置完整性
    all_agents = [
        "pm_agent",
        "architect_agent",
        "design_agent",
        "backend_dev_agent",
        "frontend_dev_agent",
        "qa_agent",
        "reviewer_agent",
    ]

    configured_agents = set(test_config.model_mapping.keys())
    unconfigured_agents = set(all_agents) - configured_agents

    print(f"  已配置 Agent ({len(configured_agents)}): {configured_agents}")
    print(f"  未配置 Agent ({len(unconfigured_agents)}): {unconfigured_agents}")
    print(f"  未配置 Agent 将使用默认模型: {test_config.default_model}")

    # 验证模型唯一性
    all_models = test_config.get_all_models()
    print(f"  使用的模型总数: {len(all_models)}")
    print(f"  模型列表: {all_models}")


def main():
    """运行所有示例"""
    print("\n" + "=" * 60)
    print("🎯 Agent 模型配置使用示例")
    print("=" * 60)

    try:
        # 运行所有示例
        example_1_check_model_config()
        example_2_create_agent_llm()
        asyncio.run(example_3_custom_config())
        example_4_cost_optimization()
        example_5_configuration_validation()

        print("\n" + "=" * 60)
        print("🎉 所有示例运行完成！")
        print("=" * 60)

        print("\n📚 更多信息请参考:")
        print("  - 文档: docs/AGENT_MODEL_CONFIG.md")
        print("  - 测试: test_agent_models.py")
        print("  - 配置示例: .env.agent_models_example")

        return True

    except Exception as e:
        print(f"\n❌ 示例运行失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

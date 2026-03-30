#!/usr/bin/env python3
"""
自定义工作流使用示例

展示如何使用自定义工作流配置来灵活控制 Agent 执行流程
"""
import asyncio
from pathlib import Path

import sys

# 添加项目根目录到 Python 路径
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from src.core.workflow_loader import WorkflowLoader
from src.core.workflow_engine import WorkflowEngine
from src.models.state import AgentState
from src.models.workflow import WorkflowTemplates


async def example_1_use_template():
    """示例 1: 使用预定义模板"""
    print("=" * 60)
    print("示例 1: 使用预定义模板")
    print("=" * 60)

    loader = WorkflowLoader()

    # 加载快速原型模板
    workflow = loader.load_template("rapid_prototype")

    print(f"\n📋 工作流名称: {workflow.name}")
    print(f"   描述: {workflow.description}")
    print(f"   阶段数量: {len(workflow.stages)}")

    for i, stage in enumerate(workflow.stages, 1):
        agents = ", ".join([agent.name for agent in stage.agents])
        print(f"   阶段 {i}: {stage.name} ({stage.mode.value}) - {agents}")


async def example_2_load_from_file():
    """示例 2: 从文件加载配置"""
    print("\n" + "=" * 60)
    print("示例 2: 从文件加载配置")
    print("=" * 60)

    loader = WorkflowLoader()

    # 加载 YAML 配置文件
    workflow = loader.load_from_file("workflows/full_pipeline.yaml")

    print(f"\n📋 从文件加载: {workflow.name}")
    print(f"   描述: {workflow.description}")
    print(f"   版本: {workflow.version}")

    # 显示全局设置
    if workflow.global_settings:
        print(f"   全局设置: {workflow.global_settings}")


async def example_3_custom_workflow():
    """示例 3: 创建自定义工作流"""
    print("\n" + "=" * 60)
    print("示例 3: 创建自定义工作流")
    print("=" * 60)

    loader = WorkflowLoader()

    # 创建自定义工作流 - 只做设计，不做开发
    workflow = loader.create_custom_workflow(
        name="design_only_workflow",
        agents=["pm_agent", "architect_agent", "design_agent"],
        parallel=False,
        skip_review=False,
    )

    print(f"\n📋 自定义工作流: {workflow.name}")
    print(f"   阶段数量: {len(workflow.stages)}")

    stage = workflow.stages[0]
    print(f"   Agent 列表: {[agent.name for agent in stage.agents]}")
    print(f"   执行模式: {stage.mode.value}")
    print(f"   审查启用: {stage.review.enabled}")


async def example_4_skip_agents():
    """示例 4: 跳过某些 Agent"""
    print("\n" + "=" * 60)
    print("示例 4: 跳过某些 Agent")
    print("=" * 60)

    # 加载完整流水线
    workflow = WorkflowTemplates().full_pipeline()

    # 跳过设计阶段
    workflow.skip_agents = ["design_agent"]

    print(f"\n📋 工作流: {workflow.name}")
    print(f"   跳过的 Agent: {workflow.skip_agents}")

    print("\n   执行计划:")
    for i, stage in enumerate(workflow.stages, 1):
        active_agents = [a for a in stage.agents if a.name not in workflow.skip_agents]
        if active_agents:
            agents = ", ".join([a.name for a in active_agents])
            print(f"   阶段 {i}: {stage.name} - {agents}")
        else:
            print(f"   阶段 {i}: {stage.name} - (已跳过)")


async def example_5_parallel_execution():
    """示例 5: 并行执行"""
    print("\n" + "=" * 60)
    print("示例 5: 并行执行配置")
    print("=" * 60)

    # 加载完整流水线
    workflow = WorkflowTemplates().full_pipeline()

    print(f"\n📋 工作流: {workflow.name}")
    print("\n   并行执行阶段:")

    for stage in workflow.stages:
        if stage.mode.value == "parallel":
            agents = ", ".join([a.name for a in stage.agents])
            print(f"   ✓ {stage.name}: {agents}")


async def example_6_save_custom_workflow():
    """示例 6: 保存自定义工作流"""
    print("\n" + "=" * 60)
    print("示例 6: 保存自定义工作流")
    print("=" * 60)

    loader = WorkflowLoader()

    # 创建自定义工作流
    workflow = loader.create_custom_workflow(
        name="my_custom_workflow",
        agents=["pm_agent", "backend_dev_agent"],
        parallel=False,
        skip_review=True,
    )

    # 保存到文件
    output_path = Path("workflows/my_custom_workflow.yaml")
    loader.save_to_file(workflow, output_path, format="yaml")

    print(f"\n✅ 工作流已保存到: {output_path}")
    print(f"   可以通过以下命令加载:")
    print(f"   loader.load_from_file('{output_path}')")


async def example_7_workflow_execution():
    """示例 7: 执行工作流（模拟）"""
    print("\n" + "=" * 60)
    print("示例 7: 执行工作流（模拟）")
    print("=" * 60)

    # 加载快速原型模板
    workflow = WorkflowTemplates().rapid_prototype()

    # 创建工作流引擎
    engine = WorkflowEngine(workflow)

    print(f"\n🚀 模拟执行工作流: {workflow.name}")
    print(f"   阶段数量: {len(workflow.stages)}")

    # 模拟初始状态
    initial_state = AgentState(
        messages=[{"role": "user", "content": "创建一个简单的 TODO 应用"}],
        sender="user",
    )

    print("\n   执行计划:")
    for i, stage in enumerate(workflow.stages, 1):
        agents = ", ".join([a.name for a in stage.agents])
        print(f"   {i}. {stage.name} ({stage.mode.value})")
        print(f"      Agents: {agents}")
        print(f"      审查: {'启用' if stage.review.enabled else '跳过'}")

    # 注意: 实际执行需要有效的 API Key
    print("\n   ⚠️  实际执行需要配置有效的 API Key")
    print("   这里只是展示执行计划，不会真正执行")


async def example_8_list_available_workflows():
    """示例 8: 列出所有可用的工作流"""
    print("\n" + "=" * 60)
    print("示例 8: 列出所有可用的工作流")
    print("=" * 60)

    loader = WorkflowLoader()

    # 列出预定义模板
    print("\n📦 预定义模板:")
    templates = [
        "full_pipeline",
        "rapid_prototype",
        "design_only",
        "backend_only",
        "frontend_only",
    ]
    for template in templates:
        print(f"   - {template}")

    # 列出配置文件
    print("\n📁 配置文件:")
    config_files = loader.list_available_workflows()
    if config_files:
        for config in config_files:
            print(f"   - {config}")
    else:
        print("   (没有找到配置文件)")


async def main():
    """运行所有示例"""
    print("\n" + "=" * 60)
    print("🎯 自定义工作流使用示例")
    print("=" * 60)

    try:
        # 运行所有示例
        await example_1_use_template()
        await example_2_load_from_file()
        await example_3_custom_workflow()
        await example_4_skip_agents()
        await example_5_parallel_execution()
        await example_6_save_custom_workflow()
        await example_7_workflow_execution()
        await example_8_list_available_workflows()

        print("\n" + "=" * 60)
        print("🎉 所有示例运行完成！")
        print("=" * 60)

        print("\n📚 更多信息:")
        print("  - 工作流配置: workflows/")
        print("  - 文档: docs/CUSTOM_WORKFLOW.md")
        print("  - API: src/core/workflow_engine.py")

        return True

    except Exception as e:
        print(f"\n❌ 示例运行失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)

"""E2E 真实 LLM 测试 — PM → Reviewer → Architect → Reviewer → Design → Reviewer 全流程"""
import asyncio
import json
import time
from datetime import datetime

from langchain_core.messages import HumanMessage

from src.core.orchestrator import build_graph
from src.models.state import AgentPhase


def log_section(title: str):
    """打印分隔线"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def log_subsection(title: str):
    """打印子分隔线"""
    print(f"\n{'─'*40}")
    print(f"  {title}")
    print(f"{'─'*40}\n")


def format_timestamp() -> str:
    """格式化时间戳"""
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]


async def main():
    """完整的 E2E 测试 - PM 到 Design 全流程"""
    start_time = time.time()
    log_section("🚀 完整 E2E 测试 - PM → Reviewer → Architect → Reviewer → Design → Reviewer")

    # 配置
    thread_id = f"full-test-{int(time.time())}"
    config = {
        "configurable": {
            "thread_id": thread_id,
            "recursion_limit": 25  # 增加递归限制以支持完整流程
        }
    }

    print(f"[{format_timestamp()}] 📝 配置:")
    print(f"  Thread ID: {thread_id}")
    print(f"  Recursion Limit: 25")

    # 构建图
    print(f"[{format_timestamp()}] 🔧 构建 LangGraph...")
    graph = build_graph()
    print(f"  ✅ Graph 构建完成")

    # 准备输入
    log_subsection("📋 初始输入")
    initial_state = {
        "messages": [
            HumanMessage(content="我想做一个简单的番茄钟应用，包含计时器和休息提醒功能")
        ],
        "current_phase": AgentPhase.REQUIREMENT_GATHERING,
        "sender": "user",
    }

    print(f"  用户需求: {initial_state['messages'][0].content}")

    # 执行流程
    log_section("⚡ 执行完整流程")
    print(f"[{format_timestamp()}] 🎬 开始执行完整流程...")
    print(f"  包含阶段: PM → Reviewer → Architect → Reviewer → Design → Reviewer")
    print(f"  提示: 这将调用多个 LLM API，可能需要 10-20 分钟\n")

    execution_start = time.time()

    try:
        result = await graph.ainvoke(initial_state, config)

        execution_time = time.time() - execution_start
        print(f"[{format_timestamp()}] ✅ 流程执行完成")
        print(f"  执行耗时: {execution_time:.2f} 秒 ({execution_time/60:.1f} 分钟)\n")

        # 分析结果
        log_section("📊 结果分析")

        sender = result.get("sender", "N/A")
        revision_counts = result.get("revision_counts", {})
        messages = result.get("messages", [])
        current_phase = result.get("current_phase", "N/A")

        print("📍 基本信息:")
        print(f"  最终发送者: {sender}")
        print(f"  当前阶段: {current_phase}")
        print(f"  修订统计: {revision_counts}")
        print(f"  消息总数: {len(messages)}")

        total_revisions = sum(revision_counts.values()) if revision_counts else 0
        print(f"  总修订次数: {total_revisions}\n")

        # 显示消息流摘要
        log_subsection("💬 消息流摘要")
        print(f"  共 {len(messages)} 条消息\n")

        # 按发送者分组统计
        sender_counts = {}
        for msg in messages:
            name = getattr(msg, "name", "unknown")
            sender_counts[name] = sender_counts.get(name, 0) + 1

        print("  各 Agent 消息统计:")
        for sender_name, count in sorted(sender_counts.items()):
            print(f"    {sender_name}: {count} 条")
        print()

        # PRD 分析
        prd = result.get("prd")
        if prd:
            log_subsection("📄 PRD (产品需求文档)")
            print(f"✅ PRD 已生成")
            print(f"  产品愿景: {prd.vision}")
            print(f"  目标用户: {prd.target_audience}")
            print(f"  核心功能 ({len(prd.core_features)} 项):")
            for i, feature in enumerate(prd.core_features, 1):
                print(f"    {i}. {feature}")
            print(f"  用户故事: {len(prd.user_stories)} 条")
            print(f"  业务流程: {prd.mermaid_flowchart[:80]}...")
        else:
            print("❌ PRD 未生成\n")

        # TRD 分析
        trd = result.get("trd")
        if trd:
            log_subsection("🏗️ TRD (技术设计文档)")
            print(f"✅ TRD 已生成")
            print(f"  技术栈:")
            print(f"    前端: {trd.tech_stack.frontend}")
            print(f"    后端: {trd.tech_stack.backend}")
            print(f"    数据库: {trd.tech_stack.database}")
            print(f"    基础设施: {trd.tech_stack.infra}")
            print(f"  API 端点: {len(trd.api_endpoints)} 个")
            for i, api in enumerate(trd.api_endpoints[:3], 1):
                print(f"    {i}. {api.method} {api.path} — {api.description}")
            if len(trd.api_endpoints) > 3:
                print(f"    ... 还有 {len(trd.api_endpoints) - 3} 个")
            print(f"  架构概述: {trd.architecture_overview[:100]}...")
        else:
            print("❌ TRD 未生成\n")

        # Design 分析
        design = result.get("design_doc")
        if design:
            log_subsection("🎨 DesignDocument (UI/UX 设计)")
            print(f"✅ 设计文档已生成")
            print(f"  页面规格: {len(design.page_specs)} 个页面")
            for i, page in enumerate(design.page_specs[:3], 1):
                print(f"    {i}. {page.page_name}: {page.description}")
            if len(design.page_specs) > 3:
                print(f"    ... 还有 {len(design.page_specs) - 3} 个页面")

            print(f"  设计 Tokens:")
            print(f"    主色调: {design.design_tokens.color_primary}")
            print(f"    字体: {design.design_tokens.font_family}")
            print(f"  组件库: {', '.join(design.component_library[:3])}")
            if len(design.component_library) > 3:
                print(f"    ... 还有 {len(design.component_library) - 3} 个组件")
            print(f"  用户旅程: {design.user_journey[:100]}...")
        else:
            print("❌ 设计文档未生成\n")

        # 最终审查
        review = result.get("latest_review")
        if review:
            log_subsection("🔍 最终审查结果")
            status_emoji = "✅" if review.status == "APPROVED" else "❌"
            print(f"{status_emoji} 审查状态: {review.status}")
            print(f"  审查意见: {review.comments[:300]}")
            if len(review.comments) > 300:
                print(f"    ...(还有 {len(review.comments) - 300} 字符)")
        else:
            print("⚠️  没有最终审查结果\n")

        # 统计总结
        log_section("📈 执行统计")

        total_time = time.time() - start_time

        print(f"⏱️  时间统计:")
        print(f"  总耗时: {total_time:.2f} 秒 ({total_time/60:.1f} 分钟)")
        print(f"  执行时间: {execution_time:.2f} 秒")

        print(f"\n📊 数据统计:")
        print(f"  消息总数: {len(messages)}")
        print(f"  总修订次数: {total_revisions}")

        if revision_counts:
            print(f"\n🔄 各 Agent 修订详情:")
            for agent, count in sorted(revision_counts.items()):
                print(f"    {agent}: {count} 次")

        # 保存结果
        log_subsection("💾 保存结果")
        output_file = f"test_output_full_{thread_id}.json"
        output_data = {
            "thread_id": thread_id,
            "timestamp": datetime.now().isoformat(),
            "total_time": total_time,
            "execution_time": execution_time,
            "sender": sender,
            "current_phase": current_phase,
            "revision_counts": revision_counts,
            "message_count": len(messages),
            "sender_counts": sender_counts,
            "has_prd": prd is not None,
            "has_trd": trd is not None,
            "has_design": design is not None,
            "final_review": {
                "status": review.status,
                "comments": review.comments
            } if review else None,
        }

        try:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            print(f"  ✅ 结果已保存到: {output_file}")
        except Exception as e:
            print(f"  ⚠️  保存失败: {e}")

        log_section("✅ 测试完成")
        print(f"🎉 完整流程测试成功！")
        print(f"📁 结果文件: {output_file}")
        print(f"⏱️  总耗时: {total_time:.2f} 秒 ({total_time/60:.1f} 分钟)")

        # 显示完成度
        completed_stages = []
        if prd:
            completed_stages.append("PM")
        if trd:
            completed_stages.append("Architect")
        if design:
            completed_stages.append("Design")

        print(f"\n📈 完成阶段: {' → '.join(completed_stages)}")
        if len(completed_stages) == 3:
            print(f"🏆 所有阶段都已完成！")

    except Exception as e:
        execution_time = time.time() - execution_start
        print(f"[{format_timestamp()}] ❌ 执行失败 (耗时 {execution_time:.2f}s)")
        print(f"  错误类型: {type(e).__name__}")
        print(f"  错误信息: {str(e)}")

        # 显示部分结果（如果有）
        if 'result' in locals() and result:
            log_section("📊 部分结果")
            print(f"  发送者: {result.get('sender', 'N/A')}")
            print(f"  阶段: {result.get('current_phase', 'N/A')}")
            print(f"  消息数: {len(result.get('messages', []))}")

            has_prd = result.get('prd') is not None
            has_trd = result.get('trd') is not None
            has_design = result.get('design_doc') is not None

            print(f"  已完成:")
            if has_prd:
                print(f"    ✅ PM (PRD)")
            if has_trd:
                print(f"    ✅ Architect (TRD)")
            if has_design:
                print(f"    ✅ Design")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
    except Exception as e:
        print(f"\n\n❌ 测试失败:")
        print(f"  {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()

"""E2E 真实 LLM 测试 — PM → Reviewer 闭环"""
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


def print_message_summary(msg, index: int):
    """打印消息摘要"""
    role = getattr(msg, "type", "unknown")
    name = getattr(msg, "name", None)
    content = getattr(msg, "content", "")

    # 添加名称前缀（如果有）
    name_prefix = f"[{name}]" if name else ""

    # 截断内容
    if len(content) > 150:
        content = content[:150] + "..."

    print(f"  {index+1}. {name_prefix}[{role}] {content}")


async def main():
    """主测试函数"""
    start_time = time.time()
    log_section("🚀 E2E 测试启动 - PM → Reviewer 流程")

    # 1. 初始化配置
    print(f"[{format_timestamp()}] 📝 初始化配置...")
    thread_id = f"e2e-test-{int(time.time())}"
    config = {"configurable": {"thread_id": thread_id}}
    print(f"  Thread ID: {thread_id}")

    # 2. 构建图
    print(f"[{format_timestamp()}] 🔧 构建 LangGraph...")
    graph = build_graph()
    print(f"  Graph 构建完成")

    # 3. 准备初始状态
    log_subsection("📋 初始状态")
    initial_state = {
        "messages": [
            HumanMessage(
                content="我想做一个遛狗APP，帮助忙碌的都市养狗人找到靠谱的遛狗服务者"
            )
        ],
        "current_phase": AgentPhase.REQUIREMENT_GATHERING,
        "sender": "user",
    }

    print(f"  当前阶段: {initial_state['current_phase']}")
    print(f"  发送者: {initial_state['sender']}")
    print(f"  用户消息: {initial_state['messages'][0].content}")

    # 4. 执行流程
    log_section("⚡ 执行 Multi-Agent 流程")
    print(f"[{format_timestamp()}] 🎬 开始执行...")
    print(f"  提示: 此过程将调用真实的 LLM API，可能需要几分钟\n")

    execution_start = time.time()
    result = await graph.ainvoke(initial_state, config)
    execution_time = time.time() - execution_start

    print(f"[{format_timestamp()}] ✅ 流程执行完成")
    print(f"  总耗时: {execution_time:.2f} 秒 ({execution_time/60:.1f} 分钟)")

    # 5. 结果分析
    log_section("📊 执行结果分析")

    # 基本信息
    print("📍 基本信息:")
    sender = result.get("sender", "N/A")
    revision_counts = result.get("revision_counts", {})
    current_phase = result.get("current_phase", "N/A")

    print(f"  最终发送者: {sender}")
    print(f"  当前阶段: {current_phase}")
    print(f"  修订次数统计: {revision_counts}")

    # 消息历史
    messages = result.get("messages", [])
    log_subsection(f"💬 消息历史 (共 {len(messages)} 条)")
    for i, msg in enumerate(messages):
        print_message_summary(msg, i)

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
        print(f"  用户故事 ({len(prd.user_stories)} 条):")
        for i, story in enumerate(prd.user_stories[:3], 1):  # 只显示前3条
            print(f"    {i}. {story.title[:50]}...")
        if len(prd.user_stories) > 3:
            print(f"    ... 还有 {len(prd.user_stories) - 3} 条")
        print(f"  非功能性需求: {prd.non_functional}")
        print(f"  业务流程图: {prd.mermaid_flowchart[:80]}...")
    else:
        log_subsection("📄 PRD 状态")
        print("❌ PRD 未生成")

    # 审查结果
    review = result.get("latest_review")
    if review:
        log_subsection("🔍 审查结果")
        status_emoji = "✅" if review.status == "APPROVED" else "❌"
        print(f"{status_emoji} 审查状态: {review.status}")
        print(f"  审查意见: {review.comments}")
    else:
        log_subsection("🔍 审查状态")
        print("⚠️  没有审查结果")

    # 统计信息
    log_section("📈 统计信息")

    total_time = time.time() - start_time
    print(f"  总执行时间: {total_time:.2f} 秒 ({total_time/60:.1f} 分钟)")
    print(f"  消息总数: {len(messages)}")
    print(f"  修订轮次: {sum(revision_counts.values()) if revision_counts else 0}")

    if revision_counts:
        print(f"  各 Agent 修订次数:")
        for agent, count in revision_counts.items():
            print(f"    - {agent}: {count} 次")

    # 上下文管理统计
    from src.memory.agent_context import get_context_stats
    context_stats = get_context_stats()
    print(f"\n  🧠 上下文管理统计:")
    print(f"    - 总消息数: {context_stats.get('total_messages', 0)}")
    print(f"    - 估算 tokens: {context_stats.get('estimated_tokens', 0)}")
    print(f"    - 压缩次数: {context_stats.get('compression_count', 0)}")
    if context_stats.get('last_compaction_ratio', 0) > 0:
        print(f"    - 最后压缩率: {context_stats['last_compaction_ratio']:.1%}")

    # 保存结果（可选）
    log_subsection("💾 保存结果")
    output_file = f"test_output_{thread_id}.json"
    output_data = {
        "thread_id": thread_id,
        "timestamp": datetime.now().isoformat(),
        "execution_time": total_time,
        "sender": sender,
        "current_phase": current_phase,
        "revision_counts": revision_counts,
        "message_count": len(messages),
        "prd": prd.model_dump() if prd else None,
        "review": review.model_dump() if review else None,
        "context_stats": context_stats,
    }

    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        print(f"  ✅ 结果已保存到: {output_file}")
    except Exception as e:
        print(f"  ⚠️  保存结果失败: {e}")

    # 完成
    log_section("✅ 测试完成")
    print(f"🎉 所有测试通过！")
    print(f"📁 结果文件: {output_file}")
    print(f"⏱️  总耗时: {total_time:.2f} 秒\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
    except Exception as e:
        print(f"\n\n❌ 测试执行失败:")
        print(f"  错误类型: {type(e).__name__}")
        print(f"  错误信息: {str(e)}")
        import traceback
        print(f"\n详细堆栈:")
        traceback.print_exc()

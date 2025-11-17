"""
中间件集成示例

展示如何组合使用多个中间件来增强 LangChain 1.0 分析师
"""

from langchain_openai import ChatOpenAI

# 导入 v2 分析师
from tradingagents.agents.analysts.market_analyst_v2 import create_market_analyst_node_v2
from tradingagents.agents.analysts.news_analyst_v2 import create_news_analyst_node_v2
from tradingagents.agents.analysts.fundamentals_analyst_v2 import create_fundamentals_analyst_node_v2

# 导入中间件
from tradingagents.middleware.base import MiddlewareChain
from tradingagents.middleware.risk_control import RiskControlMiddleware
from tradingagents.middleware.human_approval import HumanApprovalMiddleware, ApprovalMethod
from tradingagents.middleware.conversation_summary import ConversationSummaryMiddleware

from tradingagents.utils.logging_manager import get_logger

logger = get_logger('examples.middleware_integration')


# ============================================
# 示例 1: 单个中间件使用
# ============================================

def example_1_single_middleware():
    """示例 1: 使用单个风险控制中间件"""

    logger.info("=" * 60)
    logger.info("示例 1: 单个风险控制中间件")
    logger.info("=" * 60)

    # 创建 LLM
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    # 创建市场分析师节点
    market_analyst_node = create_market_analyst_node_v2(llm)

    # 创建风险控制中间件
    risk_middleware = RiskControlMiddleware(
        risk_threshold=0.85,      # 置信度 > 85% 视为高风险
        block_high_risk=False,    # 不拦截，仅记录
        alert_channels=['log']    # 告警到日志
    )

    # 创建中间件链
    chain = MiddlewareChain()
    chain.add(risk_middleware)

    # 应用中间件
    wrapped_analyst = chain.apply(market_analyst_node)

    # 测试
    state = {
        "messages": [("user", "分析平安银行(000001)的技术面")],
        "session_id": "example_1"
    }

    result = wrapped_analyst(state)

    # 查看统计
    stats = risk_middleware.get_stats()
    logger.info(f"高风险决策数: {stats['high_risk_count']}")
    logger.info(f"拦截数: {stats['blocked_count']}")

    return result


# ============================================
# 示例 2: 多个中间件组合
# ============================================

def example_2_multiple_middleware():
    """示例 2: 组合多个中间件（对话总结 + 风险控制 + 人工审批）"""

    logger.info("=" * 60)
    logger.info("示例 2: 多个中间件组合")
    logger.info("=" * 60)

    # 创建 LLM
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    # 创建新闻分析师节点
    news_analyst_node = create_news_analyst_node_v2(llm)

    # 创建中间件链
    chain = MiddlewareChain()

    # 1. 对话总结中间件（最先执行，压缩对话）
    chain.add(ConversationSummaryMiddleware(
        llm=llm,
        max_messages=20,
        keep_recent=5
    ))

    # 2. 风险控制中间件（检测高风险）
    chain.add(RiskControlMiddleware(
        risk_threshold=0.85,
        block_high_risk=False,
        alert_channels=['log']
    ))

    # 3. 人工审批中间件（需要人工确认）
    chain.add(HumanApprovalMiddleware(
        approval_method=ApprovalMethod.AUTO,  # 自动审批（演示用）
        timeout_seconds=60
    ))

    # 应用中间件
    wrapped_analyst = chain.apply(news_analyst_node)

    # 测试
    state = {
        "messages": [("user", "分析贵州茅台(600519)的最新新闻")],
        "session_id": "example_2"
    }

    result = wrapped_analyst(state)

    logger.info("✅ 示例 2 完成")

    return result


# ============================================
# 示例 3: 自定义审批回调
# ============================================

def example_3_custom_approval():
    """示例 3: 使用自定义审批回调"""

    logger.info("=" * 60)
    logger.info("示例 3: 自定义审批回调")
    logger.info("=" * 60)

    # 自定义审批逻辑
    def my_approval_callback(analysis_result, matched_rules, timeout):
        """
        自定义审批逻辑

        Args:
            analysis_result: 分析结果
            matched_rules: 触发的规则
            timeout: 超时时间

        Returns:
            (ApprovalDecision, modified_result)
        """
        from tradingagents.middleware.human_approval import ApprovalDecision

        logger.info("🔔 [自定义审批] 收到审批请求")
        logger.info(f"   股票: {analysis_result.get('ticker')}")
        logger.info(f"   建议: {analysis_result.get('recommendation')}")
        logger.info(f"   置信度: {analysis_result.get('confidence', 0):.0%}")

        # 示例逻辑：置信度 > 0.9 自动批准，否则拒绝
        if analysis_result.get('confidence', 0) > 0.9:
            logger.info("✅ [自定义审批] 置信度高，自动批准")
            return ApprovalDecision.APPROVED, None
        else:
            logger.info("❌ [自定义审批] 置信度不足，拒绝")
            return ApprovalDecision.REJECTED, None

    # 创建 LLM
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    # 创建基本面分析师节点
    fundamentals_analyst_node = create_fundamentals_analyst_node_v2(llm)

    # 创建带自定义回调的人工审批中间件
    approval_middleware = HumanApprovalMiddleware(
        approval_method=ApprovalMethod.API,
        approval_callback=my_approval_callback
    )

    # 创建中间件链
    chain = MiddlewareChain()
    chain.add(approval_middleware)

    # 应用中间件
    wrapped_analyst = chain.apply(fundamentals_analyst_node)

    # 测试
    state = {
        "messages": [("user", "分析苹果公司(AAPL)的基本面")],
        "session_id": "example_3"
    }

    result = wrapped_analyst(state)

    # 查看统计
    stats = approval_middleware.get_stats()
    logger.info(f"审批请求数: {stats['approval_count']}")
    logger.info(f"批准率: {stats['approval_rate']:.0%}")

    return result


# ============================================
# 示例 4: 生产环境配置
# ============================================

def example_4_production_setup():
    """示例 4: 生产环境中间件配置"""

    logger.info("=" * 60)
    logger.info("示例 4: 生产环境配置")
    logger.info("=" * 60)

    # 创建 LLM
    llm = ChatOpenAI(model="gpt-4o", temperature=0)  # 生产环境使用更强的模型

    # 创建市场分析师节点
    market_analyst_node = create_market_analyst_node_v2(llm)

    # 创建中间件链（生产环境推荐配置）
    chain = MiddlewareChain()

    # 1. 对话总结（节省成本）
    chain.add(ConversationSummaryMiddleware(
        llm=ChatOpenAI(model="gpt-4o-mini", temperature=0),  # 使用便宜模型总结
        max_messages=30,
        keep_recent=10
    ))

    # 2. 风险控制（拦截模式）
    chain.add(RiskControlMiddleware(
        risk_threshold=0.80,           # 更严格的阈值
        block_high_risk=True,          # ⚠️ 生产环境：拦截高风险
        alert_channels=['log', 'email', 'webhook']  # 多渠道告警
    ))

    # 3. 人工审批（CLI 或 Web）
    chain.add(HumanApprovalMiddleware(
        approval_method=ApprovalMethod.WEB,  # 生产环境使用 Web 界面
        timeout_seconds=600,                  # 10分钟超时
        default_on_timeout='reject'           # 超时拒绝
    ))

    # 应用中间件
    wrapped_analyst = chain.apply(market_analyst_node)

    logger.info("✅ 生产环境中间件配置完成")
    logger.info("   - 对话总结: ✓")
    logger.info("   - 风险控制: ✓ (拦截模式)")
    logger.info("   - 人工审批: ✓ (Web)")

    # 在生产环境中使用
    # result = wrapped_analyst(state)

    return wrapped_analyst


# ============================================
# 示例 5: 条件性启用中间件
# ============================================

def example_5_conditional_middleware():
    """示例 5: 根据条件启用/禁用中间件"""

    logger.info("=" * 60)
    logger.info("示例 5: 条件性启用中间件")
    logger.info("=" * 60)

    # 创建 LLM
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    # 创建市场分析师节点
    market_analyst_node = create_market_analyst_node_v2(llm)

    # 创建中间件（默认启用）
    risk_middleware = RiskControlMiddleware(
        risk_threshold=0.85,
        block_high_risk=False
    )

    approval_middleware = HumanApprovalMiddleware(
        approval_method=ApprovalMethod.AUTO
    )

    # 创建中间件链
    chain = MiddlewareChain()
    chain.add(risk_middleware)
    chain.add(approval_middleware)

    # 应用中间件
    wrapped_analyst = chain.apply(market_analyst_node)

    # 测试 1: 正常使用（中间件启用）
    logger.info("--- 测试 1: 中间件启用 ---")
    state = {
        "messages": [("user", "分析比亚迪(002594)")],
        "session_id": "example_5_test1"
    }
    result1 = wrapped_analyst(state)

    # 测试 2: 禁用人工审批中间件
    logger.info("--- 测试 2: 禁用人工审批 ---")
    approval_middleware.disable()
    state = {
        "messages": [("user", "分析宁德时代(300750)")],
        "session_id": "example_5_test2"
    }
    result2 = wrapped_analyst(state)

    # 测试 3: 重新启用
    logger.info("--- 测试 3: 重新启用 ---")
    approval_middleware.enable()
    state = {
        "messages": [("user", "分析隆基绿能(601012)")],
        "session_id": "example_5_test3"
    }
    result3 = wrapped_analyst(state)

    logger.info("✅ 示例 5 完成")


# ============================================
# 示例 6: 中间件统计和监控
# ============================================

def example_6_middleware_stats():
    """示例 6: 收集和展示中间件统计"""

    logger.info("=" * 60)
    logger.info("示例 6: 中间件统计和监控")
    logger.info("=" * 60)

    # 创建 LLM
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    # 创建分析师节点
    market_analyst_node = create_market_analyst_node_v2(llm)

    # 创建中间件
    summary_middleware = ConversationSummaryMiddleware(llm=llm, max_messages=10)
    risk_middleware = RiskControlMiddleware(risk_threshold=0.85)
    approval_middleware = HumanApprovalMiddleware(approval_method=ApprovalMethod.AUTO)

    # 创建中间件链
    chain = MiddlewareChain()
    chain.add(summary_middleware)
    chain.add(risk_middleware)
    chain.add(approval_middleware)

    # 应用中间件
    wrapped_analyst = chain.apply(market_analyst_node)

    # 执行多次分析
    tickers = ["000001", "600519", "AAPL", "TSLA", "MSFT"]
    for ticker in tickers:
        state = {
            "messages": [("user", f"分析{ticker}的投资价值")],
            "session_id": "example_6"
        }
        wrapped_analyst(state)

    # 收集统计
    logger.info("\n" + "=" * 60)
    logger.info("📊 中间件统计报告")
    logger.info("=" * 60)

    # 对话总结统计
    summary_stats = summary_middleware.get_stats()
    logger.info(f"\n💬 对话总结中间件:")
    logger.info(f"   调用次数: {summary_stats['call_count']}")
    logger.info(f"   总结次数: {summary_stats['summarize_count']}")
    logger.info(f"   节省 tokens: {summary_stats['total_tokens_saved']}")

    # 风险控制统计
    risk_stats = risk_middleware.get_stats()
    logger.info(f"\n🛡️ 风险控制中间件:")
    logger.info(f"   调用次数: {risk_stats['call_count']}")
    logger.info(f"   高风险决策: {risk_stats['high_risk_count']}")
    logger.info(f"   拦截次数: {risk_stats['blocked_count']}")
    logger.info(f"   高风险率: {risk_stats['high_risk_rate']:.0%}")

    # 人工审批统计
    approval_stats = approval_middleware.get_stats()
    logger.info(f"\n👨‍💼 人工审批中间件:")
    logger.info(f"   调用次数: {approval_stats['call_count']}")
    logger.info(f"   审批请求: {approval_stats['approval_count']}")
    logger.info(f"   批准次数: {approval_stats['approved_count']}")
    logger.info(f"   拒绝次数: {approval_stats['rejected_count']}")
    logger.info(f"   批准率: {approval_stats['approval_rate']:.0%}")

    logger.info("\n" + "=" * 60)


# ============================================
# 主函数
# ============================================

def main():
    """运行所有示例"""

    logger.info("\n\n")
    logger.info("🎯 中间件集成示例")
    logger.info("=" * 60)

    try:
        # 示例 1: 单个中间件
        example_1_single_middleware()

        # 示例 2: 多个中间件组合
        example_2_multiple_middleware()

        # 示例 3: 自定义审批回调
        example_3_custom_approval()

        # 示例 4: 生产环境配置
        example_4_production_setup()

        # 示例 5: 条件性启用中间件
        example_5_conditional_middleware()

        # 示例 6: 中间件统计
        example_6_middleware_stats()

        logger.info("\n\n")
        logger.info("=" * 60)
        logger.info("✅ 所有示例运行完成！")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"\n\n❌ 运行示例时出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 注意：运行此脚本需要设置 API key
    # export OPENAI_API_KEY=your_api_key

    # 可以选择运行单个示例
    # example_1_single_middleware()

    # 或运行所有示例
    main()


# ============================================
# 输出示例
# ============================================

"""
运行结果示例：

============================================================
🎯 中间件集成示例
============================================================

============================================================
示例 1: 单个风险控制中间件
============================================================
🛡️ [风险控制] 初始化
   - 风险阈值: 0.85
   - 拦截高风险: False
   - 告警渠道: ['log']
🔍 [风险控制] 开始风险检查
✅ [风险控制] 低风险决策，无需处理
高风险决策数: 0
拦截数: 0

============================================================
示例 2: 多个中间件组合
============================================================
📝 [对话总结] 初始化
   - 最大消息数: 20
   - 保留最近: 5 条
   - 总结频率: 每 10 条
🛡️ [风险控制] 初始化
👨‍💼 [人工审批] 初始化
   - 审批方式: auto
📊 [对话总结] 当前消息数: 1
🔍 [风险控制] 开始风险检查
🔍 [人工审批] 检查是否需要审批
✅ 示例 2 完成

============================================================
示例 6: 中间件统计和监控
============================================================
...执行5次分析...

============================================================
📊 中间件统计报告
============================================================

💬 对话总结中间件:
   调用次数: 5
   总结次数: 0
   节省 tokens: 0

🛡️ 风险控制中间件:
   调用次数: 5
   高风险决策: 2
   拦截次数: 0
   高风险率: 40%

👨‍💼 人工审批中间件:
   调用次数: 5
   审批请求: 2
   批准次数: 2
   拒绝次数: 0
   批准率: 100%

============================================================
✅ 所有示例运行完成！
============================================================
"""

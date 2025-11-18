"""
Content Blocks 集成示例

展示如何使用 LangChain 1.0 的 content_blocks 功能：
- 推理过程展示（OpenAI o1, DeepSeek R1）
- 引用溯源（Claude Citations, RAG）
- 与中间件系统集成
"""

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

from tradingagents.middleware.base import MiddlewareChain
from tradingagents.middleware.content_blocks import ContentBlocksMiddleware
from tradingagents.middleware.reasoning_handler import ReasoningHandler, ReasoningModelType
from tradingagents.middleware.citations_handler import CitationsHandler

from tradingagents.agents.analysts.market_analyst_v2 import create_market_analyst_node_v2

from tradingagents.utils.logging_manager import get_logger

logger = get_logger('examples.content_blocks')


# ============================================
# 示例 1: OpenAI o1 推理过程展示
# ============================================

def example_1_openai_o1_reasoning():
    """示例 1: 使用 OpenAI o1 展示推理过程"""

    logger.info("=" * 60)
    logger.info("示例 1: OpenAI o1 推理过程")
    logger.info("=" * 60)

    # 创建 OpenAI o1 模型
    # 注意：o1 模型 temperature 必须为 1
    llm = ChatOpenAI(
        model="o1-preview",  # 或 "o1-mini"
        temperature=1
    )

    # 创建推理处理器
    reasoning_handler = ReasoningHandler(
        enable_detailed_logging=True,
        reasoning_max_display=1000
    )

    # 执行推理任务
    logger.info("📝 执行分析任务...")

    prompt = """请深入分析贵州茅台(600519)的投资价值，考虑以下因素：
    1. 行业地位和竞争优势
    2. 财务健康度
    3. 估值水平
    4. 宏观经济环境影响

    请展示你的推理过程。"""

    response = llm.invoke([("user", prompt)])

    # 提取推理过程
    trace = reasoning_handler.extract_reasoning(response)

    if trace:
        logger.info("✅ 成功提取推理过程")

        # 格式化展示
        display_text = reasoning_handler.format_reasoning_display(trace)
        print("\n" + display_text)

        # 分析推理质量
        quality = reasoning_handler.analyze_reasoning_quality(trace)
        logger.info(f"推理质量评分: {quality['quality_score']}/100")
        logger.info(f"  - 有结构化思考: {quality['has_structured_thinking']}")
        logger.info(f"  - 有分析过程: {quality['has_analysis']}")
        logger.info(f"  - 有结论: {quality['has_conclusion']}")

    else:
        logger.warning("⚠️ 未提取到推理过程")

    # 查看统计
    stats = reasoning_handler.get_stats()
    logger.info(f"\n统计信息:")
    logger.info(f"  - 总推理次数: {stats['total_traces']}")
    logger.info(f"  - 总推理 tokens: {stats['total_reasoning_tokens']:,}")
    logger.info(f"  - 平均推理 tokens: {stats['avg_reasoning_tokens']:.0f}")

    return response


# ============================================
# 示例 2: DeepSeek R1 推理过程
# ============================================

def example_2_deepseek_r1_reasoning():
    """示例 2: 使用 DeepSeek R1 展示推理过程"""

    logger.info("=" * 60)
    logger.info("示例 2: DeepSeek R1 推理过程")
    logger.info("=" * 60)

    # 注意：DeepSeek R1 需要配置相应的 API
    # 这里仅作示例，实际使用需要配置 base_url 和 api_key

    try:
        from langchain_community.chat_models import ChatOpenAI as ChatDeepSeek

        llm = ChatDeepSeek(
            model="deepseek-r1",
            base_url="https://api.deepseek.com",  # DeepSeek API endpoint
            # api_key="your_deepseek_api_key",
            temperature=0.7
        )

        reasoning_handler = ReasoningHandler()

        prompt = "分析比亚迪(002594)的新能源汽车业务前景"

        response = llm.invoke([("user", prompt)])

        # 提取推理
        trace = reasoning_handler.extract_reasoning(response, ReasoningModelType.DEEPSEEK_R1)

        if trace:
            display_text = reasoning_handler.format_reasoning_display(trace)
            print("\n" + display_text)

    except Exception as e:
        logger.warning(f"⚠️ DeepSeek R1 示例跳过: {e}")
        logger.info("💡 要使用 DeepSeek R1，请配置 API key")


# ============================================
# 示例 3: Content Blocks 中间件集成
# ============================================

def example_3_content_blocks_middleware():
    """示例 3: 使用 Content Blocks 中间件"""

    logger.info("=" * 60)
    logger.info("示例 3: Content Blocks 中间件")
    logger.info("=" * 60)

    # 创建 LLM
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    # 创建市场分析师节点
    market_analyst_node = create_market_analyst_node_v2(llm)

    # 创建 Content Blocks 中间件
    content_blocks_middleware = ContentBlocksMiddleware(
        enable_reasoning_display=True,
        enable_citations_display=True,
        enable_tool_calls_display=True,
        reasoning_max_length=800
    )

    # 创建中间件链
    chain = MiddlewareChain()
    chain.add(content_blocks_middleware)

    # 应用中间件
    wrapped_analyst = chain.apply(market_analyst_node)

    # 执行分析
    state = {
        "messages": [("user", "分析平安银行(000001)的技术面")],
        "session_id": "example_3",
        "ticker": "000001"
    }

    result = wrapped_analyst(state)

    logger.info("✅ 分析完成")

    # 查看统计
    stats = content_blocks_middleware.get_stats()
    logger.info(f"\nContent Blocks 统计:")
    logger.info(f"  - 推理次数: {stats['reasoning_count']}")
    logger.info(f"  - 引用次数: {stats['citations_count']}")
    logger.info(f"  - 工具调用次数: {stats['tool_calls_count']}")

    return result


# ============================================
# 示例 4: RAG 引用集成
# ============================================

def example_4_rag_citations():
    """示例 4: RAG 应用中的引用"""

    logger.info("=" * 60)
    logger.info("示例 4: RAG 引用")
    logger.info("=" * 60)

    # 创建引用处理器
    citations_handler = CitationsHandler(
        enable_citation_validation=True,
        enable_duplicate_detection=True
    )

    # 模拟 RAG 场景
    # 假设我们从向量数据库检索到相关文档
    source_documents = [
        {
            "page_content": "贵州茅台2023年年报显示，营业收入达到1234.56亿元，同比增长15.2%。净利润为567.89亿元，同比增长18.5%。",
            "metadata": {
                "source": "贵州茅台2023年年报",
                "url": "https://example.com/maotai-2023-report.pdf",
                "doc_type": "financial_report",
                "publish_date": "2024-03-15"
            }
        },
        {
            "page_content": "行业分析报告指出，高端白酒市场在2023年保持稳健增长，贵州茅台市占率达到35%，继续领跑行业。",
            "metadata": {
                "source": "白酒行业分析报告2023",
                "url": "https://example.com/baijiu-report-2023.pdf",
                "doc_type": "industry_report",
                "publish_date": "2024-01-20"
            }
        },
        {
            "page_content": "机构研报显示，贵州茅台当前PE为40倍，PB为12倍，估值处于历史中位数水平。",
            "metadata": {
                "source": "券商研报",
                "url": "https://example.com/maotai-research.pdf",
                "doc_type": "research_report",
                "publish_date": "2024-04-01"
            }
        }
    ]

    # 生成的答案（模拟）
    answer = """根据最新财报数据[1]，贵州茅台2023年表现优异，营收和净利润均实现双位数增长。

从行业地位来看[2]，贵州茅台继续稳居高端白酒市场龙头地位，市占率达到35%。

估值方面[3]，当前PE为40倍，处于合理估值区间。

综合来看，建议"买入"评级。"""

    # 引用的文档ID
    cited_doc_ids = [0, 1, 2]

    # 从 RAG 响应提取引用
    citations = citations_handler.extract_citations_from_rag_response(
        answer,
        source_documents,
        cited_doc_ids
    )

    logger.info(f"✅ 提取到 {len(citations)} 个引用")

    # 格式化展示
    display_text = citations_handler.format_citations_display(citations)
    print("\n" + display_text)

    # 验证引用
    validation = citations_handler.validate_citations(answer, citations)

    logger.info(f"\n引用验证:")
    logger.info(f"  - 有效: {validation['valid']}")
    logger.info(f"  - 总引用数: {validation['total_citations']}")
    logger.info(f"  - 问题数: {validation['issues_count']}")

    if validation['issues']:
        for issue in validation['issues']:
            logger.warning(f"    ⚠️ {issue}")

    # 获取统计
    stats = citations_handler.get_stats()
    logger.info(f"\n统计信息:")
    logger.info(f"  - 总引用数: {stats['total_citations']}")
    logger.info(f"  - 有URL的引用: {stats['citations_with_url']}")
    logger.info(f"  - 按类型: {stats['by_type']}")


# ============================================
# 示例 5: 新闻引用
# ============================================

def example_5_news_citations():
    """示例 5: 从新闻创建引用"""

    logger.info("=" * 60)
    logger.info("示例 5: 新闻引用")
    logger.info("=" * 60)

    citations_handler = CitationsHandler()

    # 模拟新闻数据
    news_articles = [
        {
            "title": "贵州茅台股价创历史新高",
            "summary": "受业绩超预期影响，贵州茅台今日股价上涨5.2%，创历史新高。市场分析认为，高端白酒需求复苏是主要推动力。",
            "url": "https://finance.example.com/news/maotai-new-high",
            "publish_date": "2024-04-10",
            "source": "财经日报",
            "sentiment": "positive"
        },
        {
            "title": "茅台一季度业绩预增公告",
            "summary": "贵州茅台发布一季度业绩预增公告，预计营收增长20%以上，净利润增长25%以上。",
            "url": "https://finance.example.com/news/maotai-q1-preview",
            "publish_date": "2024-04-08",
            "source": "证券时报",
            "sentiment": "positive"
        },
        {
            "title": "茅台经销商大会召开，释放积极信号",
            "summary": "2024年茅台经销商大会在贵州召开，公司管理层表示对全年业绩充满信心。",
            "url": "https://finance.example.com/news/maotai-dealer-meeting",
            "publish_date": "2024-03-25",
            "source": "第一财经",
            "sentiment": "positive"
        }
    ]

    # 创建引用
    citations = citations_handler.extract_citations_from_news(news_articles)

    logger.info(f"✅ 创建了 {len(citations)} 个新闻引用")

    # 格式化展示
    display_text = citations_handler.format_citations_display(citations, max_content_length=150)
    print("\n" + display_text)

    # 统计
    stats = citations_handler.get_stats()
    logger.info(f"\n统计信息:")
    logger.info(f"  - 总引用数: {stats['total_citations']}")
    logger.info(f"  - 新闻引用: {stats['by_type'].get('news_article', 0)}")


# ============================================
# 示例 6: 完整工作流 - 推理 + 引用
# ============================================

def example_6_complete_workflow():
    """示例 6: 完整工作流（推理 + 引用）"""

    logger.info("=" * 60)
    logger.info("示例 6: 完整工作流（推理 + 引用）")
    logger.info("=" * 60)

    # 创建处理器
    reasoning_handler = ReasoningHandler(reasoning_max_display=500)
    citations_handler = CitationsHandler()

    # 创建 LLM（这里用 gpt-4o 模拟，实际应该用 o1）
    llm = ChatOpenAI(model="gpt-4o", temperature=0)

    # 创建中间件
    from tradingagents.middleware.risk_control import RiskControlMiddleware
    from tradingagents.middleware.human_approval import HumanApprovalMiddleware, ApprovalMethod

    content_blocks_middleware = ContentBlocksMiddleware(
        enable_reasoning_display=True,
        enable_citations_display=True
    )

    risk_middleware = RiskControlMiddleware(risk_threshold=0.85)

    approval_middleware = HumanApprovalMiddleware(
        approval_method=ApprovalMethod.AUTO
    )

    # 创建中间件链
    chain = MiddlewareChain()
    chain.add(content_blocks_middleware)  # 1. 提取推理和引用
    chain.add(risk_middleware)            # 2. 风险控制
    chain.add(approval_middleware)        # 3. 人工审批

    # 创建分析师
    market_analyst_node = create_market_analyst_node_v2(llm)

    # 应用中间件
    wrapped_analyst = chain.apply(market_analyst_node)

    # 执行分析
    state = {
        "messages": [("user", "综合分析宁德时代(300750)的投资价值，并提供数据来源")],
        "session_id": "example_6",
        "ticker": "300750"
    }

    logger.info("📝 执行综合分析...")
    result = wrapped_analyst(state)

    logger.info("✅ 分析完成")

    # 汇总统计
    logger.info("\n" + "=" * 60)
    logger.info("📊 完整工作流统计")
    logger.info("=" * 60)

    cb_stats = content_blocks_middleware.get_stats()
    logger.info(f"\nContent Blocks:")
    logger.info(f"  - 推理次数: {cb_stats['reasoning_count']}")
    logger.info(f"  - 引用次数: {cb_stats['citations_count']}")
    logger.info(f"  - 工具调用次数: {cb_stats['tool_calls_count']}")

    risk_stats = risk_middleware.get_stats()
    logger.info(f"\n风险控制:")
    logger.info(f"  - 高风险决策: {risk_stats['high_risk_count']}")
    logger.info(f"  - 拦截次数: {risk_stats['blocked_count']}")

    approval_stats = approval_middleware.get_stats()
    logger.info(f"\n人工审批:")
    logger.info(f"  - 审批请求: {approval_stats['approval_count']}")
    logger.info(f"  - 批准率: {approval_stats['approval_rate']:.0%}")

    logger.info("\n" + "=" * 60)

    return result


# ============================================
# 主函数
# ============================================

def main():
    """运行所有示例"""

    logger.info("\n\n")
    logger.info("🎯 Content Blocks 集成示例")
    logger.info("=" * 60)

    try:
        # 示例 1: OpenAI o1 推理（需要 o1 API access）
        # example_1_openai_o1_reasoning()

        # 示例 2: DeepSeek R1 推理（需要 DeepSeek API）
        # example_2_deepseek_r1_reasoning()

        # 示例 3: Content Blocks 中间件
        example_3_content_blocks_middleware()

        # 示例 4: RAG 引用
        example_4_rag_citations()

        # 示例 5: 新闻引用
        example_5_news_citations()

        # 示例 6: 完整工作流
        example_6_complete_workflow()

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
    # export ANTHROPIC_API_KEY=your_api_key (可选)
    # export DEEPSEEK_API_KEY=your_api_key (可选)

    # 可以选择运行单个示例
    # example_4_rag_citations()

    # 或运行所有示例
    main()


# ============================================
# 输出示例
# ============================================

"""
运行结果示例：

============================================================
🎯 Content Blocks 集成示例
============================================================

============================================================
示例 4: RAG 引用
============================================================
📚 [引用处理器] 从 RAG 提取到 3 个引用
✅ 提取到 3 个引用

---
## 📚 引用来源

**[1] 贵州茅台2023年年报**
📊 *类型: financial_report*
> 贵州茅台2023年年报显示，营业收入达到1234.56亿元，同比增长15.2%。净利润为567.89亿元，同比增长18.5%。
🔗 [https://example.com/maotai-2023-report.pdf](https://example.com/maotai-2023-report.pdf)
*publish_date: 2024-03-15, doc_type: financial_report*

**[2] 白酒行业分析报告2023**
📄 *类型: rag_document*
> 行业分析报告指出，高端白酒市场在2023年保持稳健增长，贵州茅台市占率达到35%，继续领跑行业。
🔗 [https://example.com/baijiu-report-2023.pdf](https://example.com/baijiu-report-2023.pdf)
*publish_date: 2024-01-20, doc_type: industry_report*

**[3] 券商研报**
📄 *类型: rag_document*
> 机构研报显示，贵州茅台当前PE为40倍，PB为12倍，估值处于历史中位数水平。
🔗 [https://example.com/maotai-research.pdf](https://example.com/maotai-research.pdf)
*publish_date: 2024-04-01, doc_type: research_report*

*📖 共引用 3 个来源*
---

引用验证:
  - 有效: True
  - 总引用数: 3
  - 问题数: 0

统计信息:
  - 总引用数: 3
  - 有URL的引用: 3
  - 按类型: {'rag_document': 3}

============================================================
✅ 所有示例运行完成！
============================================================
"""

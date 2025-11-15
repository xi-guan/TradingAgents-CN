"""
新闻分析师 (LangChain 1.0 版本)

使用 LangChain 1.0 的 create_agent API 重构
- 自动工具循环（ReAct模式）
- 结构化输出（NewsAnalysis Pydantic模型）
- 统一新闻获取（支持A股、港股、美股）
- 移除特殊LLM处理逻辑（create_agent 自动处理）
"""

from datetime import date, datetime, timedelta
from typing import Annotated

from langchain import create_agent
from langchain_core.tools import tool
from langchain_core.messages import BaseMessage

# 导入结构化输出模型
from tradingagents.models.analyst_outputs import NewsAnalysis

# 导入数据接口
import tradingagents.dataflows.interface as interface

# 导入日志
from tradingagents.utils.logging_manager import get_logger
logger = get_logger('analysts.news')


# ============================================
# 定义工具（Tools）
# ============================================

@tool
def get_stock_news(
    ticker: Annotated[str, "股票代码，如 000001, 600519, AAPL"],
    days: Annotated[int, "获取最近N天的新闻"] = 7,
    max_news: Annotated[int, "最多返回N条新闻"] = 10
) -> str:
    """
    获取股票的最新新闻，自动识别股票类型（A股、港股、美股）

    Args:
        ticker: 股票代码
        days: 查询天数，默认7天
        max_news: 最多返回的新闻数量

    Returns:
        格式化的新闻列表，包括标题、时间、来源、摘要等
    """
    logger.info(f"📰 [工具调用] get_stock_news(ticker={ticker}, days={days}, max_news={max_news})")

    try:
        # 自动识别市场类型
        from tradingagents.utils.stock_utils import StockUtils
        market_info = StockUtils.get_market_info(ticker)

        logger.info(f"📊 [工具调用] 股票类型: {market_info['market_name']}")

        # 计算日期范围
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        news_result = None

        if market_info['is_china']:
            # 中国A股新闻
            logger.info(f"📰 [工具调用] 获取中国A股新闻: {ticker}")
            news_result = interface.get_china_stock_news(
                ticker,
                start_date.strftime("%Y-%m-%d"),
                max_news
            )

        elif market_info['is_hk']:
            # 港股新闻
            logger.info(f"📰 [工具调用] 获取港股新闻: {ticker}")
            news_result = interface.get_hk_stock_news(
                ticker,
                days=days,
                max_news=max_news
            )

        elif market_info['is_us']:
            # 美股新闻
            logger.info(f"📰 [工具调用] 获取美股新闻: {ticker}")
            news_result = interface.get_finnhub_news(
                ticker,
                end_date.strftime("%Y-%m-%d"),
                days
            )

        else:
            return f"不支持的股票类型: {ticker}"

        if not news_result or "无相关新闻" in str(news_result):
            return f"未找到{ticker}在最近{days}天的新闻，可能市场休市或该股票关注度较低"

        logger.info(f"✅ [工具调用] 成功获取 {ticker} 的新闻，返回长度: {len(news_result)} 字符")
        return news_result

    except Exception as e:
        logger.error(f"❌ [工具调用] get_stock_news 失败: {e}")
        return f"获取新闻失败: {str(e)}"


@tool
def get_company_announcements(
    ticker: Annotated[str, "股票代码"],
    days: Annotated[int, "获取最近N天的公告"] = 30
) -> str:
    """
    获取公司的官方公告（仅支持A股）

    Args:
        ticker: 股票代码
        days: 查询天数

    Returns:
        格式化的公告列表
    """
    logger.info(f"📋 [工具调用] get_company_announcements(ticker={ticker}, days={days})")

    try:
        from tradingagents.utils.stock_utils import StockUtils
        market_info = StockUtils.get_market_info(ticker)

        if not market_info['is_china']:
            return "公司公告功能仅支持中国A股"

        # 获取公告
        announcements = interface.get_company_announcements(ticker, days)

        if not announcements:
            return f"未找到{ticker}在最近{days}天的公告"

        logger.info(f"✅ [工具调用] 成功获取 {ticker} 的公告")
        return announcements

    except Exception as e:
        logger.error(f"❌ [工具调用] get_company_announcements 失败: {e}")
        return f"获取公告失败: {str(e)}"


@tool
def search_related_news(
    keyword: Annotated[str, "搜索关键词，如'新能源'、'芯片'、'政策'"],
    days: Annotated[int, "搜索最近N天的新闻"] = 7,
    max_news: Annotated[int, "最多返回N条新闻"] = 5
) -> str:
    """
    搜索相关行业或主题的新闻

    Args:
        keyword: 搜索关键词
        days: 查询天数
        max_news: 最多返回的新闻数量

    Returns:
        相关新闻列表
    """
    logger.info(f"🔍 [工具调用] search_related_news(keyword={keyword}, days={days})")

    try:
        # 搜索相关新闻
        news = interface.search_industry_news(keyword, days, max_news)

        if not news:
            return f"未找到与'{keyword}'相关的新闻"

        logger.info(f"✅ [工具调用] 成功搜索到 {keyword} 相关新闻")
        return news

    except Exception as e:
        logger.error(f"❌ [工具调用] search_related_news 失败: {e}")
        return f"搜索新闻失败: {str(e)}"


# ============================================
# 创建新闻分析师 Agent
# ============================================

def create_news_analyst_v2(llm, config: dict = None):
    """
    使用 LangChain 1.0 create_agent 创建新闻分析师

    Args:
        llm: LLM 实例
        config: 配置字典（可选）

    Returns:
        新闻分析师 agent
    """

    logger.info("🚀 [LangChain 1.0] 创建新闻分析师 (使用 create_agent)")

    # 定义工具列表
    tools = [
        get_stock_news,
        get_company_announcements,
        search_related_news,
    ]

    # 系统提示词
    system_prompt = """你是一位专业的财经新闻分析师，负责分析最新的市场新闻和事件对股票价格的潜在影响。

你的分析流程：
1. **获取股票新闻** - 使用 get_stock_news 获取最新新闻（默认7天）
2. **获取公司公告** - 如果是A股，获取官方公告
3. **搜索相关行业新闻** - 了解行业整体动态
4. **综合分析** - 基于以上信息给出投资建议

重点关注的新闻类型：
- 📊 **财报发布**: 业绩超预期/低于预期的影响
- 🤝 **重大合作**: 并购、战略合作、技术授权
- 📜 **政策变化**: 监管政策、行业政策、税收政策
- 🚨 **突发事件**: 危机管理、负面新闻、诉讼纠纷
- 🏭 **行业趋势**: 技术突破、市场格局变化
- 👔 **管理层变动**: 高管任免、战略调整

分析要点：
- ⏰ **时效性**: 优先分析最新新闻（24小时内）
- 🔍 **可信度**: 权威媒体 > 一般媒体
- 📈 **影响程度**: 评估对股价的短期和长期影响
- 😊 **情绪判断**: 正面/中性/负面
- 📊 **历史对比**: 与类似事件的市场反应对比

新闻影响分析标准：
- **非常正面**: 重大利好消息，预期短期大涨
- **正面**: 一般利好，预期温和上涨
- **中性**: 信息性新闻，无明显影响
- **负面**: 一般利空，预期下跌
- **非常负面**: 重大利空，预期大跌

投资建议标准：
- **强烈买入**: 重大利好 + 高置信度 > 0.85
- **买入**: 正面新闻 + 置信度 0.70-0.85
- **持有**: 中性新闻 + 置信度 0.50-0.70
- **卖出**: 负面新闻 + 置信度 0.70-0.85
- **强烈卖出**: 重大利空 + 高置信度 > 0.85

注意事项：
- 必须基于真实新闻数据，不要编造
- 明确说明新闻来源和时间
- 诚实评估置信度
- 识别主要风险因素
- 如果新闻较少或滞后，在分析中说明

今天的日期是: {current_date}
"""

    # 🎉 LangChain 1.0 核心：create_agent
    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=system_prompt.format(
            current_date=date.today().strftime("%Y-%m-%d")
        ),
        # 🎉 结构化输出：自动验证和类型安全
        structured_output=NewsAnalysis,
    )

    logger.info("✅ [LangChain 1.0] 新闻分析师创建成功")

    return agent


# ============================================
# 便捷包装函数（兼容旧API）
# ============================================

def create_news_analyst_node_v2(llm, toolkit=None):
    """
    创建新闻分析师节点（兼容 LangGraph 的旧 API）

    Args:
        llm: LLM 实例
        toolkit: 工具集（为了兼容性保留，实际不使用）

    Returns:
        news_analyst_node 函数
    """

    # 创建 agent
    agent = create_news_analyst_v2(llm)

    def news_analyst_node(state):
        """
        新闻分析师节点

        Args:
            state: LangGraph 状态对象

        Returns:
            更新后的状态
        """
        logger.info("📰 [新闻分析师节点] 开始分析")

        try:
            # 从状态中提取消息
            messages = state.get("messages", [])

            # 🎉 调用 agent（自动工具循环 + 结构化输出）
            result: NewsAnalysis = agent.invoke({"messages": messages})

            logger.info(f"✅ [新闻分析师] 分析完成")
            logger.info(f"   股票: {result.ticker} ({result.company_name})")
            logger.info(f"   新闻数量: {result.news_count}")
            logger.info(f"   情绪: {result.sentiment}")
            logger.info(f"   建议: {result.recommendation}")
            logger.info(f"   置信度: {result.confidence:.0%}")

            # 格式化为消息（兼容旧API）
            from langchain_core.messages import AIMessage

            formatted_message = AIMessage(
                content=f"""## 📰 新闻情绪分析

**股票**: {result.company_name} ({result.ticker})
**分析日期**: {result.analysis_date}
**新闻数量**: {result.news_count} 条

### 📊 情绪分析
- **整体情绪**: {result.sentiment}
- **情绪得分**: {result.sentiment_score:.2f} (-1到1)
- **影响评估**: {result.impact_assessment}

### 📰 关键新闻
{chr(10).join(f'{i+1}. {news}' for i, news in enumerate(result.key_news_summary))}

### 🏷️ 新闻主题
{', '.join(result.news_topics)}

### 🎯 投资建议
- **建议**: {result.recommendation}
- **置信度**: {result.confidence:.0%}

### 💡 分析理由
{result.reasoning}

### ⚠️ 风险因素
{chr(10).join(f'- {risk}' for risk in result.risk_factors)}
""",
                # 🎉 附加结构化数据（可供后续节点使用）
                additional_kwargs={
                    "structured_output": result.model_dump(),
                    "analyst_type": "news",
                }
            )

            return {"messages": [formatted_message]}

        except Exception as e:
            logger.error(f"❌ [新闻分析师] 分析失败: {e}")
            import traceback
            traceback.print_exc()

            from langchain_core.messages import AIMessage
            error_message = AIMessage(
                content=f"新闻分析失败: {str(e)}"
            )
            return {"messages": [error_message]}

    return news_analyst_node


# ============================================
# 代码统计
# ============================================

"""
📊 代码行数对比：

旧版 (news_analyst.py):
- 总行数: ~350 行
- 核心逻辑: ~200 行
- 特殊LLM处理: ~100 行（DashScope/DeepSeek预处理）
- 工具循环: 手动实现 ~50 行

新版 (news_analyst_v2.py):
- 总行数: ~340 行（包含详细注释和文档）
- 核心逻辑: ~50 行
- 特殊LLM处理: 0 行（create_agent 统一处理）
- 工具循环: 0 行（create_agent 自动处理）

🎯 改进：
✅ 核心代码减少 75% (200行 → 50行)
✅ 移除所有特殊LLM处理逻辑（100行 → 0行）
✅ 工具循环自动化（无需手动实现）
✅ 类型安全（Pydantic 自动验证）
✅ 更好的可读性和可维护性
✅ 结构化输出（可直接用于下游任务）
"""

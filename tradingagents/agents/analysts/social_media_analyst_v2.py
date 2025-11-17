"""
社交媒体分析师 (LangChain 1.0 版本)

使用 LangChain 1.0 的 create_agent API 重构
- 自动工具循环
- 结构化输出（SocialMediaAnalysis Pydantic模型）
- 分析投资者情绪和讨论热度
"""

from datetime import date
from typing import Annotated

from langchain import create_agent
from langchain_core.tools import tool

from tradingagents.models.analyst_outputs import SocialMediaAnalysis
import tradingagents.dataflows.interface as interface

from tradingagents.utils.logging_manager import get_logger
logger = get_logger('analysts.social_media')


# ============================================
# 工具定义
# ============================================

@tool
def get_reddit_sentiment(
    ticker: Annotated[str, "股票代码，主要支持美股"],
    days: Annotated[int, "获取最近N天的讨论"] = 7
) -> str:
    """获取Reddit上关于该股票的讨论和情绪"""
    logger.info(f"🗣️ [工具调用] get_reddit_sentiment(ticker={ticker})")

    try:
        result = interface.get_reddit_company_news(ticker, days)
        if not result:
            return f"未找到{ticker}在Reddit上的讨论"
        logger.info(f"✅ 成功获取Reddit情绪")
        return result
    except Exception as e:
        logger.error(f"❌ get_reddit_sentiment 失败: {e}")
        return f"获取Reddit情绪失败: {str(e)}"


@tool
def get_chinese_social_sentiment(
    ticker: Annotated[str, "股票代码，支持A股、港股"]
) -> str:
    """获取中国社交媒体（雪球、东方财富股吧等）的情绪分析"""
    logger.info(f"🗣️ [工具调用] get_chinese_social_sentiment(ticker={ticker})")

    try:
        result = interface.get_chinese_social_sentiment(ticker)
        if not result:
            return f"未找到{ticker}在中国社交媒体的讨论"
        logger.info(f"✅ 成功获取中国社交媒体情绪")
        return result
    except Exception as e:
        logger.error(f"❌ get_chinese_social_sentiment 失败: {e}")
        return f"获取中国社交媒体情绪失败: {str(e)}"


@tool
def analyze_discussion_trends(
    ticker: Annotated[str, "股票代码"]
) -> str:
    """分析讨论热度趋势（上升/平稳/下降）"""
    logger.info(f"📈 [工具调用] analyze_discussion_trends(ticker={ticker})")

    try:
        result = interface.get_discussion_trend_analysis(ticker)
        if not result:
            return f"暂无{ticker}的讨论趋势数据"
        logger.info(f"✅ 成功分析讨论趋势")
        return result
    except Exception as e:
        logger.error(f"❌ analyze_discussion_trends 失败: {e}")
        return f"分析讨论趋势失败: {str(e)}"


# ============================================
# 创建社交媒体分析师 Agent
# ============================================

def create_social_media_analyst_v2(llm, config: dict = None):
    """使用 LangChain 1.0 create_agent 创建社交媒体分析师"""

    logger.info("🚀 [LangChain 1.0] 创建社交媒体分析师")

    tools = [
        get_reddit_sentiment,
        get_chinese_social_sentiment,
        analyze_discussion_trends,
    ]

    system_prompt = """你是一位专业的社交媒体情绪分析师，专注于分析投资者在社交平台上的讨论和情绪。

分析流程：
1. 获取社交媒体讨论数据（Reddit、雪球、股吧等）
2. 分析讨论热度和趋势
3. 评估整体情绪（乐观/中性/悲观）
4. 识别关键话题和影响力观点
5. 给出基于社交情绪的投资建议

关注要点：
- 📊 **讨论热度**: 帖子数、评论数、浏览量
- 😊 **情绪倾向**: 正面/中性/负面比例
- 📈 **情绪趋势**: 近期变化方向
- 🔥 **热门话题**: 投资者关注的焦点
- 👥 **影响力用户**: 大V、分析师的观点

情绪评估标准：
- **非常乐观**: 90%+ 正面讨论，热度高
- **乐观**: 60-90% 正面讨论
- **中性**: 正负面基本均衡
- **悲观**: 60-90% 负面讨论
- **非常悲观**: 90%+ 负面讨论，恐慌情绪

投资建议标准：
- **强烈买入**: 情绪极度乐观 + 基本面支撑 (置信度0.7-0.8)
- **买入**: 情绪乐观 + 讨论热度上升 (置信度0.6-0.7)
- **持有**: 情绪中性或分歧较大 (置信度0.4-0.6)
- **卖出**: 情绪悲观 + 负面话题多 (置信度0.6-0.7)
- **强烈卖出**: 恐慌性抛售讨论 (置信度0.7-0.8)

⚠️ 注意：
- 社交情绪可能存在羊群效应和情绪波动
- 不能单独依赖社交情绪做决策
- 需结合基本面和技术面综合判断
- 置信度通常低于技术分析和基本面分析

今天的日期是: {current_date}
"""

    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=system_prompt.format(current_date=date.today().strftime("%Y-%m-%d")),
        structured_output=SocialMediaAnalysis,
    )

    logger.info("✅ 社交媒体分析师创建成功")
    return agent


def create_social_media_analyst_node_v2(llm, toolkit=None):
    """创建社交媒体分析师节点（兼容旧API）"""

    agent = create_social_media_analyst_v2(llm)

    def social_media_analyst_node(state):
        logger.info("🗣️ [社交媒体分析师节点] 开始分析")

        try:
            messages = state.get("messages", [])
            result: SocialMediaAnalysis = agent.invoke({"messages": messages})

            logger.info(f"✅ [社交媒体分析师] 分析完成")
            logger.info(f"   股票: {result.ticker}")
            logger.info(f"   讨论热度: {result.discussion_volume}")
            logger.info(f"   情绪: {result.sentiment}")
            logger.info(f"   建议: {result.recommendation}")

            from langchain_core.messages import AIMessage

            formatted_message = AIMessage(
                content=f"""## 🗣️ 社交媒体情绪分析

**股票**: {result.company_name} ({result.ticker})
**分析日期**: {result.analysis_date}

### 📊 社交媒体指标
- **讨论热度**: {result.discussion_volume}
- **投资者情绪**: {result.sentiment}
- **情绪趋势**: {result.sentiment_trend}

### 🔥 热门话题
{chr(10).join(f'- {topic}' for topic in result.hot_topics)}

### 👥 影响力观点
- **整体倾向**: {result.influencer_sentiment if result.influencer_sentiment else '未分析'}

### 🎯 投资建议
- **建议**: {result.recommendation}
- **置信度**: {result.confidence:.0%}

### 💭 分析理由
{result.reasoning}

### ⚠️ 风险提示
{chr(10).join(f'- {risk}' for risk in result.risk_factors)}
""",
                additional_kwargs={
                    "structured_output": result.model_dump(),
                    "analyst_type": "social_media",
                }
            )

            return {"messages": [formatted_message]}

        except Exception as e:
            logger.error(f"❌ [社交媒体分析师] 分析失败: {e}")
            import traceback
            traceback.print_exc()

            from langchain_core.messages import AIMessage
            return {"messages": [AIMessage(content=f"社交媒体分析失败: {str(e)}")]}

    return social_media_analyst_node

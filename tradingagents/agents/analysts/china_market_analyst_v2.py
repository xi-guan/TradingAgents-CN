"""
中国市场分析师 (LangChain 1.0 版本)

使用 LangChain 1.0 的 create_agent API 重构
- 专注于中国市场特有因素分析
- 结构化输出（ChinaMarketAnalysis Pydantic模型）
- 分析政策影响、资金流向、机构动向
"""

from datetime import date
from typing import Annotated

from langchain import create_agent
from langchain_core.tools import tool

from tradingagents.models.analyst_outputs import ChinaMarketAnalysis
import tradingagents.dataflows.interface as interface

from tradingagents.utils.logging_manager import get_logger
logger = get_logger('analysts.china_market')


# ============================================
# 工具定义
# ============================================

@tool
def get_market_environment(
    date_str: Annotated[str, "日期，格式YYYY-MM-DD"] = None
) -> str:
    """获取当前市场大环境（牛市/震荡市/熊市）"""
    logger.info(f"📊 [工具调用] get_market_environment(date={date_str})")

    try:
        result = interface.get_market_environment_analysis(date_str)
        if not result:
            return "暂无市场环境数据"
        logger.info(f"✅ 成功获取市场环境")
        return result
    except Exception as e:
        logger.error(f"❌ get_market_environment 失败: {e}")
        return f"获取市场环境失败: {str(e)}"


@tool
def get_sector_performance(
    sector: Annotated[str, "行业名称，如'银行'、'新能源'、'半导体'"]
) -> str:
    """获取指定行业的表现情况"""
    logger.info(f"🏭 [工具调用] get_sector_performance(sector={sector})")

    try:
        result = interface.get_sector_performance(sector)
        if not result:
            return f"未找到{sector}行业的表现数据"
        logger.info(f"✅ 成功获取行业表现")
        return result
    except Exception as e:
        logger.error(f"❌ get_sector_performance 失败: {e}")
        return f"获取行业表现失败: {str(e)}"


@tool
def get_policy_impact(
    ticker: Annotated[str, "股票代码"]
) -> str:
    """分析政策对该股票的影响"""
    logger.info(f"📜 [工具调用] get_policy_impact(ticker={ticker})")

    try:
        result = interface.get_policy_impact_analysis(ticker)
        if not result:
            return f"暂无{ticker}的政策影响分析"
        logger.info(f"✅ 成功分析政策影响")
        return result
    except Exception as e:
        logger.error(f"❌ get_policy_impact 失败: {e}")
        return f"分析政策影响失败: {str(e)}"


@tool
def get_capital_flow(
    ticker: Annotated[str, "股票代码"],
    days: Annotated[int, "查询天数"] = 5
) -> str:
    """获取主力资金流向（净流入/净流出）"""
    logger.info(f"💰 [工具调用] get_capital_flow(ticker={ticker}, days={days})")

    try:
        result = interface.get_capital_flow_analysis(ticker, days)
        if not result:
            return f"暂无{ticker}的资金流向数据"
        logger.info(f"✅ 成功获取资金流向")
        return result
    except Exception as e:
        logger.error(f"❌ get_capital_flow 失败: {e}")
        return f"获取资金流向失败: {str(e)}"


@tool
def get_institutional_holdings(
    ticker: Annotated[str, "股票代码"]
) -> str:
    """获取机构持仓变化（QFII、北向资金等）"""
    logger.info(f"👔 [工具调用] get_institutional_holdings(ticker={ticker})")

    try:
        result = interface.get_institutional_holdings(ticker)
        if not result:
            return f"暂无{ticker}的机构持仓数据"
        logger.info(f"✅ 成功获取机构持仓")
        return result
    except Exception as e:
        logger.error(f"❌ get_institutional_holdings 失败: {e}")
        return f"获取机构持仓失败: {str(e)}"


# ============================================
# 创建中国市场分析师 Agent
# ============================================

def create_china_market_analyst_v2(llm, config: dict = None):
    """使用 LangChain 1.0 create_agent 创建中国市场分析师"""

    logger.info("🚀 [LangChain 1.0] 创建中国市场分析师")

    tools = [
        get_market_environment,
        get_sector_performance,
        get_policy_impact,
        get_capital_flow,
        get_institutional_holdings,
    ]

    system_prompt = """你是一位专业的中国市场分析师，深入理解中国资本市场的特点和运行机制。

分析流程：
1. 评估市场大环境（牛市/震荡市/熊市）
2. 分析所属行业表现
3. 评估政策影响
4. 追踪主力资金流向
5. 分析机构投资者动向
6. 综合给出投资建议

中国市场特色因素：
- 🏛️ **政策导向**: 产业政策、监管政策的影响
- 💰 **资金流向**: 北向资金、QFII、国家队动向
- 🏭 **行业轮动**: 政策驱动的行业轮动特征
- 📊 **市场情绪**: A股特有的情绪化和投机性
- 🌍 **国际环境**: 中美关系、全球经济对A股的影响

关键分析维度：

1. **市场环境评估**
   - 牛市: 趋势向上，政策宽松
   - 震荡市: 区间波动，等待方向
   - 熊市: 趋势向下，信心不足

2. **政策影响分析**
   - 重大利好: 产业支持、税收优惠、准入放松
   - 利好: 政策提及、规划纳入
   - 中性: 无明确政策指引
   - 利空: 监管加强、限制政策
   - 重大利空: 行业整顿、准入收紧

3. **资金流向解读**
   - 大幅流入: 连续5天净流入，金额大
   - 流入: 净流入为主
   - 平衡: 流入流出基本平衡
   - 流出: 净流出为主
   - 大幅流出: 连续5天净流出，金额大

4. **机构动向分析**
   - 增持: 北向资金/QFII持续增持
   - 持有: 仓位稳定
   - 减持: 持仓比例下降

投资建议标准：
- **强烈买入**: 政策利好+资金流入+机构增持 (置信度0.75-0.85)
- **买入**: 政策支持+资金面积极 (置信度0.65-0.75)
- **持有**: 政策中性+资金平衡 (置信度0.50-0.65)
- **卖出**: 政策不利+资金流出 (置信度0.65-0.75)
- **强烈卖出**: 政策打压+大幅资金流出 (置信度0.75-0.85)

注意事项：
- 高度关注政策变化和官方表态
- 重视北向资金和机构资金动向
- 考虑行业轮动和市场风格切换
- 警惕市场情绪极端时期

今天的日期是: {current_date}
"""

    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=system_prompt.format(current_date=date.today().strftime("%Y-%m-%d")),
        structured_output=ChinaMarketAnalysis,
    )

    logger.info("✅ 中国市场分析师创建成功")
    return agent


def create_china_market_analyst_node_v2(llm, toolkit=None):
    """创建中国市场分析师节点（兼容旧API）"""

    agent = create_china_market_analyst_v2(llm)

    def china_market_analyst_node(state):
        logger.info("🇨🇳 [中国市场分析师节点] 开始分析")

        try:
            messages = state.get("messages", [])
            result: ChinaMarketAnalysis = agent.invoke({"messages": messages})

            logger.info(f"✅ [中国市场分析师] 分析完成")
            logger.info(f"   股票: {result.ticker}")
            logger.info(f"   市场环境: {result.market_environment}")
            logger.info(f"   行业表现: {result.sector_performance}")
            logger.info(f"   建议: {result.recommendation}")

            from langchain_core.messages import AIMessage

            formatted_message = AIMessage(
                content=f"""## 🇨🇳 中国市场专项分析

**股票**: {result.company_name} ({result.ticker})
**分析日期**: {result.analysis_date}

### 📊 市场环境
- **大盘环境**: {result.market_environment}
- **行业表现**: {result.sector_performance}

### 📜 政策影响
- **影响评估**: {result.policy_impact if result.policy_impact else '未评估'}

### 💰 资金面
- **资金流向**: {result.capital_flow if result.capital_flow else '未分析'}
- **机构动向**: {result.institutional_action if result.institutional_action else '未分析'}

### 🎯 投资建议
- **建议**: {result.recommendation}
- **置信度**: {result.confidence:.0%}

### 🔍 中国市场关键因素
{chr(10).join(f'- {factor}' for factor in result.key_china_factors)}

### 💭 分析理由
{result.reasoning}

### ⚠️ 风险因素
{chr(10).join(f'- {risk}' for risk in result.risk_factors)}
""",
                additional_kwargs={
                    "structured_output": result.model_dump(),
                    "analyst_type": "china_market",
                }
            )

            return {"messages": [formatted_message]}

        except Exception as e:
            logger.error(f"❌ [中国市场分析师] 分析失败: {e}")
            import traceback
            traceback.print_exc()

            from langchain_core.messages import AIMessage
            return {"messages": [AIMessage(content=f"中国市场分析失败: {str(e)}")]}

    return china_market_analyst_node

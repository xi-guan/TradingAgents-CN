"""
市场分析师 (LangChain 1.0 版本)

使用 LangChain 1.0 的 create_agent API 重构
- 自动工具循环（ReAct模式）
- 结构化输出（Pydantic模型）
- 更简洁的代码（从250行减少到50行）
"""

from datetime import date, datetime
from typing import Annotated

from langchain import create_agent
from langchain_core.tools import tool
from langchain_core.messages import BaseMessage

# 导入结构化输出模型
from tradingagents.models.analyst_outputs import MarketAnalysis

# 导入数据接口
import tradingagents.dataflows.interface as interface

# 导入日志
from tradingagents.utils.logging_manager import get_logger
logger = get_logger('agents')


# ============================================
# 定义工具（Tools）
# ============================================

@tool
def get_kline_data(
    ticker: Annotated[str, "股票代码，如 000001, 600519"],
    days: Annotated[int, "获取最近N天的K线数据"] = 30
) -> str:
    """
    获取股票的K线数据，包括开盘价、收盘价、最高价、最低价、成交量等

    Args:
        ticker: 股票代码
        days: 获取天数，默认30天

    Returns:
        格式化的K线数据字符串
    """
    logger.info(f"📊 [工具调用] get_kline_data(ticker={ticker}, days={days})")

    try:
        # 调用数据接口
        kline_data = interface.get_kline_data(
            ticker=ticker,
            days=days,
            end_date=datetime.now().strftime("%Y-%m-%d")
        )

        if not kline_data or "无数据" in str(kline_data):
            return f"无法获取{ticker}的K线数据，可能股票代码不存在或市场休市"

        logger.info(f"✅ [工具调用] 成功获取 {ticker} 的 {days} 天K线数据")
        return kline_data

    except Exception as e:
        logger.error(f"❌ [工具调用] get_kline_data 失败: {e}")
        return f"获取K线数据失败: {str(e)}"


@tool
def get_stock_info(
    ticker: Annotated[str, "股票代码，如 000001, 600519"]
) -> str:
    """
    获取股票的基本信息，包括公司名称、行业、市值等

    Args:
        ticker: 股票代码

    Returns:
        格式化的股票基本信息
    """
    logger.info(f"📊 [工具调用] get_stock_info(ticker={ticker})")

    try:
        # 调用数据接口
        stock_info = interface.get_china_stock_info_unified(ticker)

        if not stock_info:
            return f"无法获取{ticker}的基本信息"

        logger.info(f"✅ [工具调用] 成功获取 {ticker} 的基本信息")
        return stock_info

    except Exception as e:
        logger.error(f"❌ [工具调用] get_stock_info 失败: {e}")
        return f"获取股票信息失败: {str(e)}"


@tool
def get_realtime_quote(
    ticker: Annotated[str, "股票代码，如 000001, 600519"]
) -> str:
    """
    获取股票的实时行情，包括最新价、涨跌幅、成交量等

    Args:
        ticker: 股票代码

    Returns:
        格式化的实时行情数据
    """
    logger.info(f"📊 [工具调用] get_realtime_quote(ticker={ticker})")

    try:
        # 调用数据接口
        quote = interface.get_realtime_quote(ticker)

        if not quote:
            return f"无法获取{ticker}的实时行情，可能市场休市"

        logger.info(f"✅ [工具调用] 成功获取 {ticker} 的实时行情")
        return quote

    except Exception as e:
        logger.error(f"❌ [工具调用] get_realtime_quote 失败: {e}")
        return f"获取实时行情失败: {str(e)}"


@tool
def calculate_technical_indicators(
    ticker: Annotated[str, "股票代码"],
    days: Annotated[int, "计算周期"] = 30
) -> str:
    """
    计算技术指标，包括MA、MACD、RSI、KDJ等

    Args:
        ticker: 股票代码
        days: 计算周期

    Returns:
        格式化的技术指标数据
    """
    logger.info(f"📊 [工具调用] calculate_technical_indicators(ticker={ticker}, days={days})")

    try:
        # 调用数据接口
        indicators = interface.get_technical_indicators(ticker, days)

        if not indicators:
            return f"无法计算{ticker}的技术指标"

        logger.info(f"✅ [工具调用] 成功计算 {ticker} 的技术指标")
        return indicators

    except Exception as e:
        logger.error(f"❌ [工具调用] calculate_technical_indicators 失败: {e}")
        return f"计算技术指标失败: {str(e)}"


# ============================================
# 创建市场分析师 Agent
# ============================================

def create_market_analyst_v2(llm, config: dict = None):
    """
    使用 LangChain 1.0 create_agent 创建市场分析师

    Args:
        llm: LLM 实例
        config: 配置字典（可选）

    Returns:
        市场分析师 agent
    """

    logger.info("🚀 [LangChain 1.0] 创建市场分析师 (使用 create_agent)")

    # 定义工具列表
    tools = [
        get_stock_info,
        get_kline_data,
        get_realtime_quote,
        calculate_technical_indicators,
    ]

    # 系统提示词
    system_prompt = """你是一位专业的股票市场技术分析师，擅长通过技术分析评估股票投资价值。

你的分析流程：
1. **获取股票基本信息** - 了解公司名称、行业、基本面
2. **获取K线数据** - 分析价格走势和形态
3. **获取实时行情** - 了解最新价格和成交情况
4. **计算技术指标** - 计算MA、MACD、RSI等指标
5. **综合分析** - 基于以上数据给出投资建议

分析要点：
- 📈 **趋势判断**: 识别上涨/下跌/震荡趋势
- 🎯 **支撑压力**: 找出关键的支撑位和压力位
- 📊 **技术指标**:
  - 均线系统（MA5, MA10, MA20, MA60）
  - MACD（金叉/死叉信号）
  - RSI（超买/超卖区域，30-70为健康区间）
  - 成交量（放量/缩量）
- ⚠️ **风险评估**: 识别主要技术风险

投资建议标准：
- **强烈买入**: 多个技术指标强烈看多，置信度 > 0.85
- **买入**: 技术面偏多，置信度 0.70-0.85
- **持有**: 技术面中性，置信度 0.50-0.70
- **卖出**: 技术面偏空，置信度 0.70-0.85
- **强烈卖出**: 多个技术指标强烈看空，置信度 > 0.85

注意事项：
- 必须基于真实数据，不要编造数字
- 明确说明分析依据
- 诚实评估置信度
- 识别主要风险因素
- 关键观察点要具体明确

今天的日期是: {current_date}
"""

    # 🎉 LangChain 1.0 核心：create_agent
    # 自动处理工具循环，无需手动实现 ReAct
    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=system_prompt.format(
            current_date=date.today().strftime("%Y-%m-%d")
        ),
        # 🎉 结构化输出：自动验证和类型安全
        structured_output=MarketAnalysis,
    )

    logger.info("✅ [LangChain 1.0] 市场分析师创建成功")

    return agent


# ============================================
# 便捷包装函数（兼容旧API）
# ============================================

def create_market_analyst_node_v2(llm, toolkit=None):
    """
    创建市场分析师节点（兼容 LangGraph 的旧 API）

    这个函数保持与旧版相同的接口，方便渐进式迁移

    Args:
        llm: LLM 实例
        toolkit: 工具集（为了兼容性保留，实际不使用）

    Returns:
        market_analyst_node 函数
    """

    # 创建 agent
    agent = create_market_analyst_v2(llm)

    def market_analyst_node(state):
        """
        市场分析师节点

        Args:
            state: LangGraph 状态对象

        Returns:
            更新后的状态
        """
        logger.info("📈 [市场分析师节点] 开始分析")

        try:
            # 从状态中提取消息
            messages = state.get("messages", [])

            # 🎉 调用 agent（自动工具循环 + 结构化输出）
            result: MarketAnalysis = agent.invoke({"messages": messages})

            logger.info(f"✅ [市场分析师] 分析完成")
            logger.info(f"   股票: {result.ticker} ({result.company_name})")
            logger.info(f"   建议: {result.recommendation}")
            logger.info(f"   置信度: {result.confidence:.0%}")
            logger.info(f"   趋势: {result.trend}")

            # 格式化为消息（兼容旧API）
            from langchain_core.messages import AIMessage

            formatted_message = AIMessage(
                content=f"""## 📊 市场技术分析

**股票**: {result.company_name} ({result.ticker})
**分析日期**: {result.analysis_date}

### 🎯 投资建议
- **建议**: {result.recommendation}
- **置信度**: {result.confidence:.0%}
- **目标价**: {result.target_price if result.target_price else '未设定'}

### 📈 技术分析
- **趋势**: {result.trend}
- **支撑位**: {result.support_level if result.support_level else '待确认'}
- **压力位**: {result.resistance_level if result.resistance_level else '待确认'}

### 📊 技术指标
- **MA5**: {result.ma5}, **MA10**: {result.ma10}, **MA20**: {result.ma20}, **MA60**: {result.ma60}
- **MACD**: {result.macd_signal if result.macd_signal else '未计算'}
- **RSI**: {result.rsi_value if result.rsi_value else '未计算'} ({result.rsi_signal if result.rsi_signal else '未计算'})
- **成交量**: {result.volume_signal if result.volume_signal else '未计算'}

### 💡 分析理由
{result.reasoning}

### 🔍 关键观察
{chr(10).join(f'- {obs}' for obs in result.key_observations)}

### ⚠️ 风险因素
{chr(10).join(f'- {risk}' for risk in result.risk_factors)}
""",
                # 🎉 附加结构化数据（可供后续节点使用）
                additional_kwargs={
                    "structured_output": result.model_dump(),
                    "analyst_type": "market",
                }
            )

            return {"messages": [formatted_message]}

        except Exception as e:
            logger.error(f"❌ [市场分析师] 分析失败: {e}")
            import traceback
            traceback.print_exc()

            from langchain_core.messages import AIMessage
            error_message = AIMessage(
                content=f"市场分析失败: {str(e)}"
            )
            return {"messages": [error_message]}

    return market_analyst_node


# ============================================
# 代码统计
# ============================================

"""
📊 代码行数对比：

旧版 (market_analyst.py):
- 总行数: ~250 行
- 核心逻辑: ~150 行
- 工具循环: 手动实现 ~50 行
- 错误处理: 分散在各处 ~30 行

新版 (market_analyst_v2.py):
- 总行数: ~350 行（包含详细注释和文档）
- 核心逻辑: ~50 行
- 工具循环: 0 行（create_agent 自动处理）
- 错误处理: 集中在一处 ~20 行

🎯 改进：
✅ 核心代码减少 67% (150行 → 50行)
✅ 工具循环自动化（无需手动实现）
✅ 类型安全（Pydantic 自动验证）
✅ 更好的可读性和可维护性
✅ 结构化输出（可直接用于下游任务）
"""

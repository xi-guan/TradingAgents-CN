"""
LangChain 现代化重构示例

对比当前实现与现代化实现的差异
"""

from typing import Literal
from pydantic import BaseModel, Field
from langchain_core.runnables import RunnablePassthrough, RunnableLambda, RunnableWithFallbacks
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

# ============================================
# 示例 1: 结构化输出
# ============================================

# --- 当前方式 (需要手动解析) ---
def current_approach():
    llm = ChatOpenAI(model="gpt-4")
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是股票分析师，请分析 {ticker}"),
        ("user", "给出投资建议，包括：建议、置信度、目标价、理由")
    ])

    chain = prompt | llm
    response = chain.invoke({"ticker": "000001"})

    # ❌ 需要手动解析文本
    text = response.content
    # 容易出错的字符串解析
    if "买入" in text:
        recommendation = "买入"
    elif "卖出" in text:
        recommendation = "卖出"
    else:
        recommendation = "持有"

    # ❌ 没有类型检查，运行时才发现错误
    return {"recommendation": recommendation, "text": text}


# --- 现代化方式 (自动结构化) ---
class StockRecommendation(BaseModel):
    """股票投资建议"""
    recommendation: Literal["买入", "持有", "卖出"] = Field(
        description="投资建议，必须是买入、持有或卖出之一"
    )
    confidence: float = Field(
        ge=0.0, le=1.0,
        description="置信度，范围0-1"
    )
    target_price: float | None = Field(
        default=None,
        description="目标价格（可选）"
    )
    reasoning: str = Field(
        min_length=10,
        description="分析理由，至少10个字符"
    )
    risk_factors: list[str] = Field(
        default_factory=list,
        description="主要风险因素"
    )

def modern_approach():
    llm = ChatOpenAI(model="gpt-4")
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是专业股票分析师"),
        ("user", "分析股票 {ticker} 并给出投资建议")
    ])

    # ✅ 自动结构化输出，带类型验证
    structured_llm = llm.with_structured_output(StockRecommendation)
    chain = prompt | structured_llm

    result: StockRecommendation = chain.invoke({"ticker": "000001"})

    # ✅ IDE 自动补全，编译时类型检查
    print(f"建议: {result.recommendation}")
    print(f"置信度: {result.confidence:.2%}")
    print(f"目标价: {result.target_price}")

    # ✅ 自动验证（confidence 必须在0-1之间）
    return result


# ============================================
# 示例 2: Fallback 容错机制
# ============================================

# --- 当前方式 (手动异常处理) ---
def current_fallback_approach(ticker: str):
    from tradingagents.llm_adapters.deepseek_adapter import ChatDeepSeek
    from tradingagents.llm_adapters.dashscope_openai_adapter import ChatDashScopeOpenAI

    try:
        # 尝试 DeepSeek
        llm = ChatDeepSeek(model="deepseek-chat")
        result = llm.invoke([("user", f"分析 {ticker}")])
        return result
    except Exception as e:
        print(f"DeepSeek 失败: {e}")
        try:
            # 降级到 Qwen
            llm = ChatDashScopeOpenAI(model="qwen-max")
            result = llm.invoke([("user", f"分析 {ticker}")])
            return result
        except Exception as e2:
            print(f"Qwen 也失败: {e2}")
            # 最后降级到 GPT
            llm = ChatOpenAI(model="gpt-4o-mini")
            result = llm.invoke([("user", f"分析 {ticker}")])
            return result


# --- 现代化方式 (自动降级) ---
def modern_fallback_approach(ticker: str):
    from tradingagents.llm_adapters.deepseek_adapter import ChatDeepSeek
    from tradingagents.llm_adapters.dashscope_openai_adapter import ChatDashScopeOpenAI

    # ✅ 声明式定义降级链
    primary = ChatDeepSeek(model="deepseek-chat")
    fallback1 = ChatDashScopeOpenAI(model="qwen-max")
    fallback2 = ChatOpenAI(model="gpt-4o-mini")

    # ✅ 自动重试，自动降级
    resilient_llm = primary.with_fallbacks(
        [fallback1, fallback2],
        exceptions_to_handle=(Exception,)
    )

    prompt = ChatPromptTemplate.from_messages([
        ("user", "分析股票 {ticker}")
    ])

    chain = prompt | resilient_llm.with_structured_output(StockRecommendation)

    # ✅ 一行调用，自动处理所有失败场景
    result = chain.invoke({"ticker": ticker})
    return result


# ============================================
# 示例 3: 批量并发处理
# ============================================

# --- 当前方式 (串行处理) ---
def current_batch_approach(tickers: list[str]):
    results = []
    for ticker in tickers:
        # ❌ 串行执行，10只股票需要10x时间
        result = modern_approach()  # 假设每个5秒
        results.append(result)
    # 总耗时: 5s × 10 = 50秒
    return results


# --- 现代化方式 (自动并发) ---
def modern_batch_approach(tickers: list[str]):
    llm = ChatOpenAI(model="gpt-4")
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是专业股票分析师"),
        ("user", "分析股票 {ticker}")
    ])

    chain = prompt | llm.with_structured_output(StockRecommendation)

    # ✅ 自动并发处理（最大10个并发）
    results = chain.batch(
        [{"ticker": t} for t in tickers],
        config={"max_concurrency": 10}
    )
    # 总耗时: ~5秒（所有并发执行）
    return results


# ============================================
# 示例 4: LCEL 链式组合
# ============================================

# --- 当前方式 (命令式) ---
def current_pipeline(ticker: str):
    # 步骤1: 获取数据
    from tradingagents.dataflows.interface import get_kline_data, get_china_stock_news
    kline = get_kline_data(ticker, days=30)
    news = get_china_stock_news(ticker, days=7)

    # 步骤2: 构造prompt
    prompt_text = f"股票: {ticker}\nK线: {kline}\n新闻: {news}\n请分析"

    # 步骤3: 调用LLM
    llm = ChatOpenAI(model="gpt-4")
    response = llm.invoke([("user", prompt_text)])

    # 步骤4: 手动解析
    # ... 复杂的解析逻辑

    return response


# --- 现代化方式 (声明式 LCEL) ---
def modern_pipeline(ticker: str):
    from tradingagents.dataflows.interface import get_kline_data, get_china_stock_news

    # ✅ 定义可复用的链式组件
    def fetch_data(inputs: dict) -> dict:
        """获取市场数据"""
        ticker = inputs["ticker"]
        return {
            "ticker": ticker,
            "kline": get_kline_data(ticker, days=30),
            "news": get_china_stock_news(ticker, days=7)
        }

    def format_context(data: dict) -> dict:
        """格式化上下文"""
        return {
            "context": f"股票: {data['ticker']}\n"
                      f"K线数据:\n{data['kline']}\n"
                      f"新闻:\n{data['news']}"
        }

    # ✅ 声明式组合（像管道一样）
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是专业股票分析师"),
        ("user", "{context}\n\n请给出投资建议")
    ])

    llm = ChatOpenAI(model="gpt-4")

    # ✅ 完整的分析链
    analysis_chain = (
        RunnablePassthrough()                              # 输入: {"ticker": "000001"}
        | RunnableLambda(fetch_data)                       # -> {"ticker", "kline", "news"}
        | RunnableLambda(format_context)                   # -> {"context": "..."}
        | prompt                                            # -> ChatPromptValue
        | llm.with_structured_output(StockRecommendation)  # -> StockRecommendation
    )

    # ✅ 一行调用，自动支持流式、批处理、重试
    result = analysis_chain.invoke({"ticker": ticker})

    # ✅ 也可以流式处理
    for chunk in analysis_chain.stream({"ticker": ticker}):
        print(chunk)

    # ✅ 也可以批处理
    results = analysis_chain.batch([
        {"ticker": "000001"},
        {"ticker": "600519"},
        {"ticker": "000858"}
    ])

    return result


# ============================================
# 示例 5: LangGraph 子图模块化
# ============================================

from langgraph.graph import StateGraph, END
from typing import TypedDict

class AnalysisState(TypedDict):
    ticker: str
    market_data: dict
    news_data: dict
    technical_analysis: dict
    fundamental_analysis: dict
    final_report: StockRecommendation

# --- 当前方式 (单体图) ---
def current_graph():
    workflow = StateGraph(AnalysisState)

    # ❌ 所有节点都在一个大图里
    workflow.add_node("fetch_market", fetch_market_node)
    workflow.add_node("fetch_news", fetch_news_node)
    workflow.add_node("technical", technical_analysis_node)
    workflow.add_node("fundamental", fundamental_analysis_node)
    workflow.add_node("synthesize", synthesize_node)

    # ❌ 复杂的边连接
    workflow.add_edge("fetch_market", "technical")
    workflow.add_edge("fetch_news", "fundamental")
    workflow.add_conditional_edges("technical", should_continue, {...})
    # ... 大量边定义

    return workflow.compile()


# --- 现代化方式 (子图模块化) ---
def create_data_fetching_subgraph():
    """数据获取子图"""
    graph = StateGraph(AnalysisState)
    graph.add_node("market", fetch_market_node)
    graph.add_node("news", fetch_news_node)
    graph.add_edge("market", "news")
    graph.add_edge("news", END)
    return graph.compile()

def create_analysis_subgraph():
    """分析子图"""
    graph = StateGraph(AnalysisState)
    graph.add_node("technical", technical_analysis_node)
    graph.add_node("fundamental", fundamental_analysis_node)
    graph.add_edge("technical", "fundamental")
    graph.add_edge("fundamental", END)
    return graph.compile()

def modern_graph():
    """✅ 主图组合子图（模块化）"""
    workflow = StateGraph(AnalysisState)

    # ✅ 复用预构建的子图
    workflow.add_node("fetch_data", create_data_fetching_subgraph())
    workflow.add_node("analyze", create_analysis_subgraph())
    workflow.add_node("synthesize", synthesize_node)

    # ✅ 简洁的高层连接
    workflow.add_edge("fetch_data", "analyze")
    workflow.add_edge("analyze", "synthesize")
    workflow.add_edge("synthesize", END)

    return workflow.compile()


# ============================================
# 总结：现代化收益
# ============================================

"""
1. 结构化输出
   - 类型安全：编译时发现错误
   - 自动验证：范围、枚举、必填字段
   - 更好的IDE支持

2. Fallback 机制
   - 可用性：99%+ -> 99.9%+
   - 自动降级：无需手动try-catch
   - 成本优化：优先用便宜模型

3. 批处理并发
   - 性能：10x 提升（10只股票并发）
   - 自动负载均衡
   - 更好的资源利用

4. LCEL 链式组合
   - 可组合性：像乐高积木
   - 自动支持：流式、批处理、重试
   - 易于测试：每个组件独立

5. 子图模块化
   - 代码复用：60% 样板代码减少
   - 更好的抽象：高层次思考
   - 易于维护：模块独立演进

建议优先级：
🔴 P0: 结构化输出 + Fallback （1-2周，收益极高）
🟡 P1: 批处理优化 （1周，性能提升明显）
🟢 P2: LCEL 重构 + 子图模块化 （1-2个月，长期收益）
"""

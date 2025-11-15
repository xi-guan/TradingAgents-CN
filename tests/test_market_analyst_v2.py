"""
测试 LangChain 1.0 版本的市场分析师

运行方式:
    pytest tests/test_market_analyst_v2.py -v
    pytest tests/test_market_analyst_v2.py::test_market_analyst_basic -v
"""

import pytest
from unittest.mock import Mock, patch
from datetime import date

# 导入要测试的模块
from tradingagents.agents.analysts.market_analyst_v2 import (
    create_market_analyst_v2,
    create_market_analyst_node_v2,
    get_kline_data,
    get_stock_info,
)
from tradingagents.models.analyst_outputs import MarketAnalysis


class TestMarketAnalystV2:
    """测试 LangChain 1.0 市场分析师"""

    def test_pydantic_model_validation(self):
        """测试 Pydantic 模型验证"""

        # 测试正确的数据
        valid_data = {
            "ticker": "000001",
            "company_name": "平安银行",
            "analysis_date": "2025-11-15",
            "current_price": 12.50,
            "trend": "温和上涨",
            "recommendation": "买入",
            "confidence": 0.75,
            "reasoning": "技术面显示多头排列，MACD金叉，成交量放大"
        }

        analysis = MarketAnalysis(**valid_data)
        assert analysis.ticker == "000001"
        assert analysis.confidence == 0.75
        assert 0 <= analysis.confidence <= 1

    def test_pydantic_model_validation_fails(self):
        """测试 Pydantic 模型验证失败的情况"""

        # 置信度超出范围
        with pytest.raises(ValueError):
            MarketAnalysis(
                ticker="000001",
                company_name="平安银行",
                analysis_date="2025-11-15",
                trend="温和上涨",
                recommendation="买入",
                confidence=1.5,  # 超出 0-1 范围
                reasoning="测试"
            )

        # 目标价为负数
        with pytest.raises(ValueError):
            MarketAnalysis(
                ticker="000001",
                company_name="平安银行",
                analysis_date="2025-11-15",
                trend="温和上涨",
                recommendation="买入",
                confidence=0.75,
                target_price=-10.0,  # 负数
                reasoning="测试"
            )

    @patch('tradingagents.agents.analysts.market_analyst_v2.interface')
    def test_get_kline_data_tool(self, mock_interface):
        """测试 get_kline_data 工具"""

        # Mock 返回数据
        mock_interface.get_kline_data.return_value = "日期,开盘,收盘,最高,最低,成交量\n2025-11-15,12.5,12.6,12.7,12.4,1000000"

        # 调用工具
        result = get_kline_data.invoke({"ticker": "000001", "days": 30})

        # 验证
        assert "日期" in result
        assert "开盘" in result
        mock_interface.get_kline_data.assert_called_once()

    @patch('tradingagents.agents.analysts.market_analyst_v2.interface')
    def test_get_stock_info_tool(self, mock_interface):
        """测试 get_stock_info 工具"""

        # Mock 返回数据
        mock_interface.get_china_stock_info_unified.return_value = "股票名称: 平安银行\n股票代码: 000001\n行业: 银行"

        # 调用工具
        result = get_stock_info.invoke({"ticker": "000001"})

        # 验证
        assert "平安银行" in result
        assert "000001" in result
        mock_interface.get_china_stock_info_unified.assert_called_once_with("000001")

    @pytest.mark.skip(reason="需要真实的 LLM API key")
    def test_create_market_analyst_integration(self):
        """集成测试：创建并使用市场分析师"""

        from langchain_openai import ChatOpenAI

        # 创建 LLM
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

        # 创建 agent
        agent = create_market_analyst_v2(llm)

        # 调用 agent
        result = agent.invoke({
            "messages": [("user", "分析平安银行(000001)的技术面")]
        })

        # 验证结果类型
        assert isinstance(result, MarketAnalysis)
        assert result.ticker == "000001"
        assert result.recommendation in ["强烈买入", "买入", "持有", "卖出", "强烈卖出"]
        assert 0 <= result.confidence <= 1

    def test_create_market_analyst_node_structure(self):
        """测试 market_analyst_node 的结构"""

        # Mock LLM
        mock_llm = Mock()

        # 创建节点
        node_fn = create_market_analyst_node_v2(mock_llm)

        # 验证返回的是函数
        assert callable(node_fn)

    @pytest.mark.skip(reason="需要真实的 LLM API key")
    def test_market_analyst_node_execution(self):
        """测试 market_analyst_node 的执行"""

        from langchain_openai import ChatOpenAI
        from langchain_core.messages import HumanMessage

        # 创建 LLM
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

        # 创建节点
        node_fn = create_market_analyst_node_v2(llm)

        # 准备状态
        state = {
            "messages": [
                HumanMessage(content="分析平安银行(000001)的技术面")
            ]
        }

        # 执行节点
        result = node_fn(state)

        # 验证结果
        assert "messages" in result
        assert len(result["messages"]) > 0

        message = result["messages"][0]
        assert hasattr(message, "content")
        assert "structured_output" in message.additional_kwargs


class TestToolFunctions:
    """测试工具函数"""

    @patch('tradingagents.agents.analysts.market_analyst_v2.interface')
    def test_get_realtime_quote(self, mock_interface):
        """测试实时行情获取"""
        from tradingagents.agents.analysts.market_analyst_v2 import get_realtime_quote

        mock_interface.get_realtime_quote.return_value = "最新价: 12.50\n涨跌幅: +2.3%"

        result = get_realtime_quote.invoke({"ticker": "000001"})

        assert "最新价" in result
        mock_interface.get_realtime_quote.assert_called_once_with("000001")

    @patch('tradingagents.agents.analysts.market_analyst_v2.interface')
    def test_calculate_technical_indicators(self, mock_interface):
        """测试技术指标计算"""
        from tradingagents.agents.analysts.market_analyst_v2 import calculate_technical_indicators

        mock_interface.get_technical_indicators.return_value = "MA5: 12.30\nMACD: 金叉\nRSI: 58.5"

        result = calculate_technical_indicators.invoke({
            "ticker": "000001",
            "days": 30
        })

        assert "MA5" in result
        mock_interface.get_technical_indicators.assert_called_once()


@pytest.mark.benchmark
class TestPerformance:
    """性能测试"""

    def test_pydantic_validation_performance(self, benchmark):
        """测试 Pydantic 验证性能"""

        data = {
            "ticker": "000001",
            "company_name": "平安银行",
            "analysis_date": "2025-11-15",
            "current_price": 12.50,
            "trend": "温和上涨",
            "recommendation": "买入",
            "confidence": 0.75,
            "reasoning": "技术面显示多头排列"
        }

        # 基准测试：创建 Pydantic 模型
        result = benchmark(MarketAnalysis, **data)

        assert result.ticker == "000001"


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "--tb=short"])

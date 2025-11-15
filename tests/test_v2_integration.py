"""
LangChain 1.0 v2 分析师集成测试

测试 v2 分析师在主工作流中的集成
"""

import pytest
from unittest.mock import Mock, patch
from langchain_core.messages import AIMessage

# 导入 v2 分析师
from tradingagents.agents.analysts.market_analyst_v2 import create_market_analyst_node_v2
from tradingagents.agents.analysts.news_analyst_v2 import create_news_analyst_node_v2
from tradingagents.agents.analysts.fundamentals_analyst_v2 import create_fundamentals_analyst_node_v2
from tradingagents.agents.analysts.social_media_analyst_v2 import create_social_media_analyst_node_v2

# 导入中间件
from tradingagents.middleware import (
    MiddlewareChain,
    RiskControlMiddleware,
    ContentBlocksMiddleware
)


class TestV2AnalystIntegration:
    """测试 v2 分析师集成"""

    @pytest.fixture
    def mock_llm(self):
        """创建模拟的 LLM"""
        llm = Mock()

        # 模拟 LLM 响应
        mock_response = Mock()
        mock_response.ticker = "000001"
        mock_response.company_name = "平安银行"
        mock_response.recommendation = "买入"
        mock_response.confidence = 0.75
        mock_response.trend = "温和上涨"
        mock_response.reasoning = "技术面良好"
        mock_response.model_dump.return_value = {
            "ticker": "000001",
            "company_name": "平安银行",
            "recommendation": "买入",
            "confidence": 0.75
        }

        llm.invoke.return_value = mock_response

        return llm

    @pytest.fixture
    def sample_state(self):
        """创建示例状态"""
        return {
            "messages": [
                ("user", "分析平安银行(000001)的投资价值")
            ],
            "company_of_interest": "平安银行",
            "ticker": "000001",
            "trade_date": "2024-01-15"
        }

    def test_market_analyst_v2_node(self, mock_llm, sample_state):
        """测试市场分析师 v2 节点"""
        # 创建节点
        node = create_market_analyst_node_v2(mock_llm)

        # 执行节点
        result = node(sample_state)

        # 验证结果
        assert "messages" in result
        assert len(result["messages"]) > 0
        assert isinstance(result["messages"][0], AIMessage)

        # 验证 structured_output
        message = result["messages"][0]
        assert "structured_output" in message.additional_kwargs
        assert message.additional_kwargs["analyst_type"] == "market"

    def test_news_analyst_v2_node(self, mock_llm, sample_state):
        """测试新闻分析师 v2 节点"""
        # 创建节点
        node = create_news_analyst_node_v2(mock_llm)

        # 执行节点
        result = node(sample_state)

        # 验证结果
        assert "messages" in result
        assert len(result["messages"]) > 0

    def test_fundamentals_analyst_v2_node(self, mock_llm, sample_state):
        """测试基本面分析师 v2 节点"""
        # 创建节点
        node = create_fundamentals_analyst_node_v2(mock_llm)

        # 执行节点
        result = node(sample_state)

        # 验证结果
        assert "messages" in result
        assert len(result["messages"]) > 0

    def test_social_media_analyst_v2_node(self, mock_llm, sample_state):
        """测试社交媒体分析师 v2 节点"""
        # 创建节点
        node = create_social_media_analyst_node_v2(mock_llm)

        # 执行节点
        result = node(sample_state)

        # 验证结果
        assert "messages" in result
        assert len(result["messages"]) > 0

    def test_middleware_integration(self, mock_llm, sample_state):
        """测试中间件集成"""
        # 创建节点
        node = create_market_analyst_node_v2(mock_llm)

        # 创建中间件链
        chain = MiddlewareChain()
        chain.add(RiskControlMiddleware(
            risk_threshold=0.85,
            block_high_risk=False
        ))
        chain.add(ContentBlocksMiddleware(
            enable_reasoning_display=True,
            enable_citations_display=True
        ))

        # 应用中间件
        wrapped_node = chain.apply(node)

        # 执行包装后的节点
        result = wrapped_node(sample_state)

        # 验证结果
        assert "messages" in result
        assert len(result["messages"]) > 0

    def test_state_compatibility(self, mock_llm, sample_state):
        """测试 state 兼容性"""
        # 创建 v2 节点
        node = create_market_analyst_node_v2(mock_llm)

        # 执行节点
        result = node(sample_state)

        # 验证输出格式与 v1 兼容
        assert isinstance(result, dict)
        assert "messages" in result
        assert isinstance(result["messages"], list)

        # 验证可以继续传递给下一个节点
        next_state = {**sample_state, **result}
        assert "messages" in next_state
        assert "company_of_interest" in next_state

    def test_structured_output_validation(self, mock_llm, sample_state):
        """测试结构化输出验证"""
        # 创建节点
        node = create_market_analyst_node_v2(mock_llm)

        # 执行节点
        result = node(sample_state)

        # 提取 structured_output
        message = result["messages"][0]
        structured_data = message.additional_kwargs.get("structured_output")

        # 验证必需字段
        assert structured_data is not None
        assert "ticker" in structured_data
        assert "company_name" in structured_data
        assert "recommendation" in structured_data
        assert "confidence" in structured_data

    def test_error_handling(self, mock_llm, sample_state):
        """测试错误处理"""
        # 模拟 LLM 错误
        mock_llm.invoke.side_effect = Exception("LLM Error")

        # 创建节点
        node = create_market_analyst_node_v2(mock_llm)

        # 执行节点（不应崩溃）
        result = node(sample_state)

        # 验证返回错误消息
        assert "messages" in result
        assert len(result["messages"]) > 0
        assert "失败" in result["messages"][0].content or "错误" in result["messages"][0].content


class TestMiddlewareWrapper:
    """测试中间件包装器"""

    def test_middleware_chain_apply(self):
        """测试中间件链应用"""
        # 创建简单的节点函数
        def simple_node(state):
            return {"messages": [AIMessage(content="test")]}

        # 创建中间件链
        chain = MiddlewareChain()
        chain.add(RiskControlMiddleware(
            risk_threshold=0.85,
            block_high_risk=False
        ))

        # 应用中间件
        wrapped_node = chain.apply(simple_node)

        # 执行
        state = {"messages": []}
        result = wrapped_node(state)

        # 验证
        assert "messages" in result

    def test_middleware_disabled(self):
        """测试禁用中间件"""
        def simple_node(state):
            return {"messages": [AIMessage(content="test")]}

        # 创建中间件
        middleware = RiskControlMiddleware()

        # 禁用
        middleware.disable()

        # 创建链
        chain = MiddlewareChain()
        chain.add(middleware)

        # 应用
        wrapped_node = chain.apply(simple_node)

        # 执行（应该跳过中间件）
        state = {"messages": []}
        result = wrapped_node(state)

        # 验证
        assert "messages" in result

    def test_middleware_stats(self):
        """测试中间件统计"""
        # 创建中间件
        risk_middleware = RiskControlMiddleware(
            risk_threshold=0.85,
            block_high_risk=False
        )

        # 创建节点
        def node_with_high_risk(state):
            return {
                "messages": [
                    AIMessage(
                        content="强烈买入",
                        additional_kwargs={
                            "structured_output": {
                                "recommendation": "强烈买入",
                                "confidence": 0.95
                            }
                        }
                    )
                ]
            }

        # 应用中间件
        chain = MiddlewareChain()
        chain.add(risk_middleware)
        wrapped_node = chain.apply(node_with_high_risk)

        # 执行多次
        for _ in range(3):
            wrapped_node({"messages": []})

        # 获取统计
        stats = risk_middleware.get_stats()

        # 验证
        assert stats["call_count"] == 3
        assert stats["high_risk_count"] >= 0


# ============================================
# 集成测试
# ============================================

class TestEndToEndIntegration:
    """端到端集成测试"""

    @pytest.mark.integration
    def test_full_workflow_with_v2(self):
        """测试完整工作流（使用 v2 分析师）"""
        # 注意：这个测试需要真实的 LLM，标记为 integration 测试
        pytest.skip("需要真实的 LLM API key，跳过")

    @pytest.mark.integration
    def test_performance_comparison(self):
        """性能对比测试（v1 vs v2）"""
        # 注意：这个测试需要真实的 LLM，标记为 integration 测试
        pytest.skip("需要真实的 LLM API key，跳过")


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "-s"])

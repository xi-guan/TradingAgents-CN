"""
风险控制中间件

在分析过程中自动检测高风险决策并记录/拦截
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from tradingagents.middleware.base import BaseMiddleware, create_event, save_event_to_db
from tradingagents.utils.logging_manager import get_logger

logger = get_logger('middleware.risk_control')


class RiskControlMiddleware(BaseMiddleware):
    """
    风险控制中间件

    功能：
    1. 检测高风险决策（强烈买入/强烈卖出）
    2. 评估置信度是否合理
    3. 记录所有风险决策到数据库
    4. 可选：拦截超高风险决策
    """

    def __init__(
        self,
        risk_threshold: float = 0.85,
        block_high_risk: bool = False,
        alert_channels: List[str] = None,
        db_connection = None
    ):
        """
        初始化风险控制中间件

        Args:
            risk_threshold: 风险阈值（置信度 > 此值视为高风险）
            block_high_risk: 是否拦截高风险决策
            alert_channels: 告警渠道列表（email, sms, webhook等）
            db_connection: 数据库连接
        """
        super().__init__(name="RiskControlMiddleware")

        self.risk_threshold = risk_threshold
        self.block_high_risk = block_high_risk
        self.alert_channels = alert_channels or []
        self.db_connection = db_connection

        self.high_risk_count = 0
        self.blocked_count = 0

        logger.info(f"🛡️ [风险控制] 初始化")
        logger.info(f"   - 风险阈值: {risk_threshold}")
        logger.info(f"   - 拦截高风险: {block_high_risk}")
        logger.info(f"   - 告警渠道: {alert_channels}")

    def after_call(self, input_state: Dict[str, Any], output_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析完成后检查风险

        Args:
            input_state: 输入状态
            output_state: 输出状态（包含分析结果）

        Returns:
            处理后的输出状态
        """
        logger.debug(f"🔍 [风险控制] 开始风险检查")

        # 提取分析结果
        messages = output_state.get("messages", [])
        if not messages:
            return output_state

        # 检查最新消息中的结构化输出
        latest_message = messages[-1]
        if not hasattr(latest_message, 'additional_kwargs'):
            return output_state

        structured_output = latest_message.additional_kwargs.get('structured_output')
        if not structured_output:
            return output_state

        # 执行风险检查
        risk_level = self._assess_risk(structured_output)

        if risk_level == "HIGH":
            self.high_risk_count += 1
            logger.warning(f"⚠️ [风险控制] 检测到高风险决策")

            # 记录事件
            self._log_risk_event(input_state, structured_output, risk_level)

            # 发送告警
            self._send_alert(structured_output, risk_level)

            # 如果配置了拦截，则阻止执行
            if self.block_high_risk:
                self.blocked_count += 1
                logger.error(f"🚫 [风险控制] 拦截高风险决策")

                # 修改输出，添加拦截信息
                from langchain_core.messages import AIMessage
                block_message = AIMessage(
                    content=f"""## 🚫 高风险决策已被拦截

**原因**: 决策风险超过阈值

**风险评估**:
- 风险等级: {risk_level}
- 投资建议: {structured_output.get('recommendation', 'N/A')}
- 置信度: {structured_output.get('confidence', 0):.0%}

**风险控制策略**:
- 风险阈值: {self.risk_threshold}
- 当前配置: 拦截模式

**建议**:
1. 仔细审查分析理由
2. 与其他分析师结果对比
3. 降低交易仓位
4. 联系风险管理团队

此决策需要人工审批后才能执行。
"""
                )

                output_state["messages"] = messages[:-1] + [block_message]
                output_state["risk_blocked"] = True

        elif risk_level == "MEDIUM":
            logger.info(f"ℹ️ [风险控制] 中等风险决策，予以记录")
            self._log_risk_event(input_state, structured_output, risk_level)

        else:
            logger.debug(f"✅ [风险控制] 低风险决策，无需处理")

        return output_state

    def _assess_risk(self, analysis_result: Dict[str, Any]) -> str:
        """
        评估风险等级

        Args:
            analysis_result: 分析结果（结构化输出）

        Returns:
            风险等级: LOW, MEDIUM, HIGH
        """
        recommendation = analysis_result.get('recommendation', '')
        confidence = analysis_result.get('confidence', 0)

        # 规则 1: 强烈买入/强烈卖出 + 高置信度 = 高风险
        if recommendation in ['强烈买入', '强烈卖出', 'STRONG_BUY', 'STRONG_SELL']:
            if confidence >= self.risk_threshold:
                return "HIGH"
            elif confidence >= 0.70:
                return "MEDIUM"

        # 规则 2: 一般买入/卖出 + 极高置信度 = 中等风险
        if recommendation in ['买入', '卖出', 'BUY', 'SELL']:
            if confidence >= 0.90:
                return "MEDIUM"

        # 规则 3: 持有或低置信度 = 低风险
        return "LOW"

    def _log_risk_event(
        self,
        input_state: Dict[str, Any],
        analysis_result: Dict[str, Any],
        risk_level: str
    ):
        """
        记录风险事件到数据库

        Args:
            input_state: 输入状态
            analysis_result: 分析结果
            risk_level: 风险等级
        """
        event = create_event(
            middleware_name=self.name,
            event_type="risk_detected",
            ticker=analysis_result.get('ticker'),
            agent_name=analysis_result.get('analyst_type', 'unknown'),
            session_id=input_state.get('session_id'),
            output_data={
                "risk_level": risk_level,
                "recommendation": analysis_result.get('recommendation'),
                "confidence": analysis_result.get('confidence'),
                "reasoning": analysis_result.get('reasoning', '')[:200]  # 截取前200字符
            },
            metadata={
                "risk_threshold": self.risk_threshold,
                "blocked": self.block_high_risk and risk_level == "HIGH"
            }
        )

        save_event_to_db(event, self.db_connection)

        logger.info(f"📝 [风险控制] 风险事件已记录: {event.event_id}")

    def _send_alert(self, analysis_result: Dict[str, Any], risk_level: str):
        """
        发送风险告警

        Args:
            analysis_result: 分析结果
            risk_level: 风险等级
        """
        if not self.alert_channels:
            return

        alert_message = f"""
🚨 高风险决策告警

股票: {analysis_result.get('ticker')} ({analysis_result.get('company_name', 'N/A')})
风险等级: {risk_level}
投资建议: {analysis_result.get('recommendation')}
置信度: {analysis_result.get('confidence', 0):.0%}

时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

        for channel in self.alert_channels:
            try:
                if channel == 'email':
                    self._send_email_alert(alert_message)
                elif channel == 'sms':
                    self._send_sms_alert(alert_message)
                elif channel == 'webhook':
                    self._send_webhook_alert(analysis_result, risk_level)
                elif channel == 'log':
                    logger.warning(f"⚠️ [告警] {alert_message}")
            except Exception as e:
                logger.error(f"❌ [风险控制] 发送告警失败 ({channel}): {e}")

    def _send_email_alert(self, message: str):
        """发送邮件告警"""
        # TODO: 实现邮件发送逻辑
        logger.info(f"📧 [风险控制] 发送邮件告警")

    def _send_sms_alert(self, message: str):
        """发送短信告警"""
        # TODO: 实现短信发送逻辑
        logger.info(f"📱 [风险控制] 发送短信告警")

    def _send_webhook_alert(self, analysis_result: Dict, risk_level: str):
        """发送Webhook告警"""
        # TODO: 实现Webhook发送逻辑
        logger.info(f"🔗 [风险控制] 发送Webhook告警")

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        base_stats = super().get_stats()
        base_stats.update({
            "high_risk_count": self.high_risk_count,
            "blocked_count": self.blocked_count,
            "high_risk_rate": self.high_risk_count / self.call_count if self.call_count > 0 else 0,
            "block_rate": self.blocked_count / self.high_risk_count if self.high_risk_count > 0 else 0
        })
        return base_stats


# ============================================
# 使用示例
# ============================================

"""
from tradingagents.middleware.risk_control import RiskControlMiddleware
from tradingagents.middleware.base import MiddlewareChain

# 创建风险控制中间件
risk_middleware = RiskControlMiddleware(
    risk_threshold=0.85,              # 置信度 > 85% 视为高风险
    block_high_risk=True,             # 拦截高风险决策
    alert_channels=['log', 'email'], # 告警渠道
)

# 创建中间件链
chain = MiddlewareChain()
chain.add(risk_middleware)

# 应用到agent
wrapped_agent = chain.apply(original_agent_fn)

# 执行分析
result = wrapped_agent(state)

# 查看统计
stats = risk_middleware.get_stats()
print(f"高风险决策数: {stats['high_risk_count']}")
print(f"拦截数: {stats['blocked_count']}")
"""

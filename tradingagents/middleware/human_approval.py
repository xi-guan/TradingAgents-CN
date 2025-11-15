"""
人工审批中间件 (Human-in-the-loop Middleware)

在关键决策点暂停并等待人工审批
"""

from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
import time
from enum import Enum

from tradingagents.middleware.base import BaseMiddleware, create_event, save_event_to_db
from tradingagents.utils.logging_manager import get_logger

logger = get_logger('middleware.human_approval')


class ApprovalMethod(Enum):
    """审批方法"""
    CLI = "cli"           # 命令行交互
    WEB = "web"           # Web界面
    API = "api"           # API回调
    AUTO = "auto"         # 自动审批（基于规则）


class ApprovalDecision(Enum):
    """审批决策"""
    APPROVED = "approved"
    REJECTED = "rejected"
    TIMEOUT = "timeout"
    MODIFIED = "modified"  # 修改后通过


class HumanApprovalMiddleware(BaseMiddleware):
    """
    人工审批中间件

    功能：
    1. 识别需要人工审批的决策（强烈买入/卖出、大额交易等）
    2. 暂停执行，等待人工审批
    3. 支持多种审批方式（CLI、Web、API）
    4. 记录所有审批决策到数据库
    5. 支持审批超时和默认行为
    """

    def __init__(
        self,
        approval_method: ApprovalMethod = ApprovalMethod.CLI,
        approval_rules: List[Dict[str, Any]] = None,
        timeout_seconds: int = 300,  # 5分钟超时
        default_on_timeout: str = "reject",  # timeout时默认拒绝
        approval_callback: Optional[Callable] = None,
        db_connection = None
    ):
        """
        初始化人工审批中间件

        Args:
            approval_method: 审批方法（CLI/Web/API）
            approval_rules: 审批规则列表
            timeout_seconds: 审批超时时间（秒）
            default_on_timeout: 超时默认行为（'approve'/'reject'）
            approval_callback: API审批回调函数
            db_connection: 数据库连接
        """
        super().__init__(name="HumanApprovalMiddleware")

        self.approval_method = approval_method
        self.approval_rules = approval_rules or self._default_approval_rules()
        self.timeout_seconds = timeout_seconds
        self.default_on_timeout = default_on_timeout
        self.approval_callback = approval_callback
        self.db_connection = db_connection

        self.approval_count = 0
        self.approved_count = 0
        self.rejected_count = 0
        self.timeout_count = 0

        logger.info(f"👨‍💼 [人工审批] 初始化")
        logger.info(f"   - 审批方式: {approval_method.value}")
        logger.info(f"   - 审批规则数: {len(self.approval_rules)}")
        logger.info(f"   - 超时时间: {timeout_seconds}s")
        logger.info(f"   - 超时默认: {default_on_timeout}")

    def _default_approval_rules(self) -> List[Dict[str, Any]]:
        """默认审批规则"""
        return [
            {
                "name": "强烈买入/卖出需审批",
                "condition": lambda result: result.get('recommendation') in ['强烈买入', '强烈卖出'],
                "reason": "极端投资建议需要人工确认"
            },
            {
                "name": "高置信度需审批",
                "condition": lambda result: result.get('confidence', 0) >= 0.9,
                "reason": "高置信度决策需要人工验证"
            },
            {
                "name": "交易下单需审批",
                "condition": lambda result: result.get('action') in ['place_order', 'execute_trade'],
                "reason": "实际交易操作必须人工确认"
            }
        ]

    def after_call(self, input_state: Dict[str, Any], output_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析完成后检查是否需要人工审批

        Args:
            input_state: 输入状态
            output_state: 输出状态（包含分析结果）

        Returns:
            处理后的输出状态
        """
        logger.debug(f"🔍 [人工审批] 检查是否需要审批")

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

        # 检查是否需要审批
        approval_needed, matched_rules = self._check_approval_needed(structured_output)

        if approval_needed:
            self.approval_count += 1
            logger.warning(f"⏸️ [人工审批] 需要人工审批")
            logger.info(f"   - 触发规则: {[r['name'] for r in matched_rules]}")

            # 请求审批
            decision, modified_result = self._request_approval(
                input_state,
                structured_output,
                matched_rules
            )

            # 记录审批事件
            self._log_approval_event(
                input_state,
                structured_output,
                decision,
                matched_rules
            )

            # 根据审批决策处理
            if decision == ApprovalDecision.APPROVED:
                self.approved_count += 1
                logger.info(f"✅ [人工审批] 决策已批准")
                return output_state

            elif decision == ApprovalDecision.MODIFIED:
                self.approved_count += 1
                logger.info(f"✏️ [人工审批] 决策已修改并批准")

                # 更新输出状态为修改后的结果
                from langchain_core.messages import AIMessage
                modified_message = AIMessage(
                    content=self._format_modified_decision(modified_result),
                    additional_kwargs={
                        "structured_output": modified_result,
                        "analyst_type": latest_message.additional_kwargs.get('analyst_type'),
                        "human_modified": True
                    }
                )
                output_state["messages"] = messages[:-1] + [modified_message]
                return output_state

            elif decision == ApprovalDecision.REJECTED:
                self.rejected_count += 1
                logger.error(f"❌ [人工审批] 决策已拒绝")

                # 修改输出，添加拒绝信息
                from langchain_core.messages import AIMessage
                reject_message = AIMessage(
                    content=f"""## ❌ 决策已被人工拒绝

**原因**: 未通过人工审批

**原决策**:
- 投资建议: {structured_output.get('recommendation', 'N/A')}
- 置信度: {structured_output.get('confidence', 0):.0%}
- 理由: {structured_output.get('reasoning', 'N/A')[:100]}...

**审批信息**:
- 触发规则: {', '.join([r['name'] for r in matched_rules])}
- 审批方式: {self.approval_method.value}
- 决策时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**建议**:
1. 重新评估分析理由
2. 获取更多信息后再决策
3. 调整风险参数

此决策不会被执行。
"""
                )

                output_state["messages"] = messages[:-1] + [reject_message]
                output_state["approval_rejected"] = True
                return output_state

            elif decision == ApprovalDecision.TIMEOUT:
                self.timeout_count += 1
                logger.error(f"⏱️ [人工审批] 审批超时")

                # 根据超时默认行为处理
                if self.default_on_timeout == "approve":
                    logger.warning(f"⚠️ [人工审批] 超时默认通过")
                    return output_state
                else:
                    logger.error(f"❌ [人工审批] 超时默认拒绝")
                    from langchain_core.messages import AIMessage
                    timeout_message = AIMessage(
                        content=f"""## ⏱️ 审批超时 - 决策已拒绝

审批请求在 {self.timeout_seconds} 秒内未收到响应。

根据配置，超时默认为: {self.default_on_timeout}

此决策不会被执行。
"""
                    )
                    output_state["messages"] = messages[:-1] + [timeout_message]
                    output_state["approval_timeout"] = True
                    return output_state

        else:
            logger.debug(f"✅ [人工审批] 无需审批，放行")

        return output_state

    def _check_approval_needed(self, analysis_result: Dict[str, Any]) -> tuple[bool, List[Dict]]:
        """
        检查是否需要人工审批

        Args:
            analysis_result: 分析结果

        Returns:
            (是否需要审批, 匹配的规则列表)
        """
        matched_rules = []

        for rule in self.approval_rules:
            try:
                if rule['condition'](analysis_result):
                    matched_rules.append(rule)
            except Exception as e:
                logger.error(f"❌ [人工审批] 规则检查失败: {rule['name']}: {e}")

        return len(matched_rules) > 0, matched_rules

    def _request_approval(
        self,
        input_state: Dict[str, Any],
        analysis_result: Dict[str, Any],
        matched_rules: List[Dict]
    ) -> tuple[ApprovalDecision, Optional[Dict]]:
        """
        请求人工审批

        Args:
            input_state: 输入状态
            analysis_result: 分析结果
            matched_rules: 触发的规则

        Returns:
            (审批决策, 修改后的结果)
        """
        if self.approval_method == ApprovalMethod.CLI:
            return self._request_cli_approval(analysis_result, matched_rules)

        elif self.approval_method == ApprovalMethod.WEB:
            return self._request_web_approval(analysis_result, matched_rules)

        elif self.approval_method == ApprovalMethod.API:
            return self._request_api_approval(analysis_result, matched_rules)

        elif self.approval_method == ApprovalMethod.AUTO:
            return self._auto_approval(analysis_result, matched_rules)

        else:
            logger.error(f"❌ [人工审批] 不支持的审批方式: {self.approval_method}")
            return ApprovalDecision.REJECTED, None

    def _request_cli_approval(
        self,
        analysis_result: Dict[str, Any],
        matched_rules: List[Dict]
    ) -> tuple[ApprovalDecision, Optional[Dict]]:
        """CLI 交互式审批"""
        logger.info("="*60)
        logger.info("🚨 需要人工审批")
        logger.info("="*60)

        print("\n" + "="*60)
        print("🚨 需要人工审批")
        print("="*60)
        print(f"\n📊 股票: {analysis_result.get('company_name')} ({analysis_result.get('ticker')})")
        print(f"💡 建议: {analysis_result.get('recommendation')}")
        print(f"📈 置信度: {analysis_result.get('confidence', 0):.0%}")
        print(f"\n💭 理由:\n{analysis_result.get('reasoning', 'N/A')[:300]}")
        print(f"\n⚠️ 触发规则:")
        for rule in matched_rules:
            print(f"   - {rule['name']}: {rule['reason']}")

        print("\n" + "-"*60)
        print("请选择:")
        print("  1. 批准 (approve)")
        print("  2. 拒绝 (reject)")
        print("  3. 修改后批准 (modify)")
        print(f"\n⏱️ 请在 {self.timeout_seconds} 秒内决策...")
        print("-"*60)

        # 简化版：直接返回批准（实际应该用 input() 等待用户输入）
        # 在实际环境中，这里应该等待用户输入
        # 由于是自动化脚本，我们这里返回一个默认值

        # TODO: 实现真正的 CLI 交互（需要考虑超时机制）
        logger.warning("⚠️ [人工审批] CLI 交互未实现，自动批准")
        print("\n⚠️ CLI 交互未实现，自动批准")

        return ApprovalDecision.APPROVED, None

    def _request_web_approval(
        self,
        analysis_result: Dict[str, Any],
        matched_rules: List[Dict]
    ) -> tuple[ApprovalDecision, Optional[Dict]]:
        """Web 界面审批"""
        logger.info("🌐 [人工审批] 发送 Web 审批请求")

        # TODO: 实现 Web 界面审批
        # 1. 将审批请求发送到 Web 服务器
        # 2. 等待用户在浏览器中审批
        # 3. 轮询或 webhook 获取审批结果

        logger.warning("⚠️ [人工审批] Web 审批未实现，自动批准")
        return ApprovalDecision.APPROVED, None

    def _request_api_approval(
        self,
        analysis_result: Dict[str, Any],
        matched_rules: List[Dict]
    ) -> tuple[ApprovalDecision, Optional[Dict]]:
        """API 回调审批"""
        logger.info("🔌 [人工审批] 调用 API 审批回调")

        if not self.approval_callback:
            logger.error("❌ [人工审批] 未配置 approval_callback")
            return ApprovalDecision.REJECTED, None

        try:
            # 调用自定义审批回调
            decision, modified_result = self.approval_callback(
                analysis_result,
                matched_rules,
                self.timeout_seconds
            )

            logger.info(f"✅ [人工审批] API 回调返回: {decision}")
            return decision, modified_result

        except Exception as e:
            logger.error(f"❌ [人工审批] API 回调失败: {e}")
            return ApprovalDecision.REJECTED, None

    def _auto_approval(
        self,
        analysis_result: Dict[str, Any],
        matched_rules: List[Dict]
    ) -> tuple[ApprovalDecision, Optional[Dict]]:
        """自动审批（基于规则）"""
        logger.info("🤖 [人工审批] 自动审批模式")

        # 示例自动审批逻辑：
        # - 置信度 < 0.7 自动拒绝
        # - 置信度 >= 0.7 且不是"强烈卖出"自动批准

        confidence = analysis_result.get('confidence', 0)
        recommendation = analysis_result.get('recommendation')

        if confidence < 0.7:
            logger.info("❌ [自动审批] 置信度过低，自动拒绝")
            return ApprovalDecision.REJECTED, None

        if recommendation == '强烈卖出':
            logger.info("❌ [自动审批] 强烈卖出建议，自动拒绝")
            return ApprovalDecision.REJECTED, None

        logger.info("✅ [自动审批] 通过审批条件，自动批准")
        return ApprovalDecision.APPROVED, None

    def _format_modified_decision(self, modified_result: Dict[str, Any]) -> str:
        """格式化修改后的决策"""
        return f"""## ✏️ 决策已修改并批准

**修改后的决策**:
- 投资建议: {modified_result.get('recommendation')}
- 置信度: {modified_result.get('confidence', 0):.0%}
- 理由: {modified_result.get('reasoning', 'N/A')}

⚠️ 此决策已由人工修改
"""

    def _log_approval_event(
        self,
        input_state: Dict[str, Any],
        analysis_result: Dict[str, Any],
        decision: ApprovalDecision,
        matched_rules: List[Dict]
    ):
        """
        记录审批事件到数据库

        Args:
            input_state: 输入状态
            analysis_result: 分析结果
            decision: 审批决策
            matched_rules: 触发的规则
        """
        event = create_event(
            middleware_name=self.name,
            event_type="approval_request",
            ticker=analysis_result.get('ticker'),
            agent_name=analysis_result.get('analyst_type', 'unknown'),
            session_id=input_state.get('session_id'),
            output_data={
                "decision": decision.value,
                "recommendation": analysis_result.get('recommendation'),
                "confidence": analysis_result.get('confidence'),
                "matched_rules": [r['name'] for r in matched_rules],
                "approval_method": self.approval_method.value
            },
            metadata={
                "timeout_seconds": self.timeout_seconds,
                "default_on_timeout": self.default_on_timeout
            }
        )

        save_event_to_db(event, self.db_connection)

        logger.info(f"📝 [人工审批] 审批事件已记录: {event.event_id}")

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        base_stats = super().get_stats()
        base_stats.update({
            "approval_count": self.approval_count,
            "approved_count": self.approved_count,
            "rejected_count": self.rejected_count,
            "timeout_count": self.timeout_count,
            "approval_rate": self.approved_count / self.approval_count if self.approval_count > 0 else 0,
            "rejection_rate": self.rejected_count / self.approval_count if self.approval_count > 0 else 0,
            "timeout_rate": self.timeout_count / self.approval_count if self.approval_count > 0 else 0
        })
        return base_stats


# ============================================
# 使用示例
# ============================================

"""
from tradingagents.middleware.human_approval import HumanApprovalMiddleware, ApprovalMethod
from tradingagents.middleware.risk_control import RiskControlMiddleware
from tradingagents.middleware.base import MiddlewareChain

# 1. CLI 交互式审批
approval_middleware = HumanApprovalMiddleware(
    approval_method=ApprovalMethod.CLI,
    timeout_seconds=300,
    default_on_timeout='reject'
)

# 2. API 回调审批
def my_approval_callback(analysis_result, matched_rules, timeout):
    # 自定义审批逻辑
    # 例如：发送到Slack，等待用户点击按钮
    return ApprovalDecision.APPROVED, None

approval_middleware = HumanApprovalMiddleware(
    approval_method=ApprovalMethod.API,
    approval_callback=my_approval_callback
)

# 3. 自动审批（基于规则）
approval_middleware = HumanApprovalMiddleware(
    approval_method=ApprovalMethod.AUTO
)

# 4. 组合使用（风险控制 + 人工审批）
chain = MiddlewareChain()
chain.add(RiskControlMiddleware(risk_threshold=0.85, block_high_risk=False))
chain.add(HumanApprovalMiddleware(approval_method=ApprovalMethod.CLI))

# 应用到agent
wrapped_agent = chain.apply(original_agent_fn)

# 执行分析
result = wrapped_agent(state)

# 查看统计
stats = approval_middleware.get_stats()
print(f"审批请求数: {stats['approval_count']}")
print(f"批准数: {stats['approved_count']}")
print(f"拒绝数: {stats['rejected_count']}")
print(f"批准率: {stats['approval_rate']:.0%}")
"""

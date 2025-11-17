"""
对话总结中间件 (Conversation Summarization Middleware)

自动压缩长对话历史，减少 token 消耗
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage

from tradingagents.middleware.base import BaseMiddleware, create_event, save_event_to_db
from tradingagents.utils.logging_manager import get_logger

logger = get_logger('middleware.conversation_summary')


class ConversationSummaryMiddleware(BaseMiddleware):
    """
    对话总结中间件

    功能：
    1. 监控对话长度（消息数量或 token 数）
    2. 达到阈值时自动触发总结
    3. 使用 LLM 总结旧消息
    4. 保留最近的重要消息
    5. 减少 token 消耗
    """

    def __init__(
        self,
        llm = None,
        max_messages: int = 20,  # 最多保留20条消息
        max_tokens: Optional[int] = None,  # 或按 token 数限制
        keep_recent: int = 5,  # 始终保留最近5条消息
        summarize_every: int = 10,  # 每10条消息触发一次总结
        db_connection = None
    ):
        """
        初始化对话总结中间件

        Args:
            llm: 用于总结的 LLM 实例
            max_messages: 最多保留的消息数
            max_tokens: 最多保留的 token 数（可选）
            keep_recent: 始终保留最近N条消息
            summarize_every: 每N条消息触发一次总结
            db_connection: 数据库连接
        """
        super().__init__(name="ConversationSummaryMiddleware")

        self.llm = llm
        self.max_messages = max_messages
        self.max_tokens = max_tokens
        self.keep_recent = keep_recent
        self.summarize_every = summarize_every
        self.db_connection = db_connection

        self.summarize_count = 0
        self.total_tokens_saved = 0

        logger.info(f"📝 [对话总结] 初始化")
        logger.info(f"   - 最大消息数: {max_messages}")
        logger.info(f"   - 保留最近: {keep_recent} 条")
        logger.info(f"   - 总结频率: 每 {summarize_every} 条")

    def before_call(self, input_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        在调用前检查是否需要总结

        Args:
            input_state: 输入状态

        Returns:
            处理后的输入状态
        """
        messages = input_state.get("messages", [])
        message_count = len(messages)

        logger.debug(f"📊 [对话总结] 当前消息数: {message_count}")

        # 检查是否需要总结
        if message_count > self.max_messages:
            logger.info(f"🔄 [对话总结] 消息数超过阈值 ({message_count} > {self.max_messages})，开始总结")

            # 执行总结
            summarized_messages = self._summarize_messages(messages)

            # 更新状态
            input_state["messages"] = summarized_messages
            input_state["conversation_summarized"] = True

            self.summarize_count += 1

            logger.info(f"✅ [对话总结] 总结完成: {message_count} → {len(summarized_messages)} 条消息")

        return input_state

    def _summarize_messages(self, messages: List[BaseMessage]) -> List[BaseMessage]:
        """
        总结消息列表

        Args:
            messages: 原始消息列表

        Returns:
            总结后的消息列表
        """
        if len(messages) <= self.keep_recent:
            logger.debug(f"📊 [对话总结] 消息数未超过保留阈值，跳过总结")
            return messages

        # 分割：需要总结的旧消息 + 保留的新消息
        messages_to_summarize = messages[:-self.keep_recent]
        messages_to_keep = messages[-self.keep_recent:]

        logger.info(f"📝 [对话总结] 总结 {len(messages_to_summarize)} 条旧消息，保留 {len(messages_to_keep)} 条新消息")

        # 如果没有配置 LLM，使用简单压缩
        if not self.llm:
            summary = self._simple_summary(messages_to_summarize)
        else:
            summary = self._llm_summary(messages_to_summarize)

        # 创建总结消息
        summary_message = SystemMessage(
            content=f"""## 📝 历史对话总结

以下是之前 {len(messages_to_summarize)} 条消息的总结：

{summary}

---
*此总结由系统自动生成，压缩了 {len(messages_to_summarize)} 条历史消息*
"""
        )

        # 返回：总结 + 最近的消息
        result_messages = [summary_message] + messages_to_keep

        # 记录 token 节省（估算）
        original_tokens = self._estimate_tokens(messages_to_summarize)
        summary_tokens = self._estimate_tokens([summary_message])
        tokens_saved = original_tokens - summary_tokens

        self.total_tokens_saved += tokens_saved

        logger.info(f"💰 [对话总结] 估算节省 {tokens_saved} tokens")

        return result_messages

    def _simple_summary(self, messages: List[BaseMessage]) -> str:
        """
        简单总结（不使用 LLM）

        Args:
            messages: 消息列表

        Returns:
            总结文本
        """
        summary_parts = []

        for i, msg in enumerate(messages):
            role = self._get_role_name(msg)
            content_preview = msg.content[:100] if msg.content else ""

            summary_parts.append(f"{i+1}. **{role}**: {content_preview}...")

        return "\n".join(summary_parts)

    def _llm_summary(self, messages: List[BaseMessage]) -> str:
        """
        使用 LLM 进行智能总结

        Args:
            messages: 消息列表

        Returns:
            总结文本
        """
        logger.info(f"🤖 [对话总结] 使用 LLM 进行智能总结")

        # 构建对话历史文本
        conversation_text = self._format_conversation(messages)

        # 总结提示词
        summary_prompt = f"""请总结以下对话历史，保留关键信息和决策要点：

{conversation_text}

请提供简洁的总结，包括：
1. 讨论的主要股票和主题
2. 重要的分析结论
3. 关键的投资建议
4. 任何重要的风险提示

总结应控制在200-300字以内。
"""

        try:
            # 调用 LLM
            from langchain_core.messages import HumanMessage
            response = self.llm.invoke([HumanMessage(content=summary_prompt)])

            summary = response.content

            logger.info(f"✅ [对话总结] LLM 总结完成")
            return summary

        except Exception as e:
            logger.error(f"❌ [对话总结] LLM 总结失败: {e}")
            logger.warning(f"⚠️ [对话总结] 回退到简单总结")
            return self._simple_summary(messages)

    def _format_conversation(self, messages: List[BaseMessage]) -> str:
        """
        格式化对话历史为文本

        Args:
            messages: 消息列表

        Returns:
            格式化的对话文本
        """
        lines = []

        for msg in messages:
            role = self._get_role_name(msg)
            content = msg.content if msg.content else "[empty]"

            lines.append(f"{role}: {content}")
            lines.append("-" * 40)

        return "\n".join(lines)

    def _get_role_name(self, message: BaseMessage) -> str:
        """获取消息角色名称"""
        if isinstance(message, HumanMessage):
            return "用户"
        elif isinstance(message, AIMessage):
            return "AI助手"
        elif isinstance(message, SystemMessage):
            return "系统"
        else:
            return "其他"

    def _estimate_tokens(self, messages: List[BaseMessage]) -> int:
        """
        估算消息的 token 数量

        简单估算：中文 1字 ≈ 2 tokens，英文 1词 ≈ 1.3 tokens
        更精确的方法应使用 tiktoken

        Args:
            messages: 消息列表

        Returns:
            估算的 token 数
        """
        total_chars = sum(len(msg.content) if msg.content else 0 for msg in messages)

        # 简化估算：平均 1.5 tokens per character
        estimated_tokens = int(total_chars * 1.5)

        return estimated_tokens

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        base_stats = super().get_stats()
        base_stats.update({
            "summarize_count": self.summarize_count,
            "total_tokens_saved": self.total_tokens_saved,
            "avg_tokens_saved_per_summary": (
                self.total_tokens_saved / self.summarize_count
                if self.summarize_count > 0 else 0
            )
        })
        return base_stats


# ============================================
# 使用示例
# ============================================

"""
from langchain_openai import ChatOpenAI
from tradingagents.middleware.conversation_summary import ConversationSummaryMiddleware
from tradingagents.middleware.base import MiddlewareChain

# 创建 LLM（用于智能总结）
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# 1. 使用 LLM 进行智能总结
summary_middleware = ConversationSummaryMiddleware(
    llm=llm,
    max_messages=20,        # 最多保留20条消息
    keep_recent=5,          # 始终保留最近5条
    summarize_every=10      # 每10条触发总结
)

# 2. 不使用 LLM（简单压缩）
summary_middleware = ConversationSummaryMiddleware(
    llm=None,               # 不使用 LLM
    max_messages=15,
    keep_recent=3
)

# 3. 组合使用多个中间件
from tradingagents.middleware.risk_control import RiskControlMiddleware
from tradingagents.middleware.human_approval import HumanApprovalMiddleware

chain = MiddlewareChain()
chain.add(ConversationSummaryMiddleware(llm=llm, max_messages=20))  # 对话压缩
chain.add(RiskControlMiddleware(risk_threshold=0.85))               # 风险控制
chain.add(HumanApprovalMiddleware(approval_method=ApprovalMethod.CLI))  # 人工审批

# 应用到agent
wrapped_agent = chain.apply(original_agent_fn)

# 执行分析（长对话会自动总结）
result = wrapped_agent(state)

# 查看统计
stats = summary_middleware.get_stats()
print(f"总结次数: {stats['summarize_count']}")
print(f"节省 tokens: {stats['total_tokens_saved']}")
print(f"平均每次节省: {stats['avg_tokens_saved_per_summary']:.0f} tokens")
"""

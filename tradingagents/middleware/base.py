"""
TradingAgents 中间件系统基础架构

LangChain 1.0 中间件允许在 agent 执行的每一步插入自定义逻辑。
本模块提供 TradingAgents 专用的中间件基类和工具函数。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Callable, Optional, List
from datetime import datetime
import json

from langchain_core.messages import BaseMessage, AIMessage, HumanMessage
from pydantic import BaseModel, Field

from tradingagents.utils.logging_manager import get_logger
logger = get_logger('middleware')


# ============================================
# 中间件事件模型
# ============================================

class MiddlewareEvent(BaseModel):
    """中间件事件数据模型"""

    event_id: str = Field(description="事件唯一ID")
    timestamp: datetime = Field(default_factory=datetime.now, description="事件时间")
    middleware_name: str = Field(description="中间件名称")
    event_type: str = Field(description="事件类型：before_call, after_call, on_error, on_decision")

    # 上下文信息
    agent_name: Optional[str] = Field(default=None, description="Agent名称")
    session_id: Optional[str] = Field(default=None, description="会话ID")
    ticker: Optional[str] = Field(default=None, description="股票代码")

    # 执行信息
    input_data: Optional[Dict[str, Any]] = Field(default=None, description="输入数据")
    output_data: Optional[Dict[str, Any]] = Field(default=None, description="输出数据")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="元数据")

    # 决策信息（用于需要人工确认的场景）
    requires_approval: bool = Field(default=False, description="是否需要人工批准")
    approval_status: Optional[str] = Field(default=None, description="批准状态：pending, approved, rejected")
    approval_reason: Optional[str] = Field(default=None, description="批准/拒绝原因")

    class Config:
        json_schema_extra = {
            "example": {
                "event_id": "evt_20251115_001",
                "middleware_name": "RiskControlMiddleware",
                "event_type": "on_decision",
                "agent_name": "market_analyst",
                "ticker": "000001",
                "requires_approval": True,
                "approval_status": "pending"
            }
        }


# ============================================
# 中间件基类
# ============================================

class BaseMiddleware(ABC):
    """
    中间件基类

    所有自定义中间件都应继承此类并实现 __call__ 方法
    """

    def __init__(self, name: str = None, enabled: bool = True):
        """
        初始化中间件

        Args:
            name: 中间件名称
            enabled: 是否启用
        """
        self.name = name or self.__class__.__name__
        self.enabled = enabled
        self.call_count = 0
        self.error_count = 0

        logger.info(f"🔧 [中间件] 初始化: {self.name} (enabled={enabled})")

    def __call__(self, state: Dict[str, Any], next_fn: Callable) -> Dict[str, Any]:
        """
        中间件调用入口

        Args:
            state: 当前状态
            next_fn: 下一个函数（可能是另一个中间件或实际的agent函数）

        Returns:
            处理后的状态
        """
        if not self.enabled:
            # 如果未启用，直接调用下一个函数
            return next_fn(state)

        self.call_count += 1

        try:
            # 前置处理
            state = self.before_call(state)

            # 调用下一个函数
            result = next_fn(state)

            # 后置处理
            result = self.after_call(state, result)

            return result

        except Exception as e:
            self.error_count += 1
            logger.error(f"❌ [中间件] {self.name} 执行失败: {e}")

            # 错误处理
            return self.on_error(state, e)

    def before_call(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        前置处理：在agent执行前调用

        Args:
            state: 当前状态

        Returns:
            处理后的状态
        """
        logger.debug(f"🔄 [{self.name}] before_call")
        return state

    def after_call(self, input_state: Dict[str, Any], output_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        后置处理：在agent执行后调用

        Args:
            input_state: 输入状态
            output_state: 输出状态

        Returns:
            处理后的输出状态
        """
        logger.debug(f"🔄 [{self.name}] after_call")
        return output_state

    def on_error(self, state: Dict[str, Any], error: Exception) -> Dict[str, Any]:
        """
        错误处理：当执行出错时调用

        Args:
            state: 当前状态
            error: 错误对象

        Returns:
            错误处理后的状态
        """
        logger.error(f"❌ [{self.name}] on_error: {error}")

        # 默认：在消息中添加错误信息
        error_message = AIMessage(
            content=f"中间件 {self.name} 处理失败: {str(error)}"
        )

        state.setdefault("messages", []).append(error_message)
        return state

    def get_stats(self) -> Dict[str, Any]:
        """获取中间件统计信息"""
        return {
            "name": self.name,
            "enabled": self.enabled,
            "call_count": self.call_count,
            "error_count": self.error_count,
            "error_rate": self.error_count / self.call_count if self.call_count > 0 else 0
        }


# ============================================
# 中间件链管理器
# ============================================

class MiddlewareChain:
    """
    中间件链管理器

    管理多个中间件的执行顺序和组合
    """

    def __init__(self, middlewares: List[BaseMiddleware] = None):
        """
        初始化中间件链

        Args:
            middlewares: 中间件列表（按执行顺序）
        """
        self.middlewares = middlewares or []
        logger.info(f"🔗 [中间件链] 初始化，包含 {len(self.middlewares)} 个中间件")

    def add(self, middleware: BaseMiddleware) -> 'MiddlewareChain':
        """
        添加中间件到链尾

        Args:
            middleware: 中间件实例

        Returns:
            self（支持链式调用）
        """
        self.middlewares.append(middleware)
        logger.info(f"➕ [中间件链] 添加中间件: {middleware.name}")
        return self

    def remove(self, middleware_name: str) -> bool:
        """
        移除指定名称的中间件

        Args:
            middleware_name: 中间件名称

        Returns:
            是否成功移除
        """
        for i, mw in enumerate(self.middlewares):
            if mw.name == middleware_name:
                self.middlewares.pop(i)
                logger.info(f"➖ [中间件链] 移除中间件: {middleware_name}")
                return True
        return False

    def apply(self, agent_fn: Callable) -> Callable:
        """
        将中间件链应用到agent函数

        Args:
            agent_fn: 原始agent函数

        Returns:
            包装后的函数
        """
        def wrapped_fn(state: Dict[str, Any]) -> Dict[str, Any]:
            # 从右到左组合中间件（最后一个中间件最先执行 before_call）
            fn = agent_fn
            for middleware in reversed(self.middlewares):
                original_fn = fn
                fn = lambda s, mw=middleware, orig=original_fn: mw(s, orig)

            return fn(state)

        return wrapped_fn

    def get_stats(self) -> List[Dict[str, Any]]:
        """获取所有中间件的统计信息"""
        return [mw.get_stats() for mw in self.middlewares]


# ============================================
# 工具函数
# ============================================

def create_event(
    middleware_name: str,
    event_type: str,
    **kwargs
) -> MiddlewareEvent:
    """
    创建中间件事件

    Args:
        middleware_name: 中间件名称
        event_type: 事件类型
        **kwargs: 其他事件属性

    Returns:
        MiddlewareEvent 实例
    """
    import uuid

    event_id = f"evt_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

    return MiddlewareEvent(
        event_id=event_id,
        middleware_name=middleware_name,
        event_type=event_type,
        **kwargs
    )


def save_event_to_db(event: MiddlewareEvent, db_connection = None):
    """
    保存事件到数据库

    Args:
        event: 中间件事件
        db_connection: 数据库连接（可选）
    """
    # TODO: 实现数据库保存逻辑
    logger.debug(f"💾 [事件] 保存到数据库: {event.event_id}")

    # 示例：保存到MongoDB
    # if db_connection:
    #     db_connection.middleware_events.insert_one(event.model_dump())


# ============================================
# 使用示例
# ============================================

"""
# 示例 1: 创建简单中间件

class LoggingMiddleware(BaseMiddleware):
    def before_call(self, state):
        logger.info(f"执行前: {state.get('ticker', 'N/A')}")
        return state

    def after_call(self, input_state, output_state):
        logger.info(f"执行后: 成功")
        return output_state


# 示例 2: 使用中间件链

chain = MiddlewareChain()
chain.add(LoggingMiddleware())
chain.add(RiskControlMiddleware())
chain.add(HumanApprovalMiddleware())

# 包装agent函数
wrapped_agent = chain.apply(original_agent_fn)

# 执行
result = wrapped_agent(state)


# 示例 3: 与 LangChain 1.0 create_agent 集成

from langchain import create_agent

# 创建agent
agent = create_agent(
    model=llm,
    tools=[...],
    system_prompt="...",
)

# 应用中间件（需要自定义wrapper）
def agent_with_middleware(state):
    wrapped = chain.apply(lambda s: agent.invoke(s))
    return wrapped(state)
"""

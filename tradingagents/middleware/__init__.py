"""
LangChain 1.0 中间件系统

提供细粒度的 agent 执行控制和增强功能
"""

from tradingagents.middleware.base import (
    BaseMiddleware,
    MiddlewareChain,
    MiddlewareEvent,
    create_event,
    save_event_to_db
)

from tradingagents.middleware.risk_control import RiskControlMiddleware

from tradingagents.middleware.human_approval import (
    HumanApprovalMiddleware,
    ApprovalMethod,
    ApprovalDecision
)

from tradingagents.middleware.conversation_summary import ConversationSummaryMiddleware

__all__ = [
    # Base
    "BaseMiddleware",
    "MiddlewareChain",
    "MiddlewareEvent",
    "create_event",
    "save_event_to_db",

    # Risk Control
    "RiskControlMiddleware",

    # Human Approval
    "HumanApprovalMiddleware",
    "ApprovalMethod",
    "ApprovalDecision",

    # Conversation Summary
    "ConversationSummaryMiddleware",
]

__version__ = "1.0.0"

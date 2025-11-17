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

from tradingagents.middleware.content_blocks import (
    ContentBlocksMiddleware,
    ContentBlockType
)

from tradingagents.middleware.reasoning_handler import (
    ReasoningHandler,
    ReasoningModelType,
    ReasoningTrace
)

from tradingagents.middleware.citations_handler import (
    CitationsHandler,
    CitationType,
    Citation,
    CitedAnswer
)

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

    # Content Blocks
    "ContentBlocksMiddleware",
    "ContentBlockType",

    # Reasoning
    "ReasoningHandler",
    "ReasoningModelType",
    "ReasoningTrace",

    # Citations
    "CitationsHandler",
    "CitationType",
    "Citation",
    "CitedAnswer",
]

__version__ = "1.1.0"

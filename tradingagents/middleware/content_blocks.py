"""
Content Blocks 提取中间件

支持 LangChain 1.0 的 content_blocks API：
- 推理过程展示（OpenAI o1, DeepSeek R1, Claude Extended Thinking）
- 引用溯源（Claude Citations）
- 工具调用详情
- 多模态内容
"""

from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from enum import Enum

from langchain_core.messages import BaseMessage, AIMessage

from tradingagents.middleware.base import BaseMiddleware, create_event, save_event_to_db
from tradingagents.utils.logging_manager import get_logger

logger = get_logger('middleware.content_blocks')


class ContentBlockType(Enum):
    """内容块类型"""
    REASONING = "reasoning"      # 推理过程 (OpenAI o1, DeepSeek R1, Claude)
    THINKING = "thinking"        # 思考过程 (Claude Extended Thinking)
    TEXT = "text"                # 普通文本
    CITATION = "citation"        # 引用
    TOOL_CALL = "tool_call"      # 工具调用
    TOOL_RESULT = "tool_result"  # 工具结果
    IMAGE = "image"              # 图片
    PDF = "pdf"                  # PDF
    AUDIO = "audio"              # 音频
    UNKNOWN = "unknown"          # 未知类型


class ContentBlocksMiddleware(BaseMiddleware):
    """
    Content Blocks 提取中间件

    功能：
    1. 从 AIMessage 中提取 content_blocks
    2. 解析推理过程（reasoning）并展示
    3. 解析引用（citations）并验证
    4. 格式化工具调用详情
    5. 支持多模态内容
    6. 保存结构化内容到数据库
    """

    def __init__(
        self,
        enable_reasoning_display: bool = True,
        enable_citations_display: bool = True,
        enable_tool_calls_display: bool = False,
        reasoning_max_length: int = 1000,  # 推理过程最大显示长度
        save_to_db: bool = True,
        db_connection = None
    ):
        """
        初始化 Content Blocks 中间件

        Args:
            enable_reasoning_display: 是否展示推理过程
            enable_citations_display: 是否展示引用
            enable_tool_calls_display: 是否展示工具调用
            reasoning_max_length: 推理过程最大显示长度
            save_to_db: 是否保存到数据库
            db_connection: 数据库连接
        """
        super().__init__(name="ContentBlocksMiddleware")

        self.enable_reasoning_display = enable_reasoning_display
        self.enable_citations_display = enable_citations_display
        self.enable_tool_calls_display = enable_tool_calls_display
        self.reasoning_max_length = reasoning_max_length
        self.save_to_db = save_to_db
        self.db_connection = db_connection

        self.reasoning_count = 0
        self.citations_count = 0
        self.tool_calls_count = 0
        self.total_reasoning_tokens = 0

        logger.info(f"🧩 [Content Blocks] 初始化")
        logger.info(f"   - 推理展示: {enable_reasoning_display}")
        logger.info(f"   - 引用展示: {enable_citations_display}")
        logger.info(f"   - 工具调用展示: {enable_tool_calls_display}")

    def after_call(self, input_state: Dict[str, Any], output_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析完成后提取和处理 content_blocks

        Args:
            input_state: 输入状态
            output_state: 输出状态（包含分析结果）

        Returns:
            处理后的输出状态（添加了格式化的内容块）
        """
        logger.debug(f"🧩 [Content Blocks] 开始提取内容块")

        # 提取消息
        messages = output_state.get("messages", [])
        if not messages:
            return output_state

        # 获取最新的 AI 消息
        latest_message = messages[-1]
        if not isinstance(latest_message, AIMessage):
            logger.debug(f"🧩 [Content Blocks] 最新消息不是 AIMessage，跳过")
            return output_state

        # 提取 content_blocks
        try:
            content_blocks = self._extract_content_blocks(latest_message)

            if not content_blocks:
                logger.debug(f"🧩 [Content Blocks] 未找到 content_blocks")
                return output_state

            logger.info(f"🧩 [Content Blocks] 提取到 {len(content_blocks)} 个内容块")

            # 分类处理内容块
            reasoning_blocks = []
            citation_blocks = []
            tool_call_blocks = []
            text_blocks = []
            other_blocks = []

            for block in content_blocks:
                block_type = self._get_block_type(block)

                if block_type == ContentBlockType.REASONING or block_type == ContentBlockType.THINKING:
                    reasoning_blocks.append(block)
                    self.reasoning_count += 1
                elif block_type == ContentBlockType.CITATION:
                    citation_blocks.append(block)
                    self.citations_count += 1
                elif block_type == ContentBlockType.TOOL_CALL:
                    tool_call_blocks.append(block)
                    self.tool_calls_count += 1
                elif block_type == ContentBlockType.TEXT:
                    text_blocks.append(block)
                else:
                    other_blocks.append(block)

            # 构建增强的输出
            enhanced_content = self._build_enhanced_content(
                reasoning_blocks,
                citation_blocks,
                tool_call_blocks,
                text_blocks,
                other_blocks
            )

            # 如果有推理或引用，添加到消息中
            if reasoning_blocks or citation_blocks:
                from langchain_core.messages import AIMessage

                # 创建新的消息，包含原始内容 + 增强内容
                original_content = latest_message.content if latest_message.content else ""

                enhanced_message = AIMessage(
                    content=f"{original_content}\n\n{enhanced_content}",
                    additional_kwargs={
                        **latest_message.additional_kwargs,
                        "content_blocks_processed": True,
                        "reasoning_count": len(reasoning_blocks),
                        "citations_count": len(citation_blocks),
                        "tool_calls_count": len(tool_call_blocks)
                    }
                )

                # 替换最新消息
                output_state["messages"] = messages[:-1] + [enhanced_message]

            # 保存到数据库
            if self.save_to_db:
                self._save_content_blocks_to_db(
                    input_state,
                    reasoning_blocks,
                    citation_blocks,
                    tool_call_blocks
                )

        except Exception as e:
            logger.error(f"❌ [Content Blocks] 处理失败: {e}")
            import traceback
            traceback.print_exc()

        return output_state

    def _extract_content_blocks(self, message: AIMessage) -> List[Dict[str, Any]]:
        """
        从 AIMessage 中提取 content_blocks

        Args:
            message: AI 消息

        Returns:
            内容块列表
        """
        # 方法 1: 使用 content_blocks 属性 (LangChain 1.0)
        if hasattr(message, 'content_blocks'):
            try:
                blocks = message.content_blocks
                if blocks:
                    logger.debug(f"🧩 [Content Blocks] 通过 content_blocks 属性提取到 {len(blocks)} 个块")
                    return blocks
            except Exception as e:
                logger.debug(f"🧩 [Content Blocks] content_blocks 属性访问失败: {e}")

        # 方法 2: 从 content 中提取（如果 content 是列表）
        if isinstance(message.content, list):
            logger.debug(f"🧩 [Content Blocks] 从 content 列表中提取到 {len(message.content)} 个块")
            return message.content

        # 方法 3: 从 additional_kwargs 中提取
        if hasattr(message, 'additional_kwargs'):
            if 'content_blocks' in message.additional_kwargs:
                blocks = message.additional_kwargs['content_blocks']
                logger.debug(f"🧩 [Content Blocks] 从 additional_kwargs 中提取到 {len(blocks)} 个块")
                return blocks

        # 方法 4: 从 response_metadata 中提取推理
        if hasattr(message, 'response_metadata'):
            metadata = message.response_metadata

            # OpenAI o1 reasoning
            if 'reasoning' in metadata or 'thinking' in metadata:
                reasoning_content = metadata.get('reasoning') or metadata.get('thinking')
                logger.debug(f"🧩 [Content Blocks] 从 response_metadata 中提取到推理内容")
                return [
                    {"type": "reasoning", "reasoning": reasoning_content},
                    {"type": "text", "text": message.content}
                ]

        return []

    def _get_block_type(self, block: Union[Dict, Any]) -> ContentBlockType:
        """
        获取内容块类型

        Args:
            block: 内容块

        Returns:
            内容块类型
        """
        if isinstance(block, dict):
            block_type = block.get('type', '').lower()
        elif hasattr(block, 'type'):
            block_type = block.type.lower()
        else:
            return ContentBlockType.UNKNOWN

        # 映射到枚举
        type_mapping = {
            'reasoning': ContentBlockType.REASONING,
            'thinking': ContentBlockType.THINKING,
            'text': ContentBlockType.TEXT,
            'citation': ContentBlockType.CITATION,
            'tool_call': ContentBlockType.TOOL_CALL,
            'tool_use': ContentBlockType.TOOL_CALL,
            'tool_result': ContentBlockType.TOOL_RESULT,
            'image': ContentBlockType.IMAGE,
            'pdf': ContentBlockType.PDF,
            'audio': ContentBlockType.AUDIO,
        }

        return type_mapping.get(block_type, ContentBlockType.UNKNOWN)

    def _build_enhanced_content(
        self,
        reasoning_blocks: List[Dict],
        citation_blocks: List[Dict],
        tool_call_blocks: List[Dict],
        text_blocks: List[Dict],
        other_blocks: List[Dict]
    ) -> str:
        """
        构建增强的内容展示

        Args:
            reasoning_blocks: 推理块
            citation_blocks: 引用块
            tool_call_blocks: 工具调用块
            text_blocks: 文本块
            other_blocks: 其他块

        Returns:
            格式化的内容字符串
        """
        parts = []

        # 1. 推理过程
        if reasoning_blocks and self.enable_reasoning_display:
            parts.append(self._format_reasoning_blocks(reasoning_blocks))

        # 2. 引用
        if citation_blocks and self.enable_citations_display:
            parts.append(self._format_citation_blocks(citation_blocks))

        # 3. 工具调用
        if tool_call_blocks and self.enable_tool_calls_display:
            parts.append(self._format_tool_call_blocks(tool_call_blocks))

        # 4. 其他块
        if other_blocks:
            parts.append(self._format_other_blocks(other_blocks))

        return "\n\n".join(parts)

    def _format_reasoning_blocks(self, blocks: List[Dict]) -> str:
        """格式化推理过程"""
        lines = ["---", "## 🧠 AI 推理过程", ""]

        for i, block in enumerate(blocks, 1):
            # 提取推理内容
            reasoning = None
            if isinstance(block, dict):
                reasoning = block.get('reasoning') or block.get('thinking')
            elif hasattr(block, 'reasoning'):
                reasoning = block.reasoning
            elif hasattr(block, 'thinking'):
                reasoning = block.thinking

            if reasoning:
                # 截断过长的推理
                if len(reasoning) > self.reasoning_max_length:
                    reasoning = reasoning[:self.reasoning_max_length] + "..."
                    truncated = True
                else:
                    truncated = False

                lines.append(f"**推理步骤 {i}:**")
                lines.append(f"```")
                lines.append(reasoning)
                lines.append(f"```")

                if truncated:
                    lines.append(f"*（推理过程已截断，完整内容超过 {self.reasoning_max_length} 字符）*")

                lines.append("")

                # 估算 token 数
                estimated_tokens = len(reasoning) * 1.5
                self.total_reasoning_tokens += estimated_tokens

        lines.append(f"*💡 推理过程由模型生成，展示了 AI 的思考步骤*")
        lines.append("---")

        return "\n".join(lines)

    def _format_citation_blocks(self, blocks: List[Dict]) -> str:
        """格式化引用"""
        lines = ["---", "## 📚 引用来源", ""]

        for i, block in enumerate(blocks, 1):
            # 提取引用内容
            if isinstance(block, dict):
                citation_text = block.get('citation') or block.get('text', '')
                source = block.get('source', 'Unknown')
                source_id = block.get('source_id', i)
                url = block.get('url')
            else:
                citation_text = getattr(block, 'citation', '') or getattr(block, 'text', '')
                source = getattr(block, 'source', 'Unknown')
                source_id = getattr(block, 'source_id', i)
                url = getattr(block, 'url', None)

            lines.append(f"**[{source_id}] {source}**")

            if citation_text:
                lines.append(f"> {citation_text}")

            if url:
                lines.append(f"🔗 [{url}]({url})")

            lines.append("")

        lines.append(f"*📖 以上引用来自分析过程中使用的数据源*")
        lines.append("---")

        return "\n".join(lines)

    def _format_tool_call_blocks(self, blocks: List[Dict]) -> str:
        """格式化工具调用"""
        lines = ["---", "## 🔧 工具调用详情", ""]

        for i, block in enumerate(blocks, 1):
            if isinstance(block, dict):
                tool_name = block.get('name', 'unknown_tool')
                tool_input = block.get('input', {})
            else:
                tool_name = getattr(block, 'name', 'unknown_tool')
                tool_input = getattr(block, 'input', {})

            lines.append(f"**工具 {i}: {tool_name}**")
            lines.append(f"```json")
            import json
            lines.append(json.dumps(tool_input, indent=2, ensure_ascii=False))
            lines.append(f"```")
            lines.append("")

        lines.append("---")

        return "\n".join(lines)

    def _format_other_blocks(self, blocks: List[Dict]) -> str:
        """格式化其他类型的块"""
        lines = ["---", "## 📎 其他内容", ""]

        for block in blocks:
            block_type = self._get_block_type(block)
            lines.append(f"- 类型: {block_type.value}")

        lines.append("---")

        return "\n".join(lines)

    def _save_content_blocks_to_db(
        self,
        input_state: Dict[str, Any],
        reasoning_blocks: List[Dict],
        citation_blocks: List[Dict],
        tool_call_blocks: List[Dict]
    ):
        """
        保存内容块到数据库

        Args:
            input_state: 输入状态
            reasoning_blocks: 推理块
            citation_blocks: 引用块
            tool_call_blocks: 工具调用块
        """
        event = create_event(
            middleware_name=self.name,
            event_type="content_blocks_extracted",
            ticker=input_state.get('ticker'),
            agent_name=input_state.get('agent_name', 'unknown'),
            session_id=input_state.get('session_id'),
            output_data={
                "reasoning_count": len(reasoning_blocks),
                "citations_count": len(citation_blocks),
                "tool_calls_count": len(tool_call_blocks),
                "reasoning_blocks": reasoning_blocks[:5],  # 只保存前5个
                "citation_blocks": citation_blocks,
            },
            metadata={
                "total_reasoning_tokens": self.total_reasoning_tokens
            }
        )

        save_event_to_db(event, self.db_connection)

        logger.info(f"📝 [Content Blocks] 内容块已记录到数据库")

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        base_stats = super().get_stats()
        base_stats.update({
            "reasoning_count": self.reasoning_count,
            "citations_count": self.citations_count,
            "tool_calls_count": self.tool_calls_count,
            "total_reasoning_tokens": self.total_reasoning_tokens,
            "avg_reasoning_tokens": (
                self.total_reasoning_tokens / self.reasoning_count
                if self.reasoning_count > 0 else 0
            )
        })
        return base_stats


# ============================================
# 使用示例
# ============================================

"""
from langchain_openai import ChatOpenAI
from tradingagents.middleware.content_blocks import ContentBlocksMiddleware
from tradingagents.middleware.base import MiddlewareChain

# 1. 基础使用（展示推理和引用）
content_blocks_middleware = ContentBlocksMiddleware(
    enable_reasoning_display=True,
    enable_citations_display=True,
    reasoning_max_length=1000
)

# 2. 仅展示推理过程
reasoning_middleware = ContentBlocksMiddleware(
    enable_reasoning_display=True,
    enable_citations_display=False,
    enable_tool_calls_display=False
)

# 3. 组合使用
from tradingagents.middleware.risk_control import RiskControlMiddleware

chain = MiddlewareChain()
chain.add(ContentBlocksMiddleware())  # 提取推理和引用
chain.add(RiskControlMiddleware())    # 风险控制

# 应用到 agent
wrapped_agent = chain.apply(market_analyst_node)

# 执行分析（自动提取和展示 content_blocks）
result = wrapped_agent(state)

# 查看统计
stats = content_blocks_middleware.get_stats()
print(f"推理次数: {stats['reasoning_count']}")
print(f"引用次数: {stats['citations_count']}")
print(f"推理 tokens: {stats['total_reasoning_tokens']}")
"""

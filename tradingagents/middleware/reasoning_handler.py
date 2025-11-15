"""
推理过程处理器

专门处理支持推理的模型：
- OpenAI o1 (o1-preview, o1-mini)
- DeepSeek R1 (deepseek-r1)
- Claude Extended Thinking (claude-3-opus with extended_thinking)
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from tradingagents.utils.logging_manager import get_logger

logger = get_logger('middleware.reasoning_handler')


class ReasoningModelType(Enum):
    """推理模型类型"""
    OPENAI_O1 = "openai_o1"              # OpenAI o1-preview, o1-mini
    DEEPSEEK_R1 = "deepseek_r1"          # DeepSeek R1
    CLAUDE_THINKING = "claude_thinking"   # Claude Extended Thinking
    UNKNOWN = "unknown"


@dataclass
class ReasoningTrace:
    """推理轨迹数据结构"""
    model_type: ReasoningModelType
    reasoning_content: str
    reasoning_tokens: int
    timestamp: datetime
    metadata: Dict[str, Any]

    def get_summary(self, max_length: int = 200) -> str:
        """获取推理摘要"""
        if len(self.reasoning_content) <= max_length:
            return self.reasoning_content

        return self.reasoning_content[:max_length] + "..."

    def get_word_count(self) -> int:
        """获取推理字数"""
        # 简单统计：中文按字数，英文按单词数
        chinese_chars = sum(1 for c in self.reasoning_content if '\u4e00' <= c <= '\u9fff')
        english_words = len([w for w in self.reasoning_content.split() if w.isalpha()])

        return chinese_chars + english_words


class ReasoningHandler:
    """
    推理过程处理器

    功能：
    1. 识别推理模型类型
    2. 提取和解析推理内容
    3. 格式化推理过程展示
    4. 统计推理 token 消耗
    5. 分析推理质量指标
    """

    def __init__(
        self,
        enable_detailed_logging: bool = True,
        reasoning_max_display: int = 1000
    ):
        """
        初始化推理处理器

        Args:
            enable_detailed_logging: 是否详细记录推理过程
            reasoning_max_display: 推理过程最大显示长度
        """
        self.enable_detailed_logging = enable_detailed_logging
        self.reasoning_max_display = reasoning_max_display

        self.reasoning_traces: List[ReasoningTrace] = []
        self.total_reasoning_tokens = 0

    def detect_model_type(self, message: Any, response_metadata: Dict = None) -> ReasoningModelType:
        """
        检测推理模型类型

        Args:
            message: AI 消息
            response_metadata: 响应元数据

        Returns:
            推理模型类型
        """
        if response_metadata is None:
            response_metadata = getattr(message, 'response_metadata', {})

        # 检查模型名称
        model_name = response_metadata.get('model_name', '').lower()

        if 'o1' in model_name:
            return ReasoningModelType.OPENAI_O1
        elif 'deepseek-r1' in model_name or 'deepseek_r1' in model_name:
            return ReasoningModelType.DEEPSEEK_R1
        elif 'claude' in model_name and 'thinking' in str(response_metadata):
            return ReasoningModelType.CLAUDE_THINKING

        # 检查 provider
        provider = response_metadata.get('model_provider', '').lower()

        if provider == 'openai' and 'reasoning' in response_metadata:
            return ReasoningModelType.OPENAI_O1
        elif provider == 'deepseek':
            return ReasoningModelType.DEEPSEEK_R1
        elif provider == 'anthropic' and 'thinking' in response_metadata:
            return ReasoningModelType.CLAUDE_THINKING

        return ReasoningModelType.UNKNOWN

    def extract_reasoning(
        self,
        message: Any,
        model_type: Optional[ReasoningModelType] = None
    ) -> Optional[ReasoningTrace]:
        """
        提取推理内容

        Args:
            message: AI 消息
            model_type: 模型类型（可选，自动检测）

        Returns:
            推理轨迹对象，如果没有推理内容则返回 None
        """
        if model_type is None:
            model_type = self.detect_model_type(message)

        response_metadata = getattr(message, 'response_metadata', {})

        # 根据模型类型提取推理内容
        reasoning_content = None
        reasoning_tokens = 0
        metadata = {}

        if model_type == ReasoningModelType.OPENAI_O1:
            # OpenAI o1 推理在 response_metadata 中
            reasoning_content = response_metadata.get('reasoning')
            reasoning_tokens = response_metadata.get('reasoning_tokens', 0)

            # 获取额外信息
            metadata = {
                'completion_tokens': response_metadata.get('completion_tokens', 0),
                'reasoning_tokens': reasoning_tokens,
                'model': response_metadata.get('model_name', 'o1-preview')
            }

        elif model_type == ReasoningModelType.DEEPSEEK_R1:
            # DeepSeek R1 推理在 content_blocks 或 response_metadata 中
            if hasattr(message, 'content_blocks'):
                for block in message.content_blocks:
                    if isinstance(block, dict) and block.get('type') == 'reasoning':
                        reasoning_content = block.get('reasoning')
                        break
                    elif hasattr(block, 'type') and block.type == 'reasoning':
                        reasoning_content = block.reasoning
                        break

            if not reasoning_content:
                reasoning_content = response_metadata.get('reasoning')

            # 估算 tokens（DeepSeek 可能不提供）
            if reasoning_content:
                reasoning_tokens = int(len(reasoning_content) * 1.5)

            metadata = {
                'model': response_metadata.get('model_name', 'deepseek-r1'),
                'estimated_tokens': True
            }

        elif model_type == ReasoningModelType.CLAUDE_THINKING:
            # Claude Extended Thinking
            if hasattr(message, 'content_blocks'):
                for block in message.content_blocks:
                    if isinstance(block, dict) and block.get('type') == 'thinking':
                        reasoning_content = block.get('thinking')
                        break
                    elif hasattr(block, 'type') and block.type == 'thinking':
                        reasoning_content = block.thinking
                        break

            if not reasoning_content:
                reasoning_content = response_metadata.get('thinking')

            # Claude 提供 thinking tokens
            reasoning_tokens = response_metadata.get('usage', {}).get('input_tokens_cache_create', 0)

            metadata = {
                'model': response_metadata.get('model_name', 'claude-3-opus'),
                'thinking_signature': response_metadata.get('thinking_signature')
            }

        if not reasoning_content:
            return None

        # 创建推理轨迹
        trace = ReasoningTrace(
            model_type=model_type,
            reasoning_content=reasoning_content,
            reasoning_tokens=reasoning_tokens,
            timestamp=datetime.now(),
            metadata=metadata
        )

        # 记录
        self.reasoning_traces.append(trace)
        self.total_reasoning_tokens += reasoning_tokens

        if self.enable_detailed_logging:
            logger.info(f"🧠 [推理处理器] 提取到推理内容")
            logger.info(f"   - 模型: {model_type.value}")
            logger.info(f"   - 长度: {len(reasoning_content)} 字符")
            logger.info(f"   - Tokens: {reasoning_tokens}")

        return trace

    def format_reasoning_display(self, trace: ReasoningTrace) -> str:
        """
        格式化推理过程展示

        Args:
            trace: 推理轨迹

        Returns:
            格式化的展示文本
        """
        lines = []

        # 标题
        model_name_map = {
            ReasoningModelType.OPENAI_O1: "OpenAI o1",
            ReasoningModelType.DEEPSEEK_R1: "DeepSeek R1",
            ReasoningModelType.CLAUDE_THINKING: "Claude Extended Thinking"
        }

        model_display_name = model_name_map.get(trace.model_type, "Unknown Model")

        lines.append("---")
        lines.append(f"## 🧠 {model_display_name} 推理过程")
        lines.append("")

        # 元信息
        lines.append(f"**模型**: {trace.metadata.get('model', 'unknown')}")
        lines.append(f"**推理 Tokens**: {trace.reasoning_tokens:,}")
        lines.append(f"**推理字数**: {trace.get_word_count():,}")
        lines.append(f"**时间**: {trace.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

        # 推理内容
        reasoning_content = trace.reasoning_content

        # 截断过长内容
        if len(reasoning_content) > self.reasoning_max_display:
            reasoning_content = reasoning_content[:self.reasoning_max_display]
            truncated = True
        else:
            truncated = False

        lines.append("**推理内容**:")
        lines.append("```")
        lines.append(reasoning_content)
        lines.append("```")

        if truncated:
            lines.append("")
            lines.append(f"*（推理过程已截断，完整内容 {len(trace.reasoning_content)} 字符，仅显示前 {self.reasoning_max_display} 字符）*")

        lines.append("")

        # 特殊说明
        if trace.model_type == ReasoningModelType.OPENAI_O1:
            lines.append("💡 **关于 OpenAI o1**:")
            lines.append("- o1 系列是 OpenAI 的推理模型，在回答前进行深度思考")
            lines.append("- 推理 tokens 单独计费，不计入输出 tokens")
            lines.append("- 适合复杂的分析、数学、编程等任务")

        elif trace.model_type == ReasoningModelType.DEEPSEEK_R1:
            lines.append("💡 **关于 DeepSeek R1**:")
            lines.append("- R1 是 DeepSeek 的推理增强模型")
            lines.append("- 采用强化学习训练，提升复杂推理能力")
            lines.append("- 开源模型，性能接近 o1-mini")

        elif trace.model_type == ReasoningModelType.CLAUDE_THINKING:
            lines.append("💡 **关于 Claude Extended Thinking**:")
            lines.append("- Claude 3 Opus 支持扩展思考模式")
            lines.append("- 可以展示详细的思考过程")
            lines.append("- 通过 `extended_thinking=True` 参数启用")

        lines.append("")
        lines.append("---")

        return "\n".join(lines)

    def analyze_reasoning_quality(self, trace: ReasoningTrace) -> Dict[str, Any]:
        """
        分析推理质量

        Args:
            trace: 推理轨迹

        Returns:
            质量分析指标
        """
        reasoning = trace.reasoning_content

        # 简单的质量指标
        metrics = {
            'length': len(reasoning),
            'word_count': trace.get_word_count(),
            'token_count': trace.reasoning_tokens,
            'avg_chars_per_token': len(reasoning) / trace.reasoning_tokens if trace.reasoning_tokens > 0 else 0,
        }

        # 检测推理结构
        has_steps = any(marker in reasoning for marker in ['步骤', 'Step', '1.', '2.', '首先', '然后', '最后'])
        has_analysis = any(marker in reasoning for marker in ['分析', 'Analysis', '因为', 'because', '根据'])
        has_conclusion = any(marker in reasoning for marker in ['结论', 'Conclusion', '因此', 'Therefore', '综上'])

        metrics['has_structured_thinking'] = has_steps
        metrics['has_analysis'] = has_analysis
        metrics['has_conclusion'] = has_conclusion

        # 质量评分（0-100）
        quality_score = 0

        if metrics['word_count'] > 100:
            quality_score += 20  # 足够的推理长度

        if has_steps:
            quality_score += 30  # 有结构化思考

        if has_analysis:
            quality_score += 30  # 有分析过程

        if has_conclusion:
            quality_score += 20  # 有结论

        metrics['quality_score'] = quality_score

        return metrics

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        if not self.reasoning_traces:
            return {
                'total_traces': 0,
                'total_reasoning_tokens': 0,
                'avg_reasoning_tokens': 0,
                'avg_reasoning_length': 0
            }

        total_length = sum(len(t.reasoning_content) for t in self.reasoning_traces)

        # 按模型类型统计
        model_stats = {}
        for trace in self.reasoning_traces:
            model_type = trace.model_type.value
            if model_type not in model_stats:
                model_stats[model_type] = {
                    'count': 0,
                    'total_tokens': 0
                }

            model_stats[model_type]['count'] += 1
            model_stats[model_type]['total_tokens'] += trace.reasoning_tokens

        return {
            'total_traces': len(self.reasoning_traces),
            'total_reasoning_tokens': self.total_reasoning_tokens,
            'avg_reasoning_tokens': self.total_reasoning_tokens / len(self.reasoning_traces),
            'avg_reasoning_length': total_length / len(self.reasoning_traces),
            'model_distribution': model_stats
        }


# ============================================
# 使用示例
# ============================================

"""
from langchain_openai import ChatOpenAI
from tradingagents.middleware.reasoning_handler import ReasoningHandler, ReasoningModelType

# 创建推理处理器
reasoning_handler = ReasoningHandler(
    enable_detailed_logging=True,
    reasoning_max_display=1000
)

# 使用 OpenAI o1 模型
llm = ChatOpenAI(model="o1-preview", temperature=1)

# 执行推理
messages = [("user", "分析贵州茅台的投资价值")]
response = llm.invoke(messages)

# 提取推理
trace = reasoning_handler.extract_reasoning(response)

if trace:
    # 格式化展示
    display_text = reasoning_handler.format_reasoning_display(trace)
    print(display_text)

    # 分析质量
    quality = reasoning_handler.analyze_reasoning_quality(trace)
    print(f"推理质量评分: {quality['quality_score']}/100")

# 获取统计
stats = reasoning_handler.get_stats()
print(f"总推理次数: {stats['total_traces']}")
print(f"总推理 tokens: {stats['total_reasoning_tokens']:,}")
print(f"平均推理 tokens: {stats['avg_reasoning_tokens']:.0f}")
"""

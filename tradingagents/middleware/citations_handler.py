"""
引用处理器

支持引用溯源：
- Claude Citations（原生支持）
- RAG 应用引用（自定义实现）
- 新闻来源链接
- 财报数据溯源
"""

from typing import Dict, Any, List, Optional, Set
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from pydantic import BaseModel, Field

from tradingagents.utils.logging_manager import get_logger

logger = get_logger('middleware.citations_handler')


class CitationType(Enum):
    """引用类型"""
    CLAUDE_NATIVE = "claude_native"        # Claude 原生引用
    RAG_DOCUMENT = "rag_document"          # RAG 文档引用
    NEWS_ARTICLE = "news_article"          # 新闻文章
    FINANCIAL_REPORT = "financial_report"  # 财报
    MARKET_DATA = "market_data"            # 市场数据
    SOCIAL_MEDIA = "social_media"          # 社交媒体
    WEB_SEARCH = "web_search"              # 网页搜索
    UNKNOWN = "unknown"


@dataclass
class Citation:
    """引用数据结构"""
    citation_id: int
    citation_type: CitationType
    source_name: str
    source_content: str
    source_url: Optional[str] = None
    metadata: Dict[str, Any] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.metadata is None:
            self.metadata = {}

    def get_preview(self, max_length: int = 100) -> str:
        """获取内容预览"""
        if len(self.source_content) <= max_length:
            return self.source_content

        return self.source_content[:max_length] + "..."

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'citation_id': self.citation_id,
            'citation_type': self.citation_type.value,
            'source_name': self.source_name,
            'source_content': self.source_content,
            'source_url': self.source_url,
            'metadata': self.metadata,
            'timestamp': self.timestamp.isoformat()
        }


class CitedAnswer(BaseModel):
    """带引用的回答（Pydantic 模型）"""
    answer: str = Field(
        ...,
        description="基于给定来源的回答"
    )
    citations: List[int] = Field(
        default_factory=list,
        description="引用的来源 ID 列表"
    )
    confidence: Optional[float] = Field(
        None,
        ge=0,
        le=1,
        description="回答的置信度"
    )


class CitationsHandler:
    """
    引用处理器

    功能：
    1. 从 content_blocks 中提取引用
    2. 解析 RAG 文档引用
    3. 验证引用的有效性
    4. 格式化引用展示
    5. 追踪引用使用统计
    """

    def __init__(
        self,
        enable_citation_validation: bool = True,
        enable_duplicate_detection: bool = True
    ):
        """
        初始化引用处理器

        Args:
            enable_citation_validation: 是否验证引用有效性
            enable_duplicate_detection: 是否检测重复引用
        """
        self.enable_citation_validation = enable_citation_validation
        self.enable_duplicate_detection = enable_duplicate_detection

        self.citations: List[Citation] = []
        self.citation_counter = 0

    def extract_citations_from_content_blocks(
        self,
        content_blocks: List[Any]
    ) -> List[Citation]:
        """
        从 content_blocks 中提取引用

        Args:
            content_blocks: 内容块列表

        Returns:
            引用列表
        """
        citations = []

        for block in content_blocks:
            citation_type_str = None
            citation_data = {}

            # 提取块数据
            if isinstance(block, dict):
                citation_type_str = block.get('type', '').lower()
                citation_data = block
            elif hasattr(block, 'type'):
                citation_type_str = block.type.lower()
                citation_data = block.__dict__ if hasattr(block, '__dict__') else {}

            # 检查是否是引用块
            if citation_type_str not in ['citation', 'source', 'reference']:
                continue

            # 创建引用对象
            citation = self._create_citation_from_block(citation_data)

            if citation:
                citations.append(citation)
                self.citations.append(citation)

        if citations:
            logger.info(f"📚 [引用处理器] 从 content_blocks 提取到 {len(citations)} 个引用")

        return citations

    def extract_citations_from_rag_response(
        self,
        answer: str,
        source_documents: List[Any],
        cited_doc_ids: Optional[List[int]] = None
    ) -> List[Citation]:
        """
        从 RAG 响应中提取引用

        Args:
            answer: 回答文本
            source_documents: 源文档列表
            cited_doc_ids: 被引用的文档 ID 列表（可选）

        Returns:
            引用列表
        """
        citations = []

        # 如果没有指定引用 ID，则引用所有文档
        if cited_doc_ids is None:
            cited_doc_ids = list(range(len(source_documents)))

        for doc_id in cited_doc_ids:
            if doc_id >= len(source_documents):
                logger.warning(f"⚠️ [引用处理器] 文档 ID {doc_id} 超出范围")
                continue

            doc = source_documents[doc_id]

            # 提取文档内容
            if isinstance(doc, dict):
                content = doc.get('page_content', doc.get('content', ''))
                metadata = doc.get('metadata', {})
            elif hasattr(doc, 'page_content'):
                content = doc.page_content
                metadata = getattr(doc, 'metadata', {})
            else:
                content = str(doc)
                metadata = {}

            # 创建引用
            citation = Citation(
                citation_id=self.citation_counter + 1,
                citation_type=CitationType.RAG_DOCUMENT,
                source_name=metadata.get('source', f'Document {doc_id}'),
                source_content=content,
                source_url=metadata.get('url'),
                metadata=metadata
            )

            self.citation_counter += 1
            citations.append(citation)
            self.citations.append(citation)

        logger.info(f"📚 [引用处理器] 从 RAG 提取到 {len(citations)} 个引用")

        return citations

    def extract_citations_from_news(
        self,
        news_articles: List[Dict[str, Any]],
        cited_indices: Optional[List[int]] = None
    ) -> List[Citation]:
        """
        从新闻文章中创建引用

        Args:
            news_articles: 新闻文章列表
            cited_indices: 被引用的文章索引（可选）

        Returns:
            引用列表
        """
        citations = []

        if cited_indices is None:
            cited_indices = list(range(len(news_articles)))

        for idx in cited_indices:
            if idx >= len(news_articles):
                continue

            article = news_articles[idx]

            citation = Citation(
                citation_id=self.citation_counter + 1,
                citation_type=CitationType.NEWS_ARTICLE,
                source_name=article.get('title', f'新闻 {idx}'),
                source_content=article.get('summary', article.get('content', ''))[:500],
                source_url=article.get('url'),
                metadata={
                    'publish_date': article.get('publish_date'),
                    'source': article.get('source'),
                    'sentiment': article.get('sentiment')
                }
            )

            self.citation_counter += 1
            citations.append(citation)
            self.citations.append(citation)

        logger.info(f"📰 [引用处理器] 从新闻创建 {len(citations)} 个引用")

        return citations

    def _create_citation_from_block(self, block_data: Dict[str, Any]) -> Optional[Citation]:
        """
        从内容块创建引用对象

        Args:
            block_data: 块数据

        Returns:
            引用对象，失败返回 None
        """
        try:
            citation = Citation(
                citation_id=self.citation_counter + 1,
                citation_type=CitationType.CLAUDE_NATIVE,
                source_name=block_data.get('source', block_data.get('source_name', 'Unknown')),
                source_content=block_data.get('citation', block_data.get('content', block_data.get('text', ''))),
                source_url=block_data.get('url', block_data.get('source_url')),
                metadata=block_data.get('metadata', {})
            )

            self.citation_counter += 1
            return citation

        except Exception as e:
            logger.error(f"❌ [引用处理器] 创建引用失败: {e}")
            return None

    def validate_citations(
        self,
        answer: str,
        citations: List[Citation]
    ) -> Dict[str, Any]:
        """
        验证引用的有效性

        Args:
            answer: 回答文本
            citations: 引用列表

        Returns:
            验证结果
        """
        if not self.enable_citation_validation:
            return {'valid': True, 'issues': []}

        issues = []

        # 检查1: 是否有重复引用
        if self.enable_duplicate_detection:
            seen_contents = set()
            for citation in citations:
                content_hash = hash(citation.source_content)

                if content_hash in seen_contents:
                    issues.append(f"发现重复引用: {citation.source_name}")

                seen_contents.add(content_hash)

        # 检查2: 引用是否为空
        for citation in citations:
            if not citation.source_content or len(citation.source_content.strip()) < 10:
                issues.append(f"引用 [{citation.citation_id}] 内容过短或为空")

        # 检查3: URL 有效性（简单检查）
        for citation in citations:
            if citation.source_url:
                if not citation.source_url.startswith(('http://', 'https://')):
                    issues.append(f"引用 [{citation.citation_id}] URL 格式不正确: {citation.source_url}")

        # 检查4: 引用ID在答案中是否被使用
        for citation in citations:
            # 检查答案中是否提到引用ID
            citation_marker = f"[{citation.citation_id}]"
            if citation_marker not in answer:
                issues.append(f"引用 [{citation.citation_id}] 在答案中未被引用")

        validation_result = {
            'valid': len(issues) == 0,
            'total_citations': len(citations),
            'issues_count': len(issues),
            'issues': issues
        }

        if issues:
            logger.warning(f"⚠️ [引用处理器] 发现 {len(issues)} 个引用问题")

        return validation_result

    def format_citations_display(
        self,
        citations: List[Citation],
        include_content: bool = True,
        max_content_length: int = 200
    ) -> str:
        """
        格式化引用展示

        Args:
            citations: 引用列表
            include_content: 是否包含引用内容
            max_content_length: 内容最大长度

        Returns:
            格式化的展示文本
        """
        if not citations:
            return ""

        lines = ["---", "## 📚 引用来源", ""]

        for citation in citations:
            # 引用标题
            lines.append(f"**[{citation.citation_id}] {citation.source_name}**")

            # 引用类型
            type_emoji = {
                CitationType.CLAUDE_NATIVE: "🤖",
                CitationType.RAG_DOCUMENT: "📄",
                CitationType.NEWS_ARTICLE: "📰",
                CitationType.FINANCIAL_REPORT: "📊",
                CitationType.MARKET_DATA: "💹",
                CitationType.SOCIAL_MEDIA: "💬",
                CitationType.WEB_SEARCH: "🔍"
            }

            emoji = type_emoji.get(citation.citation_type, "📎")
            lines.append(f"{emoji} *类型: {citation.citation_type.value}*")

            # 引用内容
            if include_content:
                preview = citation.get_preview(max_content_length)
                lines.append(f"> {preview}")

            # URL 链接
            if citation.source_url:
                lines.append(f"🔗 [{citation.source_url}]({citation.source_url})")

            # 元信息
            if citation.metadata:
                # 只显示重要的元信息
                important_keys = ['publish_date', 'source', 'author', 'sentiment']
                metadata_items = []

                for key in important_keys:
                    if key in citation.metadata:
                        value = citation.metadata[key]
                        metadata_items.append(f"{key}: {value}")

                if metadata_items:
                    lines.append(f"*{', '.join(metadata_items)}*")

            lines.append("")

        lines.append(f"*📖 共引用 {len(citations)} 个来源*")
        lines.append("---")

        return "\n".join(lines)

    def get_citation_by_id(self, citation_id: int) -> Optional[Citation]:
        """根据 ID 获取引用"""
        for citation in self.citations:
            if citation.citation_id == citation_id:
                return citation

        return None

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        if not self.citations:
            return {
                'total_citations': 0,
                'by_type': {}
            }

        # 按类型统计
        by_type = {}
        for citation in self.citations:
            citation_type = citation.citation_type.value

            if citation_type not in by_type:
                by_type[citation_type] = 0

            by_type[citation_type] += 1

        # 统计有URL的引用
        citations_with_url = sum(1 for c in self.citations if c.source_url)

        return {
            'total_citations': len(self.citations),
            'by_type': by_type,
            'citations_with_url': citations_with_url,
            'citations_with_url_rate': citations_with_url / len(self.citations) if self.citations else 0
        }


# ============================================
# 使用示例
# ============================================

"""
from langchain_anthropic import ChatAnthropic
from tradingagents.middleware.citations_handler import CitationsHandler, CitationType

# 创建引用处理器
citations_handler = CitationsHandler(
    enable_citation_validation=True,
    enable_duplicate_detection=True
)

# 场景1: 从 Claude content_blocks 提取引用
llm = ChatAnthropic(model="claude-3-opus-20240229")
response = llm.invoke("分析贵州茅台，并提供引用来源")

if hasattr(response, 'content_blocks'):
    citations = citations_handler.extract_citations_from_content_blocks(response.content_blocks)

    # 格式化展示
    display_text = citations_handler.format_citations_display(citations)
    print(display_text)

# 场景2: 从 RAG 响应提取引用
answer = "根据财报数据，贵州茅台2023年营收达到1234亿元[1]，净利润456亿元[2]"
source_documents = [
    {"page_content": "贵州茅台2023年年报...", "metadata": {"source": "2023年报", "url": "https://..."}},
    {"page_content": "贵州茅台利润表...", "metadata": {"source": "利润表", "url": "https://..."}}
]
cited_doc_ids = [0, 1]

citations = citations_handler.extract_citations_from_rag_response(
    answer, source_documents, cited_doc_ids
)

# 验证引用
validation = citations_handler.validate_citations(answer, citations)
if not validation['valid']:
    print(f"引用问题: {validation['issues']}")

# 场景3: 从新闻创建引用
news_articles = [
    {
        "title": "贵州茅台股价创新高",
        "summary": "今日贵州茅台股价上涨5%...",
        "url": "https://news.example.com/1",
        "publish_date": "2024-01-15",
        "source": "财经日报"
    }
]

news_citations = citations_handler.extract_citations_from_news(news_articles)

# 获取统计
stats = citations_handler.get_stats()
print(f"总引用数: {stats['total_citations']}")
print(f"按类型: {stats['by_type']}")
"""

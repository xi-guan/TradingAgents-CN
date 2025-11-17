"""
向量存储服务 - 基于 Qdrant
提供新闻、研报、财报等文本的向量存储和语义检索
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import hashlib

from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    Range,
    DatetimeRange,
)

from app.core.database_v2 import get_async_qdrant_client, get_qdrant_client

logger = logging.getLogger(__name__)


# ============================================================================
# 向量存储服务
# ============================================================================

class VectorStoreService:
    """Qdrant 向量存储服务"""

    # 集合配置
    COLLECTIONS = {
        "financial_news": {
            "description": "金融新闻向量存储",
            "vector_size": 1536,  # OpenAI text-embedding-ada-002
            "distance": Distance.COSINE,
        },
        "research_reports": {
            "description": "研究报告向量存储",
            "vector_size": 1536,
            "distance": Distance.COSINE,
        },
        "earnings_calls": {
            "description": "财报电话会议向量存储",
            "vector_size": 1536,
            "distance": Distance.COSINE,
        },
    }

    @staticmethod
    async def init_collections():
        """初始化所有集合"""
        try:
            client = get_async_qdrant_client()

            # 获取现有集合
            collections = await client.get_collections()
            existing_names = [col.name for col in collections.collections]

            # 创建缺失的集合
            for name, config in VectorStoreService.COLLECTIONS.items():
                if name not in existing_names:
                    await client.create_collection(
                        collection_name=name,
                        vectors_config=VectorParams(
                            size=config["vector_size"],
                            distance=config["distance"]
                        )
                    )
                    logger.info(f"✅ 创建向量集合: {name}")
                else:
                    logger.info(f"📋 集合已存在: {name}")

            logger.info("✅ 所有向量集合初始化完成")

        except Exception as e:
            logger.error(f"❌ 初始化向量集合失败: {e}")
            raise

    @staticmethod
    def _generate_id(content: str) -> str:
        """根据内容生成唯一ID"""
        return hashlib.md5(content.encode()).hexdigest()


# ============================================================================
# 新闻向量服务
# ============================================================================

class NewsVectorService:
    """新闻向量存储服务"""

    COLLECTION_NAME = "financial_news"

    @staticmethod
    async def add_news(
        news_id: str,
        title: str,
        content: str,
        embedding: List[float],
        metadata: Dict[str, Any]
    ) -> bool:
        """
        添加新闻向量

        Args:
            news_id: 新闻ID
            title: 标题
            content: 内容
            embedding: 向量（1536维）
            metadata: 元数据（date, source, symbols, industry等）

        Returns:
            成功返回 True
        """
        try:
            client = get_async_qdrant_client()

            # 构建 payload
            payload = {
                "title": title,
                "content": content[:500],  # 存储前500字符
                "date": metadata.get("date"),
                "source": metadata.get("source"),
                "symbols": metadata.get("symbols", []),
                "industry": metadata.get("industry"),
                "sentiment": metadata.get("sentiment"),
                "sentiment_score": metadata.get("sentiment_score"),
                "category": metadata.get("category"),
                "url": metadata.get("url"),
                "created_at": datetime.now().isoformat(),
            }

            # 插入向量
            await client.upsert(
                collection_name=NewsVectorService.COLLECTION_NAME,
                points=[
                    PointStruct(
                        id=news_id,
                        vector=embedding,
                        payload=payload
                    )
                ]
            )

            logger.info(f"✅ 新闻向量已保存: {news_id}")
            return True

        except Exception as e:
            logger.error(f"❌ 保存新闻向量失败: {e}")
            return False

    @staticmethod
    async def search_news(
        query_vector: List[float],
        symbols: Optional[List[str]] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        industry: Optional[str] = None,
        sentiment: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        搜索相关新闻

        Args:
            query_vector: 查询向量
            symbols: 股票代码列表
            date_from: 起始日期（YYYY-MM-DD）
            date_to: 结束日期（YYYY-MM-DD）
            industry: 行业
            sentiment: 情绪（positive/negative/neutral）
            limit: 返回数量

        Returns:
            相关新闻列表（按相似度排序）
        """
        try:
            client = get_async_qdrant_client()

            # 构建过滤条件
            must_conditions = []

            if symbols:
                for symbol in symbols:
                    must_conditions.append(
                        FieldCondition(
                            key="symbols",
                            match=MatchValue(value=symbol)
                        )
                    )

            if date_from or date_to:
                must_conditions.append(
                    FieldCondition(
                        key="date",
                        range=Range(
                            gte=date_from if date_from else None,
                            lte=date_to if date_to else None
                        )
                    )
                )

            if industry:
                must_conditions.append(
                    FieldCondition(
                        key="industry",
                        match=MatchValue(value=industry)
                    )
                )

            if sentiment:
                must_conditions.append(
                    FieldCondition(
                        key="sentiment",
                        match=MatchValue(value=sentiment)
                    )
                )

            # 构建过滤器
            query_filter = Filter(must=must_conditions) if must_conditions else None

            # 执行搜索
            results = await client.search(
                collection_name=NewsVectorService.COLLECTION_NAME,
                query_vector=query_vector,
                query_filter=query_filter,
                limit=limit
            )

            # 格式化结果
            news_list = []
            for result in results:
                news_list.append({
                    "id": result.id,
                    "score": result.score,
                    **result.payload
                })

            logger.info(f"✅ 搜索到 {len(news_list)} 条相关新闻")
            return news_list

        except Exception as e:
            logger.error(f"❌ 搜索新闻失败: {e}")
            return []


# ============================================================================
# 研报向量服务
# ============================================================================

class ResearchReportVectorService:
    """研究报告向量服务"""

    COLLECTION_NAME = "research_reports"

    @staticmethod
    async def add_report(
        report_id: str,
        title: str,
        content: str,
        embedding: List[float],
        metadata: Dict[str, Any]
    ) -> bool:
        """
        添加研报向量

        Args:
            report_id: 报告ID
            title: 标题
            content: 内容
            embedding: 向量
            metadata: 元数据（company, analyst, rating, target_price等）

        Returns:
            成功返回 True
        """
        try:
            client = get_async_qdrant_client()

            payload = {
                "title": title,
                "summary": content[:1000],
                "company": metadata.get("company"),
                "symbols": metadata.get("symbols", []),
                "analyst": metadata.get("analyst"),
                "institution": metadata.get("institution"),
                "rating": metadata.get("rating"),
                "target_price": metadata.get("target_price"),
                "publish_date": metadata.get("publish_date"),
                "industry": metadata.get("industry"),
                "report_type": metadata.get("report_type"),
                "created_at": datetime.now().isoformat(),
            }

            await client.upsert(
                collection_name=ResearchReportVectorService.COLLECTION_NAME,
                points=[
                    PointStruct(
                        id=report_id,
                        vector=embedding,
                        payload=payload
                    )
                ]
            )

            logger.info(f"✅ 研报向量已保存: {report_id}")
            return True

        except Exception as e:
            logger.error(f"❌ 保存研报向量失败: {e}")
            return False

    @staticmethod
    async def search_reports(
        query_vector: List[float],
        company: Optional[str] = None,
        symbols: Optional[List[str]] = None,
        rating: Optional[str] = None,
        analyst: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        搜索相关研报

        Args:
            query_vector: 查询向量
            company: 公司名称
            symbols: 股票代码列表
            rating: 评级（买入/增持/中性/减持/卖出）
            analyst: 分析师姓名
            limit: 返回数量

        Returns:
            相关研报列表
        """
        try:
            client = get_async_qdrant_client()

            must_conditions = []

            if company:
                must_conditions.append(
                    FieldCondition(key="company", match=MatchValue(value=company))
                )

            if symbols:
                for symbol in symbols:
                    must_conditions.append(
                        FieldCondition(key="symbols", match=MatchValue(value=symbol))
                    )

            if rating:
                must_conditions.append(
                    FieldCondition(key="rating", match=MatchValue(value=rating))
                )

            if analyst:
                must_conditions.append(
                    FieldCondition(key="analyst", match=MatchValue(value=analyst))
                )

            query_filter = Filter(must=must_conditions) if must_conditions else None

            results = await client.search(
                collection_name=ResearchReportVectorService.COLLECTION_NAME,
                query_vector=query_vector,
                query_filter=query_filter,
                limit=limit
            )

            reports = [
                {
                    "id": result.id,
                    "score": result.score,
                    **result.payload
                }
                for result in results
            ]

            logger.info(f"✅ 搜索到 {len(reports)} 篇相关研报")
            return reports

        except Exception as e:
            logger.error(f"❌ 搜索研报失败: {e}")
            return []


# ============================================================================
# 财报电话会议向量服务
# ============================================================================

class EarningsCallVectorService:
    """财报电话会议向量服务"""

    COLLECTION_NAME = "earnings_calls"

    @staticmethod
    async def add_earnings_call(
        call_id: str,
        transcript: str,
        embedding: List[float],
        metadata: Dict[str, Any]
    ) -> bool:
        """
        添加财报电话会议向量

        Args:
            call_id: 会议ID
            transcript: 会议文字稿
            embedding: 向量
            metadata: 元数据（company, quarter, year等）

        Returns:
            成功返回 True
        """
        try:
            client = get_async_qdrant_client()

            payload = {
                "transcript_excerpt": transcript[:2000],
                "company": metadata.get("company"),
                "symbol": metadata.get("symbol"),
                "quarter": metadata.get("quarter"),
                "year": metadata.get("year"),
                "call_date": metadata.get("call_date"),
                "participants": metadata.get("participants", []),
                "topics": metadata.get("topics", []),
                "sentiment": metadata.get("sentiment"),
                "created_at": datetime.now().isoformat(),
            }

            await client.upsert(
                collection_name=EarningsCallVectorService.COLLECTION_NAME,
                points=[
                    PointStruct(
                        id=call_id,
                        vector=embedding,
                        payload=payload
                    )
                ]
            )

            logger.info(f"✅ 财报会议向量已保存: {call_id}")
            return True

        except Exception as e:
            logger.error(f"❌ 保存财报会议向量失败: {e}")
            return False

    @staticmethod
    async def search_earnings_calls(
        query_vector: List[float],
        symbol: Optional[str] = None,
        year: Optional[int] = None,
        quarter: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        搜索相关财报会议

        Args:
            query_vector: 查询向量
            symbol: 股票代码
            year: 年份
            quarter: 季度（Q1/Q2/Q3/Q4）
            limit: 返回数量

        Returns:
            相关会议列表
        """
        try:
            client = get_async_qdrant_client()

            must_conditions = []

            if symbol:
                must_conditions.append(
                    FieldCondition(key="symbol", match=MatchValue(value=symbol))
                )

            if year:
                must_conditions.append(
                    FieldCondition(key="year", match=MatchValue(value=year))
                )

            if quarter:
                must_conditions.append(
                    FieldCondition(key="quarter", match=MatchValue(value=quarter))
                )

            query_filter = Filter(must=must_conditions) if must_conditions else None

            results = await client.search(
                collection_name=EarningsCallVectorService.COLLECTION_NAME,
                query_vector=query_vector,
                query_filter=query_filter,
                limit=limit
            )

            calls = [
                {
                    "id": result.id,
                    "score": result.score,
                    **result.payload
                }
                for result in results
            ]

            logger.info(f"✅ 搜索到 {len(calls)} 场相关财报会议")
            return calls

        except Exception as e:
            logger.error(f"❌ 搜索财报会议失败: {e}")
            return []


# ============================================================================
# 导出服务实例
# ============================================================================

vector_store_service = VectorStoreService()
news_vector_service = NewsVectorService()
research_vector_service = ResearchReportVectorService()
earnings_vector_service = EarningsCallVectorService()

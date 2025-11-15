"""
数据库连接管理模块 V2
支持 TimescaleDB + Qdrant + Redis
"""

import logging
import asyncio
from typing import Optional, AsyncGenerator
from contextlib import asynccontextmanager

# PostgreSQL/TimescaleDB
import asyncpg
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool

# Qdrant
from qdrant_client import QdrantClient
from qdrant_client.async_qdrant_client import AsyncQdrantClient

# Redis
from redis.asyncio import Redis, ConnectionPool
from redis.exceptions import ConnectionError as RedisConnectionError

# Config
from .config import settings

logger = logging.getLogger(__name__)

# SQLAlchemy Base
Base = declarative_base()

# ============================================================================
# 全局连接实例
# ============================================================================

# PostgreSQL/TimescaleDB
pg_pool: Optional[asyncpg.Pool] = None
async_engine = None
async_session_maker: Optional[async_sessionmaker] = None

# Qdrant
qdrant_client: Optional[QdrantClient] = None
async_qdrant_client: Optional[AsyncQdrantClient] = None

# Redis
redis_client: Optional[Redis] = None
redis_pool: Optional[ConnectionPool] = None


# ============================================================================
# PostgreSQL/TimescaleDB 连接管理
# ============================================================================

class PostgreSQLManager:
    """PostgreSQL/TimescaleDB 连接管理器"""

    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        self._healthy = False

    async def init_pool(self):
        """初始化 asyncpg 连接池"""
        try:
            logger.info("🔄 正在初始化 PostgreSQL/TimescaleDB 连接池...")

            self.pool = await asyncpg.create_pool(
                host=settings.POSTGRES_HOST,
                port=settings.POSTGRES_PORT,
                database=settings.POSTGRES_DB,
                user=settings.POSTGRES_USER,
                password=settings.POSTGRES_PASSWORD,
                min_size=settings.POSTGRES_MIN_CONNECTIONS,
                max_size=settings.POSTGRES_MAX_CONNECTIONS,
                command_timeout=60,
                timeout=30,
            )

            # 测试连接
            async with self.pool.acquire() as conn:
                version = await conn.fetchval('SELECT version()')
                ts_version = await conn.fetchval(
                    "SELECT extversion FROM pg_extension WHERE extname = 'timescaledb'"
                )
                logger.info(f"✅ PostgreSQL 版本: {version}")
                if ts_version:
                    logger.info(f"✅ TimescaleDB 版本: {ts_version}")
                else:
                    logger.warning("⚠️ TimescaleDB 扩展未安装")

            self._healthy = True
            logger.info(
                f"✅ PostgreSQL 连接池初始化成功 "
                f"({settings.POSTGRES_MIN_CONNECTIONS}-{settings.POSTGRES_MAX_CONNECTIONS} 连接)"
            )

        except Exception as e:
            logger.error(f"❌ PostgreSQL 连接池初始化失败: {e}")
            self._healthy = False
            raise

    async def init_sqlalchemy(self):
        """初始化 SQLAlchemy 异步引擎"""
        try:
            global async_engine, async_session_maker

            logger.info("🔄 正在初始化 SQLAlchemy 异步引擎...")

            # 构建异步连接字符串
            database_url = (
                f"postgresql+asyncpg://{settings.POSTGRES_USER}:"
                f"{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:"
                f"{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
            )

            async_engine = create_async_engine(
                database_url,
                echo=settings.DEBUG,
                pool_pre_ping=True,
                pool_recycle=3600,
                poolclass=NullPool,  # 使用 asyncpg 连接池，不使用 SQLAlchemy 连接池
            )

            async_session_maker = async_sessionmaker(
                async_engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )

            logger.info("✅ SQLAlchemy 异步引擎初始化成功")

        except Exception as e:
            logger.error(f"❌ SQLAlchemy 引擎初始化失败: {e}")
            raise

    async def close(self):
        """关闭连接池"""
        logger.info("🔄 正在关闭 PostgreSQL 连接...")

        if self.pool:
            await self.pool.close()
            self._healthy = False
            logger.info("✅ PostgreSQL 连接池已关闭")

        if async_engine:
            await async_engine.dispose()
            logger.info("✅ SQLAlchemy 引擎已关闭")

    async def health_check(self) -> dict:
        """健康检查"""
        status = {"status": "unknown", "details": None}

        try:
            if self.pool:
                async with self.pool.acquire() as conn:
                    result = await conn.fetchval('SELECT 1')
                    if result == 1:
                        status = {
                            "status": "healthy",
                            "details": {
                                "pool_size": self.pool.get_size(),
                                "free_connections": self.pool.get_free_size(),
                            }
                        }
                        self._healthy = True
            else:
                status["status"] = "disconnected"
        except Exception as e:
            status = {"status": "unhealthy", "details": {"error": str(e)}}
            self._healthy = False

        return status

    @property
    def is_healthy(self) -> bool:
        return self._healthy


# ============================================================================
# Qdrant 连接管理
# ============================================================================

class QdrantManager:
    """Qdrant 向量数据库连接管理器"""

    def __init__(self):
        self.client: Optional[QdrantClient] = None
        self.async_client: Optional[AsyncQdrantClient] = None
        self._healthy = False

    async def init_client(self):
        """初始化 Qdrant 客户端"""
        try:
            logger.info("🔄 正在初始化 Qdrant 向量数据库连接...")

            # 同步客户端（用于非异步上下文）
            self.client = QdrantClient(
                host=settings.QDRANT_HOST,
                port=settings.QDRANT_PORT,
                api_key=settings.QDRANT_API_KEY if settings.QDRANT_API_KEY else None,
                timeout=30,
            )

            # 异步客户端（推荐使用）
            self.async_client = AsyncQdrantClient(
                host=settings.QDRANT_HOST,
                port=settings.QDRANT_PORT,
                api_key=settings.QDRANT_API_KEY if settings.QDRANT_API_KEY else None,
                timeout=30,
            )

            # 测试连接
            collections = await self.async_client.get_collections()
            self._healthy = True

            logger.info("✅ Qdrant 连接成功建立")
            logger.info(f"📊 现有集合数量: {len(collections.collections)}")

        except Exception as e:
            logger.error(f"❌ Qdrant 连接失败: {e}")
            self._healthy = False
            raise

    async def close(self):
        """关闭 Qdrant 连接"""
        logger.info("🔄 正在关闭 Qdrant 连接...")

        if self.async_client:
            await self.async_client.close()
            self._healthy = False
            logger.info("✅ Qdrant 连接已关闭")

    async def health_check(self) -> dict:
        """健康检查"""
        status = {"status": "unknown", "details": None}

        try:
            if self.async_client:
                collections = await self.async_client.get_collections()
                status = {
                    "status": "healthy",
                    "details": {"collections_count": len(collections.collections)}
                }
                self._healthy = True
            else:
                status["status"] = "disconnected"
        except Exception as e:
            status = {"status": "unhealthy", "details": {"error": str(e)}}
            self._healthy = False

        return status

    @property
    def is_healthy(self) -> bool:
        return self._healthy


# ============================================================================
# Redis 连接管理
# ============================================================================

class RedisManager:
    """Redis 缓存连接管理器"""

    def __init__(self):
        self.client: Optional[Redis] = None
        self.pool: Optional[ConnectionPool] = None
        self._healthy = False

    async def init_client(self):
        """初始化 Redis 连接"""
        try:
            logger.info("🔄 正在初始化 Redis 连接...")

            # 创建连接池
            self.pool = ConnectionPool.from_url(
                settings.REDIS_URL,
                max_connections=settings.REDIS_MAX_CONNECTIONS,
                retry_on_timeout=settings.REDIS_RETRY_ON_TIMEOUT,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=10,
            )

            # 创建客户端
            self.client = Redis(connection_pool=self.pool)

            # 测试连接
            await self.client.ping()
            self._healthy = True

            logger.info("✅ Redis 连接成功建立")
            logger.info(f"🔗 连接池大小: {settings.REDIS_MAX_CONNECTIONS}")

        except Exception as e:
            logger.error(f"❌ Redis 连接失败: {e}")
            self._healthy = False
            raise

    async def close(self):
        """关闭 Redis 连接"""
        logger.info("🔄 正在关闭 Redis 连接...")

        if self.client:
            await self.client.close()
            self._healthy = False
            logger.info("✅ Redis 连接已关闭")

        if self.pool:
            await self.pool.disconnect()
            logger.info("✅ Redis 连接池已关闭")

    async def health_check(self) -> dict:
        """健康检查"""
        status = {"status": "unknown", "details": None}

        try:
            if self.client:
                result = await self.client.ping()
                if result:
                    status = {"status": "healthy", "details": {"ping": "pong"}}
                    self._healthy = True
            else:
                status["status"] = "disconnected"
        except Exception as e:
            status = {"status": "unhealthy", "details": {"error": str(e)}}
            self._healthy = False

        return status

    @property
    def is_healthy(self) -> bool:
        return self._healthy


# ============================================================================
# 全局管理器实例
# ============================================================================

pg_manager = PostgreSQLManager()
qdrant_manager = QdrantManager()
redis_manager = RedisManager()


# ============================================================================
# 数据库初始化和关闭函数
# ============================================================================

async def init_database():
    """初始化所有数据库连接"""
    global pg_pool, redis_client, redis_pool, qdrant_client, async_qdrant_client

    try:
        # 1. 初始化 PostgreSQL/TimescaleDB
        await pg_manager.init_pool()
        await pg_manager.init_sqlalchemy()
        pg_pool = pg_manager.pool

        # 2. 初始化 Qdrant
        await qdrant_manager.init_client()
        qdrant_client = qdrant_manager.client
        async_qdrant_client = qdrant_manager.async_client

        # 3. 初始化 Redis
        await redis_manager.init_client()
        redis_client = redis_manager.client
        redis_pool = redis_manager.pool

        logger.info("🎉 所有数据库连接初始化完成")

    except Exception as e:
        logger.error(f"💥 数据库初始化失败: {e}")
        raise


async def close_database():
    """关闭所有数据库连接"""
    global pg_pool, redis_client, redis_pool, qdrant_client, async_qdrant_client

    await pg_manager.close()
    await qdrant_manager.close()
    await redis_manager.close()

    # 清空全局变量
    pg_pool = None
    redis_client = None
    redis_pool = None
    qdrant_client = None
    async_qdrant_client = None


async def get_database_health() -> dict:
    """获取所有数据库健康状态"""
    return {
        "postgresql": await pg_manager.health_check(),
        "qdrant": await qdrant_manager.health_check(),
        "redis": await redis_manager.health_check(),
    }


# ============================================================================
# 依赖注入函数（用于 FastAPI）
# ============================================================================

def get_pg_pool() -> asyncpg.Pool:
    """获取 PostgreSQL 连接池"""
    if pg_pool is None:
        raise RuntimeError("PostgreSQL 连接池未初始化")
    return pg_pool


async def get_pg_connection() -> asyncpg.Connection:
    """获取 PostgreSQL 连接（用于依赖注入）"""
    pool = get_pg_pool()
    async with pool.acquire() as conn:
        yield conn


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """获取 SQLAlchemy 异步会话（上下文管理器）"""
    if async_session_maker is None:
        raise RuntimeError("SQLAlchemy Session Maker 未初始化")

    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_qdrant_client() -> QdrantClient:
    """获取 Qdrant 同步客户端"""
    if qdrant_client is None:
        raise RuntimeError("Qdrant 客户端未初始化")
    return qdrant_client


def get_async_qdrant_client() -> AsyncQdrantClient:
    """获取 Qdrant 异步客户端"""
    if async_qdrant_client is None:
        raise RuntimeError("Qdrant 异步客户端未初始化")
    return async_qdrant_client


def get_redis_client() -> Redis:
    """获取 Redis 客户端"""
    if redis_client is None:
        raise RuntimeError("Redis 客户端未初始化")
    return redis_client


# ============================================================================
# 兼容性别名
# ============================================================================

init_db = init_database
close_db = close_database
get_database = get_pg_pool


# ============================================================================
# 工具函数
# ============================================================================

async def execute_sql(query: str, *args):
    """执行 SQL 查询（使用 asyncpg）"""
    pool = get_pg_pool()
    async with pool.acquire() as conn:
        return await conn.fetch(query, *args)


async def execute_sql_one(query: str, *args):
    """执行 SQL 查询并返回单条记录"""
    pool = get_pg_pool()
    async with pool.acquire() as conn:
        return await conn.fetchrow(query, *args)


async def execute_sql_value(query: str, *args):
    """执行 SQL 查询并返回单个值"""
    pool = get_pg_pool()
    async with pool.acquire() as conn:
        return await conn.fetchval(query, *args)

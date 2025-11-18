from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Dict, Any
import os
import warnings
from pathlib import Path
import yaml

# Legacy env var aliases (deprecated): map API_HOST/PORT/DEBUG -> HOST/PORT/DEBUG
_LEGACY_ENV_ALIASES = {
    "API_HOST": "HOST",
    "API_PORT": "PORT",
    "API_DEBUG": "DEBUG",
}
for _legacy, _new in _LEGACY_ENV_ALIASES.items():
    if _new not in os.environ and _legacy in os.environ:
        os.environ[_new] = os.environ[_legacy]
        warnings.warn(
            f"Environment variable {_legacy} is deprecated; use {_new} instead.",
            DeprecationWarning,
            stacklevel=2,
        )


def load_yaml_config() -> Dict[str, Any]:
    """
    从 config/local.yaml 加载配置

    Returns:
        配置字典，如果文件不存在则返回空字典
    """
    # 获取项目根目录
    # 从 backend/app/core/config.py 向上4层到达项目根目录
    project_root = Path(__file__).parent.parent.parent.parent
    config_file = project_root / "config" / "local.yaml"

    if not config_file.exists():
        # 配置文件不存在时，返回空字典
        # 这允许系统使用环境变量或默认值
        return {}

    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # 将嵌套的YAML配置扁平化为环境变量格式
        flat_config = _flatten_yaml_config(config)
        return flat_config
    except Exception as e:
        warnings.warn(
            f"Failed to load config/local.yaml: {e}. Using environment variables instead.",
            stacklevel=2,
        )
        return {}


def _flatten_yaml_config(data: Dict[str, Any], parent_key: str = '', sep: str = '_') -> Dict[str, Any]:
    """
    将嵌套的YAML配置扁平化为环境变量格式

    例如:
        {'database': {'timescaledb': {'host': 'localhost'}}}
    转换为:
        {'DATABASE_TIMESCALEDB_HOST': 'localhost'}

    Args:
        data: 输入配置字典
        parent_key: 父键名
        sep: 分隔符

    Returns:
        扁平化的配置字典
    """
    items = []
    for k, v in data.items():
        new_key = f"{parent_key}{sep}{k}".upper() if parent_key else k.upper()

        if isinstance(v, dict):
            items.extend(_flatten_yaml_config(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            # 列表转换为逗号分隔的字符串
            items.append((new_key, ','.join(map(str, v))))
        elif v is not None:
            items.append((new_key, v))

    return dict(items)


def _get_yaml_to_env_mappings() -> Dict[str, str]:
    """
    获取YAML配置键到环境变量名的映射

    Returns:
        映射字典 {YAML_KEY: ENV_VAR_NAME}
    """
    return {
        # 应用配置
        'APP_HOST': 'HOST',
        'APP_PORT': 'PORT',
        'APP_DEBUG': 'DEBUG',
        'APP_TIMEZONE': 'TIMEZONE',

        # TimescaleDB 配置
        'DATABASE_TIMESCALEDB_HOST': 'POSTGRES_HOST',
        'DATABASE_TIMESCALEDB_PORT': 'POSTGRES_PORT',
        'DATABASE_TIMESCALEDB_DATABASE': 'POSTGRES_DB',
        'DATABASE_TIMESCALEDB_USERNAME': 'POSTGRES_USER',
        'DATABASE_TIMESCALEDB_PASSWORD': 'POSTGRES_PASSWORD',
        'DATABASE_TIMESCALEDB_MIN_CONNECTIONS': 'POSTGRES_MIN_CONNECTIONS',
        'DATABASE_TIMESCALEDB_MAX_CONNECTIONS': 'POSTGRES_MAX_CONNECTIONS',

        # Qdrant 配置
        'DATABASE_QDRANT_HOST': 'QDRANT_HOST',
        'DATABASE_QDRANT_PORT': 'QDRANT_PORT',
        'DATABASE_QDRANT_GRPC_PORT': 'QDRANT_GRPC_PORT',
        'DATABASE_QDRANT_API_KEY': 'QDRANT_API_KEY',

        # Redis 配置
        'DATABASE_REDIS_HOST': 'REDIS_HOST',
        'DATABASE_REDIS_PORT': 'REDIS_PORT',
        'DATABASE_REDIS_PASSWORD': 'REDIS_PASSWORD',
        'DATABASE_REDIS_DB': 'REDIS_DB',
        'DATABASE_REDIS_MAX_CONNECTIONS': 'REDIS_MAX_CONNECTIONS',

        # JWT 配置
        'SECURITY_JWT_SECRET': 'JWT_SECRET',
        'SECURITY_JWT_ALGORITHM': 'JWT_ALGORITHM',
        'SECURITY_JWT_ACCESS_TOKEN_EXPIRE_MINUTES': 'ACCESS_TOKEN_EXPIRE_MINUTES',
        'SECURITY_JWT_REFRESH_TOKEN_EXPIRE_DAYS': 'REFRESH_TOKEN_EXPIRE_DAYS',

        # CSRF 配置
        'SECURITY_CSRF_SECRET': 'CSRF_SECRET',

        # Bcrypt 配置
        'SECURITY_BCRYPT_ROUNDS': 'BCRYPT_ROUNDS',

        # 数据源配置
        'DATA_SOURCES_TUSHARE_TOKEN': 'TUSHARE_TOKEN',
        'DATA_SOURCES_TUSHARE_ENABLED': 'TUSHARE_ENABLED',
        'DATA_SOURCES_TUSHARE_TIER': 'TUSHARE_TIER',

        # LLM 配置
        'LLM_OPENAI_API_KEY': 'OPENAI_API_KEY',
        'LLM_ANTHROPIC_API_KEY': 'ANTHROPIC_API_KEY',
        'LLM_GOOGLE_API_KEY': 'GOOGLE_API_KEY',

        # 日志配置
        'LOGGING_LEVEL': 'LOG_LEVEL',
        'LOGGING_FORMAT': 'LOG_FORMAT',
        'LOGGING_FILE': 'LOG_FILE',

        # 缓存配置
        'CACHE_TTL': 'CACHE_TTL',
        'CACHE_SCREENING_TTL': 'SCREENING_CACHE_TTL',

        # 限流配置
        'LIMITS_RATE_LIMIT_ENABLED': 'RATE_LIMIT_ENABLED',
        'LIMITS_RATE_LIMIT_DEFAULT_LIMIT': 'DEFAULT_RATE_LIMIT',
        'LIMITS_CONCURRENCY_USER_LIMIT': 'DEFAULT_USER_CONCURRENT_LIMIT',
        'LIMITS_CONCURRENCY_GLOBAL_LIMIT': 'GLOBAL_CONCURRENT_LIMIT',
        'LIMITS_QUOTA_DAILY_LIMIT': 'DEFAULT_DAILY_QUOTA',

        # CORS 配置
        'CORS_ALLOWED_ORIGINS': 'ALLOWED_ORIGINS',
        'CORS_ALLOW_CREDENTIALS': 'ALLOW_CREDENTIALS',

        # 文件上传配置
        'UPLOAD_MAX_SIZE': 'MAX_UPLOAD_SIZE',
        'UPLOAD_UPLOAD_DIR': 'UPLOAD_DIR',

        # 代理配置
        'PROXY_HTTP_PROXY': 'HTTP_PROXY',
        'PROXY_HTTPS_PROXY': 'HTTPS_PROXY',
        'PROXY_NO_PROXY': 'NO_PROXY',

        # 任务调度配置
        'SCHEDULER_STOCK_BASICS_SYNC_ENABLED': 'SYNC_STOCK_BASICS_ENABLED',
        'SCHEDULER_STOCK_BASICS_SYNC_CRON': 'SYNC_STOCK_BASICS_CRON',
        'SCHEDULER_QUOTES_INGEST_ENABLED': 'QUOTES_INGEST_ENABLED',
        'SCHEDULER_QUOTES_INGEST_INTERVAL_SECONDS': 'QUOTES_INGEST_INTERVAL_SECONDS',
        'SCHEDULER_NEWS_SYNC_ENABLED': 'NEWS_SYNC_ENABLED',
        'SCHEDULER_NEWS_SYNC_CRON': 'NEWS_SYNC_CRON',
    }


def _merge_yaml_to_env():
    """
    将YAML配置合并到环境变量
    优先级: 环境变量 > YAML配置 > 默认值
    """
    yaml_config = load_yaml_config()
    mappings = _get_yaml_to_env_mappings()

    for yaml_key, value in yaml_config.items():
        # 使用映射表转换键名
        env_key = mappings.get(yaml_key, yaml_key)

        # 只有当环境变量不存在时，才使用YAML配置
        if env_key not in os.environ:
            os.environ[env_key] = str(value)


# 在加载Settings之前，先将YAML配置合并到环境变量
_merge_yaml_to_env()


class Settings(BaseSettings):
    # 基础配置
    DEBUG: bool = Field(default=True)
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8000)
    ALLOWED_ORIGINS: List[str] = Field(default_factory=lambda: ["*"])
    ALLOWED_HOSTS: List[str] = Field(default_factory=lambda: ["*"])

    # PostgreSQL/TimescaleDB 配置
    POSTGRES_HOST: str = Field(default="localhost")
    POSTGRES_PORT: int = Field(default=5432)
    POSTGRES_USER: str = Field(default="tradingagents")
    POSTGRES_PASSWORD: str = Field(default="your_password_here")
    POSTGRES_DB: str = Field(default="tradingagents")
    POSTGRES_MAX_CONNECTIONS: int = Field(default=100)
    POSTGRES_MIN_CONNECTIONS: int = Field(default=10)

    @property
    def POSTGRES_URI(self) -> str:
        """构建 PostgreSQL URI"""
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def POSTGRES_ASYNC_URI(self) -> str:
        """构建 PostgreSQL 异步 URI (asyncpg)"""
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # Qdrant 向量数据库配置
    QDRANT_HOST: str = Field(default="localhost")
    QDRANT_PORT: int = Field(default=6333)
    QDRANT_API_KEY: str = Field(default="")  # 如果使用 Qdrant Cloud，需要设置
    QDRANT_GRPC_PORT: int = Field(default=6334)  # gRPC 端口（可选）

    # Redis配置
    REDIS_HOST: str = Field(default="localhost")
    REDIS_PORT: int = Field(default=6379)
    REDIS_PASSWORD: str = Field(default="")
    REDIS_DB: int = Field(default=0)
    REDIS_MAX_CONNECTIONS: int = Field(default=100)  # 优化：增加连接池以支持更高并发
    REDIS_RETRY_ON_TIMEOUT: bool = Field(default=True)

    @property
    def REDIS_URL(self) -> str:
        """构建Redis URL"""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        else:
            return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # JWT配置
    JWT_SECRET: str = Field(default="change-me-in-production")
    JWT_ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=30)

    # 队列配置
    QUEUE_MAX_SIZE: int = Field(default=10000)
    QUEUE_VISIBILITY_TIMEOUT: int = Field(default=300)  # 5分钟
    QUEUE_MAX_RETRIES: int = Field(default=3)
    WORKER_HEARTBEAT_INTERVAL: int = Field(default=30)  # 30秒


    # 队列轮询/清理间隔（秒）
    QUEUE_POLL_INTERVAL_SECONDS: float = Field(default=1.0)
    QUEUE_CLEANUP_INTERVAL_SECONDS: float = Field(default=60.0)

    # 并发控制
    DEFAULT_USER_CONCURRENT_LIMIT: int = Field(default=3)
    GLOBAL_CONCURRENT_LIMIT: int = Field(default=50)
    DEFAULT_DAILY_QUOTA: int = Field(default=1000)

    # 速率限制
    RATE_LIMIT_ENABLED: bool = Field(default=True)
    DEFAULT_RATE_LIMIT: int = Field(default=100)  # 每分钟请求数

    # 日志配置
    LOG_LEVEL: str = Field(default="INFO")
    LOG_FORMAT: str = Field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    LOG_FILE: str = Field(default="logs/tradingagents.log")

    # 代理配置
    # 用于配置需要绕过代理的域名（国内数据源）
    # 多个域名用逗号分隔
    # ⚠️ Windows 不支持通配符 *，必须使用完整域名
    # 详细说明: docs/proxy_configuration.md
    HTTP_PROXY: str = Field(default="")
    HTTPS_PROXY: str = Field(default="")
    NO_PROXY: str = Field(
        default="localhost,127.0.0.1,eastmoney.com,push2.eastmoney.com,82.push2.eastmoney.com,82.push2delay.eastmoney.com,gtimg.cn,sinaimg.cn,api.tushare.pro,baostock.com"
    )

    # 文件上传配置
    MAX_UPLOAD_SIZE: int = Field(default=10 * 1024 * 1024)  # 10MB
    UPLOAD_DIR: str = Field(default="uploads")

    # 缓存配置
    CACHE_TTL: int = Field(default=3600)  # 1小时
    SCREENING_CACHE_TTL: int = Field(default=1800)  # 30分钟

    # 安全配置
    BCRYPT_ROUNDS: int = Field(default=12)
    SESSION_EXPIRE_HOURS: int = Field(default=24)
    CSRF_SECRET: str = Field(default="change-me-csrf-secret")

    # 外部服务配置
    STOCK_DATA_API_URL: str = Field(default="")
    STOCK_DATA_API_KEY: str = Field(default="")

    # SSE 配置
    SSE_POLL_TIMEOUT_SECONDS: float = Field(default=1.0)
    SSE_HEARTBEAT_INTERVAL_SECONDS: int = Field(default=10)
    SSE_TASK_MAX_IDLE_SECONDS: int = Field(default=300)
    SSE_BATCH_POLL_INTERVAL_SECONDS: float = Field(default=2.0)
    SSE_BATCH_MAX_IDLE_SECONDS: int = Field(default=600)


    # 监控配置
    METRICS_ENABLED: bool = Field(default=True)
    HEALTH_CHECK_INTERVAL: int = Field(default=60)  # 60秒


    # 配置真相来源（方案A）：file|db|hybrid
    # - file：以文件/env 为准（推荐，生产缺省）
    # - db：以数据库为准（仅兼容旧版，不推荐）
    # - hybrid：文件/env 优先，DB 作为兜底
    CONFIG_SOT: str = Field(default="file")


    # 基础信息同步任务配置（可配置调度）
    SYNC_STOCK_BASICS_ENABLED: bool = Field(default=True)
    # 优先使用 CRON 表达式，例如 "30 6 * * *" 表示每日 06:30
    SYNC_STOCK_BASICS_CRON: str = Field(default="")
    # 若未提供 CRON，则使用简单时间字符串 "HH:MM"（24小时制）
    SYNC_STOCK_BASICS_TIME: str = Field(default="06:30")
    # 时区
    TIMEZONE: str = Field(default="Asia/Shanghai")

    # 实时行情入库任务
    QUOTES_INGEST_ENABLED: bool = Field(default=True)
    QUOTES_INGEST_INTERVAL_SECONDS: int = Field(
        default=360,
        description="实时行情采集间隔（秒）。默认360秒（6分钟），免费用户建议>=300秒，付费用户可设置5-60秒"
    )
    # 休市期/启动兜底补数（填充上一笔快照）
    QUOTES_BACKFILL_ON_STARTUP: bool = Field(default=True)
    QUOTES_BACKFILL_ON_OFFHOURS: bool = Field(default=True)

    # 实时行情接口轮换配置
    QUOTES_ROTATION_ENABLED: bool = Field(
        default=True,
        description="启用接口轮换机制（Tushare → AKShare东方财富 → AKShare新浪财经）"
    )
    QUOTES_TUSHARE_HOURLY_LIMIT: int = Field(
        default=2,
        description="Tushare rt_k接口每小时调用次数限制（免费用户2次，付费用户可设置更高）"
    )
    QUOTES_AUTO_DETECT_TUSHARE_PERMISSION: bool = Field(
        default=True,
        description="自动检测Tushare rt_k接口权限，付费用户自动切换到高频模式（5秒）"
    )

    # Tushare基础配置
    TUSHARE_TOKEN: str = Field(default="", description="Tushare API Token")
    TUSHARE_ENABLED: bool = Field(default=True, description="启用Tushare数据源")
    TUSHARE_TIER: str = Field(default="standard", description="Tushare积分等级 (free/basic/standard/premium/vip)")
    TUSHARE_RATE_LIMIT_SAFETY_MARGIN: float = Field(default=0.8, ge=0.1, le=1.0, description="速率限制安全边际")

    # Tushare统一数据同步配置
    TUSHARE_UNIFIED_ENABLED: bool = Field(default=True)
    TUSHARE_BASIC_INFO_SYNC_ENABLED: bool = Field(default=True)
    TUSHARE_BASIC_INFO_SYNC_CRON: str = Field(default="0 2 * * *")  # 每日凌晨2点
    TUSHARE_QUOTES_SYNC_ENABLED: bool = Field(default=True)
    TUSHARE_QUOTES_SYNC_CRON: str = Field(default="*/5 9-15 * * 1-5")  # 交易时间每5分钟
    TUSHARE_HISTORICAL_SYNC_ENABLED: bool = Field(default=True)
    TUSHARE_HISTORICAL_SYNC_CRON: str = Field(default="0 16 * * 1-5")  # 工作日16点
    TUSHARE_FINANCIAL_SYNC_ENABLED: bool = Field(default=True)
    TUSHARE_FINANCIAL_SYNC_CRON: str = Field(default="0 3 * * 0")  # 周日凌晨3点
    TUSHARE_STATUS_CHECK_ENABLED: bool = Field(default=True)
    TUSHARE_STATUS_CHECK_CRON: str = Field(default="0 * * * *")  # 每小时

    # Tushare数据初始化配置
    TUSHARE_INIT_HISTORICAL_DAYS: int = Field(default=365, ge=1, le=3650, description="初始化历史数据天数")
    TUSHARE_INIT_BATCH_SIZE: int = Field(default=100, ge=10, le=1000, description="初始化批处理大小")
    TUSHARE_INIT_AUTO_START: bool = Field(default=False, description="应用启动时自动检查并初始化数据")

    # AKShare统一数据同步配置
    AKSHARE_UNIFIED_ENABLED: bool = Field(default=True, description="启用AKShare统一数据同步")
    AKSHARE_BASIC_INFO_SYNC_ENABLED: bool = Field(default=True, description="启用基础信息同步")
    AKSHARE_BASIC_INFO_SYNC_CRON: str = Field(default="0 3 * * *", description="基础信息同步CRON表达式")  # 每日凌晨3点
    AKSHARE_QUOTES_SYNC_ENABLED: bool = Field(default=True, description="启用行情同步")
    AKSHARE_QUOTES_SYNC_CRON: str = Field(default="*/30 9-15 * * 1-5", description="行情同步CRON表达式")  # 交易时间每30分钟（避免频率限制）
    AKSHARE_HISTORICAL_SYNC_ENABLED: bool = Field(default=True, description="启用历史数据同步")
    AKSHARE_HISTORICAL_SYNC_CRON: str = Field(default="0 17 * * 1-5", description="历史数据同步CRON表达式")  # 工作日17点
    AKSHARE_FINANCIAL_SYNC_ENABLED: bool = Field(default=True, description="启用财务数据同步")
    AKSHARE_FINANCIAL_SYNC_CRON: str = Field(default="0 4 * * 0", description="财务数据同步CRON表达式")  # 周日凌晨4点
    AKSHARE_STATUS_CHECK_ENABLED: bool = Field(default=True, description="启用状态检查")
    AKSHARE_STATUS_CHECK_CRON: str = Field(default="30 * * * *", description="状态检查CRON表达式")  # 每小时30分

    # AKShare数据初始化配置
    AKSHARE_INIT_HISTORICAL_DAYS: int = Field(default=365, ge=1, le=3650, description="初始化历史数据天数")
    AKSHARE_INIT_BATCH_SIZE: int = Field(default=100, ge=10, le=1000, description="初始化批处理大小")
    AKSHARE_INIT_AUTO_START: bool = Field(default=False, description="应用启动时自动检查并初始化数据")

    # ==================== 分析师数据获取配置 ====================

    # 市场分析师数据范围配置
    # 默认60天：可覆盖MA60等所有常用技术指标（MA5/10/20/60, MACD, RSI, BOLL）
    MARKET_ANALYST_LOOKBACK_DAYS: int = Field(default=60, ge=5, le=365, description="市场分析回溯天数（用于技术分析）")

    # ==================== BaoStock统一数据同步配置 ====================

    # BaoStock统一数据同步总开关
    BAOSTOCK_UNIFIED_ENABLED: bool = Field(default=True, description="启用BaoStock统一数据同步")

    # BaoStock数据同步任务配置
    BAOSTOCK_BASIC_INFO_SYNC_ENABLED: bool = Field(default=True, description="启用基础信息同步")
    BAOSTOCK_BASIC_INFO_SYNC_CRON: str = Field(default="0 4 * * *", description="基础信息同步CRON表达式")  # 每日凌晨4点
    BAOSTOCK_DAILY_QUOTES_SYNC_ENABLED: bool = Field(default=True, description="启用日K线同步（注意：BaoStock不支持实时行情）")
    BAOSTOCK_DAILY_QUOTES_SYNC_CRON: str = Field(default="0 16 * * 1-5", description="日K线同步CRON表达式")  # 工作日收盘后16:00
    BAOSTOCK_HISTORICAL_SYNC_ENABLED: bool = Field(default=True, description="启用历史数据同步")
    BAOSTOCK_HISTORICAL_SYNC_CRON: str = Field(default="0 18 * * 1-5", description="历史数据同步CRON表达式")  # 工作日18点
    BAOSTOCK_STATUS_CHECK_ENABLED: bool = Field(default=True, description="启用状态检查")
    BAOSTOCK_STATUS_CHECK_CRON: str = Field(default="45 * * * *", description="状态检查CRON表达式")  # 每小时45分

    # BaoStock数据初始化配置
    BAOSTOCK_INIT_HISTORICAL_DAYS: int = Field(default=365, ge=1, le=3650, description="初始化历史数据天数")
    BAOSTOCK_INIT_BATCH_SIZE: int = Field(default=50, ge=10, le=500, description="初始化批处理大小")
    BAOSTOCK_INIT_AUTO_START: bool = Field(default=False, description="应用启动时自动检查并初始化数据")

    # 数据目录配置
    TRADINGAGENTS_DATA_DIR: str = Field(default="./data")

    @property
    def log_dir(self) -> str:
        """获取日志目录"""
        return os.path.dirname(self.LOG_FILE)

    # ==================== 港股数据配置 ====================

    # 港股数据源配置（按需获取+缓存模式）
    HK_DATA_CACHE_HOURS: int = Field(default=24, ge=1, le=168, description="港股数据缓存时长（小时）")
    HK_DEFAULT_DATA_SOURCE: str = Field(default="yfinance", description="港股默认数据源（yfinance/akshare）")

    # ==================== 美股数据配置 ====================

    # 美股数据源配置（按需获取+缓存模式）
    US_DATA_CACHE_HOURS: int = Field(default=24, ge=1, le=168, description="美股数据缓存时长（小时）")
    US_DEFAULT_DATA_SOURCE: str = Field(default="yfinance", description="美股默认数据源（yfinance/finnhub）")

    # ===== 新闻数据同步服务配置 =====
    NEWS_SYNC_ENABLED: bool = Field(default=True)
    NEWS_SYNC_CRON: str = Field(default="0 */2 * * *")  # 每2小时
    NEWS_SYNC_HOURS_BACK: int = Field(default=24)
    NEWS_SYNC_MAX_PER_SOURCE: int = Field(default=50)

    @property
    def is_production(self) -> bool:
        """是否为生产环境"""
        return not self.DEBUG

    # Ignore any extra environment variables present in .env or process env
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()

# 自动将代理配置设置到环境变量
# 这样 requests 库可以直接读取 os.environ['NO_PROXY']
if settings.HTTP_PROXY:
    os.environ['HTTP_PROXY'] = settings.HTTP_PROXY
if settings.HTTPS_PROXY:
    os.environ['HTTPS_PROXY'] = settings.HTTPS_PROXY
if settings.NO_PROXY:
    os.environ['NO_PROXY'] = settings.NO_PROXY


def get_settings() -> Settings:
    """获取配置实例"""
    return settings
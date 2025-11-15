-- ============================================================================
-- TimescaleDB Schema Design for TradingAgents-CN
-- 设计目标：支持金融时序数据高效存储和查询
-- ============================================================================

-- 启用 TimescaleDB 扩展
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- ============================================================================
-- 1. 枚举类型定义
-- ============================================================================

-- 市场类型
CREATE TYPE market_type AS ENUM ('CN', 'HK', 'US');

-- 交易所类型
CREATE TYPE exchange_type AS ENUM ('SZSE', 'SSE', 'SEHK', 'NYSE', 'NASDAQ', 'BSE');

-- 股票状态
CREATE TYPE stock_status AS ENUM ('L', 'D', 'P');  -- L=上市, D=退市, P=暂停

-- 货币类型
CREATE TYPE currency_type AS ENUM ('CNY', 'HKD', 'USD');

-- 报告类型
CREATE TYPE report_type AS ENUM ('quarterly', 'annual');

-- 新闻类别
CREATE TYPE news_category AS ENUM (
    'company_announcement',
    'industry_news',
    'market_news',
    'research_report'
);

-- 情绪类型
CREATE TYPE sentiment_type AS ENUM ('positive', 'negative', 'neutral');

-- 数据源类型
CREATE TYPE data_source_type AS ENUM ('tushare', 'akshare', 'baostock', 'yfinance', 'finnhub', 'multi_source');


-- ============================================================================
-- 2. 基础表（普通表）
-- ============================================================================

-- 2.1 股票基础信息表
CREATE TABLE stock_info (
    -- 主键
    symbol VARCHAR(20) PRIMARY KEY,  -- 标准化股票代码（如 000001.SZ）

    -- 基础信息
    code VARCHAR(10) NOT NULL,  -- 6位股票代码
    name VARCHAR(100) NOT NULL,
    name_en VARCHAR(200),
    full_symbol VARCHAR(30) NOT NULL,  -- 完整标准化代码

    -- 市场信息
    market market_type NOT NULL,
    exchange exchange_type NOT NULL,
    exchange_name VARCHAR(100),
    board VARCHAR(50),  -- 板块

    -- 行业分类
    industry VARCHAR(100),
    industry_code VARCHAR(50),
    sector VARCHAR(100),  -- GICS 行业

    -- 地域信息
    area VARCHAR(100),
    currency currency_type DEFAULT 'CNY',
    timezone VARCHAR(50) DEFAULT 'Asia/Shanghai',

    -- 上市信息
    list_date DATE,
    delist_date DATE,
    status stock_status DEFAULT 'L',

    -- 股本信息
    total_shares DECIMAL(20, 2),  -- 总股本（万股）
    float_shares DECIMAL(20, 2),  -- 流通股本（万股）

    -- 港股特有
    lot_size INTEGER,  -- 每手股数

    -- 标记
    is_hs BOOLEAN DEFAULT FALSE,  -- 是否沪深港通标的

    -- 元数据
    data_source data_source_type NOT NULL,
    data_version INTEGER DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX idx_stock_info_market ON stock_info(market);
CREATE INDEX idx_stock_info_industry ON stock_info(industry);
CREATE INDEX idx_stock_info_status ON stock_info(status);
CREATE INDEX idx_stock_info_code ON stock_info(code);
CREATE INDEX idx_stock_info_exchange ON stock_info(exchange);

COMMENT ON TABLE stock_info IS '股票基础信息表';
COMMENT ON COLUMN stock_info.symbol IS '标准化股票代码（主键）';
COMMENT ON COLUMN stock_info.code IS '6位股票代码';


-- 2.2 用户表
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(200),
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,

    -- 配额和权限
    daily_quota INTEGER DEFAULT 1000,
    concurrent_limit INTEGER DEFAULT 3,

    -- 时间戳
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMPTZ
);

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);

COMMENT ON TABLE users IS '用户表';


-- ============================================================================
-- 3. 时序表（Hypertables）
-- ============================================================================

-- 3.1 日K线表
CREATE TABLE stock_daily_quotes (
    time TIMESTAMPTZ NOT NULL,  -- 交易日期时间
    symbol VARCHAR(20) NOT NULL,

    -- OHLC 数据
    open DECIMAL(12, 3) NOT NULL,
    high DECIMAL(12, 3) NOT NULL,
    low DECIMAL(12, 3) NOT NULL,
    close DECIMAL(12, 3) NOT NULL,
    pre_close DECIMAL(12, 3),

    -- 成交数据
    volume BIGINT,  -- 成交量（股）
    amount DECIMAL(20, 2),  -- 成交额（元）

    -- 涨跌幅
    change DECIMAL(12, 3),  -- 涨跌额
    pct_chg DECIMAL(8, 3),  -- 涨跌幅 %

    -- 换手率
    turnover_rate DECIMAL(8, 3),
    volume_ratio DECIMAL(8, 3),

    -- 估值指标
    pe DECIMAL(12, 3),
    pe_ttm DECIMAL(12, 3),
    pb DECIMAL(12, 3),
    pb_mrq DECIMAL(12, 3),
    ps DECIMAL(12, 3),
    dv_ratio DECIMAL(8, 3),  -- 股息率
    dv_ttm DECIMAL(8, 3),

    -- 市值
    total_mv DECIMAL(20, 2),  -- 总市值（亿元）
    circ_mv DECIMAL(20, 2),  -- 流通市值（亿元）

    -- 复权因子
    adj_factor DECIMAL(12, 6) DEFAULT 1.0,

    -- 元数据
    data_source data_source_type NOT NULL,
    period VARCHAR(20) DEFAULT 'daily',  -- daily/weekly/monthly
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (time, symbol, data_source, period)
);

-- 转换为 Hypertable
SELECT create_hypertable('stock_daily_quotes', 'time',
    chunk_time_interval => INTERVAL '1 month',
    if_not_exists => TRUE
);

-- 创建索引
CREATE INDEX idx_daily_quotes_symbol ON stock_daily_quotes(symbol, time DESC);
CREATE INDEX idx_daily_quotes_pct_chg ON stock_daily_quotes(pct_chg DESC);
CREATE INDEX idx_daily_quotes_volume ON stock_daily_quotes(volume DESC);

-- 启用压缩（压缩 7 天前的数据）
ALTER TABLE stock_daily_quotes SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'symbol,data_source',
    timescaledb.compress_orderby = 'time DESC'
);

SELECT add_compression_policy('stock_daily_quotes', INTERVAL '7 days');

-- 数据保留策略（可选：删除 10 年前的数据）
-- SELECT add_retention_policy('stock_daily_quotes', INTERVAL '10 years');

COMMENT ON TABLE stock_daily_quotes IS '股票日K线数据（时序表）';


-- 3.2 分钟K线表（高频数据）
CREATE TABLE stock_minute_quotes (
    time TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(20) NOT NULL,

    -- OHLC
    open DECIMAL(12, 3) NOT NULL,
    high DECIMAL(12, 3) NOT NULL,
    low DECIMAL(12, 3) NOT NULL,
    close DECIMAL(12, 3) NOT NULL,

    -- 成交数据
    volume BIGINT,
    amount DECIMAL(20, 2),

    -- 元数据
    data_source data_source_type NOT NULL,
    period VARCHAR(20) DEFAULT '1min',  -- 1min/5min/15min/30min/60min
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (time, symbol, data_source, period)
);

-- 转换为 Hypertable
SELECT create_hypertable('stock_minute_quotes', 'time',
    chunk_time_interval => INTERVAL '7 days',
    if_not_exists => TRUE
);

CREATE INDEX idx_minute_quotes_symbol ON stock_minute_quotes(symbol, time DESC);

-- 启用压缩（压缩 1 天前的分钟数据）
ALTER TABLE stock_minute_quotes SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'symbol,data_source,period',
    timescaledb.compress_orderby = 'time DESC'
);

SELECT add_compression_policy('stock_minute_quotes', INTERVAL '1 day');

-- 数据保留策略（删除 2 年前的分钟数据）
SELECT add_retention_policy('stock_minute_quotes', INTERVAL '2 years');

COMMENT ON TABLE stock_minute_quotes IS '股票分钟K线数据（高频时序表）';


-- 3.3 实时行情快照表
CREATE TABLE stock_realtime_quotes (
    time TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(20) NOT NULL,

    -- 当前价格
    current_price DECIMAL(12, 3) NOT NULL,
    pre_close DECIMAL(12, 3),
    open DECIMAL(12, 3),
    high DECIMAL(12, 3),
    low DECIMAL(12, 3),

    -- 涨跌
    change DECIMAL(12, 3),
    pct_chg DECIMAL(8, 3),

    -- 成交数据
    volume BIGINT,
    amount DECIMAL(20, 2),
    turnover_rate DECIMAL(8, 3),
    volume_ratio DECIMAL(8, 3),

    -- 五档行情（使用 ARRAY 存储）
    bid_prices DECIMAL(12, 3)[5],
    bid_volumes BIGINT[5],
    ask_prices DECIMAL(12, 3)[5],
    ask_volumes BIGINT[5],

    -- 元数据
    data_source data_source_type NOT NULL,

    PRIMARY KEY (time, symbol, data_source)
);

-- 转换为 Hypertable
SELECT create_hypertable('stock_realtime_quotes', 'time',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

CREATE INDEX idx_realtime_quotes_symbol ON stock_realtime_quotes(symbol, time DESC);

-- 启用压缩（压缩 1 小时前的实时数据）
ALTER TABLE stock_realtime_quotes SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'symbol,data_source',
    timescaledb.compress_orderby = 'time DESC'
);

SELECT add_compression_policy('stock_realtime_quotes', INTERVAL '1 hour');

-- 数据保留策略（删除 30 天前的实时快照）
SELECT add_retention_policy('stock_realtime_quotes', INTERVAL '30 days');

COMMENT ON TABLE stock_realtime_quotes IS '实时行情快照表（高频时序表）';


-- 3.4 财务数据表
CREATE TABLE stock_financial_data (
    time TIMESTAMPTZ NOT NULL,  -- 报告期对应的时间戳
    symbol VARCHAR(20) NOT NULL,
    report_period VARCHAR(10) NOT NULL,  -- YYYYMMDD 格式
    report_type report_type NOT NULL,
    ann_date DATE,  -- 公告日期

    -- 资产负债表
    total_assets DECIMAL(20, 2),
    total_liab DECIMAL(20, 2),
    total_equity DECIMAL(20, 2),
    total_cur_assets DECIMAL(20, 2),
    total_nca DECIMAL(20, 2),
    total_cur_liab DECIMAL(20, 2),
    total_ncl DECIMAL(20, 2),
    cash_and_equivalents DECIMAL(20, 2),

    -- 利润表
    total_revenue DECIMAL(20, 2),
    revenue DECIMAL(20, 2),
    oper_cost DECIMAL(20, 2),
    gross_profit DECIMAL(20, 2),
    oper_profit DECIMAL(20, 2),
    total_profit DECIMAL(20, 2),
    net_income DECIMAL(20, 2),
    net_income_attr_p DECIMAL(20, 2),  -- 归母净利润
    basic_eps DECIMAL(12, 4),
    diluted_eps DECIMAL(12, 4),

    -- 现金流量表
    n_cashflow_act DECIMAL(20, 2),
    n_cashflow_inv_act DECIMAL(20, 2),
    n_cashflow_fin_act DECIMAL(20, 2),
    c_cash_equ_end DECIMAL(20, 2),
    c_cash_equ_beg DECIMAL(20, 2),

    -- 财务指标
    roe DECIMAL(8, 3),
    roa DECIMAL(8, 3),
    gross_margin DECIMAL(8, 3),
    net_margin DECIMAL(8, 3),
    netprofit_margin DECIMAL(8, 3),
    debt_to_assets DECIMAL(8, 3),
    current_ratio DECIMAL(8, 3),
    quick_ratio DECIMAL(8, 3),
    bvps DECIMAL(12, 4),

    -- 元数据
    data_source data_source_type NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (time, symbol, report_period, data_source)
);

-- 转换为 Hypertable
SELECT create_hypertable('stock_financial_data', 'time',
    chunk_time_interval => INTERVAL '1 year',
    if_not_exists => TRUE
);

CREATE INDEX idx_financial_symbol ON stock_financial_data(symbol, time DESC);
CREATE INDEX idx_financial_report_period ON stock_financial_data(report_period DESC);
CREATE INDEX idx_financial_type ON stock_financial_data(report_type);

-- 启用压缩（压缩 90 天前的财务数据）
ALTER TABLE stock_financial_data SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'symbol,data_source',
    timescaledb.compress_orderby = 'time DESC'
);

SELECT add_compression_policy('stock_financial_data', INTERVAL '90 days');

COMMENT ON TABLE stock_financial_data IS '股票财务数据（时序表）';


-- 3.5 新闻数据表
CREATE TABLE stock_news (
    time TIMESTAMPTZ NOT NULL,  -- 发布时间
    id SERIAL,

    -- 新闻内容
    title TEXT NOT NULL,
    content TEXT,
    summary TEXT,
    url TEXT,
    source VARCHAR(100),
    author VARCHAR(200),

    -- 关联股票（使用 ARRAY 支持多股票）
    symbols VARCHAR(20)[],

    -- 分类
    category news_category,
    keywords TEXT[],
    importance VARCHAR(20) DEFAULT 'medium',
    language VARCHAR(10) DEFAULT 'zh-CN',

    -- 情绪分析
    sentiment sentiment_type,
    sentiment_score DECIMAL(4, 3),  -- -1.0 到 1.0

    -- 元数据
    data_source data_source_type,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (time, id)
);

-- 转换为 Hypertable
SELECT create_hypertable('stock_news', 'time',
    chunk_time_interval => INTERVAL '1 month',
    if_not_exists => TRUE
);

CREATE INDEX idx_news_symbols ON stock_news USING GIN(symbols);
CREATE INDEX idx_news_category ON stock_news(category);
CREATE INDEX idx_news_sentiment ON stock_news(sentiment);
CREATE INDEX idx_news_keywords ON stock_news USING GIN(keywords);

-- 启用压缩（压缩 30 天前的新闻）
ALTER TABLE stock_news SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'category,data_source',
    timescaledb.compress_orderby = 'time DESC'
);

SELECT add_compression_policy('stock_news', INTERVAL '30 days');

-- 数据保留策略（删除 3 年前的新闻）
SELECT add_retention_policy('stock_news', INTERVAL '3 years');

COMMENT ON TABLE stock_news IS '股票新闻数据（时序表）';


-- ============================================================================
-- 4. 连续聚合（Continuous Aggregates）- 自动物化视图
-- ============================================================================

-- 4.1 每日市场统计
CREATE MATERIALIZED VIEW stock_daily_stats
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', time) AS day,
    symbol,
    first(open, time) AS day_open,
    max(high) AS day_high,
    min(low) AS day_low,
    last(close, time) AS day_close,
    sum(volume) AS total_volume,
    sum(amount) AS total_amount,
    data_source
FROM stock_minute_quotes
GROUP BY day, symbol, data_source
WITH NO DATA;

-- 刷新策略（每小时刷新）
SELECT add_continuous_aggregate_policy('stock_daily_stats',
    start_offset => INTERVAL '3 days',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour');

COMMENT ON MATERIALIZED VIEW stock_daily_stats IS '日K线数据自动聚合（从分钟数据）';


-- 4.2 移动平均线（MA）
CREATE MATERIALIZED VIEW stock_moving_averages
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', time) AS day,
    symbol,
    avg(close) OVER (PARTITION BY symbol ORDER BY time ROWS BETWEEN 4 PRECEDING AND CURRENT ROW) AS ma_5,
    avg(close) OVER (PARTITION BY symbol ORDER BY time ROWS BETWEEN 9 PRECEDING AND CURRENT ROW) AS ma_10,
    avg(close) OVER (PARTITION BY symbol ORDER BY time ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS ma_20,
    avg(close) OVER (PARTITION BY symbol ORDER BY time ROWS BETWEEN 59 PRECEDING AND CURRENT ROW) AS ma_60,
    last(close, time) AS close
FROM stock_daily_quotes
GROUP BY day, symbol
WITH NO DATA;

SELECT add_continuous_aggregate_policy('stock_moving_averages',
    start_offset => INTERVAL '90 days',
    end_offset => INTERVAL '1 day',
    schedule_interval => INTERVAL '1 day');

COMMENT ON MATERIALIZED VIEW stock_moving_averages IS '移动平均线自动计算';


-- ============================================================================
-- 5. 辅助表
-- ============================================================================

-- 5.1 数据同步日志
CREATE TABLE data_sync_logs (
    id SERIAL PRIMARY KEY,
    task_id VARCHAR(100) UNIQUE NOT NULL,
    data_type VARCHAR(50) NOT NULL,
    data_source data_source_type NOT NULL,
    symbols TEXT[],
    sync_date DATE NOT NULL,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ,
    status VARCHAR(20) DEFAULT 'pending',  -- pending/running/success/failed
    total_records INTEGER DEFAULT 0,
    success_records INTEGER DEFAULT 0,
    failed_records INTEGER DEFAULT 0,
    error_message TEXT,
    performance JSONB,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sync_logs_task_id ON data_sync_logs(task_id);
CREATE INDEX idx_sync_logs_status ON data_sync_logs(status);
CREATE INDEX idx_sync_logs_sync_date ON data_sync_logs(sync_date DESC);

COMMENT ON TABLE data_sync_logs IS '数据同步日志表';


-- 5.2 操作日志表
CREATE TABLE operation_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    operation_type VARCHAR(50) NOT NULL,
    operation_detail JSONB,
    ip_address INET,
    user_agent TEXT,
    status VARCHAR(20),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_operation_logs_user ON operation_logs(user_id, created_at DESC);
CREATE INDEX idx_operation_logs_type ON operation_logs(operation_type);

COMMENT ON TABLE operation_logs IS '用户操作日志表';


-- ============================================================================
-- 6. 函数和触发器
-- ============================================================================

-- 6.1 自动更新 updated_at 字段
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 为需要的表创建触发器
CREATE TRIGGER update_stock_info_updated_at BEFORE UPDATE ON stock_info
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


-- ============================================================================
-- 7. 权限设置（可选）
-- ============================================================================

-- 创建应用用户
-- CREATE USER tradingagents_app WITH PASSWORD 'your_password_here';

-- 授予权限
-- GRANT CONNECT ON DATABASE tradingagents TO tradingagents_app;
-- GRANT USAGE ON SCHEMA public TO tradingagents_app;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO tradingagents_app;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO tradingagents_app;


-- ============================================================================
-- 8. 示例查询
-- ============================================================================

-- 示例1: 查询最近 30 天的 K 线数据
-- SELECT * FROM stock_daily_quotes
-- WHERE symbol = '000001.SZ'
--   AND time >= NOW() - INTERVAL '30 days'
-- ORDER BY time DESC;

-- 示例2: 计算实时移动平均
-- SELECT
--     time,
--     symbol,
--     close,
--     avg(close) OVER (PARTITION BY symbol ORDER BY time ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS ma_20
-- FROM stock_daily_quotes
-- WHERE symbol = '000001.SZ'
-- ORDER BY time DESC
-- LIMIT 100;

-- 示例3: 查询最新财务数据
-- SELECT * FROM stock_financial_data
-- WHERE symbol = '000001.SZ'
-- ORDER BY time DESC
-- LIMIT 1;

-- 示例4: 查询涨幅前 10 的股票
-- SELECT symbol, close, pct_chg
-- FROM stock_daily_quotes
-- WHERE time = (SELECT MAX(time) FROM stock_daily_quotes)
-- ORDER BY pct_chg DESC
-- LIMIT 10;


-- ============================================================================
-- Schema 设计完成
-- ============================================================================

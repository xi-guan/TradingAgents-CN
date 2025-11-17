# 🚀 Database V2 快速开始指南

## 新架构概览

**TradingAgents-CN** 已升级到 V2 数据库架构：

| 组件 | 技术栈 | 用途 |
|------|--------|------|
| **时序数据库** | TimescaleDB | 股票行情、K线、财务数据 |
| **向量数据库** | Qdrant | 新闻、研报语义检索 |
| **缓存数据库** | Redis | 会话、限流、热点数据 |

---

## ⚡ 5分钟快速开始

### 1. 启动数据库服务

```bash
# 进入项目目录
cd TradingAgents-CN

# 启动所有数据库（TimescaleDB + Qdrant + Redis）
docker-compose up -d timescaledb qdrant redis

# 查看服务状态
docker-compose ps

# 预期输出：
# NAME                           STATUS
# tradingagents-timescaledb      Up (healthy)
# tradingagents-qdrant           Up (healthy)
# tradingagents-redis            Up (healthy)
```

### 2. 验证数据库连接

```bash
# 测试 TimescaleDB
docker exec -it tradingagents-timescaledb psql -U tradingagents -d tradingagents -c "SELECT version();"

# 测试 Qdrant
curl http://localhost:6333/collections

# 测试 Redis
docker exec -it tradingagents-redis redis-cli -a tradingagents123 ping
# 应该返回: PONG
```

### 3. 运行示例代码

```bash
# 安装依赖
pip install -r requirements.txt

# 运行示例
python examples/database_v2_example.py
```

---

## 📝 基础使用

### 初始化数据库连接

```python
from app.core.database_v2 import init_database, close_database

# 初始化
await init_database()

# 使用完毕后关闭
await close_database()
```

### 股票信息操作

```python
from app.services.stock_service_v2 import stock_info_service

# 查询股票信息
info = await stock_info_service.get_stock_info("000001.SZ")
print(f"{info['name']}: {info['industry']}")

# 搜索股票
results = await stock_info_service.search_stocks(
    keyword="平安",
    market="CN",
    limit=10
)
```

### 行情数据操作

```python
from app.services.stock_service_v2 import market_quotes_service

# 获取最新行情
quote = await market_quotes_service.get_latest_quote("000001.SZ")
print(f"收盘价: {quote['close']}, 涨跌幅: {quote['pct_chg']}%")

# 查询历史K线
quotes = await market_quotes_service.get_daily_quotes(
    symbol="000001.SZ",
    start_date=date(2024, 1, 1),
    limit=30
)

# 计算移动平均线
ma_data = await market_quotes_service.get_moving_averages(
    symbol="000001.SZ",
    days=60
)
```

### 财务数据操作

```python
from app.services.stock_service_v2 import financial_data_service

# 获取最新财务数据
financial = await financial_data_service.get_latest_financial("000001.SZ")
print(f"ROE: {financial['roe']}%, 净利润: {financial['net_income']}M")

# 查询财务历史
history = await financial_data_service.get_financial_history(
    symbol="000001.SZ",
    report_type="annual",
    limit=5
)
```

### 向量搜索操作

```python
from app.services.vector_store_service import (
    vector_store_service,
    news_vector_service
)

# 初始化向量集合
await vector_store_service.init_collections()

# 添加新闻向量
await news_vector_service.add_news(
    news_id="news_001",
    title="平安银行Q4业绩超预期",
    content="...",
    embedding=embedding_vector,  # 1536维向量
    metadata={
        "date": "2024-01-15",
        "symbols": ["000001.SZ"],
        "sentiment": "positive"
    }
)

# 搜索相关新闻
results = await news_vector_service.search_news(
    query_vector=query_embedding,
    symbols=["000001.SZ"],
    sentiment="positive",
    limit=10
)
```

---

## 🔧 管理工具

### pgAdmin（PostgreSQL/TimescaleDB 管理）

```bash
# 启动 pgAdmin
docker-compose --profile management up -d pgadmin

# 访问 http://localhost:5050
# Email: admin@tradingagents.com
# Password: tradingagents123
```

**添加服务器连接：**
- Host: `timescaledb`
- Port: `5432`
- Database: `tradingagents`
- Username: `tradingagents`
- Password: `tradingagents123`

### Qdrant Dashboard

```bash
# Qdrant 自带 Web UI
open http://localhost:6333/dashboard
```

### Redis Commander

```bash
# 启动 Redis 管理工具
docker-compose --profile management up -d redis-commander

# 访问 http://localhost:8081
```

---

## 🗄️ 数据库 Schema

### Hypertables（时序表）

| 表名 | 用途 | 压缩策略 | 保留期 |
|------|------|---------|--------|
| `stock_daily_quotes` | 日K线 | 7天前压缩 | 永久 |
| `stock_minute_quotes` | 分钟K线 | 1天前压缩 | 2年 |
| `stock_realtime_quotes` | 实时行情 | 1小时前压缩 | 30天 |
| `stock_financial_data` | 财务数据 | 90天前压缩 | 永久 |
| `stock_news` | 新闻数据 | 30天前压缩 | 3年 |

### 连续聚合（自动物化视图）

| 视图名 | 功能 | 刷新频率 |
|--------|------|---------|
| `stock_daily_stats` | 从分钟数据聚合日K | 每小时 |
| `stock_moving_averages` | 自动计算MA5/10/20/60 | 每天 |

### Qdrant 集合

| 集合名 | 用途 | 向量维度 |
|--------|------|---------|
| `financial_news` | 金融新闻 | 1536 |
| `research_reports` | 研究报告 | 1536 |
| `earnings_calls` | 财报会议 | 1536 |

---

## 📊 SQL 查询示例

### 查询最近30天涨幅前10

```sql
SELECT symbol, name, pct_chg
FROM stock_daily_quotes q
JOIN stock_info i ON q.symbol = i.symbol
WHERE q.time >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY pct_chg DESC
LIMIT 10;
```

### 计算实时MA20

```sql
SELECT
    time,
    symbol,
    close,
    avg(close) OVER (
        PARTITION BY symbol
        ORDER BY time
        ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
    ) AS ma_20
FROM stock_daily_quotes
WHERE symbol = '000001.SZ'
ORDER BY time DESC
LIMIT 100;
```

### 查询ROE最高的银行股

```sql
SELECT
    i.symbol,
    i.name,
    f.roe,
    f.net_income
FROM stock_info i
JOIN stock_financial_data f ON i.symbol = f.symbol
WHERE i.industry = '银行'
    AND f.report_type = 'annual'
ORDER BY f.roe DESC
LIMIT 10;
```

---

## 🛠️ 数据库维护

### 查看压缩状态

```sql
-- 查看压缩统计
SELECT * FROM timescaledb_information.compressed_chunk_stats;

-- 手动压缩特定chunk
SELECT compress_chunk('_timescaledb_internal._hyper_1_1_chunk');
```

### 备份和恢复

```bash
# 备份数据库
docker exec tradingagents-timescaledb pg_dump -U tradingagents tradingagents > backup.sql

# 恢复数据库
docker exec -i tradingagents-timescaledb psql -U tradingagents tradingagents < backup.sql
```

### 查看数据库大小

```sql
-- 查看所有表大小
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

---

## 🚨 常见问题

### Q1: 如何查看 Hypertable 状态？

```sql
SELECT * FROM timescaledb_information.hypertables;
```

### Q2: 数据压缩后还能查询吗？

是的！压缩是完全透明的，查询语法完全相同，TimescaleDB 会自动解压。

### Q3: 如何调整压缩策略？

```sql
-- 修改压缩策略（改为3天前压缩）
SELECT remove_compression_policy('stock_daily_quotes');
SELECT add_compression_policy('stock_daily_quotes', INTERVAL '3 days');
```

### Q4: Qdrant 数据存储在哪里？

Docker volume `qdrant_data`，使用以下命令查看：

```bash
docker volume inspect tradingagents_qdrant_data
```

### Q5: 如何停止所有服务？

```bash
docker-compose down
```

---

## 📚 相关文档

- [完整迁移指南](./DATABASE_MIGRATION_GUIDE.md)
- [TimescaleDB 官方文档](https://docs.timescale.com/)
- [Qdrant 官方文档](https://qdrant.tech/documentation/)
- [示例代码](../examples/database_v2_example.py)

---

## 💡 下一步

1. ✅ 启动数据库服务
2. ✅ 运行示例代码
3. ✅ 浏览管理工具
4. 🔄 开始实际开发！

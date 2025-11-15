-- ============================================================================
-- TimescaleDB 数据库初始化脚本
-- 用于首次创建数据库和配置
-- ============================================================================

-- 创建数据库（如果不存在）
-- 注意：需要以 postgres 超级用户身份执行
-- CREATE DATABASE tradingagents;

-- 连接到数据库
\c tradingagents

-- 启用 TimescaleDB 扩展
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- 启用其他有用的扩展
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;  -- 性能监控
CREATE EXTENSION IF NOT EXISTS btree_gin;  -- GIN 索引性能优化
CREATE EXTENSION IF NOT EXISTS btree_gist;  -- GIST 索引性能优化

-- 设置时区
SET timezone = 'Asia/Shanghai';

-- 显示版本信息
SELECT version();
SELECT extversion FROM pg_extension WHERE extname = 'timescaledb';

-- 执行主 schema 文件
\i /docker-entrypoint-initdb.d/schema.sql

-- 完成
SELECT 'TimescaleDB 初始化完成！' AS status;

-- 创建 tradingagents 用户和数据库
-- 使用方法: psql -U postgres -f backend/setup_database.sql

-- 创建用户
CREATE USER tradingagents WITH PASSWORD 'tradingagents123';

-- 创建数据库
CREATE DATABASE tradingagents OWNER tradingagents;

-- 授予权限
GRANT ALL PRIVILEGES ON DATABASE tradingagents TO tradingagents;

-- 连接到 tradingagents 数据库
\c tradingagents

-- 授予 schema 权限
GRANT ALL ON SCHEMA public TO tradingagents;

-- 启用 TimescaleDB 扩展（如果已安装）
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- 授予默认权限
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO tradingagents;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO tradingagents;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO tradingagents;

-- 完成
\echo '✓ Database and user created successfully!'
\echo 'Database: tradingagents'
\echo 'User: tradingagents'
\echo 'Password: tradingagents123'

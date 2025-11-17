# 🔧 TradingAgents-CN 配置系统指南

## 概览

TradingAgents-CN 使用**极简配置系统**，灵感来自 nevermind 项目的设计理念。

### 设计原则

1. **无 base.yaml**：只有一个配置文件 `config/local.yaml`
2. **自动生成**：通过 `scripts/setup.sh` 自动生成配置和密钥
3. **Git 安全**：配置文件自动加入 `.gitignore`，避免泄露敏感信息
4. **环境变量优先**：支持环境变量覆盖配置文件

---

## 📁 文件结构

```
TradingAgents-CN/
├── config/
│   └── local.yaml              # 生成的完整配置（gitignore）
│
├── scripts/
│   ├── setup.sh                # 主配置脚本
│   ├── templates/
│   │   └── local.yaml.template # 完整配置模板
│   └── utils/
│       ├── generate_secrets.py # 密钥生成工具
│       └── generate_env.py     # .env 生成工具
│
├── app/
│   └── core/
│       └── config.py           # 配置加载器
│
├── .env                        # 环境变量文件（自动生成，gitignore）
└── .gitignore                  # 已包含 config/local.yaml 和 .env
```

---

## 🚀 快速开始

### 1. 运行配置脚本

```bash
./scripts/setup.sh
```

脚本会引导你完成以下步骤：

1. **检查依赖**（Python 3.8+, PyYAML）
2. **生成安全密钥**
   - PostgreSQL 密码
   - Redis 密码
   - JWT 密钥
   - CSRF 密钥
3. **输入 API 密钥**
   - Tushare Token（可选）
   - OpenAI API Key（可选）
   - Anthropic API Key（可选）
   - Google API Key（可选）
4. **生成配置文件**
   - `config/local.yaml`：主配置文件
   - `.env`：环境变量文件

### 2. 验证配置

```bash
# 查看生成的配置
cat config/local.yaml

# 查看环境变量
cat .env
```

### 3. 启动服务

```bash
# 启动数据库
docker-compose up -d

# 启动后端
cd backend
uvicorn app.main:app --reload

# 启动前端
cd frontend
npm run dev
```

---

## 📋 配置文件说明

### config/local.yaml

```yaml
# 应用配置
app:
  name: TradingAgents-CN
  version: 1.0.0-preview
  debug: true
  host: 0.0.0.0
  port: 8000
  timezone: Asia/Shanghai

# 数据库配置
database:
  # TimescaleDB (时序数据库)
  timescaledb:
    host: localhost
    port: 5432
    database: tradingagents
    username: tradingagents
    password: <自动生成>
    min_connections: 10
    max_connections: 100

  # Qdrant (向量数据库)
  qdrant:
    host: localhost
    port: 6333
    grpc_port: 6334
    api_key: ""  # 可选

  # Redis (缓存)
  redis:
    host: localhost
    port: 6379
    password: <自动生成>
    db: 0
    max_connections: 20

# 安全配置
security:
  jwt:
    secret: <自动生成>
    algorithm: HS256
    access_token_expire_minutes: 60
    refresh_token_expire_days: 30

  csrf:
    secret: <自动生成>

  bcrypt:
    rounds: 12

# 数据源配置
data_sources:
  tushare:
    enabled: true
    token: <用户输入>
    tier: standard  # free/basic/standard/premium/vip

  akshare:
    enabled: true

  baostock:
    enabled: true

  yfinance:
    enabled: true

# LLM API 配置
llm:
  openai:
    api_key: <用户输入>
    base_url: https://api.openai.com/v1
    model: gpt-4

  anthropic:
    api_key: <用户输入>
    model: claude-3-5-sonnet-20241022

  google:
    api_key: <用户输入>
    model: gemini-pro

# 其他配置...
```

---

## 🔐 安全最佳实践

### 1. 密钥管理

- ✅ **自动生成的密钥**：PostgreSQL、Redis、JWT、CSRF
- ✅ **用户提供的密钥**：Tushare、OpenAI、Anthropic、Google
- ⚠️ **绝不提交到 Git**：`config/local.yaml` 和 `.env` 已在 `.gitignore`

### 2. 环境变量优先级

配置加载优先级：

```
环境变量 > config/local.yaml > 默认值
```

示例：

```bash
# 临时覆盖配置
export POSTGRES_PASSWORD="临时密码"
uvicorn app.main:app --reload
```

### 3. 生产环境部署

```bash
# 方式 1: 使用环境变量（推荐）
export POSTGRES_PASSWORD="prod_password"
export JWT_SECRET="prod_jwt_secret"
export TUSHARE_TOKEN="prod_token"
docker-compose up -d

# 方式 2: 使用 config/local.yaml
# 1. 在生产服务器上运行 ./scripts/setup.sh
# 2. 确保 config/local.yaml 权限为 600
chmod 600 config/local.yaml
```

---

## 🛠️ 高级用法

### 手动生成密钥

```bash
# 生成所有密钥
python3 scripts/utils/generate_secrets.py

# 输出示例:
# POSTGRES_PASSWORD=BkjnaVSCz1H5K6gumGIjZWRj
# REDIS_PASSWORD=COxv3cUW8jhMTSC0235fmv7L
# JWT_SECRET=d1b9feec9c8341d70efc4424f028b3e2...
```

### 从 YAML 生成 .env

```bash
# 前提: config/local.yaml 已存在
python3 scripts/utils/generate_env.py

# 输出: .env 文件（扁平化的环境变量）
```

### 重新配置

```bash
# 删除旧配置
rm config/local.yaml .env

# 重新运行配置脚本
./scripts/setup.sh
```

---

## 📊 配置映射表

YAML 配置如何映射到环境变量：

| YAML 路径 | 环境变量 |
|-----------|----------|
| `app.host` | `HOST` |
| `app.port` | `PORT` |
| `app.debug` | `DEBUG` |
| `database.timescaledb.host` | `POSTGRES_HOST` |
| `database.timescaledb.port` | `POSTGRES_PORT` |
| `database.timescaledb.database` | `POSTGRES_DB` |
| `database.timescaledb.username` | `POSTGRES_USER` |
| `database.timescaledb.password` | `POSTGRES_PASSWORD` |
| `database.qdrant.host` | `QDRANT_HOST` |
| `database.qdrant.port` | `QDRANT_PORT` |
| `database.redis.host` | `REDIS_HOST` |
| `database.redis.port` | `REDIS_PORT` |
| `database.redis.password` | `REDIS_PASSWORD` |
| `security.jwt.secret` | `JWT_SECRET` |
| `security.csrf.secret` | `CSRF_SECRET` |
| `data_sources.tushare.token` | `TUSHARE_TOKEN` |
| `llm.openai.api_key` | `OPENAI_API_KEY` |
| `llm.anthropic.api_key` | `ANTHROPIC_API_KEY` |
| `llm.google.api_key` | `GOOGLE_API_KEY` |

---

## 🐛 故障排查

### 问题1: 配置脚本报错 "PyYAML not found"

**解决方案**：

```bash
pip install pyyaml
```

### 问题2: 配置文件已存在

**解决方案**：

```bash
# 脚本会提示是否覆盖
./scripts/setup.sh
# 输入: y (覆盖) 或 N (取消)
```

### 问题3: 数据库连接失败

**检查配置**：

```bash
# 1. 检查 config/local.yaml 中的数据库密码
grep "password" config/local.yaml

# 2. 检查 docker-compose.yml 中的密码是否一致
grep "POSTGRES_PASSWORD" docker-compose.yml

# 3. 如果不一致，更新 docker-compose.yml
# 或重新运行 docker-compose up -d --force-recreate
```

### 问题4: 环境变量未生效

**检查优先级**：

```python
# 在 Python 中调试
import os
from app.core.config import settings

print(f"POSTGRES_HOST from env: {os.environ.get('POSTGRES_HOST')}")
print(f"POSTGRES_HOST from settings: {settings.POSTGRES_HOST}")
```

---

## 📚 相关文档

- [数据库 V2 快速开始](./DATABASE_V2_QUICK_START.md)
- [数据库迁移指南](./DATABASE_MIGRATION_GUIDE.md)
- [Docker 部署指南](./DOCKER_DEPLOYMENT.md)

---

## 💡 常见问题 (FAQ)

### Q1: 为什么不使用 base.yaml + local.yaml？

**A**: 极简设计理念。一个配置文件更容易管理，避免配置分散和合并问题。

### Q2: 如何在团队中共享配置（不包含敏感信息）？

**A**: 使用 `scripts/templates/local.yaml.template` 作为参考模板，团队成员各自运行 `setup.sh` 生成自己的配置。

### Q3: 如何在 CI/CD 中使用？

**A**: 推荐使用环境变量：

```yaml
# .github/workflows/deploy.yml
env:
  POSTGRES_PASSWORD: ${{ secrets.POSTGRES_PASSWORD }}
  JWT_SECRET: ${{ secrets.JWT_SECRET }}
  TUSHARE_TOKEN: ${{ secrets.TUSHARE_TOKEN }}
```

### Q4: 如何添加新的配置项？

**A**: 按以下步骤操作：

1. 在 `scripts/templates/local.yaml.template` 中添加配置项
2. 在 `app/core/config.py` 的 `Settings` 类中添加对应字段
3. 如果需要映射，在 `_get_yaml_to_env_mappings()` 中添加映射关系
4. 重新运行 `./scripts/setup.sh`

---

## ✅ 配置系统验证清单

部署前检查：

- [ ] 已运行 `./scripts/setup.sh` 生成配置
- [ ] `config/local.yaml` 存在且包含正确的密钥
- [ ] `.env` 文件已生成
- [ ] `config/local.yaml` 和 `.env` 在 `.gitignore` 中
- [ ] 数据库密码与 `docker-compose.yml` 一致
- [ ] API 密钥已正确配置（Tushare, OpenAI 等）
- [ ] 测试数据库连接成功
- [ ] 测试 API 服务启动成功

---

**最后更新**: 2025-11-16
**维护者**: TradingAgents-CN Team

# 🚀 TradingAgents-CN 开发环境启动指南

> 本指南详细说明如何在本地开发环境中启动 TradingAgents-CN 项目的所有组件

---

## 📋 目录

1. [前置条件](#前置条件)
2. [第一步：启动数据库服务（Docker Compose）](#第一步启动数据库服务docker-compose)
3. [第二步：启动后端服务（Backend）](#第二步启动后端服务backend)
4. [第三步：启动前端服务（Frontend）](#第三步启动前端服务frontend)
5. [验证与测试](#验证与测试)
6. [常见问题](#常见问题)
7. [停止服务](#停止服务)

---

## 前置条件

### 系统要求
- **操作系统**: macOS 或 Linux（不支持 Windows）
- **Docker**: 已安装 Docker 和 Docker Compose
- **Python**: 3.10 或更高版本
- **Node.js**: 18.0.0 或更高版本
- **npm/yarn**: npm 8.0.0+ 或 yarn

### 验证工具版本
```bash
# 检查 Docker 版本
docker --version
docker-compose --version

# 检查 Python 版本
python --version  # 或 python3 --version

# 检查 Node.js 和 npm 版本
node --version
npm --version
```

---

## 第一步：启动数据库服务（Docker Compose）

### 1.1 克隆项目（如果还没有）
```bash
git clone https://github.com/xi-guan/TradingAgents-CN.git
cd TradingAgents-CN
```

### 1.2 配置环境变量
```bash
# 复制环境变量示例文件
cp .env.example .env

# 使用您喜欢的编辑器编辑 .env 文件
# vim .env
# 或
# nano .env
# 或
# code .env  # 使用 VS Code
```

**必需配置项**：
```bash
# Docker 平台（根据您的机器选择）
DOCKER_PLATFORM=linux/arm64  # Apple Silicon (M1/M2/M3)
# DOCKER_PLATFORM=linux/amd64  # Intel/AMD 处理器

# 数据库配置（使用 Docker 时）
MONGODB_HOST=localhost
MONGODB_PORT=27017
MONGODB_USERNAME=admin
MONGODB_PASSWORD=tradingagents123
MONGODB_DATABASE=tradingagents

REDIS_HOST=localhost
REDIS_PORT=6383  # 注意：映射到本地的 6383 端口
REDIS_PASSWORD=tradingagents123

# 至少配置一个 AI 模型 API
DEEPSEEK_API_KEY=your_deepseek_api_key_here
# 或
DASHSCOPE_API_KEY=your_dashscope_api_key_here
```

### 1.3 启动 Docker 服务
```bash
# 在项目根目录执行
docker-compose up -d
```

**这将启动以下服务**：
- **TimescaleDB** (PostgreSQL + 时序扩展): `localhost:5436`
- **Qdrant** (向量数据库): `localhost:6433` (HTTP), `localhost:6434` (gRPC)
- **Redis** (缓存): `localhost:6383`

### 1.4 验证服务启动
```bash
# 查看所有容器状态
docker-compose ps

# 应该看到类似输出：
#   Name                       Command               State           Ports
# --------------------------------------------------------------------------------
# tradingagents-timescaledb   docker-entrypoint.sh postgres   Up   0.0.0.0:5436->5432/tcp
# tradingagents-qdrant        ./qdrant                        Up   0.0.0.0:6433->6333/tcp, ...
# tradingagents-redis         docker-entrypoint.sh redis ...  Up   0.0.0.0:6383->6379/tcp

# 查看服务日志（确保没有错误）
docker-compose logs -f

# 按 Ctrl+C 退出日志查看
```

### 1.5 等待服务就绪
```bash
# 等待约 30-60 秒让数据库初始化完成
# 您可以通过日志确认：
docker-compose logs timescaledb | grep "database system is ready to accept connections"

# 测试 Redis 连接
docker exec tradingagents-redis redis-cli -a tradingagents123 ping
# 应该返回: PONG
```

---

## 第二步：启动后端服务（Backend）

### 2.1 创建 Python 虚拟环境
```bash
# 在项目根目录
python -m venv venv

# 激活虚拟环境
source venv/bin/activate  # macOS/Linux

# 虚拟环境激活后，命令提示符前会显示 (venv)
```

### 2.2 安装项目依赖
```bash
# 确保在项目根目录且虚拟环境已激活
pip install --upgrade pip

# 安装项目（开发模式）
pip install -e .

# 这会安装所有依赖，可能需要几分钟
```

### 2.3 运行数据库迁移（首次启动）
```bash
# 进入 backend 目录
cd backend

# 运行 Alembic 迁移
alembic upgrade head

# 返回项目根目录
cd ..
```

### 2.4 启动后端服务
```bash
# 确保在项目根目录且虚拟环境已激活
python -m backend.app.main

# 或者，如果上面的命令不工作，尝试：
cd backend
python -m app.main
```

**成功启动后，您应该看到类似输出**：
```
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### 2.5 验证后端服务
打开新的终端窗口，运行：
```bash
# 测试 API 健康检查
curl http://localhost:8000/api/v1/health

# 或在浏览器中访问：
# http://localhost:8000/docs  # Swagger UI API 文档
# http://localhost:8000/redoc # ReDoc API 文档
```

**保持这个终端运行，不要关闭！**

---

## 第三步：启动前端服务（Frontend）

### 3.1 打开新的终端窗口
不要关闭运行后端的终端，打开一个新的终端窗口。

```bash
# 进入项目目录
cd /path/to/TradingAgents-CN/frontend
```

### 3.2 安装前端依赖
```bash
# 使用 npm（首次启动时需要）
npm install

# 或使用 yarn（如果您更喜欢）
# yarn install
```

**注意**：首次安装可能需要几分钟，会下载大量 Node.js 依赖包。

### 3.3 启动开发服务器
```bash
# 使用 npm
npm run dev

# 或使用 yarn
# yarn dev
```

**成功启动后，您应该看到类似输出**：
```
  VITE v5.0.10  ready in 1234 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
  ➜  press h + enter to show help
```

### 3.4 访问前端应用
打开浏览器访问：**http://localhost:5173**

**保持这个终端运行，不要关闭！**

---

## 验证与测试

### ✅ 完整系统检查清单

| 服务 | 访问地址 | 预期结果 |
|-----|---------|---------|
| **TimescaleDB** | `localhost:5436` | Docker 容器运行中 |
| **Redis** | `localhost:6383` | Docker 容器运行中 |
| **Qdrant** | `localhost:6433` | Docker 容器运行中 |
| **Backend API** | http://localhost:8000 | 返回 API 响应 |
| **API 文档** | http://localhost:8000/docs | 显示 Swagger UI |
| **Frontend** | http://localhost:5173 | 显示登录/主页面 |

### 🧪 端到端测试
1. 打开浏览器访问 http://localhost:5173
2. 注册/登录账号
3. 配置 LLM API 密钥（如果还没有）
4. 尝试分析一只股票（例如：`000001` 或 `AAPL`）
5. 查看分析结果

---

## 常见问题

### ❌ 问题 1: Docker 服务无法启动
```bash
# 检查端口是否被占用
lsof -i :5436  # TimescaleDB
lsof -i :6383  # Redis
lsof -i :6433  # Qdrant

# 如果端口被占用，可以在 docker-compose.yml 中修改映射的端口
# 或停止占用端口的服务
```

### ❌ 问题 2: 后端无法连接数据库
```bash
# 检查 .env 文件中的数据库配置
# 确保主机名和端口正确
MONGODB_HOST=localhost  # Docker 运行在本地时用 localhost
MONGODB_PORT=27017      # 这是容器内部端口，不是映射的外部端口
REDIS_HOST=localhost
REDIS_PORT=6383         # 这是映射到本地的端口
```

### ❌ 问题 3: 前端无法连接后端
检查前端配置文件（通常在 `frontend/.env` 或 `frontend/vite.config.ts`），确保 API 地址正确：
```typescript
// 应该指向后端地址
VITE_API_BASE_URL=http://localhost:8000
```

### ❌ 问题 4: 虚拟环境依赖安装失败
```bash
# 更新 pip
pip install --upgrade pip setuptools wheel

# 清理缓存后重试
pip cache purge
pip install -e .
```

### ❌ 问题 5: npm install 失败
```bash
# 清理 npm 缓存
npm cache clean --force

# 删除 node_modules 和 package-lock.json
rm -rf node_modules package-lock.json

# 重新安装
npm install
```

---

## 停止服务

### 停止前端和后端
在运行服务的终端窗口中按 `Ctrl+C`

### 停止 Docker 服务
```bash
# 在项目根目录
docker-compose down

# 如果需要同时删除数据卷（注意：会清空所有数据！）
# docker-compose down -v
```

### 完全清理（谨慎使用）
```bash
# 停止并删除所有容器、网络、数据卷
docker-compose down -v

# 删除虚拟环境
deactivate  # 先退出虚拟环境
rm -rf venv

# 删除前端依赖
cd frontend
rm -rf node_modules package-lock.json
```

---

## 🎯 快速启动脚本

创建一个启动脚本来简化流程（可选）：

### `start-dev.sh`
```bash
#!/bin/bash

echo "🚀 启动 TradingAgents-CN 开发环境..."

# 1. 启动 Docker 服务
echo "📦 启动数据库服务..."
docker-compose up -d

# 等待服务就绪
echo "⏳ 等待数据库启动（30秒）..."
sleep 30

# 2. 启动后端（在后台）
echo "🔧 启动后端服务..."
source venv/bin/activate
python -m backend.app.main &
BACKEND_PID=$!

# 等待后端启动
sleep 5

# 3. 启动前端
echo "🎨 启动前端服务..."
cd frontend
npm run dev

# 注意：前端会在前台运行
# 按 Ctrl+C 会停止前端，但后端和数据库仍在运行
```

### 使用方式
```bash
# 赋予执行权限
chmod +x start-dev.sh

# 运行
./start-dev.sh
```

---

## 📚 相关文档

- [README.md](../README.md) - 项目概览
- [快速开始](./QUICK_START.md) - 简化版启动指南
- [配置指南](./CONFIGURATION_GUIDE.md) - 详细配置说明
- [API 文档](http://localhost:8000/docs) - 后端 API 文档（需先启动服务）

---

## 💡 开发建议

1. **使用 IDE**: 推荐使用 VS Code 或 PyCharm
2. **热重载**: 前端和后端都支持热重载，修改代码后自动刷新
3. **日志查看**:
   - 后端日志：终端输出
   - 前端日志：浏览器开发者工具 Console
   - 数据库日志：`docker-compose logs -f`
4. **调试**:
   - 后端：可以使用 VS Code 的 Python 调试器
   - 前端：使用浏览器开发者工具

---

**祝您开发愉快！** 🎉

如有问题，请查看 [常见问题](./FAQ.md) 或提交 [Issue](https://github.com/xi-guan/TradingAgents-CN/issues)。

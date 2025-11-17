# 🚀 开发环境启动指南

## 前置条件

- macOS/Linux
- Docker & Docker Compose
- Python 3.10+
- Node.js 18+

---

## 步骤 1: 启动数据库服务

```bash
# 克隆项目
git clone https://github.com/xi-guan/TradingAgents-CN.git
cd TradingAgents-CN

# 配置环境变量
cp .env.example .env
# 编辑 .env，至少配置一个 LLM API Key (DEEPSEEK_API_KEY 或 DASHSCOPE_API_KEY)

# 启动 Docker 服务
docker-compose up -d

# 验证服务状态
docker-compose ps
```

**启动的服务**:
- TimescaleDB: `localhost:5436`
- Qdrant: `localhost:6433`
- Redis: `localhost:6383`

---

## 步骤 2: 启动后端服务

**新终端窗口**:

```bash
cd TradingAgents-CN

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # macOS/Linux

# 安装依赖
pip install -e .

# 运行数据库迁移（首次启动）
cd backend
alembic upgrade head
cd ..

# 启动后端
python -m backend.app.main
```

**访问**: http://localhost:8000/docs

---

## 步骤 3: 启动前端服务

**新终端窗口**:

```bash
cd TradingAgents-CN/frontend

# 安装依赖（首次启动）
npm install

# 启动前端
npm run dev
```

**访问**: http://localhost:5173

---

## 停止服务

```bash
# 停止前端/后端: Ctrl+C

# 停止 Docker 服务
docker-compose down
```

---

## 快速启动脚本

创建 `start.sh`:

```bash
#!/bin/bash

# 1. 启动数据库
docker-compose up -d
sleep 10

# 2. 启动后端（后台）
source venv/bin/activate
python -m backend.app.main &

# 3. 启动前端
cd frontend && npm run dev
```

使用:
```bash
chmod +x start.sh
./start.sh
```

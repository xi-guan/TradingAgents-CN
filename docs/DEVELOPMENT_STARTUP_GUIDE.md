# 🚀 开发环境启动指南

## 前置条件

- macOS/Linux
- Docker & Docker Compose
- Python 3.10+
- **uv** (Python 包管理器)
- Node.js 18+
- **pnpm** (前端包管理器)

### 安装必要工具

```bash
# 安装 uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 安装 pnpm
npm install -g pnpm

# 安装 Ollama（可选，用于本地 LLM）
brew install ollama  # macOS
# 或访问 https://ollama.com 下载
```

---

## 快速启动步骤

### 步骤 1: 克隆项目并配置

```bash
# 克隆项目
git clone https://github.com/xi-guan/TradingAgents-CN.git
cd TradingAgents-CN

# 配置环境变量
cp .env.example .env
```

### 步骤 2: 配置 LLM

编辑 `.env` 文件，选择以下**任一方式**：

**方式 A: 本地 Ollama（推荐开发）**
```bash
# 取消注释（约第 207-208 行）
CUSTOM_OPENAI_API_KEY=ollama
CUSTOM_OPENAI_BASE_URL=http://localhost:11434/v1
```

然后启动 Ollama 并下载模型：
```bash
ollama serve
ollama pull qwen2.5:7b  # 新终端
```

**方式 B: 云端 API**
```bash
# 配置任一 API Key
DEEPSEEK_API_KEY=sk-your-key-here
# 或
DASHSCOPE_API_KEY=sk-your-key-here
```

### 步骤 3: 启动数据库

```bash
docker-compose up -d
docker-compose ps  # 验证服务
```

启动的服务：TimescaleDB (5436), Qdrant (6433), Redis (6383)

### 步骤 4: 启动后端

**新终端窗口：**
```bash
cd TradingAgents-CN

# 安装依赖（首次）
uv sync

# 运行迁移（首次）
cd backend && alembic upgrade head && cd ..

# 启动服务
uv run python -m backend.app.main
```

访问 API 文档：http://localhost:8003/docs

### 步骤 5: 启动前端

**新终端窗口：**
```bash
cd TradingAgents-CN/frontend

# 安装依赖（首次）
pnpm install

# 启动服务
pnpm dev
```

访问应用：http://localhost:3004

---

## 端口总览

| 服务 | 端口 | 访问地址 |
|------|------|---------|
| 前端 (Vue) | 3004 | http://localhost:3004 |
| 后端 (FastAPI) | 8003 | http://localhost:8003 |
| TimescaleDB | 5436 | `localhost:5436` |
| Qdrant HTTP | 6433 | http://localhost:6433 |
| Qdrant gRPC | 6434 | `localhost:6434` |
| Redis | 6383 | `localhost:6383` |

---

## Web UI 配置（使用 Ollama 时）

如果使用本地 Ollama，登录后需在 Web UI 中配置：

1. 进入 **设置** → **LLM 配置**
2. 选择 **🔧 自定义 OpenAI 端点**
3. 填写：
   - API 端点: `http://localhost:11434/v1`
   - API 密钥: `ollama`
   - 模型: `qwen2.5:7b`
4. 保存并开始分析

---

## 停止服务

```bash
# 停止前端/后端：在对应终端按 Ctrl+C

# 停止数据库
docker-compose down

# 停止 Ollama（如使用）
pkill ollama
```

---

## 一键启动脚本（可选）

### 使用 Ollama

创建 `start-ollama.sh`：
```bash
#!/bin/bash
set -e

echo "🚀 启动 TradingAgents-CN (Ollama)"

# 启动 Ollama
ollama serve &
sleep 5

# 启动数据库
docker-compose up -d
sleep 10

# 启动后端
uv run python -m backend.app.main &
sleep 5

# 启动前端
cd frontend && pnpm dev
```

### 使用云端 API

创建 `start.sh`：
```bash
#!/bin/bash
set -e

echo "🚀 启动 TradingAgents-CN"

# 启动数据库
docker-compose up -d
sleep 10

# 启动后端
uv run python -m backend.app.main &
sleep 5

# 启动前端
cd frontend && pnpm dev
```

**使用：**
```bash
chmod +x start-ollama.sh  # 或 start.sh
./start-ollama.sh         # 或 ./start.sh
```

---

## 常见问题

### 端口被占用
```bash
# 检查端口占用
lsof -i :3004  # 前端
lsof -i :8003  # 后端
lsof -i :5436  # TimescaleDB
lsof -i :6433  # Qdrant
lsof -i :6383  # Redis
```

### 依赖安装失败
```bash
# 清理缓存
uv cache clean          # 后端
pnpm store prune        # 前端

# 重新安装
uv sync
cd frontend && pnpm install
```

### 数据库连接失败
```bash
# 查看日志
docker-compose logs timescaledb
docker-compose logs redis

# 重启服务
docker-compose restart
```

---

## 推荐模型（Ollama）

| 模型 | 大小 | 特点 | 命令 |
|------|------|------|------|
| qwen2.5:7b | ~4.7GB | 中文好，推荐 | `ollama pull qwen2.5:7b` |
| llama3.1:8b | ~4.7GB | 通用，英文好 | `ollama pull llama3.1:8b` |
| deepseek-r1:7b | ~4.1GB | 推理能力强 | `ollama pull deepseek-r1:7b` |

更多模型：https://ollama.com/library

---

## 备选方案

### 不使用 uv
```bash
python -m venv venv
source venv/bin/activate
pip install -e .
python -m backend.app.main
```

### 不使用 pnpm
```bash
cd frontend
yarn install  # 或 npm install
yarn dev      # 或 npm run dev
```

---

## 📚 更多文档

- **详细配置**: [configuration/custom-openai-endpoint.md](configuration/custom-openai-endpoint.md)
- **API 文档**: http://localhost:8003/docs (启动后访问)
- **项目主页**: https://github.com/xi-guan/TradingAgents-CN

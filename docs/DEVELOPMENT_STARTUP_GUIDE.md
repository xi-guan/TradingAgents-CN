# 🚀 开发环境启动指南

## 前置条件

- macOS/Linux
- Docker & Docker Compose
- Python 3.10+
- Node.js 18+
- **Ollama**（可选，用于本地 LLM）

---

## 步骤 0: 启动本地 LLM（可选）

### 使用 Ollama（推荐本地开发）

```bash
# 安装 Ollama (macOS)
brew install ollama

# 或访问 https://ollama.com 下载安装

# 启动 Ollama 服务
ollama serve

# 下载模型（新终端）
ollama pull qwen2.5:7b          # 推荐：通义千问 7B
# 或
ollama pull llama3.1:8b         # Meta Llama 3.1 8B
# 或
ollama pull deepseek-r1:7b      # DeepSeek R1 7B
```

**优势**:
- ✅ 完全免费，无需 API Key
- ✅ 数据隐私，本地运行
- ✅ 无网络限制

---

## 步骤 1: 启动数据库服务

```bash
# 克隆项目
git clone https://github.com/xi-guan/TradingAgents-CN.git
cd TradingAgents-CN

# 配置环境变量
cp .env.example .env
```

### 配置 LLM（二选一，**只需修改 .env 文件，无需改代码**）

**选项 A: 使用 Ollama（本地，推荐）**

编辑 `.env` 文件，找到以下部分并取消注释：
```bash
# 找到这两行（约在第 207-208 行）：
#CUSTOM_OPENAI_API_KEY=ollama
#CUSTOM_OPENAI_BASE_URL=http://localhost:11434/v1

# 去掉前面的 # 号：
CUSTOM_OPENAI_API_KEY=ollama
CUSTOM_OPENAI_BASE_URL=http://localhost:11434/v1
```

**选项 B: 使用云端 API**

编辑 `.env` 文件，配置以下任一 API Key：
```bash
# DeepSeek（推荐，性价比高）
DEEPSEEK_API_KEY=sk-your-key-here

# 或通义千问
DASHSCOPE_API_KEY=sk-your-key-here
```

### 启动数据库

```bash
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

## Web UI 中使用 Ollama

启动前端后（http://localhost:5173）：

1. **登录/注册**账号
2. 进入 **设置** → **LLM 配置**
3. 选择 **🔧 自定义 OpenAI 端点**
4. 配置：
   - **API 端点**: `http://localhost:11434/v1`
   - **API 密钥**: `ollama`（任意值）
   - **模型**: 选择您已下载的模型（如 `qwen2.5:7b`）
5. 保存配置
6. 开始分析股票

---

## 快速启动脚本

### 使用 Ollama

创建 `start-ollama.sh`:

```bash
#!/bin/bash

# 1. 启动 Ollama（后台）
ollama serve &
sleep 5

# 2. 启动数据库
docker-compose up -d
sleep 10

# 3. 启动后端（后台）
source venv/bin/activate
python -m backend.app.main &
sleep 5

# 4. 启动前端
cd frontend && npm run dev
```

### 使用云端 API

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
chmod +x start-ollama.sh  # 或 start.sh
./start-ollama.sh         # 或 ./start.sh
```

---

## 📚 更多信息

- **Ollama 配置详情**: [docs/configuration/custom-openai-endpoint.md](configuration/custom-openai-endpoint.md)
- **支持的模型**: https://ollama.com/library
- **项目主页**: https://github.com/xi-guan/TradingAgents-CN

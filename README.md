# TradingAgents Forked Version

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)

A forked and enhanced version of [TradingAgents-CN](https://github.com/hsliuping/TradingAgents-CN), focused on macOS/Linux support with modern architecture.

> **Note**: This is a personal fork for learning and research purposes. Not suitable for production trading.

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- **uv** (Python package manager) - [Installation](https://docs.astral.sh/uv/)
- **pnpm** (Frontend package manager) - Install via `npm install -g pnpm`

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/xi-guan/TradingAgents-CN
cd TradingAgents-CN
```

2. **Configure environment**
```bash
cp .env.example .env
# Edit .env and configure your settings (MongoDB, Redis, API keys)
```

3. **Start databases (Docker)**
```bash
# Start MongoDB and Redis
docker compose -f docker/docker-compose.hub.nginx.yml up -d mongodb redis
```

### Running the Application

#### Backend

```bash
# Install dependencies with uv
uv sync

# Run database migrations
cd backend
uv run alembic upgrade head

# Start backend server
cd ..
uv run python -m backend.app
```

The backend API will be available at:
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

#### Frontend

```bash
# Install dependencies
cd frontend
pnpm install

# Start development server
pnpm dev
```

The frontend will be available at http://localhost:5173

---

## 🏗️ Tech Stack

### Backend
- **FastAPI** - Modern async Python web framework
- **Python 3.10+** - Core language
- **MongoDB** - Primary database for stock data and analysis
- **Redis** - Caching and session management
- **uv** - Fast Python package manager

### Frontend
- **Vue 3** - Progressive JavaScript framework
- **TypeScript** - Type-safe JavaScript
- **Vite** - Next-generation frontend tooling
- **Element Plus** - UI component library
- **pnpm** - Fast, disk space efficient package manager

### Core Library
- **LangGraph** - Multi-agent orchestration
- **LangChain** - LLM application framework

---

## 📋 Features

### Core Capabilities
- Multi-agent stock analysis system
- Support for A-shares, Hong Kong, and US stocks
- Integration with multiple LLM providers
- Real-time data synchronization
- Batch analysis with progress tracking

### Web Interface
- User authentication and authorization
- LLM configuration management
- Stock screening and filtering
- Favorites management
- Analysis history and reports

---

## 🔑 API Keys Required

You'll need API keys for:

- **LLM Provider** (at least one):
  - DeepSeek API (recommended, cost-effective)
  - Alibaba DashScope (Qwen models)
  - OpenAI
  - Google AI (Gemini)

- **Data Sources**:
  - Tushare Token (recommended for A-shares)
  - FinnHub API (for US stocks)
  - AKShare (free, no key required)

---

## 📖 Documentation

- [Feature Specification](./TradingAgents-CN_Feature_Specification.md)
- [Multi-Market Data Guide](./Multi_Market_Data_Implementation_Guide.md)
- [Web Features Overview](./Web_Features_Overview.md)
- [Configuration Guide](./docs/configuration/)

---

## 🔧 Development

### Project Structure

```
TradingAgents-CN/
├── backend/                # FastAPI backend
├── frontend/               # Vue 3 frontend
├── tradingagents/          # Core multi-agent library
├── docker/                 # Docker configurations
├── docs/                   # Documentation & examples
├── tests/                  # Test suite
├── scripts/                # Utility scripts & CLI tools
├── assets/                 # Static assets & images
└── config/                 # Logging configuration
```

**Runtime directories** (not in version control):
- `data/` - Analysis results and runtime data
- `database/` - Database files
- `reports/` - Generated reports

### Running Tests

```bash
# Backend tests
uv run pytest tests/

# Frontend tests (if available)
cd frontend
pnpm test
```

### Code Style

Backend uses Ruff for linting and formatting:

```bash
# Lint code
uv run ruff check .

# Format code
uv run ruff format .
```

Frontend uses Biome:

```bash
cd frontend
pnpm check      # Lint and format
pnpm format     # Format only
pnpm lint       # Lint only
```

---

## 🐳 Docker Configuration

### Platform Support

Configure your platform in `.env`:

```bash
# In .env file
DOCKER_PLATFORM=linux/amd64  # for Intel/AMD processors
DOCKER_PLATFORM=linux/arm64  # for Apple Silicon
```

### Services

- **MongoDB**: Port 27017
- **Redis**: Port 6379

---

## 📜 License

This project uses a dual-license model:

### Open Source Components (Apache 2.0)
- Scope: All files except `app/` and `frontend/`
- Usage: Free for personal and commercial use
- Requirements: Include license and copyright notice

### Proprietary Components
- Scope: `app/` (FastAPI backend) and `frontend/` (Vue frontend)
- Personal Use: Free for learning and research
- Commercial Use: Requires separate license
- Contact: hsliup@163.com (original author)

**Note**: This is a personal fork. For commercial use of web components, please contact the original TradingAgents-CN author.

---

## 🙏 Acknowledgments

### Original Projects
- [TradingAgents](https://github.com/TauricResearch/TradingAgents) by Tauric Research
- [TradingAgents-CN](https://github.com/hsliuping/TradingAgents-CN) by hsliuping

### Community
Thanks to all contributors to the original projects and the open-source community.

---

## ⚠️ Disclaimer

**IMPORTANT**: This software is for educational and research purposes only.

- ❌ Not financial advice
- ❌ Not suitable for production trading
- ❌ No warranty or guarantee
- ✅ Use at your own risk
- ✅ Consult professional advisors for investment decisions

---

## 📞 Support

For issues and questions:
- **Issues**: [GitHub Issues](https://github.com/xi-guan/TradingAgents-CN/issues)
- **Original Project**: [TradingAgents-CN](https://github.com/hsliuping/TradingAgents-CN)

---

<div align="center">

**Personal Fork for Learning Purposes**

[Report Bug](https://github.com/xi-guan/TradingAgents-CN/issues) | [Request Feature](https://github.com/xi-guan/TradingAgents-CN/issues)

</div>

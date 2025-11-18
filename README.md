# TradingAgents Forked Version

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)

A forked and enhanced version of [TradingAgents-CN](https://github.com/hsliuping/TradingAgents-CN), focused on macOS/Linux support with modern architecture.

> **Note**: This is a personal fork for learning and research purposes. Not suitable for production trading.

---

## 🚀 Quick Start

### Prerequisites

- macOS or Linux (**Windows not supported**)
- Docker and Docker Compose
- Python 3.10+ (for source installation)

### Docker Installation (Recommended)

1. Clone the repository:
```bash
git clone https://github.com/your-username/TradingAgents-CN
cd TradingAgents-CN
```

2. Copy and configure environment variables:
```bash
cp .env.example .env
# Edit .env and add your API keys
```

3. Start services:
```bash
docker-compose up -d
```

4. Access the application:
- Web UI: http://localhost:8080
- API: http://localhost:8000

### Source Installation

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux only
```

2. Install dependencies:
```bash
pip install -e .
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env with your settings
```

4. Start databases:
```bash
docker-compose up -d
```

5. Run the application:
```bash
# Backend
python -m app.main

# Frontend (in another terminal)
cd frontend
npm install
npm run dev
```

---

## 🏗️ Tech Stack

### Backend
- **FastAPI** - Modern async Python web framework
- **Python 3.10+** - Core language
- **TimescaleDB** - Time-series database (PostgreSQL extension)
- **Qdrant** - Vector database for embeddings
- **Redis** - Caching and session management

### Frontend
- **Vue 3** - Progressive JavaScript framework
- **TypeScript** - Type-safe JavaScript
- **Vite** - Next-generation frontend tooling
- **Element Plus** - UI component library

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
│   ├── docker-compose.yml
│   ├── Dockerfile.frontend
│   ├── nginx-frontend.conf
│   └── nginx-gateway.conf
├── docs/                   # Documentation
│   ├── deployment/        # Installation & deployment configs
│   └── examples/          # Code examples
├── tests/                  # Test suite
├── scripts/                # Utility scripts
├── tools/                  # CLI tools
│   └── cli/               # Data initialization CLI
├── legacy/                 # Legacy code
│   └── web/               # Streamlit app (deprecated)
├── assets/                 # Static assets & images
├── config/                 # Global configuration
├── data/                   # Runtime data
├── database/               # Database files
└── reports/                # Generated reports
```

### Running Tests

```bash
pytest tests/
```

### Code Style

```bash
# Format code
black .
isort .

# Type checking
mypy .
```

---

## 🐳 Docker Configuration

### Platform Support

This fork defaults to ARM64 (Apple Silicon). To change:

```bash
# In .env file
DOCKER_PLATFORM=linux/amd64  # for Intel/AMD processors
DOCKER_PLATFORM=linux/arm64  # for Apple Silicon (default)
```

### Services

- **TimescaleDB**: Port 5432
- **Qdrant**: Port 6333 (HTTP), 6334 (gRPC)
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

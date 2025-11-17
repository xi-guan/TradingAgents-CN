.PHONY: help format format-check lint lint-fix test clean install

# 默认目标：显示帮助信息
help:
	@echo "TradingAgents-CN - Development Commands"
	@echo ""
	@echo "Available targets:"
	@echo "  make install        - Install dependencies (backend + frontend)"
	@echo "  make format         - Format code (backend + frontend)"
	@echo "  make format-check   - Check code formatting without changes"
	@echo "  make lint           - Run linters (backend + frontend)"
	@echo "  make lint-fix       - Run linters with auto-fix"
	@echo "  make test           - Run tests"
	@echo "  make clean          - Clean build artifacts"
	@echo ""
	@echo "Backend only:"
	@echo "  make format-backend      - Format Python code with Ruff"
	@echo "  make lint-backend        - Lint Python code with Ruff"
	@echo ""
	@echo "Frontend only:"
	@echo "  make format-frontend     - Format TypeScript/Vue with Biome"
	@echo "  make lint-frontend       - Lint TypeScript/Vue with Biome"

# ============================================================================
# 安装依赖
# ============================================================================
install: install-backend install-frontend

install-backend:
	@echo "📦 Installing backend dependencies..."
	pip install -e ".[dev]"

install-frontend:
	@echo "📦 Installing frontend dependencies..."
	cd frontend && npm install

# ============================================================================
# 格式化代码
# ============================================================================
format: format-backend format-frontend

format-backend:
	@echo "🎨 Formatting backend code with Ruff..."
	ruff format .

format-frontend:
	@echo "🎨 Formatting frontend code with Biome..."
	cd frontend && npm run format

format-check: format-check-backend format-check-frontend

format-check-backend:
	@echo "🔍 Checking backend code formatting..."
	ruff format --check .

format-check-frontend:
	@echo "🔍 Checking frontend code formatting..."
	cd frontend && npm run format:check

# ============================================================================
# Lint 检查
# ============================================================================
lint: lint-backend lint-frontend

lint-backend:
	@echo "🔍 Linting backend code with Ruff..."
	ruff check .

lint-frontend:
	@echo "🔍 Linting frontend code with Biome + ESLint..."
	cd frontend && npm run lint:biome
	cd frontend && npm run lint

lint-fix: lint-fix-backend lint-fix-frontend

lint-fix-backend:
	@echo "🔧 Fixing backend code with Ruff..."
	ruff check --fix .

lint-fix-frontend:
	@echo "🔧 Fixing frontend code with Biome..."
	cd frontend && npm run check

# ============================================================================
# 测试
# ============================================================================
test: test-backend test-frontend

test-backend:
	@echo "🧪 Running backend tests..."
	pytest

test-frontend:
	@echo "🧪 Running frontend tests..."
	@echo "⚠️  Frontend tests not configured yet"

# ============================================================================
# 清理
# ============================================================================
clean: clean-backend clean-frontend

clean-backend:
	@echo "🧹 Cleaning backend build artifacts..."
	rm -rf build/ dist/ *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

clean-frontend:
	@echo "🧹 Cleaning frontend build artifacts..."
	cd frontend && rm -rf dist/ node_modules/.vite

# ============================================================================
# 数据库
# ============================================================================
db-start:
	@echo "🐳 Starting database containers..."
	docker-compose up -d

db-stop:
	@echo "🛑 Stopping database containers..."
	docker-compose down

db-logs:
	@echo "📋 Showing database logs..."
	docker-compose logs -f

# ============================================================================
# 开发服务器
# ============================================================================
dev-backend:
	@echo "🚀 Starting backend development server..."
	cd app && uvicorn main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	@echo "🚀 Starting frontend development server..."
	cd frontend && npm run dev

# ============================================================================
# CI/CD
# ============================================================================
ci: format-check lint test
	@echo "✅ CI checks passed!"

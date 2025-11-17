# TradingAgents-CN Backend

FastAPI-based backend service for TradingAgents-CN.

## Structure

```
backend/
├── app/              # FastAPI application
│   ├── core/         # Core functionality (config, database, logging)
│   ├── models/       # Database models
│   ├── routers/      # API endpoints
│   ├── services/     # Business logic
│   ├── middleware/   # Request/response middleware
│   ├── schemas/      # Pydantic schemas
│   ├── utils/        # Utility functions
│   └── main.py       # Application entry point
├── alembic/          # Database migrations
├── alembic.ini       # Alembic configuration
└── Dockerfile        # Docker build configuration
```

## Tech Stack

- **FastAPI** - Modern async Python web framework
- **SQLAlchemy** - ORM for database operations
- **Alembic** - Database migration tool
- **TimescaleDB** - Time-series data storage
- **Redis** - Caching and session management
- **Qdrant** - Vector database for embeddings

## Running Locally

### Prerequisites

- Python 3.10+
- PostgreSQL (TimescaleDB)
- Redis
- Qdrant

### Setup

1. Install dependencies:
```bash
cd /path/to/TradingAgents-CN
pip install -e .
```

2. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your settings
```

3. Run database migrations:
```bash
cd backend
alembic upgrade head
```

4. Start the server:
```bash
python -m app.main
```

The API will be available at http://localhost:8000

## Docker Deployment

Build the backend image:
```bash
cd backend
docker build -t tradingagents-backend .
```

Or use docker-compose from the project root:
```bash
docker-compose up -d
```

## API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Database Migrations

Create a new migration:
```bash
cd backend
alembic revision --autogenerate -m "Description of changes"
```

Apply migrations:
```bash
alembic upgrade head
```

Rollback migration:
```bash
alembic downgrade -1
```

## Development

### Code Style

```bash
# Format code
black backend/app
isort backend/app

# Type checking
mypy backend/app
```

### Testing

```bash
pytest tests/
```

## License

This backend is proprietary software. See root LICENSE file for details.

For commercial use, please contact: hsliup@163.com (original author)

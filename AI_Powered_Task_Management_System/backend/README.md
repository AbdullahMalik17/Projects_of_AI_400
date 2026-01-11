# AI Task Manager - Backend

FastAPI backend for the AI-Powered Task Management System with intelligent task processing using Google Gemini and OpenAI Agent SDK.

## Technology Stack

- **Framework**: FastAPI 0.109
- **Database ORM**: SQLModel 0.0.14
- **LLM**: Google Gemini API
- **Agent Framework**: OpenAI Agent SDK
- **Package Manager**: UV (fast Python package manager)
- **Python**: 3.10+

## Prerequisites

- Python 3.10 or higher
- UV package manager ([installation instructions](https://github.com/astral-sh/uv))
- Google Gemini API key
- (Optional) OpenAI API key

## Installation

### 1. Install UV

```bash
# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Clone and Setup

```bash
cd AI_Powered_Task_Management_System/backend

# Create virtual environment with UV
uv venv

# Activate virtual environment
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

# Install dependencies
uv pip install -e .

# Install dev dependencies
uv pip install -e ".[dev]"
```

### 3. Environment Configuration

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your API keys
# Required: GEMINI_API_KEY, JWT_SECRET_KEY
```

### 4. Initialize Database

```bash
# Run database migrations (creates tables)
python -c "from app.core.database import init_db; init_db()"
```

## Running the Application

### Development Server

```bash
# Run with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Server

```bash
# Run with multiple workers
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Access the API:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Project Structure

```
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/     # API route handlers
│   │       └── api.py         # API router aggregation
│   ├── agents/                # AI agent implementations
│   │   ├── task_parser.py
│   │   ├── task_intelligence.py
│   │   └── context_manager.py
│   ├── services/              # Business logic layer
│   │   ├── task_service.py
│   │   └── analytics_service.py
│   ├── repositories/          # Data access layer
│   │   └── task_repository.py
│   ├── models/                # SQLModel database models
│   │   ├── task.py
│   │   ├── user.py
│   │   └── ...
│   ├── schemas/               # Pydantic request/response schemas
│   │   └── task.py
│   ├── core/                  # Core configuration
│   │   ├── config.py
│   │   ├── database.py
│   │   └── security.py
│   └── main.py               # Application entry point
├── tests/                    # Test suite
├── alembic/                  # Database migrations
├── pyproject.toml            # UV/Project configuration
└── .env.example              # Environment template
```

## Development

### Code Formatting

```bash
# Format code with Black
black app/

# Lint with Ruff
ruff check app/

# Type checking with mypy
mypy app/
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/
```

### Adding Dependencies

```bash
# Add a new dependency
uv pip install <package-name>

# Update pyproject.toml manually and sync
uv pip install -e .
```

## API Endpoints

### Tasks
- `POST /api/v1/tasks` - Create task (natural language or structured)
- `GET /api/v1/tasks` - List tasks with filters
- `GET /api/v1/tasks/{id}` - Get task details
- `PUT /api/v1/tasks/{id}` - Update task
- `DELETE /api/v1/tasks/{id}` - Delete task
- `POST /api/v1/tasks/{id}/complete` - Mark task complete

### AI Chat
- `POST /api/v1/chat` - Conversational AI endpoint
- `GET /api/v1/chat/history` - Get conversation history

### Analytics
- `GET /api/v1/analytics/productivity` - Productivity metrics
- `GET /api/v1/analytics/insights` - AI-generated insights

## Environment Variables

Required variables in `.env`:

```env
DATABASE_URL=sqlite:///./taskmanager.db
GEMINI_API_KEY=your_api_key_here
JWT_SECRET_KEY=your_secret_key_here
ENVIRONMENT=development
```

See `.env.example` for complete configuration options.

## Architecture

The backend follows a layered architecture:

1. **API Layer**: FastAPI endpoints with request validation
2. **Service Layer**: Business logic and orchestration
3. **Agent Layer**: AI/LLM integration for intelligent features
4. **Repository Layer**: Database access abstraction
5. **Model Layer**: SQLModel entities

See `docs/ARCHITECTURE.md` for detailed architecture documentation.

## License

Proprietary - All rights reserved

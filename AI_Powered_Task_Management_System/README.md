# AI-Powered Task Management System

An intelligent task management application leveraging artificial intelligence to enhance productivity through natural language processing, smart scheduling, and context-aware assistance.

## Overview

This system combines modern web technologies with advanced AI capabilities to provide an intuitive and intelligent task management experience. It supports natural language task creation, automatic prioritization, intelligent task breakdown, and personalized productivity insights.

## Technology Stack

### Backend
- **Framework**: FastAPI 0.109 (Python 3.10+)
- **ORM**: SQLModel 0.0.14
- **Database**: SQLite (development) / PostgreSQL (production)
- **AI/LLM**: Google Gemini API
- **Agent Framework**: OpenAI Agent SDK
- **Package Manager**: UV

### Frontend
- **Framework**: Next.js 14 (React 18)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **State Management**: Zustand
- **Data Fetching**: TanStack Query (React Query)
- **AI Chat Interface**: Chainlit (planned integration)

## Key Features

### Core Features (MVP)
- ✅ **Task CRUD Operations**: Create, read, update, delete tasks with full property management
- ✅ **Natural Language Input**: AI-powered task parsing from conversational input
- ✅ **Context-Aware AI Assistant**: Intelligent suggestions and productivity insights
- ✅ **Task Organization**: Tags, priorities, deadlines, and hierarchical tasks
- 🚧 **Smart Scheduling**: AI-suggested optimal task ordering
- 🚧 **Task Breakdown**: Automatic decomposition of complex tasks into subtasks

### Planned Features
- **Analytics Dashboard**: Productivity metrics and completion trends
- **Calendar Integration**: Sync with Google Calendar, Outlook
- **Advanced AI Capabilities**: Multi-turn conversations, proactive reminders
- **Collaboration**: Multi-user support with shared tasks
- **Mobile Experience**: Progressive Web App with offline support

**Legend**: ✅ Implemented | 🚧 In Progress | 📋 Planned

## Project Structure

```
AI_Powered_Task_Management_System/
├── backend/                # FastAPI backend application
│   ├── app/
│   │   ├── api/           # API endpoints
│   │   ├── agents/        # AI agent implementations
│   │   ├── services/      # Business logic layer
│   │   ├── repositories/  # Data access layer
│   │   ├── models/        # SQLModel database models
│   │   ├── schemas/       # Pydantic API schemas
│   │   └── core/          # Configuration and utilities
│   ├── tests/             # Backend tests
│   ├── pyproject.toml     # UV package configuration
│   └── README.md          # Backend documentation
├── frontend/              # Next.js frontend application
│   ├── app/               # Next.js App Router
│   ├── components/        # React components
│   ├── lib/               # Utilities and helpers
│   ├── package.json       # npm dependencies
│   └── README.md          # Frontend documentation
├── docs/                  # Project documentation
│   └── ARCHITECTURE.md    # Detailed architecture blueprint
└── README.md              # This file
```

## Getting Started

### Prerequisites

- **Python 3.10+** with UV package manager
- **Node.js 18+** with npm
- **Google Gemini API Key** ([Get one here](https://ai.google.dev/))
- (Optional) **PostgreSQL** for production deployment

### Installation

#### 1. Clone the Repository

```bash
git clone <repository-url>
cd AI_Powered_Task_Management_System
```

#### 2. Backend Setup

```bash
cd backend

# Install UV (if not already installed)
# Windows: powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
# Linux/macOS: curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv pip install -e .

# Configure environment
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY and JWT_SECRET_KEY

# Initialize database
python -c "from app.core.database import init_db; init_db()"

# Run development server
uvicorn app.main:app --reload
```

Backend will be available at **http://localhost:8000**
- API Documentation: **http://localhost:8000/docs**
- ReDoc: **http://localhost:8000/redoc**

#### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

Frontend will be available at **http://localhost:3000**

### Quick Test

1. **Backend**: Visit http://localhost:8000/docs and try the task endpoints
2. **Frontend**: Open http://localhost:3000 to see the landing page
3. **Create a task**: Use the API docs to POST a new task

## Development

### Backend Development

```bash
cd backend

# Format code
black app/

# Type checking
mypy app/

# Run tests
pytest

# Add new dependency
uv pip install <package-name>
```

### Frontend Development

```bash
cd frontend

# Run development server with hot reload
npm run dev

# Build for production
npm run build

# Type checking
npm run type-check

# Linting
npm run lint
```

## Architecture

The system follows a **Modular Monolith architecture** for the backend with clear separation of concerns across layers:

1. **API Layer**: FastAPI endpoints with request validation
2. **Service Layer**: Business logic and orchestration
3. **Agent Layer**: AI/LLM integration for intelligent features
4. **Repository Layer**: Database access abstraction
5. **Model Layer**: SQLModel entities

The frontend uses **Next.js App Router** with modern React patterns and TypeScript for type safety.

For detailed architecture information, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## API Documentation

### Core Endpoints

**Tasks**:
- `POST /api/v1/tasks` - Create task (structured input)
- `POST /api/v1/tasks/nl-create` - Create task (natural language)
- `GET /api/v1/tasks` - List tasks with filtering and pagination
- `GET /api/v1/tasks/{id}` - Get task details
- `PUT /api/v1/tasks/{id}` - Update task
- `DELETE /api/v1/tasks/{id}` - Delete task
- `POST /api/v1/tasks/{id}/complete` - Mark task complete

**Planned Endpoints**:
- `POST /api/v1/chat` - Conversational AI interaction
- `GET /api/v1/analytics/productivity` - Productivity metrics
- `GET /api/v1/analytics/insights` - AI-generated insights

## Configuration

### Backend Environment Variables

```env
DATABASE_URL=sqlite:///./taskmanager.db
GEMINI_API_KEY=your_api_key_here
JWT_SECRET_KEY=your_secret_key_here  # Generate with: openssl rand -hex 32
ENVIRONMENT=development
DEBUG=True
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000
```

### Frontend Environment Variables

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

## Roadmap

### Phase 1: MVP (Current) ✅
- [x] Backend API with FastAPI
- [x] Database models with SQLModel
- [x] Basic task CRUD operations
- [x] Next.js frontend setup
- [ ] Natural language task parsing with Gemini
- [ ] Basic AI agent implementation

### Phase 2: AI Enhancement 🚧
- [ ] Context-aware AI assistant
- [ ] Task intelligence (priority suggestions, breakdown)
- [ ] Productivity insights and analytics
- [ ] Chainlit chat interface integration

### Phase 3: Advanced Features 📋
- [ ] Smart scheduling algorithms
- [ ] Calendar integrations (Google, Outlook)
- [ ] Advanced analytics dashboard
- [ ] Multi-user support and collaboration

### Phase 4: Scale & Polish 📋
- [ ] Mobile app (React Native or PWA)
- [ ] Advanced AI capabilities (multi-agent system)
- [ ] Plugin architecture for third-party integrations
- [ ] Performance optimizations and cloud deployment

## Testing

### Backend Tests

```bash
cd backend
pytest tests/ -v --cov=app
```

### Frontend Tests

```bash
cd frontend
npm test
```

## Contributing

This is currently a solo project, but contributions will be welcomed once the MVP is stabilized. Please follow these guidelines:

1. Follow existing code style (Black for Python, ESLint for TypeScript)
2. Write tests for new features
3. Update documentation as needed
4. Use conventional commit messages

## Security

- Never commit `.env` files or API keys
- Use environment variables for all secrets
- JWT tokens for authentication (multi-user phase)
- Input validation via Pydantic models
- SQL injection prevention via SQLModel ORM

## License

Proprietary - All rights reserved

## Acknowledgments

- **FastAPI**: Modern Python web framework
- **SQLModel**: Elegant database ORM
- **Next.js**: Production-grade React framework
- **Google Gemini**: Advanced LLM capabilities
- **OpenAI**: Agent SDK and development patterns

## Contact & Support

For questions or issues, please open an issue on GitHub or contact the project maintainer.

---

**Built with ❤️ using cutting-edge AI and web technologies**

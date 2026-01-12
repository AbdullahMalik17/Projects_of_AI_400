# AI-Powered Task Management System

An intelligent task management application leveraging artificial intelligence to enhance productivity through natural language processing, smart scheduling, and context-aware assistance.

## 🎥 Project Demo
[Watch the Project Demo Video](./Project_Demo.mp4)

![License](https://img.shields.io/badge/license-Proprietary-blue.svg)
![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)
![Next.js](https://img.shields.io/badge/Next.js-14-black.svg)

## 🚀 Key Features

*   **🧠 AI Assistant Chat**: Interact with your database using natural language.
    *   *"Create a high priority task to buy milk"*
    *   *"Delete the task I just created"*
    *   *"List my overdue tasks"*
*   **⚡ Context-Aware Memory**: The agent remembers previous turns of the conversation.
*   **🗣️ Natural Language Processing**: Create complex tasks with due dates and tags just by typing.
*   **🤖 Smart Breakdown**: Automatically decompose complex projects into manageable subtasks.
*   **📊 Productivity Insights**: Get AI-driven analysis of your work habits.
*   **📱 Responsive UI**: Works seamlessly on Desktop, Tablet, and Mobile.

## 🛠️ Technology Stack

### Backend
- **Framework**: FastAPI (Python)
- **Database**: SQLModel (SQLite for dev, PostgreSQL ready for prod)
- **AI Engine**: Google Gemini API
- **Agent Pattern**: ReAct (Reasoning + Acting) with Tool Use

### Frontend
- **Framework**: Next.js 14 (React)
- **Styling**: Tailwind CSS
- **Icons**: Lucide React
- **Rendering**: React Markdown

## 🏁 Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- Google Gemini API Key ([Get it here](https://aistudio.google.com/app/apikey))

### 1. Backend Setup

```bash
cd backend

# Create virtual environment (using uv or standard venv)
# Option A: Standard Python
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate

# Install Dependencies
pip install -r requirements.txt

# Configure Environment
cp .env.example .env
# Open .env and paste your GEMINI_API_KEY

# Run Server
uvicorn app.main:app --reload
```
Backend runs at: `http://localhost:8000`

### 2. Frontend Setup

```bash
cd frontend

# Install Dependencies
npm install

# Run Development Server
npm run dev
```
Frontend runs at: `http://localhost:3000`

## 📦 Deployment

This project is designed for easy deployment to the cloud.

- **Frontend**: Vercel
- **Backend**: Render / Railway
- **Database**: Neon (PostgreSQL)

👉 **[Read the Full Deployment Guide](docs/DEPLOYMENT.md)**

## 🧪 Running Tests

Ensure your backend is healthy with the included test suite.

```bash
cd backend
python -m pytest
```

## 📂 Project Structure

```
AI_Powered_Task_Management_System/
├── backend/                # FastAPI Application
│   ├── app/
│   │   ├── agents/        # AI Agents (ReAct Pattern)
│   │   ├── api/           # API Endpoints
│   │   ├── models/        # Database Models
│   │   └── services/      # Business Logic
│   └── tests/             # Pytest Suite
├── frontend/              # Next.js Application
│   ├── app/               # Pages & Layouts
│   ├── components/        # React Components
│   └── lib/               # API Client
└── docs/                  # Documentation
```

## 🤝 Contact

For questions or feedback, please contact the developer.

---
*Built for University Project Submission*
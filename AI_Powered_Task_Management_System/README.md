# AI-Powered Task Management System

An intelligent, context-aware task management platform that leverages Generative AI to revolutionize personal productivity. Built with a modern tech stack, it features natural language processing, intelligent task decomposition, and a proactive AI assistant.

## 🎥 Project Demo
[Watch the Project Demo Video](./Project_Demo.mp4)

![License](https://img.shields.io/badge/license-Proprietary-blue.svg)
![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)
![Next.js](https://img.shields.io/badge/Next.js-14-black.svg)
![Status](https://img.shields.io/badge/Status-Active_Development-orange.svg)

## 📖 Overview

The **AI-Powered Task Management System** is more than just a to-do list; it's a productivity partner. By integrating Google's Gemini LLM with a robust ReAct agent architecture, the system understands your intent, helps you organize complex projects, and provides actionable insights into your work habits.

The application is architected as a **Modular Monolith** to ensure code quality and maintainability, featuring a hybrid frontend that combines the robustness of **Next.js** with the conversational flexibility of **Chainlit** (planned).

## 🚀 Key Features

### 🧠 Intelligent Task Operations
- **Natural Language Creation**: Simply type "Remind me to submit the report next Friday at 2 PM" and the system parses the title, deadline, and priority automatically.
- **Smart Breakdown**: The **Task Breakdown Agent** analyzes complex tasks (e.g., "Plan a vacation") and suggests a list of actionable subtasks.
- **Context-Aware Assistance**: The AI remembers previous interactions, allowing for multi-turn conversations about your schedule and priorities.

### ⚡ Advanced Productivity Tools
- **Automated Prioritization**: The system suggests task priority based on due dates, keywords, and your historical behavior.
- **Productivity Insights**: Get AI-driven analytics on your completion rates, peak productivity times, and work patterns.
- **Search & Discovery**: Quickly find tasks using keyword search (with Semantic Search planned).

### 💻 Modern User Experience
- **Responsive Interface**: A clean, mobile-friendly UI built with **Next.js 14** and **Tailwind CSS**.
- **Real-Time Updates**: Changes are reflected instantly across the application.
- **Visual Dashboard**: Track your progress with intuitive charts and statistics.

## 🛠️ System Architecture

The project follows a clean, layered architecture designed for scalability and ease of development.

### Backend (FastAPI + Python)
- **API Layer**: RESTful endpoints with Pydantic validation and automatic OpenAPI documentation.
- **AI Agent Layer**: Implements the **ReAct (Reasoning + Acting)** pattern. It orchestrates tools like `task_parser` and `context_manager` to fulfill user requests.
- **Service Layer**: Encapsulates business logic, ensuring separation of concerns.
- **Data Layer**: Uses **SQLModel** (SQLAlchemy + Pydantic) for type-safe database interactions. Currently supports SQLite (Dev) and PostgreSQL (Prod).

### Frontend (Next.js + React)
- **App Router**: Utilizes Next.js 14's latest routing and layout features.
- **Components**: modular, reusable UI components styled with Tailwind CSS.
- **State Management**: Efficient local and server state management.

## 🏁 Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- Google Gemini API Key ([Get it here](https://aistudio.google.com/app/apikey))

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv

# Activate environment
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
The backend API will be available at: `http://localhost:8000`  
API Documentation (Swagger UI): `http://localhost:8000/docs`

### 2. Frontend Setup

```bash
cd frontend

# Install Dependencies
npm install

# Run Development Server
npm run dev
```
The application will be running at: `http://localhost:3000`

## 🔮 Feature Roadmap

We are actively working on expanding the system's capabilities.

- **Phase 1 (Current)**: Foundation, Core AI Parsing, Basic CRUD.
- **Phase 2 (Upcoming)**: Context-Aware Chat, Smart Scheduling, Drag-and-Drop Calendar.
- **Phase 3**: Google Calendar Integration, Email-to-Task Webhooks, Semantic Search.
- **Phase 4**: Multi-user support, Team Collaboration, Mobile App.

👉 **[View Full Roadmap](docs/FEATURE_ROADMAP.md)**

## 📦 Deployment

The system is cloud-ready:
- **Frontend**: Optimized for **Vercel**.
- **Backend**: Dockerized for platforms like **Render** or **Railway**.
- **Database**: Compatible with **Neon** (Serverless PostgreSQL).

👉 **[Read Deployment Guide](docs/DEPLOYMENT.md)**

## 🧪 Testing

Run the comprehensive test suite to ensure system stability.

```bash
cd backend
python -m pytest
```

## 📂 Project Structure

```
AI_Powered_Task_Management_System/
├── backend/
│   ├── app/
│   │   ├── agents/        # ReAct Agents & Tools
│   │   ├── api/           # API Routes
│   │   ├── core/          # Config & Security
│   │   ├── models/        # SQLModel Database Schemas
│   │   ├── services/      # Business Logic
│   │   └── main.py        # App Entry Point
│   └── tests/             # Pytest Suite
├── frontend/
│   ├── app/               # Next.js Pages
│   ├── components/        # UI Components
│   └── lib/               # API Clients
└── docs/                  # Detailed Documentation
```

## 🤝 Contact & Contribution

Feedback and contributions are welcome! Please check the issues page or contact the developer.

---
*Built for University Project Submission*

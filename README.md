# AI-Driven Individualized Learning Journey Generator

An academic full-stack web application designed to create personalized, adaptive learning pathways for students based on goal setting, skill gap analysis, AI-generated structured topics, and deterministic progress tracking.

---

## Tech Stack

- **Frontend:** React.js, Vite, Vanilla/Modular CSS
- **Backend:** Python, FastAPI, Pydantic, SQLAlchemy 2.0
- **Database Driver:** `psycopg` (v3 binary)
- **Database:** PostgreSQL
- **AI Service:** Google GenAI SDK (Gemini API server-side integration)
- **Security:** JWT (JSON Web Tokens), bcrypt password hashing

---

## Project Structure

```text
ai-learning/
├── backend/
│   ├── app/
│   │   ├── auth/           # Authentication & security utilities
│   │   ├── models/         # SQLAlchemy database models
│   │   ├── routers/        # FastAPI API route controllers
│   │   ├── schemas/        # Pydantic request/response schemas
│   │   ├── services/       # AI & business logic services
│   │   ├── utils/          # Helper utilities
│   │   ├── config.py       # Pydantic Settings
│   │   ├── database.py     # SQLAlchemy + psycopg connection setup
│   │   └── main.py         # Application entry point & /health endpoint
│   ├── .env.example        # Environment variable template
│   └── requirements.txt    # Python dependencies
├── frontend/               # React + Vite client application
├── docs/                   # Academic documentation & viva prep notes
├── .gitignore
└── README.md
```

---

## Getting Started (Backend)

### 1. Create and Activate Virtual Environment
```bash
python -m venv .venv
# On Windows PowerShell:
.\.venv\Scripts\Activate.ps1
```

### 2. Install Dependencies
```bash
pip install -r backend/requirements.txt
```

### 3. Setup Environment Variables
```bash
cp backend/.env.example backend/.env
```

### 4. Run the Backend Server
```bash
uvicorn app.main:app --app-dir backend --reload --port 8000
```
- Interactive API Docs: `http://127.0.0.1:8000/docs`
- Health Check: `http://127.0.0.1:8000/health`

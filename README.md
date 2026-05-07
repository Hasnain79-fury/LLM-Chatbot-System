# LLM Chatbot System

FastAPI backend with JWT auth, SQLite, and Ollama (Mistral) integration, plus a vanilla JS chat frontend.

## Project structure

```
├── backend/              ← FastAPI API server
│   ├── main.py           ← App entry point, CORS, router registration
│   ├── requirements.txt
│   ├── dev.db            ← SQLite database (auto-created)
│   └── app/
│       ├── config.py         ← Settings loaded from .env
│       ├── database.py       ← SQLAlchemy engine + get_db dependency
│       ├── models.py         ← User, Conversation, Message ORM models
│       ├── schemas.py        ← Pydantic request/response schemas
│       ├── security.py       ← bcrypt hashing + JWT encode/decode
│       ├── dependencies.py   ← get_current_user (used by protected routes)
│       ├── llm.py            ← Ollama integration (streaming + non-streaming)
│       └── routers/
│           ├── auth.py           ← POST /auth/signup, /auth/login, GET /auth/me
│           ├── conversations.py  ← GET /conversations, GET/DELETE /conversations/{id}
│           └── chat.py           ← POST /chat, POST /chat/stream
│
├── frontend/             ← Vanilla HTML/CSS/JS chat UI
│   ├── index.html
│   ├── css/styles.css
│   └── js/
│       ├── app.js        ← Entry point + routing
│       ├── api.js        ← API client + streaming
│       ├── auth.js       ← Login/signup pages
│       ├── chat.js       ← Chat UI + sidebar
│       └── router.js     ← Hash-based SPA router
│
└── .venv/                ← Python virtual environment (shared)
```

## Quick start

```bash
# 1. Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate        # Linux/macOS: source .venv/bin/activate

# 2. Install backend dependencies
pip install -r backend/requirements.txt

# 3. Start the backend
cd backend
uvicorn main:app --reload
# API docs: http://localhost:8000/docs

# 4. Start the frontend (in a new terminal)
cd frontend
npm run dev
# Open: http://localhost:5173
```

## Prerequisites

- **Ollama** must be running for AI responses:
  ```bash
  ollama serve
  ollama pull mistral
  ```

## API endpoints

| Endpoint | Method | Auth | Purpose |
|---|---|---|---|
| `/auth/signup` | POST | ❌ | Create account |
| `/auth/login` | POST | ❌ | Get JWT token |
| `/auth/me` | GET | ✅ | Current user info |
| `/chat` | POST | ✅ | Send message (full response) |
| `/chat/stream` | POST | ✅ | Send message (streaming) |
| `/conversations` | GET | ✅ | List conversations |
| `/conversations/{id}/messages` | GET | ✅ | Get messages |
| `/conversations/{id}` | DELETE | ✅ | Delete conversation |
| `/health` | GET | ❌ | Server health check |
| `/health/llm` | GET | ❌ | Ollama health check |

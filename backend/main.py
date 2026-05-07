import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.llm import check_ollama_health
from app.routers import auth, chat, conversations

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

# Create all tables on startup (fine for dev; use Alembic in production)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="LLM Chatbot API",
    description="Backend for the LLM chatbot system",
    version="0.2.0",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(conversations.router)
app.include_router(chat.router)


# ── Startup ───────────────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup_event():
    healthy, message = check_ollama_health()
    if healthy:
        logger.info("✅ %s", message)
    else:
        logger.warning("⚠️  %s", message)


# ── Health endpoints ──────────────────────────────────────────────────────────

@app.get("/health", tags=["health"])
def health():
    """Basic server health check."""
    return {"status": "ok", "version": "0.2.0"}


@app.get("/health/llm", tags=["health"])
def health_llm():
    """Check whether Ollama is reachable and the model is loaded."""
    healthy, message = check_ollama_health()
    return {"healthy": healthy, "message": message}


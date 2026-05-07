from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.llm import LLMResponseError, LLMUnavailableError, ask_llm, ask_llm_stream
from app.models import Conversation, Message, User
from app.schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/chat", tags=["chat"])

# Max messages to send as context (keeps prompt size bounded)
MAX_HISTORY = 20


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_or_create_conversation(
    db: Session, user: User, conversation_id: int | None, first_message: str
) -> Conversation:
    if conversation_id:
        conv = db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.user_id == user.id,
        ).first()
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return conv

    title = first_message[:60] + ("…" if len(first_message) > 60 else "")
    conv = Conversation(user_id=user.id, title=title)
    db.add(conv)
    db.flush()
    return conv


def _load_history(db: Session, conversation_id: int) -> list[dict]:
    """
    Load the last MAX_HISTORY messages for the conversation and convert
    to the {"role": ..., "content": ...} format ask_llm() expects.
    """
    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.timestamp.asc())
        .limit(MAX_HISTORY)
        .all()
    )
    return [{"role": m.role, "content": m.content} for m in messages]


# ── POST /chat  (non-streaming, saves both messages) ─────────────────────────

@router.post("", response_model=ChatResponse)
def chat(
    body: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Send a message, get an AI reply, persist both to the DB.

    - If conversation_id is omitted a new conversation is created automatically.
    - The full conversation history is sent to Mistral each call for context.
    - Returns a 503 with a clear message if Ollama is not running.
    """
    conv = _get_or_create_conversation(db, current_user, body.conversation_id, body.message)

    # Persist the user message first so it's included in history sent to LLM
    user_msg = Message(conversation_id=conv.id, role="user", content=body.message)
    db.add(user_msg)
    db.flush()

    # Build history (includes the message we just flushed)
    history = _load_history(db, conv.id)

    # Call the LLM
    try:
        ai_text = ask_llm(history)
    except LLMUnavailableError as e:
        # Roll back so the user message isn't orphaned with no AI reply
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
    except LLMResponseError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e),
        )

    # Persist the AI reply
    ai_msg = Message(conversation_id=conv.id, role="assistant", content=ai_text)
    db.add(ai_msg)
    db.commit()
    db.refresh(user_msg)
    db.refresh(ai_msg)

    return ChatResponse(
        conversation_id=conv.id,
        user_message=user_msg,
        ai_message=ai_msg,
    )


# ── POST /chat/stream  (streaming, typewriter effect) ────────────────────────

@router.post("/stream")
def chat_stream(
    body: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Streaming variant — tokens arrive one by one (typewriter effect).

    The user message is saved immediately. The AI reply is accumulated
    from the stream and saved to the DB once the stream is done.

    Frontend usage with fetch:
        const res = await fetch("/chat/stream", { method: "POST", ... });
        const reader = res.body.getReader();
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            appendToken(new TextDecoder().decode(value));
        }
    """
    conv = _get_or_create_conversation(db, current_user, body.conversation_id, body.message)

    user_msg = Message(conversation_id=conv.id, role="user", content=body.message)
    db.add(user_msg)
    db.commit()                         # commit so history query sees it

    history = _load_history(db, conv.id)
    accumulated: list[str] = []

    def token_generator():
        for token in ask_llm_stream(history):
            accumulated.append(token)
            yield token

        # After stream ends, persist full AI reply
        full_reply = "".join(accumulated).strip()
        if full_reply:
            ai_msg = Message(
                conversation_id=conv.id,
                role="assistant",
                content=full_reply,
            )
            db.add(ai_msg)
            db.commit()

    return StreamingResponse(token_generator(), media_type="text/plain")

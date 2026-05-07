from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Conversation, Message, User
from app.schemas import ConversationOut, MessageOut

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("", response_model=list[ConversationOut])
def list_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return all conversations for the logged-in user, newest first."""
    return (
        db.query(Conversation)
        .filter(Conversation.user_id == current_user.id)
        .order_by(Conversation.created_at.desc())
        .all()
    )


@router.get("/{conversation_id}/messages", response_model=list[MessageOut])
def get_messages(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return all messages in a conversation (must belong to current user)."""
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id,
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.timestamp.asc())
        .all()
    )


@router.delete("/{conversation_id}", status_code=204)
def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a conversation and all its messages."""
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id,
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    db.delete(conversation)
    db.commit()

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class SignupRequest(BaseModel):
    email: EmailStr
    username: str
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    username: str
    created_at: datetime


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    conversation_id: int
    role: str
    content: str
    timestamp: datetime


class ConversationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    title: str
    created_at: datetime


class ChatRequest(BaseModel):
    message: str
    conversation_id: int | None = None


class ChatResponse(BaseModel):
    conversation_id: int
    user_message: MessageOut
    ai_message: MessageOut

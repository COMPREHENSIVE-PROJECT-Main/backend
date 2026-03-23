from enum import Enum

from pydantic import BaseModel


class MessageRole(str, Enum):
    system = "system"
    user = "user"
    assistant = "assistant"


class ChatMessage(BaseModel):
    role: MessageRole
    content: str


class LLMRequest(BaseModel):
    messages: list[ChatMessage]
    system_prompt: str


class LLMResponse(BaseModel):
    content: str
    model: str
    created_at: str | None = None

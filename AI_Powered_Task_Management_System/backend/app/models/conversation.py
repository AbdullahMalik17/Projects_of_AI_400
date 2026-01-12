"""
Conversation model for AI chat history storage.

Stores conversational messages between user and AI assistant
for context retention and conversation continuity.
"""

from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel, Column, JSON


class ConversationMessage(SQLModel, table=True):
    """
    Conversation message model for AI chat history.

    Stores individual messages in conversations between users and the AI assistant.
    Used for maintaining conversational context and enabling context-aware responses.

    Attributes:
        id: Primary key identifier
        user_id: Foreign key to user
        role: Message sender role ('user' or 'assistant')
        content: Message text content
        message_metadata: Additional message metadata (token count, model used, etc.)
        created_at: Message timestamp
    """

    __tablename__ = "conversation_messages"

    # Primary Key
    id: Optional[int] = Field(default=None, primary_key=True)

    # Foreign Key
    user_id: int = Field(foreign_key="users.id", index=True)

    # Message Fields
    role: str = Field(max_length=20)  # 'user' or 'assistant'
    content: str = Field(max_length=5000)

    # Metadata
    message_metadata: dict = Field(default_factory=dict, sa_column=Column(JSON))
    # Example message_metadata:
    # {
    #   "token_count": 150,
    #   "model_used": "gemini-1.5-flash",
    #   "intent": "task_creation",
    #   "extracted_entities": {...}
    # }

    # Timestamp
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)

    class Config:
        """Pydantic model configuration."""
        json_schema_extra = {
            "example": {
                "user_id": 1,
                "role": "user",
                "content": "Remind me to call John tomorrow at 2pm",
                "message_metadata": {
                    "intent": "task_creation",
                    "extracted_entities": {
                        "action": "call John",
                        "due_date": "2024-01-12T14:00:00"
                    }
                }
            }
        }

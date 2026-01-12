"""
Conversation Repository for database operations.
"""

from typing import List, Sequence
from sqlmodel import Session, select
from app.models.conversation import ConversationMessage

class ConversationRepository:
    def __init__(self, session: Session):
        self.session = session

    def add_message(self, user_id: int, role: str, content: str) -> ConversationMessage:
        message = ConversationMessage(
            user_id=user_id,
            role=role,
            content=content
        )
        self.session.add(message)
        self.session.commit()
        self.session.refresh(message)
        return message

    def get_recent_messages(self, user_id: int, limit: int = 10) -> Sequence[ConversationMessage]:
        statement = (
            select(ConversationMessage)
            .where(ConversationMessage.user_id == user_id)
            .order_by(ConversationMessage.created_at.desc())
            .limit(limit)
        )
        # Reverse to get chronological order for LLM context
        messages = self.session.exec(statement).all()
        return list(reversed(messages))

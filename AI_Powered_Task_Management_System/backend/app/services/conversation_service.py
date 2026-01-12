"""
Conversation Service for managing chat history.
"""

from typing import List, Sequence
from sqlmodel import Session
from app.repositories.conversation_repository import ConversationRepository
from app.models.conversation import ConversationMessage

class ConversationService:
    def __init__(self, session: Session):
        self.repository = ConversationRepository(session)

    def save_message(self, user_id: int, role: str, content: str) -> ConversationMessage:
        return self.repository.add_message(user_id, role, content)

    def get_history(self, user_id: int, limit: int = 10) -> Sequence[ConversationMessage]:
        return self.repository.get_recent_messages(user_id, limit)

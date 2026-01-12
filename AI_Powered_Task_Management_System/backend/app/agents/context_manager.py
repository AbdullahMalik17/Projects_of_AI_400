"""
Context Manager for managing user context and conversation history.

Maintains short-term and long-term memory for AI agents,
enabling context-aware task assistance and personalized recommendations.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from collections import deque

from app.models.conversation import ConversationMessage
from sqlmodel import Session, select


class ContextManager:
    """
    Manages user context and conversation history for AI agents.

    Maintains both short-term (current session) and long-term
    (persistent database) memory for context-aware interactions.
    """

    def __init__(self, session: Session, user_id: int):
        """
        Initialize context manager for a specific user.

        Args:
            session: Database session
            user_id: ID of the user
        """
        self.session = session
        self.user_id = user_id

        # Short-term memory (current session)
        self.conversation_buffer: deque = deque(maxlen=10)  # Last 10 messages
        self.working_memory: Dict[str, Any] = {}

        # Load recent conversation history
        self._load_recent_history()

    def _load_recent_history(self) -> None:
        """Load recent conversation history from database."""
        statement = (
            select(ConversationMessage)
            .where(ConversationMessage.user_id == self.user_id)
            .order_by(ConversationMessage.created_at.desc())
            .limit(10)
        )

        messages = self.session.exec(statement).all()

        # Add to buffer in chronological order
        for message in reversed(messages):
            self.conversation_buffer.append({
                "role": message.role,
                "content": message.content,
                "timestamp": message.created_at,
                "metadata": message.metadata
            })

    def add_message(
        self,
        role: str,
        content: str,
        metadata: Optional[Dict] = None,
        persist: bool = True
    ) -> None:
        """
        Add a message to conversation history.

        Args:
            role: Message role ('user' or 'assistant')
            content: Message content
            metadata: Optional metadata
            persist: Whether to save to database
        """
        message_data = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow(),
            "metadata": metadata or {}
        }

        # Add to short-term memory
        self.conversation_buffer.append(message_data)

        # Persist to database if requested
        if persist:
            conversation_message = ConversationMessage(
                user_id=self.user_id,
                role=role,
                content=content,
                metadata=metadata or {}
            )
            self.session.add(conversation_message)
            self.session.commit()

    def get_conversation_history(
        self,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get conversation history from short-term memory.

        Args:
            limit: Maximum number of messages to return

        Returns:
            List of message dictionaries
        """
        messages = list(self.conversation_buffer)

        if limit:
            messages = messages[-limit:]

        return messages

    def get_conversation_context(self) -> str:
        """
        Get formatted conversation context for AI prompt.

        Returns:
            Formatted conversation history as string
        """
        if not self.conversation_buffer:
            return "No previous conversation."

        context_lines = ["Recent Conversation:"]

        for msg in self.conversation_buffer:
            role = msg["role"].capitalize()
            content = msg["content"][:200]  # Limit length
            context_lines.append(f"{role}: {content}")

        return "\n".join(context_lines)

    def update_working_memory(
        self,
        key: str,
        value: Any
    ) -> None:
        """
        Update working memory with a key-value pair.

        Used for maintaining context within a multi-turn interaction.

        Args:
            key: Memory key
            value: Value to store
        """
        self.working_memory[key] = value

    def get_from_working_memory(
        self,
        key: str,
        default: Any = None
    ) -> Any:
        """
        Retrieve value from working memory.

        Args:
            key: Memory key
            default: Default value if key not found

        Returns:
            Stored value or default
        """
        return self.working_memory.get(key, default)

    def clear_working_memory(self) -> None:
        """Clear working memory (for new conversation context)."""
        self.working_memory.clear()

    def get_user_context(self) -> Dict[str, Any]:
        """
        Get comprehensive user context for AI agents.

        Returns:
            Dictionary with user context including preferences and patterns

        Example:
            context = manager.get_user_context()
            # Returns: {
            #   "conversation_history": [...],
            #   "working_memory": {...},
            #   "preferences": {...}
            # }
        """
        return {
            "conversation_history": self.get_conversation_history(),
            "working_memory": self.working_memory,
            "recent_context": self.get_conversation_context(),
        }

    def summarize_conversation(self) -> str:
        """
        Generate a summary of the conversation.

        Useful for maintaining context when conversation buffer is full.

        Returns:
            Summary of conversation
        """
        if not self.conversation_buffer:
            return "No conversation to summarize."

        # Simple summarization - count user vs assistant messages
        user_count = sum(1 for msg in self.conversation_buffer if msg["role"] == "user")
        assistant_count = len(self.conversation_buffer) - user_count

        # Get first and last user message
        user_messages = [msg for msg in self.conversation_buffer if msg["role"] == "user"]

        if user_messages:
            first_topic = user_messages[0]["content"][:100]
            last_topic = user_messages[-1]["content"][:100] if len(user_messages) > 1 else first_topic

            return (
                f"Conversation with {user_count} user messages and {assistant_count} responses. "
                f"Started with: '{first_topic}...' "
                f"Most recent: '{last_topic}...'"
            )

        return f"Conversation with {len(self.conversation_buffer)} messages."

    def get_task_context(
        self,
        recent_tasks: List[Any]
    ) -> Dict[str, Any]:
        """
        Build context from recent tasks for AI agents.

        Args:
            recent_tasks: List of recent task objects

        Returns:
            Dictionary with task-based context
        """
        if not recent_tasks:
            return {
                "recent_task_count": 0,
                "common_priorities": [],
                "common_categories": []
            }

        # Analyze recent tasks
        priorities = [task.priority.value for task in recent_tasks]
        common_priority = max(set(priorities), key=priorities.count) if priorities else "medium"

        # Extract categories from metadata or tags
        categories = []
        for task in recent_tasks:
            if hasattr(task, 'tags') and task.tags:
                categories.extend([tag.name for tag in task.tags])

        common_categories = list(set(categories))[:5]  # Top 5 categories

        return {
            "recent_task_count": len(recent_tasks),
            "common_priority": common_priority,
            "common_categories": common_categories,
            "recent_task_titles": [task.title for task in recent_tasks[:5]]
        }


def get_context_manager(session: Session, user_id: int) -> ContextManager:
    """
    Factory function to create ContextManager instance.

    Args:
        session: Database session
        user_id: User ID

    Returns:
        ContextManager instance
    """
    return ContextManager(session, user_id)

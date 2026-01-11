"""
User context model for storing AI-related user preferences and patterns.

Maintains user-specific context, preferences, and productivity patterns
for personalized AI assistance.
"""

from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel, Column, JSON


class UserContext(SQLModel, table=True):
    """
    User context and preferences for AI personalization.

    Stores user-specific settings, learned preferences, and productivity patterns
    that the AI uses to provide personalized task management assistance.

    Attributes:
        id: Primary key identifier
        user_id: Foreign key to user (one-to-one relationship)
        preferences: User preferences and settings
        productivity_patterns: Learned productivity patterns
        ai_context: AI-specific context and memory
        created_at: Context creation timestamp
        updated_at: Last context update timestamp
    """

    __tablename__ = "user_contexts"

    # Primary Key
    id: Optional[int] = Field(default=None, primary_key=True)

    # Foreign Key (one-to-one with User)
    user_id: int = Field(foreign_key="users.id", unique=True, index=True)

    # Context Fields (JSON storage for flexibility)
    preferences: dict = Field(default_factory=dict, sa_column=Column(JSON))
    # Example preferences:
    # {
    #   "work_hours": {"start": "09:00", "end": "17:00"},
    #   "default_priority": "medium",
    #   "auto_categorize": true,
    #   "reminder_preferences": {...}
    # }

    productivity_patterns: dict = Field(default_factory=dict, sa_column=Column(JSON))
    # Example patterns:
    # {
    #   "peak_hours": ["09:00-12:00"],
    #   "average_task_duration": 45,
    #   "completion_rate": 0.85,
    #   "common_task_categories": ["work", "personal"],
    #   "task_completion_by_hour": {...}
    # }

    ai_context: dict = Field(default_factory=dict, sa_column=Column(JSON))
    # Example AI context:
    # {
    #   "conversation_summary": "User prefers morning tasks",
    #   "learned_preferences": {...},
    #   "interaction_count": 150,
    #   "last_topics": [...]
    # }

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def update_timestamp(self) -> None:
        """Update the updated_at timestamp to current time."""
        self.updated_at = datetime.utcnow()

    class Config:
        """Pydantic model configuration."""
        json_schema_extra = {
            "example": {
                "user_id": 1,
                "preferences": {
                    "work_hours": {"start": "09:00", "end": "17:00"},
                    "default_priority": "medium",
                    "auto_categorize": True
                },
                "productivity_patterns": {
                    "peak_hours": ["09:00-12:00"],
                    "completion_rate": 0.85
                }
            }
        }

"""
Task model representing user tasks.

Defines the core Task entity with all properties, relationships,
and business logic for task management.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, TYPE_CHECKING
from sqlmodel import Field, SQLModel, Relationship, Column, JSON
from app.models.links import TaskTagLink

if TYPE_CHECKING:
    from app.models.tag import Tag
    from app.models.user import User


class TaskStatus(str, Enum):
    """Enumeration of possible task statuses."""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    ARCHIVED = "archived"


class Priority(str, Enum):
    """Enumeration of task priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Task(SQLModel, table=True):
    """
    Task model representing a user's task or to-do item.

    Supports hierarchical tasks (parent-child relationships) and
    AI-assisted properties like priority suggestions and subtask decomposition.

    Attributes:
        id: Primary key identifier
        title: Task title (required)
        description: Detailed task description
        status: Current task status
        priority: Task priority level
        due_date: Optional deadline for task completion
        estimated_duration: Estimated time to complete (in minutes)
        actual_duration: Actual time spent on task (in minutes)
        created_at: Timestamp of task creation
        updated_at: Timestamp of last update
        completed_at: Timestamp when task was marked complete
        user_id: Foreign key to owning user
        parent_task_id: Foreign key to parent task (for subtasks)
        task_metadata: JSON field for flexible AI-generated data
    """

    __tablename__ = "tasks"

    # Primary Key
    id: Optional[int] = Field(default=None, primary_key=True)

    # Core Task Fields
    title: str = Field(index=True, max_length=255)
    description: Optional[str] = Field(default=None, max_length=2000)
    status: TaskStatus = Field(default=TaskStatus.TODO, index=True)
    priority: Priority = Field(default=Priority.MEDIUM, index=True)

    # Time-related Fields
    due_date: Optional[datetime] = Field(default=None, index=True)
    estimated_duration: Optional[int] = Field(default=None, ge=0)  # minutes
    actual_duration: Optional[int] = Field(default=None, ge=0)  # minutes

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    # Foreign Keys
    user_id: int = Field(foreign_key="users.id", index=True)
    parent_task_id: Optional[int] = Field(default=None, foreign_key="tasks.id", index=True)

    # AI-Generated Metadata (flexible JSON storage)
    # Note: renamed from 'metadata' to 'task_metadata' because 'metadata' is reserved in SQLAlchemy
    task_metadata: dict = Field(default_factory=dict, sa_column=Column(JSON))
    # Example task_metadata:
    # {
    #   "ai_suggested_priority": "high",
    #   "ai_breakdown_suggestions": [...],
    #   "recurring_pattern": {...},
    #   "context": {...}
    # }

    # Relationships
    user: Optional["User"] = Relationship(back_populates="tasks")
    subtasks: List["Task"] = Relationship(
        back_populates="parent_task",
        sa_relationship_kwargs={"foreign_keys": "Task.parent_task_id"}
    )
    parent_task: Optional["Task"] = Relationship(
        back_populates="subtasks",
        sa_relationship_kwargs={
            "remote_side": "Task.id",
            "foreign_keys": "Task.parent_task_id"
        }
    )

    # Many-to-Many with Tags
    tags: List["Tag"] = Relationship(
        back_populates="tasks",
        link_model=TaskTagLink
    )

    def mark_complete(self) -> None:
        """Mark task as completed and set completion timestamp."""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def is_overdue(self) -> bool:
        """
        Check if task is overdue.

        Returns:
            True if task has a due date in the past and is not completed
        """
        if not self.due_date:
            return False
        return (
            self.status != TaskStatus.COMPLETED
            and self.due_date < datetime.utcnow()
        )

    def update_timestamp(self) -> None:
        """Update the updated_at timestamp to current time."""
        self.updated_at = datetime.utcnow()

    class Config:
        """Pydantic model configuration."""
        json_schema_extra = {
            "example": {
                "title": "Prepare quarterly budget analysis",
                "description": "Compile Q4 budget data and create presentation",
                "status": "todo",
                "priority": "high",
                "due_date": "2024-01-19T17:00:00",
                "estimated_duration": 180,
                "user_id": 1
            }
        }

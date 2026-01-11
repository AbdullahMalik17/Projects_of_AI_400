"""
Pydantic schemas for Task API requests and responses.

Defines data transfer objects (DTOs) for task-related API operations,
separate from database models for clean API contracts.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from app.models.task import TaskStatus, Priority


class TaskBase(BaseModel):
    """Base task schema with common fields."""
    title: str = Field(..., min_length=1, max_length=255, description="Task title")
    description: Optional[str] = Field(None, max_length=2000, description="Detailed description")
    status: TaskStatus = Field(default=TaskStatus.TODO, description="Current status")
    priority: Priority = Field(default=Priority.MEDIUM, description="Priority level")
    due_date: Optional[datetime] = Field(None, description="Due date and time")
    estimated_duration: Optional[int] = Field(None, ge=0, description="Estimated duration in minutes")
    parent_task_id: Optional[int] = Field(None, description="Parent task ID for subtasks")


class TaskCreate(TaskBase):
    """Schema for creating a new task."""
    tag_ids: Optional[List[int]] = Field(default=[], description="List of tag IDs to attach")

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Prepare quarterly budget analysis",
                "description": "Compile Q4 budget data and create presentation",
                "status": "todo",
                "priority": "high",
                "due_date": "2024-01-19T17:00:00",
                "estimated_duration": 180,
                "tag_ids": [1, 2]
            }
        }


class TaskUpdate(BaseModel):
    """Schema for updating an existing task. All fields optional."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    status: Optional[TaskStatus] = None
    priority: Optional[Priority] = None
    due_date: Optional[datetime] = None
    estimated_duration: Optional[int] = Field(None, ge=0)
    actual_duration: Optional[int] = Field(None, ge=0)
    parent_task_id: Optional[int] = None
    tag_ids: Optional[List[int]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "status": "in_progress",
                "actual_duration": 45
            }
        }


class TaskResponse(TaskBase):
    """Schema for task responses including generated fields."""
    id: int
    user_id: int
    actual_duration: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    metadata: dict = Field(default_factory=dict)
    tags: List["TagResponse"] = Field(default=[])
    subtasks: List["TaskResponse"] = Field(default=[])

    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    """Schema for paginated task list responses."""
    tasks: List[TaskResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class NaturalLanguageTaskCreate(BaseModel):
    """Schema for creating tasks from natural language input."""
    message: str = Field(..., min_length=1, max_length=1000, description="Natural language task description")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Remind me to call John tomorrow at 2pm about the project proposal"
            }
        }


class TaskSuggestionResponse(BaseModel):
    """Schema for AI-generated task suggestions."""
    suggested_priority: Optional[Priority] = None
    suggested_breakdown: Optional[List[str]] = None
    suggested_duration: Optional[int] = None
    reasoning: str = Field(..., description="AI explanation for suggestions")

    class Config:
        json_schema_extra = {
            "example": {
                "suggested_priority": "high",
                "suggested_breakdown": [
                    "Research project background",
                    "Create proposal outline",
                    "Draft proposal content",
                    "Review and finalize"
                ],
                "suggested_duration": 240,
                "reasoning": "Based on your past project proposals, this typically takes 4 hours and is high priority."
            }
        }


# Importing TagResponse to avoid circular import
from app.schemas.tag import TagResponse  # noqa: E402
TaskResponse.model_rebuild()

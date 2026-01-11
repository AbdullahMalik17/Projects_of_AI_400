"""
Pydantic schemas for Tag API requests and responses.
"""

from typing import Optional
from pydantic import BaseModel, Field


class TagBase(BaseModel):
    """Base tag schema with common fields."""
    name: str = Field(..., min_length=1, max_length=50)
    color: Optional[str] = Field(None, max_length=7, pattern="^#[0-9A-Fa-f]{6}$")
    description: Optional[str] = Field(None, max_length=255)


class TagCreate(TagBase):
    """Schema for creating a new tag."""
    class Config:
        json_schema_extra = {
            "example": {
                "name": "work",
                "color": "#3B82F6",
                "description": "Work-related tasks"
            }
        }


class TagUpdate(BaseModel):
    """Schema for updating an existing tag."""
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    color: Optional[str] = Field(None, max_length=7, pattern="^#[0-9A-Fa-f]{6}$")
    description: Optional[str] = Field(None, max_length=255)


class TagResponse(TagBase):
    """Schema for tag responses."""
    id: int
    user_id: int

    class Config:
        from_attributes = True

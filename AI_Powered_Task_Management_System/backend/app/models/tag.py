"""
Tag models for task categorization and organization.

Defines Tag entity and TaskTagLink association table for many-to-many relationships.
"""

from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship


class TaskTagLink(SQLModel, table=True):
    """
    Association table linking tasks and tags (many-to-many).

    This model represents the junction table for the many-to-many
    relationship between tasks and tags.
    """

    __tablename__ = "task_tag_links"

    task_id: int = Field(foreign_key="tasks.id", primary_key=True)
    tag_id: int = Field(foreign_key="tags.id", primary_key=True)


class Tag(SQLModel, table=True):
    """
    Tag model for categorizing and organizing tasks.

    Tags provide flexible categorization beyond fixed categories,
    allowing users to create custom organizational schemes.

    Attributes:
        id: Primary key identifier
        name: Tag name (unique per user)
        color: Optional color hex code for UI display
        user_id: Foreign key to owning user
    """

    __tablename__ = "tags"

    # Primary Key
    id: Optional[int] = Field(default=None, primary_key=True)

    # Tag Fields
    name: str = Field(index=True, max_length=50)
    color: Optional[str] = Field(default=None, max_length=7)  # Hex color code
    description: Optional[str] = Field(default=None, max_length=255)

    # Foreign Keys
    user_id: int = Field(foreign_key="users.id", index=True)

    # Relationships
    tasks: List["Task"] = Relationship(
        back_populates="tags",
        link_model=TaskTagLink
    )

    class Config:
        """Pydantic model configuration."""
        json_schema_extra = {
            "example": {
                "name": "work",
                "color": "#3B82F6",
                "description": "Work-related tasks",
                "user_id": 1
            }
        }

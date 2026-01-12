"""
Association models for many-to-many relationships.
"""

from sqlmodel import Field, SQLModel


class TaskTagLink(SQLModel, table=True):
    """
    Association table linking tasks and tags (many-to-many).

    This model represents the junction table for the many-to-many
    relationship between tasks and tags.
    """

    __tablename__ = "task_tag_links"

    task_id: int = Field(foreign_key="tasks.id", primary_key=True)
    tag_id: int = Field(foreign_key="tags.id", primary_key=True)

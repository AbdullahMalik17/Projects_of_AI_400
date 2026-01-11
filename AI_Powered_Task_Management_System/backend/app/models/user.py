"""
User model for authentication and user management.

Defines the User entity with authentication credentials and profile information.
"""

from datetime import datetime
from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship


class User(SQLModel, table=True):
    """
    User model for authentication and authorization.

    In Phase 1 (single-user), only one default user exists.
    In Phase 2 (multi-user), this model supports multiple users with authentication.

    Attributes:
        id: Primary key identifier
        email: User's email address (unique)
        hashed_password: Bcrypt hashed password
        full_name: User's full name
        is_active: Whether user account is active
        is_superuser: Admin privileges flag
        created_at: Account creation timestamp
        updated_at: Last profile update timestamp
    """

    __tablename__ = "users"

    # Primary Key
    id: Optional[int] = Field(default=None, primary_key=True)

    # Authentication Fields
    email: str = Field(unique=True, index=True, max_length=255)
    hashed_password: str = Field(max_length=255)

    # Profile Fields
    full_name: Optional[str] = Field(default=None, max_length=255)
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    tasks: List["Task"] = Relationship(back_populates="user")

    class Config:
        """Pydantic model configuration."""
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "full_name": "John Doe",
                "is_active": True
            }
        }

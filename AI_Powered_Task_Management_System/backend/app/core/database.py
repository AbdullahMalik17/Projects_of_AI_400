"""
Database connection and session management.

This module configures SQLModel/SQLAlchemy engine and provides
session management for dependency injection.
"""

from typing import Generator
from sqlmodel import Session, create_engine, SQLModel
from app.core.config import settings


# Create database engine
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # Log SQL queries in debug mode
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)


def init_db() -> None:
    """
    Initialize database by creating all tables.

    This function creates all tables defined by SQLModel models.
    Should be called on application startup.
    """
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """
    Dependency function for FastAPI to provide database sessions.

    Yields:
        Session: SQLModel database session

    Example:
        ```python
        @app.get("/tasks")
        def get_tasks(session: Session = Depends(get_session)):
            tasks = session.exec(select(Task)).all()
            return tasks
        ```
    """
    with Session(engine) as session:
        yield session

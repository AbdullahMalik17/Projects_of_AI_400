"""
Repository layer for data access operations.

Provides repository pattern implementations for database entities,
abstracting data access logic from business logic.
"""

from app.repositories.task_repository import TaskRepository, get_task_repository

__all__ = [
    "TaskRepository",
    "get_task_repository",
]

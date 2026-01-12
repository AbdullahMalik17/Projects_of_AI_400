"""
Service layer for business logic operations.

Provides service pattern implementations that encapsulate
business rules, validation, and orchestration logic.
"""

from app.services.task_service import TaskService, get_task_service

__all__ = [
    "TaskService",
    "get_task_service",
]

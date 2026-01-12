"""
Task Service for business logic operations.

Implements core business logic for task management including
creation, updates, scheduling, prioritization, and task intelligence.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlmodel import Session
from fastapi import HTTPException, status, Depends

from app.core.database import get_session
from app.models.task import Task, TaskStatus, Priority
from app.schemas.task import TaskCreate, TaskUpdate
from app.repositories.task_repository import TaskRepository


class TaskService:
    """
    Service layer for task management business logic.

    Encapsulates business rules, validation, and orchestration
    of task-related operations.
    """

    def __init__(self, session: Session):
        """
        Initialize service with database session.

        Args:
            session: SQLModel database session
        """
        self.session = session
        self.repository = TaskRepository(session)

    def create_task(
        self,
        task_data: TaskCreate,
        user_id: int
    ) -> Task:
        """
        Create a new task with business logic validation.

        Args:
            task_data: Task creation data
            user_id: ID of user creating the task

        Returns:
            Created task

        Raises:
            HTTPException: If validation fails

        Example:
            task = service.create_task(
                TaskCreate(title="New Task", priority="high"),
                user_id=1
            )
        """
        # Validate parent task exists if provided
        if task_data.parent_task_id:
            parent = self.repository.get_by_id(task_data.parent_task_id)
            if not parent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Parent task {task_data.parent_task_id} not found"
                )
            if parent.user_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cannot create subtask for another user's task"
                )

        # Create task instance
        task_dict = task_data.model_dump(exclude_unset=True)
        task = Task(**task_dict, user_id=user_id)

        # Apply business rules
        self._apply_creation_rules(task)

        # Save to database
        return self.repository.create(task)

    def get_task(
        self,
        task_id: int,
        user_id: int,
        load_relationships: bool = True
    ) -> Task:
        """
        Retrieve task by ID with ownership validation.

        Args:
            task_id: Task ID to retrieve
            user_id: ID of requesting user
            load_relationships: Whether to load subtasks and tags

        Returns:
            Task instance

        Raises:
            HTTPException: If task not found or access denied
        """
        task = self.repository.get_by_id(task_id, load_relationships)

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found"
            )

        if task.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this task"
            )

        return task

    def list_tasks(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        status_filter: Optional[TaskStatus] = None,
        priority_filter: Optional[Priority] = None,
        include_subtasks: bool = True
    ) -> List[Task]:
        """
        List tasks with filtering and pagination.

        Args:
            user_id: User ID to filter tasks
            skip: Pagination offset
            limit: Maximum records (capped at 100)
            status_filter: Optional status filter
            priority_filter: Optional priority filter
            include_subtasks: Whether to include subtasks

        Returns:
            List of tasks
        """
        # Cap limit at 100 for performance
        limit = min(limit, 100)

        return self.repository.get_by_user(
            user_id=user_id,
            skip=skip,
            limit=limit,
            status_filter=status_filter,
            priority_filter=priority_filter,
            include_subtasks=include_subtasks
        )

    def update_task(
        self,
        task_id: int,
        task_data: TaskUpdate,
        user_id: int
    ) -> Task:
        """
        Update task with validation and business logic.

        Args:
            task_id: Task ID to update
            task_data: Updated task data
            user_id: ID of requesting user

        Returns:
            Updated task

        Raises:
            HTTPException: If task not found or validation fails
        """
        # Get existing task
        task = self.get_task(task_id, user_id, load_relationships=False)

        # Update only provided fields
        update_data = task_data.model_dump(exclude_unset=True)

        # Validate parent task if being updated
        if "parent_task_id" in update_data and update_data["parent_task_id"]:
            if update_data["parent_task_id"] == task_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Task cannot be its own parent"
                )

            parent = self.repository.get_by_id(update_data["parent_task_id"])
            if not parent or parent.user_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Parent task not found"
                )

        # Apply updates using SQLModel's update method
        for key, value in update_data.items():
            setattr(task, key, value)

        # Apply business rules for status changes
        if "status" in update_data:
            self._handle_status_change(task, update_data["status"])

        return self.repository.update(task)

    def delete_task(
        self,
        task_id: int,
        user_id: int,
        cascade_subtasks: bool = False
    ) -> None:
        """
        Delete task with optional cascade to subtasks.

        Args:
            task_id: Task ID to delete
            user_id: ID of requesting user
            cascade_subtasks: Whether to delete subtasks as well

        Raises:
            HTTPException: If task not found or has subtasks without cascade
        """
        task = self.get_task(task_id, user_id, load_relationships=True)

        # Check for subtasks
        if task.subtasks and not cascade_subtasks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Task has subtasks. Use cascade_subtasks=true to delete all"
            )

        # Delete subtasks if cascade enabled
        if cascade_subtasks and task.subtasks:
            for subtask in task.subtasks:
                self.repository.delete(subtask)

        self.repository.delete(task)

    def complete_task(
        self,
        task_id: int,
        user_id: int,
        actual_duration: Optional[int] = None
    ) -> Task:
        """
        Mark task as completed with timestamp and optional duration.

        Args:
            task_id: Task ID to complete
            user_id: ID of requesting user
            actual_duration: Actual time spent in minutes

        Returns:
            Completed task
        """
        task = self.get_task(task_id, user_id, load_relationships=False)

        task.mark_complete()

        if actual_duration:
            task.actual_duration = actual_duration

        # Store AI insights about task completion
        if task.estimated_duration and actual_duration:
            accuracy = self._calculate_estimation_accuracy(
                task.estimated_duration,
                actual_duration
            )
            task.task_metadata["estimation_accuracy"] = accuracy

        return self.repository.update(task)

    def search_tasks(
        self,
        user_id: int,
        query: str,
        skip: int = 0,
        limit: int = 50
    ) -> List[Task]:
        """
        Search tasks by text query.

        Args:
            user_id: User ID to scope search
            query: Search text
            skip: Pagination offset
            limit: Maximum records

        Returns:
            List of matching tasks
        """
        return self.repository.search_by_text(
            user_id=user_id,
            search_query=query,
            skip=skip,
            limit=limit
        )

    def get_overdue_tasks(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Task]:
        """
        Get all overdue tasks for a user.

        Args:
            user_id: User ID
            skip: Pagination offset
            limit: Maximum records

        Returns:
            List of overdue tasks
        """
        return self.repository.get_overdue_tasks(
            user_id=user_id,
            skip=skip,
            limit=limit
        )

    def get_upcoming_tasks(
        self,
        user_id: int,
        days: int = 7,
        skip: int = 0,
        limit: int = 100
    ) -> List[Task]:
        """
        Get tasks due within specified days.

        Args:
            user_id: User ID
            days: Number of days to look ahead
            skip: Pagination offset
            limit: Maximum records

        Returns:
            List of upcoming tasks
        """
        return self.repository.get_upcoming_tasks(
            user_id=user_id,
            days=days,
            skip=skip,
            limit=limit
        )

    def get_task_statistics(
        self,
        user_id: int
    ) -> Dict[str, Any]:
        """
        Get comprehensive task statistics for user.

        Args:
            user_id: User ID

        Returns:
            Dictionary with statistics including counts and insights
        """
        stats = self.repository.get_task_statistics(user_id)

        # Add additional calculated metrics
        if stats["total"] > 0:
            stats["completion_rate"] = round(
                (stats["completed"] / stats["total"]) * 100,
                2
            )
        else:
            stats["completion_rate"] = 0.0

        return stats

    def suggest_priority(
        self,
        task: Task,
        user_context: Optional[Dict] = None
    ) -> Priority:
        """
        Suggest task priority based on due date and context.

        Business logic for intelligent priority suggestion.

        Args:
            task: Task to analyze
            user_context: Optional user context and patterns

        Returns:
            Suggested priority level
        """
        # Default to medium if no due date
        if not task.due_date:
            return Priority.MEDIUM

        now = datetime.utcnow()
        time_until_due = task.due_date - now

        # High priority if due within 24 hours
        if time_until_due <= timedelta(hours=24):
            return Priority.HIGH

        # Medium priority if due within 3 days
        if time_until_due <= timedelta(days=3):
            return Priority.MEDIUM

        # Low priority for distant deadlines
        return Priority.LOW

    def create_subtasks(
        self,
        parent_task_id: int,
        user_id: int,
        subtask_titles: List[str]
    ) -> List[Task]:
        """
        Create multiple subtasks for a parent task.

        Args:
            parent_task_id: Parent task ID
            user_id: User ID
            subtask_titles: List of subtask titles

        Returns:
            List of created subtasks

        Raises:
            HTTPException: If parent task not found
        """
        # Validate parent task exists and user owns it
        parent_task = self.get_task(parent_task_id, user_id)

        subtasks = []
        for title in subtask_titles:
            subtask_data = TaskCreate(
                title=title,
                parent_task_id=parent_task_id,
                priority=parent_task.priority,  # Inherit parent priority
                due_date=parent_task.due_date   # Inherit parent due date
            )
            subtask = self.create_task(subtask_data, user_id)
            subtasks.append(subtask)

        return subtasks

    def bulk_update_status(
        self,
        task_ids: List[int],
        new_status: TaskStatus,
        user_id: int
    ) -> int:
        """
        Bulk update status for multiple tasks.

        Args:
            task_ids: List of task IDs
            new_status: New status to set
            user_id: User ID for ownership validation

        Returns:
            Number of tasks updated

        Raises:
            HTTPException: If any task not found or not owned by user
        """
        # Validate all tasks belong to user
        for task_id in task_ids:
            self.get_task(task_id, user_id, load_relationships=False)

        return self.repository.bulk_update_status(task_ids, new_status)

    # Private helper methods

    def _apply_creation_rules(self, task: Task) -> None:
        """
        Apply business rules when creating a task.

        Args:
            task: Task instance to apply rules to
        """
        # Set default priority if not provided
        if not task.priority:
            task.priority = Priority.MEDIUM

        # Set default status
        if not task.status:
            task.status = TaskStatus.TODO

        # Initialize metadata if not present
        if not task.task_metadata:
            task.task_metadata = {}

    def _handle_status_change(
        self,
        task: Task,
        new_status: TaskStatus
    ) -> None:
        """
        Handle business logic for status changes.

        Args:
            task: Task being updated
            new_status: New status being set
        """
        # If marking as completed, set completion timestamp
        if new_status == TaskStatus.COMPLETED and task.status != TaskStatus.COMPLETED:
            task.completed_at = datetime.utcnow()

        # If unmarking as completed, clear completion timestamp
        if new_status != TaskStatus.COMPLETED and task.status == TaskStatus.COMPLETED:
            task.completed_at = None

    def _calculate_estimation_accuracy(
        self,
        estimated: int,
        actual: int
    ) -> float:
        """
        Calculate how accurate time estimation was.

        Args:
            estimated: Estimated duration in minutes
            actual: Actual duration in minutes

        Returns:
            Accuracy percentage (100 = perfect match)
        """
        if estimated == 0:
            return 0.0

        difference = abs(estimated - actual)
        accuracy = max(0, 100 - (difference / estimated * 100))

        return round(accuracy, 2)


def get_task_service(session: Session = Depends(get_session)) -> TaskService:
    """
    Factory function to create TaskService instance.

    Used for dependency injection in FastAPI endpoints.

    Args:
        session: Database session

    Returns:
        TaskService instance

    Example:
        from typing import Annotated
        from fastapi import Depends

        TaskServiceDep = Annotated[TaskService, Depends(get_task_service)]

        @app.post("/tasks")
        def create_task(service: TaskServiceDep, task: TaskCreate):
            return service.create_task(task, user_id=1)
    """
    return TaskService(session)

"""
Task Repository for database operations.

Provides data access layer for Task entities with comprehensive
CRUD operations, filtering, and query capabilities following
repository pattern and SQLModel best practices.
"""

from datetime import datetime
from typing import List, Optional, Sequence
from sqlmodel import Session, select, func, and_, or_
from sqlalchemy.orm import selectinload

from app.models.task import Task, TaskStatus, Priority
from app.models.tag import Tag


class TaskRepository:
    """
    Repository for Task entity data access operations.

    Implements repository pattern to abstract database operations
    and provide reusable query methods.
    """

    def __init__(self, session: Session):
        """
        Initialize repository with database session.

        Args:
            session: SQLModel database session
        """
        self.session = session

    def create(self, task: Task) -> Task:
        """
        Create a new task in the database.

        Args:
            task: Task instance to create

        Returns:
            Created task with generated ID and relationships loaded

        Example:
            task = Task(title="New Task", user_id=1)
            created_task = repository.create(task)
        """
        self.session.add(task)
        self.session.commit()
        self.session.refresh(task)
        return task

    def get_by_id(
        self,
        task_id: int,
        load_relationships: bool = True
    ) -> Optional[Task]:
        """
        Retrieve task by ID with optional relationship loading.

        Args:
            task_id: Task ID to retrieve
            load_relationships: Whether to eagerly load subtasks and tags

        Returns:
            Task instance or None if not found

        Example:
            task = repository.get_by_id(1, load_relationships=True)
        """
        statement = select(Task).where(Task.id == task_id)

        if load_relationships:
            # Eager load relationships to avoid N+1 queries
            statement = statement.options(
                selectinload(Task.subtasks),
                selectinload(Task.tags)
            )

        return self.session.exec(statement).first()

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        load_relationships: bool = False
    ) -> Sequence[Task]:
        """
        Retrieve all tasks with pagination.

        Args:
            skip: Number of records to skip (offset)
            limit: Maximum number of records to return
            load_relationships: Whether to eagerly load relationships

        Returns:
            List of tasks

        Example:
            tasks = repository.get_all(skip=0, limit=20)
        """
        statement = select(Task).offset(skip).limit(limit)

        if load_relationships:
            statement = statement.options(
                selectinload(Task.subtasks),
                selectinload(Task.tags)
            )

        return self.session.exec(statement).all()

    def get_by_user(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        status_filter: Optional[TaskStatus] = None,
        priority_filter: Optional[Priority] = None,
        include_subtasks: bool = True
    ) -> Sequence[Task]:
        """
        Retrieve tasks for a specific user with filtering.

        Args:
            user_id: User ID to filter tasks
            skip: Pagination offset
            limit: Maximum records to return
            status_filter: Optional status filter
            priority_filter: Optional priority filter
            include_subtasks: Whether to include subtasks or only top-level tasks

        Returns:
            Filtered list of tasks

        Example:
            tasks = repository.get_by_user(
                user_id=1,
                status_filter=TaskStatus.TODO,
                priority_filter=Priority.HIGH
            )
        """
        statement = select(Task).where(Task.user_id == user_id)

        # Filter out subtasks if requested (only get parent tasks)
        if not include_subtasks:
            statement = statement.where(Task.parent_task_id.is_(None))

        # Apply status filter
        if status_filter:
            statement = statement.where(Task.status == status_filter)

        # Apply priority filter
        if priority_filter:
            statement = statement.where(Task.priority == priority_filter)

        # Order by due date (nulls last) and priority
        statement = (
            statement
            .order_by(Task.due_date.asc().nulls_last(), Task.priority.desc())
            .offset(skip)
            .limit(limit)
        )

        return self.session.exec(statement).all()

    def search_by_text(
        self,
        user_id: int,
        search_query: str,
        skip: int = 0,
        limit: int = 50
    ) -> Sequence[Task]:
        """
        Search tasks by text in title or description.

        Args:
            user_id: User ID to scope search
            search_query: Text to search for
            skip: Pagination offset
            limit: Maximum records to return

        Returns:
            List of matching tasks

        Example:
            tasks = repository.search_by_text(
                user_id=1,
                search_query="budget"
            )
        """
        search_pattern = f"%{search_query}%"

        statement = (
            select(Task)
            .where(
                and_(
                    Task.user_id == user_id,
                    or_(
                        Task.title.ilike(search_pattern),
                        Task.description.ilike(search_pattern)
                    )
                )
            )
            .order_by(Task.updated_at.desc())
            .offset(skip)
            .limit(limit)
        )

        return self.session.exec(statement).all()

    def get_overdue_tasks(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> Sequence[Task]:
        """
        Retrieve overdue tasks for a user.

        Args:
            user_id: User ID to filter tasks
            skip: Pagination offset
            limit: Maximum records to return

        Returns:
            List of overdue tasks

        Example:
            overdue = repository.get_overdue_tasks(user_id=1)
        """
        now = datetime.utcnow()

        statement = (
            select(Task)
            .where(
                and_(
                    Task.user_id == user_id,
                    Task.due_date < now,
                    Task.status != TaskStatus.COMPLETED
                )
            )
            .order_by(Task.due_date.asc())
            .offset(skip)
            .limit(limit)
        )

        return self.session.exec(statement).all()

    def get_upcoming_tasks(
        self,
        user_id: int,
        days: int = 7,
        skip: int = 0,
        limit: int = 100
    ) -> Sequence[Task]:
        """
        Retrieve tasks due within specified number of days.

        Args:
            user_id: User ID to filter tasks
            days: Number of days to look ahead
            skip: Pagination offset
            limit: Maximum records to return

        Returns:
            List of upcoming tasks

        Example:
            upcoming = repository.get_upcoming_tasks(user_id=1, days=7)
        """
        from datetime import timedelta

        now = datetime.utcnow()
        future_date = now + timedelta(days=days)

        statement = (
            select(Task)
            .where(
                and_(
                    Task.user_id == user_id,
                    Task.due_date.between(now, future_date),
                    Task.status != TaskStatus.COMPLETED
                )
            )
            .order_by(Task.due_date.asc())
            .offset(skip)
            .limit(limit)
        )

        return self.session.exec(statement).all()

    def get_subtasks(
        self,
        parent_task_id: int
    ) -> Sequence[Task]:
        """
        Retrieve all subtasks for a parent task.

        Args:
            parent_task_id: Parent task ID

        Returns:
            List of subtasks

        Example:
            subtasks = repository.get_subtasks(parent_task_id=5)
        """
        statement = (
            select(Task)
            .where(Task.parent_task_id == parent_task_id)
            .order_by(Task.created_at.asc())
        )

        return self.session.exec(statement).all()

    def get_tasks_by_tag(
        self,
        user_id: int,
        tag_name: str,
        skip: int = 0,
        limit: int = 100
    ) -> Sequence[Task]:
        """
        Retrieve tasks filtered by tag name.

        Args:
            user_id: User ID to scope search
            tag_name: Tag name to filter by
            skip: Pagination offset
            limit: Maximum records to return

        Returns:
            List of tasks with specified tag

        Example:
            tasks = repository.get_tasks_by_tag(user_id=1, tag_name="work")
        """
        statement = (
            select(Task)
            .join(Task.tags)
            .where(
                and_(
                    Task.user_id == user_id,
                    Tag.name == tag_name
                )
            )
            .offset(skip)
            .limit(limit)
        )

        return self.session.exec(statement).all()

    def update(self, task: Task) -> Task:
        """
        Update existing task in database.

        Args:
            task: Task instance with updated values

        Returns:
            Updated task

        Example:
            task.title = "Updated Title"
            updated_task = repository.update(task)
        """
        task.update_timestamp()
        self.session.add(task)
        self.session.commit()
        self.session.refresh(task)
        return task

    def delete(self, task: Task) -> None:
        """
        Delete task from database.

        Args:
            task: Task instance to delete

        Example:
            repository.delete(task)
        """
        self.session.delete(task)
        self.session.commit()

    def count_by_status(
        self,
        user_id: int,
        status: Optional[TaskStatus] = None
    ) -> int:
        """
        Count tasks by status for a user.

        Args:
            user_id: User ID to scope count
            status: Optional status to filter by

        Returns:
            Count of tasks

        Example:
            todo_count = repository.count_by_status(user_id=1, status=TaskStatus.TODO)
        """
        statement = select(func.count(Task.id)).where(Task.user_id == user_id)

        if status:
            statement = statement.where(Task.status == status)

        return self.session.exec(statement).one()

    def get_task_statistics(
        self,
        user_id: int
    ) -> dict:
        """
        Get comprehensive task statistics for a user.

        Args:
            user_id: User ID to get statistics for

        Returns:
            Dictionary with task statistics

        Example:
            stats = repository.get_task_statistics(user_id=1)
            # Returns: {
            #   "total": 50,
            #   "todo": 20,
            #   "in_progress": 15,
            #   "completed": 15,
            #   "overdue": 5
            # }
        """
        total = self.count_by_status(user_id)
        todo = self.count_by_status(user_id, TaskStatus.TODO)
        in_progress = self.count_by_status(user_id, TaskStatus.IN_PROGRESS)
        completed = self.count_by_status(user_id, TaskStatus.COMPLETED)

        # Count overdue tasks
        now = datetime.utcnow()
        overdue_statement = select(func.count(Task.id)).where(
            and_(
                Task.user_id == user_id,
                Task.due_date < now,
                Task.status != TaskStatus.COMPLETED
            )
        )
        overdue = self.session.exec(overdue_statement).one()

        return {
            "total": total,
            "todo": todo,
            "in_progress": in_progress,
            "completed": completed,
            "overdue": overdue
        }

    def bulk_update_status(
        self,
        task_ids: List[int],
        new_status: TaskStatus
    ) -> int:
        """
        Bulk update status for multiple tasks.

        Args:
            task_ids: List of task IDs to update
            new_status: New status to set

        Returns:
            Number of tasks updated

        Example:
            count = repository.bulk_update_status([1, 2, 3], TaskStatus.COMPLETED)
        """
        statement = select(Task).where(Task.id.in_(task_ids))
        tasks = self.session.exec(statement).all()

        for task in tasks:
            task.status = new_status
            if new_status == TaskStatus.COMPLETED:
                task.completed_at = datetime.utcnow()
            task.update_timestamp()
            self.session.add(task)

        self.session.commit()
        return len(tasks)


def get_task_repository(session: Session) -> TaskRepository:
    """
    Factory function to create TaskRepository instance.

    Used for dependency injection in FastAPI endpoints.

    Args:
        session: Database session

    Returns:
        TaskRepository instance

    Example:
        from typing import Annotated
        from fastapi import Depends

        TaskRepoDep = Annotated[TaskRepository, Depends(get_task_repository)]

        @app.get("/tasks")
        def get_tasks(repo: TaskRepoDep):
            return repo.get_all()
    """
    return TaskRepository(session)

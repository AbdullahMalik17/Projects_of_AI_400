from datetime import datetime
from app.services.task_service import TaskService
from app.schemas.task import TaskCreate, TaskUpdate, TaskStatus, Priority
from typing import List, Optional, Dict, Any

class AgentTools:
    def __init__(self, service: TaskService, user_id: int):
        self.service = service
        self.user_id = user_id

    def list_tasks(self, status: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        List tasks, optionally filtered by status.
        Args:
            status: 'todo', 'in_progress', 'completed'
            limit: max number of tasks
        """
        status_enum = TaskStatus(status) if status else None
        tasks = self.service.list_tasks(user_id=self.user_id, status_filter=status_enum, limit=limit)
        return [t.model_dump() for t in tasks]

    def create_task(self, title: str, description: str = None, priority: str = "medium", due_date: str = None) -> Dict[str, Any]:
        """
        Create a new task.
        Args:
            title: Task title
            description: Task description
            priority: 'low', 'medium', 'high'
            due_date: ISO 8601 date string
        """
        priority_enum = Priority(priority) if priority else Priority.MEDIUM
        task_in = TaskCreate(
            title=title,
            description=description,
            priority=priority_enum,
            due_date=datetime.fromisoformat(due_date) if due_date else None
        )
        task = self.service.create_task(task_in, self.user_id)
        return task.model_dump()

    def delete_task(self, task_id: int) -> str:
        """Delete a task by ID."""
        self.service.delete_task(task_id, self.user_id)
        return f"Task {task_id} deleted successfully."

    def complete_task(self, task_id: int) -> Dict[str, Any]:
        """Mark a task as completed."""
        task = self.service.complete_task(task_id, self.user_id)
        return task.model_dump()

    def search_tasks(self, query: str) -> List[Dict[str, Any]]:
        """Search tasks by keyword."""
        tasks = self.service.search_tasks(self.user_id, query)
        return [t.model_dump() for t in tasks]
"""
Task API endpoints.

Provides CRUD operations and AI-enhanced functionality for tasks
using service layer and intelligent agents.
"""

from typing import List, Optional, Annotated
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from app.core.database import get_session
from app.models.task import Task, TaskStatus, Priority
from app.schemas.task import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskListResponse,
    NaturalLanguageTaskCreate,
)
from app.schemas.response import APIResponse
from app.services.task_service import TaskService, get_task_service
from app.agents.task_parser import task_parser_agent
from app.agents.task_intelligence_agent import task_intelligence_agent

router = APIRouter(prefix="/tasks", tags=["Tasks"])

# Dependency annotations
SessionDep = Annotated[Session, Depends(get_session)]
TaskServiceDep = Annotated[TaskService, Depends(get_task_service)]

# Default user ID for single-user mode
DEFAULT_USER_ID = 1


@router.post("", response_model=APIResponse[TaskResponse], status_code=status.HTTP_201_CREATED)
async def create_task(
    task_in: TaskCreate,
    service: TaskServiceDep
):
    """
    Create a new task with validation and business logic.

    Accepts structured task data and creates a task using the service layer
    with proper validation and business rules applied.

    **Example Request:**
    ```json
    {
        "title": "Prepare quarterly budget analysis",
        "description": "Compile Q4 budget data",
        "priority": "high",
        "due_date": "2026-01-19T17:00:00",
        "estimated_duration": 180
    }
    ```
    """
    task = service.create_task(task_in, user_id=DEFAULT_USER_ID)

    return APIResponse(
        success=True,
        data=task,
        message="Task created successfully"
    )


@router.get("", response_model=APIResponse[TaskListResponse])
async def list_tasks(
    service: TaskServiceDep,
    session: SessionDep,
    status_filter: Optional[TaskStatus] = Query(None, alias="status", description="Filter by status"),
    priority_filter: Optional[Priority] = Query(None, alias="priority", description="Filter by priority"),
    skip: int = Query(0, ge=0, description="Number of tasks to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum tasks to return"),
    include_subtasks: bool = Query(True, description="Include subtasks in results")
):
    """
    List tasks with filtering, pagination, and statistics.

    Returns a paginated list of tasks with optional filtering by status and priority.

    **Query Parameters:**
    - `status`: Filter by task status (todo, in_progress, completed)
    - `priority`: Filter by priority (low, medium, high)
    - `skip`: Pagination offset (default: 0)
    - `limit`: Max results per page (default: 50, max: 100)
    - `include_subtasks`: Include subtasks (default: true)
    """
    tasks = service.list_tasks(
        user_id=DEFAULT_USER_ID,
        skip=skip,
        limit=limit,
        status_filter=status_filter,
        priority_filter=priority_filter,
        include_subtasks=include_subtasks
    )

    # Get total count for pagination
    stats = service.get_task_statistics(DEFAULT_USER_ID)
    total = stats["total"]

    return APIResponse(
        success=True,
        data=TaskListResponse(
            tasks=tasks,
            total=total,
            page=skip // limit + 1,
            page_size=limit,
            has_more=(skip + limit) < total
        )
    )


@router.get("/{task_id}", response_model=APIResponse[TaskResponse])
async def get_task(
    task_id: int,
    service: TaskServiceDep
):
    """
    Get a specific task by ID with all relationships loaded.

    Returns detailed information about a single task including subtasks and tags.
    """
    task = service.get_task(task_id, user_id=DEFAULT_USER_ID, load_relationships=True)

    return APIResponse(
        success=True,
        data=task
    )


@router.put("/{task_id}", response_model=APIResponse[TaskResponse])
async def update_task(
    task_id: int,
    task_update: TaskUpdate,
    service: TaskServiceDep
):
    """
    Update an existing task with validation.

    Updates only the provided fields, maintaining existing values for others.

    **Example Request:**
    ```json
    {
        "status": "in_progress",
        "priority": "high"
    }
    ```
    """
    task = service.update_task(task_id, task_update, user_id=DEFAULT_USER_ID)

    return APIResponse(
        success=True,
        data=task,
        message="Task updated successfully"
    )


@router.delete("/{task_id}", response_model=APIResponse[dict])
async def delete_task(
    task_id: int,
    service: TaskServiceDep,
    cascade_subtasks: bool = Query(False, description="Delete subtasks as well")
):
    """
    Delete a task with optional cascade to subtasks.

    **Query Parameters:**
    - `cascade_subtasks`: If true, also deletes all subtasks
    """
    service.delete_task(task_id, user_id=DEFAULT_USER_ID, cascade_subtasks=cascade_subtasks)

    return APIResponse(
        success=True,
        data={"id": task_id},
        message="Task deleted successfully"
    )


@router.post("/{task_id}/complete", response_model=APIResponse[TaskResponse])
async def complete_task(
    task_id: int,
    service: TaskServiceDep,
    actual_duration: Optional[int] = Query(None, description="Actual time spent in minutes")
):
    """
    Mark a task as completed with optional actual duration.

    **Query Parameters:**
    - `actual_duration`: Actual time spent on task in minutes
    """
    task = service.complete_task(task_id, user_id=DEFAULT_USER_ID, actual_duration=actual_duration)

    return APIResponse(
        success=True,
        data=task,
        message="Task marked as complete"
    )


@router.post("/nl-create", response_model=APIResponse[TaskResponse], status_code=status.HTTP_201_CREATED)
async def create_task_from_natural_language(
    nl_input: NaturalLanguageTaskCreate,
    service: TaskServiceDep
):
    """
    Create a task from natural language input using AI.

    Uses Gemini AI to parse natural language and extract structured task information
    including title, description, due date, priority, and tags.

    **Example Request:**
    ```json
    {
        "message": "Remind me to call John tomorrow at 2pm about the project budget",
        "context": {"timezone": "America/New_York"}
    }
    ```

    The AI will extract:
    - Title: "Call John about the project budget"
    - Due Date: Tomorrow at 2:00 PM
    - Priority: Based on urgency keywords
    - Tags: ["communication", "project", "budget"]
    """
    # Parse natural language using AI agent
    parsed_task = await task_parser_agent.parse_natural_language_task(
        nl_input.message,
        user_context=nl_input.context
    )

    # Create task using service
    task = service.create_task(parsed_task, user_id=DEFAULT_USER_ID)

    return APIResponse(
        success=True,
        data=task,
        message="Task created successfully from natural language"
    )


@router.get("/search", response_model=APIResponse[List[TaskResponse]])
async def search_tasks(
    service: TaskServiceDep,
    q: str = Query(..., min_length=2, description="Search query"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100)
):
    """
    Search tasks by text query.

    Searches in task titles and descriptions.

    **Query Parameters:**
    - `q`: Search text (minimum 2 characters)
    - `skip`: Pagination offset
    - `limit`: Max results
    """
    tasks = service.search_tasks(user_id=DEFAULT_USER_ID, query=q, skip=skip, limit=limit)

    return APIResponse(
        success=True,
        data=tasks,
        message=f"Found {len(tasks)} matching tasks"
    )


@router.get("/overdue", response_model=APIResponse[List[TaskResponse]])
async def get_overdue_tasks(
    service: TaskServiceDep,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100)
):
    """
    Get all overdue tasks.

    Returns tasks that are past their due date and not yet completed.
    """
    tasks = service.get_overdue_tasks(user_id=DEFAULT_USER_ID, skip=skip, limit=limit)

    return APIResponse(
        success=True,
        data=tasks,
        message=f"Found {len(tasks)} overdue tasks"
    )


@router.get("/upcoming", response_model=APIResponse[List[TaskResponse]])
async def get_upcoming_tasks(
    service: TaskServiceDep,
    days: int = Query(7, ge=1, le=30, description="Days to look ahead"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100)
):
    """
    Get tasks due within specified number of days.

    **Query Parameters:**
    - `days`: Number of days to look ahead (1-30, default: 7)
    """
    tasks = service.get_upcoming_tasks(user_id=DEFAULT_USER_ID, days=days, skip=skip, limit=limit)

    return APIResponse(
        success=True,
        data=tasks,
        message=f"Found {len(tasks)} tasks due in next {days} days"
    )


@router.get("/statistics", response_model=APIResponse[dict])
async def get_task_statistics(
    service: TaskServiceDep
):
    """
    Get comprehensive task statistics.

    Returns counts by status, overdue tasks, and completion rate.

    **Response Example:**
    ```json
    {
        "total": 50,
        "todo": 20,
        "in_progress": 15,
        "completed": 15,
        "overdue": 5,
        "completion_rate": 30.0
    }
    ```
    """
    stats = service.get_task_statistics(user_id=DEFAULT_USER_ID)

    return APIResponse(
        success=True,
        data=stats,
        message="Statistics retrieved successfully"
    )


@router.post("/{task_id}/breakdown", response_model=APIResponse[List[TaskResponse]])
async def breakdown_task(
    task_id: int,
    service: TaskServiceDep
):
    """
    Break down a complex task into subtasks using AI.

    Uses intelligent agent to suggest 3-7 subtasks based on the task description.
    """
    # Get the task
    task = service.get_task(task_id, user_id=DEFAULT_USER_ID)

    # Get AI suggestions for subtasks
    subtask_titles = await task_intelligence_agent.suggest_task_breakdown(
        task.title,
        task.description or ""
    )

    # Create subtasks
    subtasks = service.create_subtasks(
        parent_task_id=task_id,
        user_id=DEFAULT_USER_ID,
        subtask_titles=subtask_titles
    )

    return APIResponse(
        success=True,
        data=subtasks,
        message=f"Created {len(subtasks)} subtasks"
    )


@router.get("/{task_id}/insights", response_model=APIResponse[dict])
async def get_task_insights(
    task_id: int,
    service: TaskServiceDep
):
    """
    Get AI-powered insights for a specific task.

    Analyzes the task and provides:
    - Priority suggestions
    - Time estimation
    - Recommendations

    **Response Example:**
    ```json
    {
        "suggested_priority": "high",
        "estimated_duration_minutes": 120,
        "recommendations": ["Break into subtasks", "Schedule in morning"],
        "complexity": "medium"
    }
    ```
    """
    task = service.get_task(task_id, user_id=DEFAULT_USER_ID)

    insights = await task_intelligence_agent.analyze_task(task)

    return APIResponse(
        success=True,
        data=insights,
        message="Insights generated successfully"
    )


@router.get("/insights/productivity", response_model=APIResponse[dict])
async def get_productivity_insights(
    service: TaskServiceDep
):
    """
    Get AI-powered productivity insights based on task statistics.

    Analyzes task patterns and provides actionable recommendations
    to improve productivity.

    **Response Example:**
    ```json
    {
        "insights": ["Good completion rate: 75%", "3 overdue tasks"],
        "recommendations": ["Review overdue tasks", "Consider time blocking"],
        "productivity_score": 75
    }
    ```
    """
    stats = service.get_task_statistics(user_id=DEFAULT_USER_ID)

    insights = await task_intelligence_agent.get_productivity_insights(stats)

    return APIResponse(
        success=True,
        data=insights,
        message="Productivity insights generated successfully"
    )

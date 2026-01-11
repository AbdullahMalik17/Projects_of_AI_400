"""
Task API endpoints.

Provides CRUD operations and AI-enhanced functionality for tasks.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
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

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.post("", response_model=APIResponse[TaskResponse], status_code=201)
async def create_task(
    task_in: TaskCreate,
    session: Session = Depends(get_session)
):
    """
    Create a new task.

    Accepts structured task data and creates a task in the database.
    In future iterations, this will integrate with AI for enhanced task parsing.
    """
    # For MVP, using default user_id = 1 (single-user mode)
    task = Task(
        **task_in.model_dump(exclude={"tag_ids"}),
        user_id=1  # Default user for single-user mode
    )

    session.add(task)
    session.commit()
    session.refresh(task)

    return APIResponse(
        success=True,
        data=task,
        message="Task created successfully"
    )


@router.get("", response_model=APIResponse[TaskListResponse])
async def list_tasks(
    status: Optional[TaskStatus] = Query(None, description="Filter by status"),
    priority: Optional[Priority] = Query(None, description="Filter by priority"),
    skip: int = Query(0, ge=0, description="Number of tasks to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum tasks to return"),
    session: Session = Depends(get_session)
):
    """
    List tasks with optional filtering and pagination.

    Returns a paginated list of tasks with filtering options for status and priority.
    """
    # Build query
    query = select(Task).where(Task.user_id == 1)  # Default user

    if status:
        query = query.where(Task.status == status)
    if priority:
        query = query.where(Task.priority == priority)

    # Get total count
    count_query = select(Task).where(Task.user_id == 1)
    if status:
        count_query = count_query.where(Task.status == status)
    if priority:
        count_query = count_query.where(Task.priority == priority)

    total = len(session.exec(count_query).all())

    # Apply pagination and ordering
    query = query.order_by(Task.created_at.desc()).offset(skip).limit(limit)
    tasks = session.exec(query).all()

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
    session: Session = Depends(get_session)
):
    """
    Get a specific task by ID.

    Returns detailed information about a single task.
    """
    task = session.get(Task, task_id)

    if not task or task.user_id != 1:  # Default user check
        raise HTTPException(status_code=404, detail="Task not found")

    return APIResponse(
        success=True,
        data=task
    )


@router.put("/{task_id}", response_model=APIResponse[TaskResponse])
async def update_task(
    task_id: int,
    task_update: TaskUpdate,
    session: Session = Depends(get_session)
):
    """
    Update an existing task.

    Updates task fields provided in the request body.
    """
    task = session.get(Task, task_id)

    if not task or task.user_id != 1:
        raise HTTPException(status_code=404, detail="Task not found")

    # Update fields
    update_data = task_update.model_dump(exclude_unset=True, exclude={"tag_ids"})
    for key, value in update_data.items():
        setattr(task, key, value)

    task.update_timestamp()

    session.add(task)
    session.commit()
    session.refresh(task)

    return APIResponse(
        success=True,
        data=task,
        message="Task updated successfully"
    )


@router.delete("/{task_id}", response_model=APIResponse[dict])
async def delete_task(
    task_id: int,
    session: Session = Depends(get_session)
):
    """
    Delete a task.

    Permanently removes a task from the database.
    """
    task = session.get(Task, task_id)

    if not task or task.user_id != 1:
        raise HTTPException(status_code=404, detail="Task not found")

    session.delete(task)
    session.commit()

    return APIResponse(
        success=True,
        data={"id": task_id},
        message="Task deleted successfully"
    )


@router.post("/{task_id}/complete", response_model=APIResponse[TaskResponse])
async def complete_task(
    task_id: int,
    session: Session = Depends(get_session)
):
    """
    Mark a task as completed.

    Updates task status to completed and sets completion timestamp.
    """
    task = session.get(Task, task_id)

    if not task or task.user_id != 1:
        raise HTTPException(status_code=404, detail="Task not found")

    task.mark_complete()

    session.add(task)
    session.commit()
    session.refresh(task)

    return APIResponse(
        success=True,
        data=task,
        message="Task marked as complete"
    )


@router.post("/nl-create", response_model=APIResponse[TaskResponse])
async def create_task_from_natural_language(
    nl_input: NaturalLanguageTaskCreate,
    session: Session = Depends(get_session)
):
    """
    Create a task from natural language input.

    Uses AI to parse natural language and extract task information.
    Currently returns a placeholder - will be implemented with Gemini integration.
    """
    # TODO: Implement AI-powered natural language parsing using Gemini
    # For now, create a basic task with the message as title

    task = Task(
        title=nl_input.message[:255],  # Truncate to max length
        description=f"Created from natural language: {nl_input.message}",
        user_id=1,
        metadata={"source": "natural_language", "original_message": nl_input.message}
    )

    session.add(task)
    session.commit()
    session.refresh(task)

    return APIResponse(
        success=True,
        data=task,
        message="Task created from natural language (AI parsing coming soon)"
    )

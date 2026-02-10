"""
Tasks API - Oppgaveadministrasjon endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.database import get_db
from app.models.task import Task, TaskStatus
from app.models.task_audit_log import TaskAuditLog, TaskAuditAction
from app.schemas.task import (
    TaskCreate, TaskUpdate, TaskComplete, TaskAutoComplete,
    TaskResponse, TaskListResponse, TaskAuditLogResponse,
    TaskTemplateApply, TaskWithSubtasks
)
from app.services.task_template_service import TaskTemplateService


router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.get("", response_model=TaskListResponse)
async def get_tasks(
    client_id: UUID = Query(..., description="Client ID"),
    period_year: int = Query(..., description="Period year"),
    period_month: Optional[int] = Query(None, description="Period month"),
    category: Optional[str] = Query(None, description="Filter by category"),
    status: Optional[str] = Query(None, description="Filter by status"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get tasks for a client and period
    """
    # Build query
    query = select(Task).filter(
        Task.client_id == client_id,
        Task.period_year == period_year
    )
    
    if period_month is not None:
        query = query.filter(Task.period_month == period_month)
    
    if category:
        query = query.filter(Task.category == category)
    
    if status:
        query = query.filter(Task.status == status)
    
    # Get tasks (parent tasks only - subtasks loaded via relationship)
    query = query.filter(Task.parent_task_id.is_(None)).order_by(
        Task.sort_order.asc().nullslast(),
        Task.created_at.asc()
    )
    result = await db.execute(query)
    tasks = result.scalars().all()
    
    # Calculate stats
    all_tasks_query = select(Task).filter(
        Task.client_id == client_id,
        Task.period_year == period_year
    )
    
    if period_month is not None:
        all_tasks_query = all_tasks_query.filter(Task.period_month == period_month)
    
    # Total count
    total_result = await db.execute(select(func.count()).select_from(all_tasks_query.subquery()))
    total = total_result.scalar() or 0
    
    # Completed count
    completed_result = await db.execute(
        select(func.count()).select_from(
            all_tasks_query.filter(Task.status == TaskStatus.COMPLETED).subquery()
        )
    )
    completed = completed_result.scalar() or 0
    
    # In progress count
    in_progress_result = await db.execute(
        select(func.count()).select_from(
            all_tasks_query.filter(Task.status == TaskStatus.IN_PROGRESS).subquery()
        )
    )
    in_progress = in_progress_result.scalar() or 0
    
    # Not started count
    not_started_result = await db.execute(
        select(func.count()).select_from(
            all_tasks_query.filter(Task.status == TaskStatus.NOT_STARTED).subquery()
        )
    )
    not_started = not_started_result.scalar() or 0
    
    # Deviations count
    deviations_result = await db.execute(
        select(func.count()).select_from(
            all_tasks_query.filter(Task.status == TaskStatus.DEVIATION).subquery()
        )
    )
    deviations = deviations_result.scalar() or 0
    
    return TaskListResponse(
        tasks=[TaskResponse.from_orm(t) for t in tasks],
        total=total,
        completed=completed,
        in_progress=in_progress,
        not_started=not_started,
        deviations=deviations
    )


@router.post("", response_model=TaskResponse)
async def create_task(
    task: TaskCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new task
    """
    db_task = Task(**task.dict())
    db.add(db_task)
    await db.flush()
    
    # Create audit log
    audit_log = TaskAuditLog(
        task_id=db_task.id,
        action=TaskAuditAction.CREATED,
        performed_by="system",
        performed_at=datetime.utcnow()
    )
    db.add(audit_log)
    
    await db.commit()
    await db.refresh(db_task)
    
    return TaskResponse.from_orm(db_task)


@router.get("/{task_id}", response_model=TaskWithSubtasks)
async def get_task(
    task_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a single task with subtasks
    """
    result = await db.execute(select(Task).filter(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return TaskWithSubtasks.from_orm(task)


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: UUID,
    task_update: TaskUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update a task
    """
    result = await db.execute(select(Task).filter(Task.id == task_id))
    db_task = result.scalar_one_or_none()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Update fields
    update_data = task_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_task, field, value)
    
    db_task.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(db_task)
    
    return TaskResponse.from_orm(db_task)


@router.post("/{task_id}/complete", response_model=TaskResponse)
async def complete_task(
    task_id: UUID,
    completion: TaskComplete,
    db: AsyncSession = Depends(get_db)
):
    """
    Manually mark task as complete (checkbox)
    """
    result = await db.execute(select(Task).filter(Task.id == task_id))
    db_task = result.scalar_one_or_none()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Update task
    db_task.status = TaskStatus.COMPLETED
    db_task.completed_by = completion.completed_by
    db_task.completed_at = datetime.utcnow()
    if completion.documentation_url:
        db_task.documentation_url = completion.documentation_url
    db_task.updated_at = datetime.utcnow()
    
    # Create audit log
    audit_log = TaskAuditLog(
        task_id=db_task.id,
        action=TaskAuditAction.MANUALLY_CHECKED,
        performed_by=completion.completed_by,
        performed_at=datetime.utcnow(),
        result="ok",
        result_description=completion.notes,
        documentation_reference=completion.documentation_url
    )
    db.add(audit_log)
    
    await db.commit()
    await db.refresh(db_task)
    
    return TaskResponse.from_orm(db_task)


@router.post("/{task_id}/auto-complete", response_model=TaskResponse)
async def auto_complete_task(
    task_id: UUID,
    auto_completion: TaskAutoComplete,
    db: AsyncSession = Depends(get_db)
):
    """
    AI auto-mark task as complete
    """
    result = await db.execute(select(Task).filter(Task.id == task_id))
    db_task = result.scalar_one_or_none()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Determine status based on result
    if auto_completion.result == "ok":
        db_task.status = TaskStatus.COMPLETED
    else:
        db_task.status = TaskStatus.DEVIATION
    
    # Update task
    db_task.completed_by = "AI"
    db_task.completed_at = datetime.utcnow()
    db_task.documentation_url = auto_completion.documentation_url
    db_task.ai_comment = auto_completion.ai_comment
    db_task.updated_at = datetime.utcnow()
    
    # Create audit log
    audit_log = TaskAuditLog(
        task_id=db_task.id,
        action=TaskAuditAction.AUTO_COMPLETED if auto_completion.result == "ok" else TaskAuditAction.MARKED_DEVIATION,
        performed_by="AI-agent",
        performed_at=datetime.utcnow(),
        result=auto_completion.result,
        result_description=auto_completion.result_description,
        documentation_reference=auto_completion.documentation_url
    )
    db.add(audit_log)
    
    await db.commit()
    await db.refresh(db_task)
    
    return TaskResponse.from_orm(db_task)


@router.get("/{task_id}/audit-log", response_model=List[TaskAuditLogResponse])
async def get_task_audit_log(
    task_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get audit trail for a task
    """
    # Verify task exists
    result = await db.execute(select(Task).filter(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Get audit logs
    logs_result = await db.execute(
        select(TaskAuditLog)
        .filter(TaskAuditLog.task_id == task_id)
        .order_by(TaskAuditLog.performed_at.desc())
    )
    logs = logs_result.scalars().all()
    
    return [TaskAuditLogResponse.from_orm(log) for log in logs]


@router.delete("/{task_id}")
async def delete_task(
    task_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a task
    """
    result = await db.execute(select(Task).filter(Task.id == task_id))
    db_task = result.scalar_one_or_none()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    await db.delete(db_task)
    await db.commit()
    
    return {"message": "Task deleted successfully"}


@router.get("/templates", response_model=List[TaskCreate])
async def get_task_templates(
    client_id: UUID = Query(..., description="Client ID"),
    period_type: str = Query("monthly", description="Period type (monthly/quarterly/yearly)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get AI-suggested task templates for a client
    """
    service = TaskTemplateService(db)
    templates = await service.generate_templates(client_id, period_type)
    return templates


@router.post("/templates/apply")
async def apply_task_template(
    template_apply: TaskTemplateApply,
    db: AsyncSession = Depends(get_db)
):
    """
    Apply task template to create tasks for a period
    """
    service = TaskTemplateService(db)
    tasks = await service.apply_template(
        template_apply.client_id,
        template_apply.period_year,
        template_apply.period_month
    )
    
    return {
        "message": f"Created {len(tasks)} tasks",
        "tasks": [TaskResponse.from_orm(t) for t in tasks]
    }

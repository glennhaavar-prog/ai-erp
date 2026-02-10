"""
Tasks API - Oppgaveadministrasjon endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
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
def get_tasks(
    client_id: UUID = Query(..., description="Client ID"),
    period_year: int = Query(..., description="Period year"),
    period_month: Optional[int] = Query(None, description="Period month"),
    category: Optional[str] = Query(None, description="Filter by category"),
    status: Optional[str] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db)
):
    """
    Get tasks for a client and period
    """
    # Build query
    query = db.query(Task).filter(
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
    tasks = query.filter(Task.parent_task_id == None).order_by(
        Task.sort_order.asc().nullslast(),
        Task.created_at.asc()
    ).all()
    
    # Calculate stats
    all_tasks_query = db.query(Task).filter(
        Task.client_id == client_id,
        Task.period_year == period_year
    )
    
    if period_month is not None:
        all_tasks_query = all_tasks_query.filter(Task.period_month == period_month)
    
    total = all_tasks_query.count()
    completed = all_tasks_query.filter(Task.status == TaskStatus.COMPLETED).count()
    in_progress = all_tasks_query.filter(Task.status == TaskStatus.IN_PROGRESS).count()
    not_started = all_tasks_query.filter(Task.status == TaskStatus.NOT_STARTED).count()
    deviations = all_tasks_query.filter(Task.status == TaskStatus.DEVIATION).count()
    
    return TaskListResponse(
        tasks=[TaskResponse.from_orm(t) for t in tasks],
        total=total,
        completed=completed,
        in_progress=in_progress,
        not_started=not_started,
        deviations=deviations
    )


@router.post("", response_model=TaskResponse)
def create_task(
    task: TaskCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new task
    """
    db_task = Task(**task.dict())
    db.add(db_task)
    db.flush()
    
    # Create audit log
    audit_log = TaskAuditLog(
        task_id=db_task.id,
        action=TaskAuditAction.CREATED,
        performed_by="system",
        performed_at=datetime.utcnow()
    )
    db.add(audit_log)
    
    db.commit()
    db.refresh(db_task)
    
    return TaskResponse.from_orm(db_task)


@router.get("/{task_id}", response_model=TaskWithSubtasks)
def get_task(
    task_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get a single task with subtasks
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return TaskWithSubtasks.from_orm(task)


@router.patch("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: UUID,
    task_update: TaskUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a task
    """
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Update fields
    update_data = task_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_task, field, value)
    
    db_task.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_task)
    
    return TaskResponse.from_orm(db_task)


@router.post("/{task_id}/complete", response_model=TaskResponse)
def complete_task(
    task_id: UUID,
    completion: TaskComplete,
    db: Session = Depends(get_db)
):
    """
    Manually mark task as complete (checkbox)
    """
    db_task = db.query(Task).filter(Task.id == task_id).first()
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
    
    db.commit()
    db.refresh(db_task)
    
    return TaskResponse.from_orm(db_task)


@router.post("/{task_id}/auto-complete", response_model=TaskResponse)
def auto_complete_task(
    task_id: UUID,
    auto_completion: TaskAutoComplete,
    db: Session = Depends(get_db)
):
    """
    AI auto-mark task as complete
    """
    db_task = db.query(Task).filter(Task.id == task_id).first()
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
    
    db.commit()
    db.refresh(db_task)
    
    return TaskResponse.from_orm(db_task)


@router.get("/{task_id}/audit-log", response_model=List[TaskAuditLogResponse])
def get_task_audit_log(
    task_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get audit trail for a task
    """
    # Verify task exists
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Get audit logs
    logs = db.query(TaskAuditLog).filter(
        TaskAuditLog.task_id == task_id
    ).order_by(TaskAuditLog.performed_at.desc()).all()
    
    return [TaskAuditLogResponse.from_orm(log) for log in logs]


@router.delete("/{task_id}")
def delete_task(
    task_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Delete a task
    """
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    db.delete(db_task)
    db.commit()
    
    return {"message": "Task deleted successfully"}


@router.get("/templates", response_model=List[TaskCreate])
def get_task_templates(
    client_id: UUID = Query(..., description="Client ID"),
    period_type: str = Query("monthly", description="Period type (monthly/quarterly/yearly)"),
    db: Session = Depends(get_db)
):
    """
    Get AI-suggested task templates for a client
    """
    service = TaskTemplateService(db)
    templates = service.generate_templates(client_id, period_type)
    return templates


@router.post("/templates/apply")
def apply_task_template(
    template_apply: TaskTemplateApply,
    db: Session = Depends(get_db)
):
    """
    Apply task template to create tasks for a period
    """
    service = TaskTemplateService(db)
    tasks = service.apply_template(
        template_apply.client_id,
        template_apply.period_year,
        template_apply.period_month
    )
    
    return {
        "message": f"Created {len(tasks)} tasks",
        "tasks": [TaskResponse.from_orm(t) for t in tasks]
    }

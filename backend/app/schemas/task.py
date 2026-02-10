"""
Task Schemas - Pydantic models for API validation
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from uuid import UUID

from app.models.task import TaskStatus, TaskFrequency, TaskCategory
from app.models.task_audit_log import TaskAuditAction, TaskAuditResult


class TaskBase(BaseModel):
    """Base task schema"""
    name: str = Field(..., max_length=255, description="Task name")
    description: Optional[str] = Field(None, description="Task description")
    category: Optional[TaskCategory] = Field(None, description="Task category")
    frequency: Optional[TaskFrequency] = Field(None, description="Task frequency")
    period_year: int = Field(..., description="Period year")
    period_month: Optional[int] = Field(None, description="Period month (NULL for yearly tasks)")
    due_date: Optional[date] = Field(None, description="Due date")
    is_checklist: bool = Field(False, description="Is this a checklist item?")
    parent_task_id: Optional[UUID] = Field(None, description="Parent task ID for sub-tasks")
    sort_order: Optional[int] = Field(None, description="Sort order")


class TaskCreate(TaskBase):
    """Schema for creating a task"""
    client_id: UUID = Field(..., description="Client ID")


class TaskUpdate(BaseModel):
    """Schema for updating a task"""
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    category: Optional[TaskCategory] = None
    frequency: Optional[TaskFrequency] = None
    due_date: Optional[date] = None
    status: Optional[TaskStatus] = None
    sort_order: Optional[int] = None


class TaskComplete(BaseModel):
    """Schema for marking task as complete"""
    completed_by: str = Field(..., max_length=100, description="Who completed the task")
    documentation_url: Optional[str] = Field(None, description="Documentation URL")
    notes: Optional[str] = Field(None, description="Completion notes")


class TaskAutoComplete(BaseModel):
    """Schema for AI auto-completion"""
    documentation_url: str = Field(..., description="Documentation URL (PDF, report)")
    ai_comment: str = Field(..., description="AI's summary/explanation")
    result: TaskAuditResult = Field(..., description="Result (ok/deviation)")
    result_description: Optional[str] = Field(None, description="Detailed description if deviation")


class TaskResponse(TaskBase):
    """Schema for task response"""
    id: UUID
    client_id: UUID
    status: TaskStatus
    completed_by: Optional[str] = None
    completed_at: Optional[datetime] = None
    documentation_url: Optional[str] = None
    ai_comment: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TaskWithSubtasks(TaskResponse):
    """Schema for task with subtasks"""
    subtasks: List[TaskResponse] = []


class TaskAuditLogResponse(BaseModel):
    """Schema for audit log response"""
    id: UUID
    task_id: UUID
    action: TaskAuditAction
    performed_by: str
    performed_at: datetime
    result: Optional[TaskAuditResult] = None
    result_description: Optional[str] = None
    documentation_reference: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    """Schema for task list with progress"""
    tasks: List[TaskResponse]
    total: int
    completed: int
    in_progress: int
    not_started: int
    deviations: int


class TaskTemplateApply(BaseModel):
    """Schema for applying task template to client"""
    client_id: UUID = Field(..., description="Client ID")
    period_year: int = Field(..., description="Period year")
    period_month: Optional[int] = Field(None, description="Period month (NULL for yearly)")

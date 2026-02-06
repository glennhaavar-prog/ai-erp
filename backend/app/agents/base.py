"""
Base Agent Classes
"""
import anthropic
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.config import settings
from app.models.agent_task import AgentTask
from app.models.agent_event import AgentEvent
from app.models.audit_trail import AuditTrail

logger = logging.getLogger(__name__)


class BaseAgent:
    """
    Base class for all specialist agents
    
    Provides common functionality:
    - Claude API client
    - Task claiming and completion
    - Event publishing
    - Audit logging
    """
    
    def __init__(self, agent_type: str):
        """Initialize agent with type"""
        self.agent_type = agent_type
        
        # Initialize Claude client
        if not settings.ANTHROPIC_API_KEY:
            logger.warning(f"{agent_type}: ANTHROPIC_API_KEY not set")
            self.client = None
        else:
            self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        
        self.model = settings.CLAUDE_MODEL
        self.max_tokens = settings.CLAUDE_MAX_TOKENS
    
    async def claim_next_task(
        self,
        db: AsyncSession,
        task_type: Optional[str] = None
    ) -> Optional[AgentTask]:
        """
        Atomically claim next pending task for this agent
        
        Args:
            db: Database session
            task_type: Optional specific task type filter
        
        Returns:
            AgentTask or None if no tasks available
        """
        query = (
            update(AgentTask)
            .where(
                AgentTask.agent_type == self.agent_type,
                AgentTask.status == 'pending'
            )
        )
        
        if task_type:
            query = query.where(AgentTask.task_type == task_type)
        
        # Atomic claim using subquery with FOR UPDATE SKIP LOCKED
        query = query.where(
            AgentTask.id == (
                select(AgentTask.id)
                .where(
                    AgentTask.agent_type == self.agent_type,
                    AgentTask.status == 'pending'
                )
                .order_by(AgentTask.priority.desc(), AgentTask.created_at.asc())
                .limit(1)
                .with_for_update(skip_locked=True)
                .scalar_subquery()
            )
        ).values(
            status='in_progress',
            started_at=datetime.utcnow()
        ).returning(AgentTask)
        
        result = await db.execute(query)
        await db.commit()
        
        task = result.scalar_one_or_none()
        
        if task:
            logger.info(
                f"{self.agent_type}: Claimed task {task.id} "
                f"(type={task.task_type}, priority={task.priority})"
            )
        
        return task
    
    async def complete_task(
        self,
        db: AsyncSession,
        task_id: str,
        result: Dict[str, Any]
    ):
        """
        Mark task as completed with result
        
        Args:
            db: Database session
            task_id: Task UUID
            result: Result data
        """
        query = (
            update(AgentTask)
            .where(AgentTask.id == task_id)
            .values(
                status='completed',
                result=result,
                completed_at=datetime.utcnow()
            )
        )
        
        await db.execute(query)
        await db.commit()
        
        logger.info(f"{self.agent_type}: Completed task {task_id}")
    
    async def fail_task(
        self,
        db: AsyncSession,
        task_id: str,
        error_message: str,
        retry: bool = True
    ):
        """
        Mark task as failed and optionally retry
        
        Args:
            db: Database session
            task_id: Task UUID
            error_message: Error description
            retry: Whether to retry (resets to pending if retries available)
        """
        # Get current task
        result = await db.execute(
            select(AgentTask).where(AgentTask.id == task_id)
        )
        task = result.scalar_one_or_none()
        
        if not task:
            logger.error(f"{self.agent_type}: Task {task_id} not found for failure")
            return
        
        # Check if retries available
        if retry and task.retry_count < task.max_retries:
            # Retry
            query = (
                update(AgentTask)
                .where(AgentTask.id == task_id)
                .values(
                    status='pending',
                    error_message=error_message,
                    retry_count=task.retry_count + 1,
                    started_at=None
                )
            )
            logger.warning(
                f"{self.agent_type}: Task {task_id} failed, retrying "
                f"({task.retry_count + 1}/{task.max_retries})"
            )
        else:
            # Max retries reached or retry=False
            query = (
                update(AgentTask)
                .where(AgentTask.id == task_id)
                .values(
                    status='failed',
                    error_message=error_message,
                    completed_at=datetime.utcnow()
                )
            )
            logger.error(
                f"{self.agent_type}: Task {task_id} failed permanently: "
                f"{error_message}"
            )
        
        await db.execute(query)
        await db.commit()
    
    async def publish_event(
        self,
        db: AsyncSession,
        tenant_id: str,
        event_type: str,
        payload: Dict[str, Any]
    ):
        """
        Publish event for orchestrator to process
        
        Args:
            db: Database session
            tenant_id: Tenant UUID
            event_type: Event type string
            payload: Event data
        """
        event = AgentEvent(
            tenant_id=tenant_id,
            event_type=event_type,
            payload=payload
        )
        
        db.add(event)
        await db.commit()
        
        logger.info(
            f"{self.agent_type}: Published event '{event_type}' "
            f"for tenant {tenant_id}"
        )
    
    async def log_audit(
        self,
        db: AsyncSession,
        tenant_id: str,
        action: str,
        entity_type: str,
        entity_id: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Log audit trail entry
        
        Args:
            db: Database session
            tenant_id: Tenant UUID
            action: Action performed
            entity_type: Type of entity
            entity_id: Entity UUID
            details: Additional details
        """
        audit = AuditTrail(
            client_id=tenant_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            actor_type='ai',
            actor_id=self.agent_type,
            details=details or {}
        )
        
        db.add(audit)
        await db.commit()
        
        logger.debug(
            f"{self.agent_type}: Logged audit: {action} on {entity_type} {entity_id}"
        )
    
    async def call_claude(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Call Claude API
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
        
        Returns:
            Claude's response text
        """
        if not self.client:
            raise Exception("Claude API not configured. Set ANTHROPIC_API_KEY.")
        
        messages = [{"role": "user", "content": prompt}]
        
        kwargs = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": messages
        }
        
        if system_prompt:
            kwargs["system"] = system_prompt
        
        logger.info(f"{self.agent_type}: Calling Claude API")
        
        message = self.client.messages.create(**kwargs)
        
        response_text = message.content[0].text
        
        logger.info(
            f"{self.agent_type}: Claude API response received "
            f"({len(response_text)} chars)"
        )
        
        return response_text
    
    async def execute_task(
        self,
        db: AsyncSession,
        task: AgentTask
    ) -> Dict[str, Any]:
        """
        Execute task - must be implemented by subclasses
        
        Args:
            db: Database session
            task: Task to execute
        
        Returns:
            Result dictionary
        """
        raise NotImplementedError(
            f"{self.agent_type} must implement execute_task()"
        )

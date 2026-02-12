"""
Task Auto-Marking Service - AI automatisk markering av oppgaver
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from uuid import UUID
from datetime import datetime

from app.models.task import Task, TaskStatus
from app.models.task_audit_log import TaskAuditLog, TaskAuditAction, TaskAuditResult


class TaskAutoMarkingService:
    """
    Service for automatically marking tasks as complete when AI completes actions
    
    Kobling mellom AI-handlinger og oppgaver:
    - Bankavstemming kjørt → mark "Bankavstemming" complete
    - Kundefordringer avstemt → mark "Avstemming kundefordringer" complete
    - Leverandørgjeld avstemt → mark "Avstemming leverandørgjeld" complete
    - Forskudd spesifisert → mark "Avstemming periodiseringer" complete
    - Alle fakturaer bokført → mark "Bokføring inngående fakturaer" complete
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def mark_bank_reconciliation_complete(
        self,
        client_id: UUID,
        period_year: int,
        period_month: int,
        difference: float,
        documentation_url: str
    ) -> Optional[Task]:
        """
        Mark bank reconciliation task as complete
        
        Args:
            client_id: Client ID
            period_year: Period year
            period_month: Period month
            difference: Reconciliation difference (0 = OK, != 0 = deviation)
            documentation_url: URL to reconciliation PDF
        
        Returns:
            Updated task or None if not found
        """
        # Find task
        task = await self._find_task(
            client_id=client_id,
            period_year=period_year,
            period_month=period_month,
            task_name_pattern="bankavstemming"
        )
        
        if not task:
            return None
        
        # Determine result
        if abs(difference) < 0.01:  # Essentially zero
            result = TaskAuditResult.OK
            status = TaskStatus.COMPLETED
            ai_comment = f"Bankavstemming fullført. Differanse: kr {difference:.2f} (OK)"
        else:
            result = TaskAuditResult.DEVIATION
            status = TaskStatus.DEVIATION
            ai_comment = f"Bankavstemming fullført med avvik. Differanse: kr {difference:.2f}"
        
        # Update task
        task.status = status
        task.completed_by = "AI"
        task.completed_at = datetime.utcnow()
        task.documentation_url = documentation_url
        task.ai_comment = ai_comment
        task.updated_at = datetime.utcnow()
        
        # Create audit log
        audit_log = TaskAuditLog(
            task_id=task.id,
            action=TaskAuditAction.AUTO_COMPLETED if result == TaskAuditResult.OK else TaskAuditAction.MARKED_DEVIATION,
            performed_by="AI-agent",
            performed_at=datetime.utcnow(),
            result=result,
            result_description=ai_comment,
            documentation_reference=documentation_url
        )
        self.db.add(audit_log)
        
        await self.db.commit()
        await self.db.refresh(task)
        
        return task
    
    async def mark_customer_receivables_complete(
        self,
        client_id: UUID,
        period_year: int,
        period_month: int,
        difference: float,
        documentation_url: str
    ) -> Optional[Task]:
        """Mark customer receivables (1500) reconciliation complete"""
        task = await self._find_task(
            client_id=client_id,
            period_year=period_year,
            period_month=period_month,
            task_name_pattern="kundefordringer"
        )
        
        if not task:
            return None
        
        return await self._mark_reconciliation_task(
            task=task,
            difference=difference,
            documentation_url=documentation_url,
            task_description="Kundefordringer (1500)"
        )
    
    async def mark_vendor_payables_complete(
        self,
        client_id: UUID,
        period_year: int,
        period_month: int,
        difference: float,
        documentation_url: str
    ) -> Optional[Task]:
        """Mark vendor payables (2400) reconciliation complete"""
        task = await self._find_task(
            client_id=client_id,
            period_year=period_year,
            period_month=period_month,
            task_name_pattern="leverandørgjeld"
        )
        
        if not task:
            return None
        
        return await self._mark_reconciliation_task(
            task=task,
            difference=difference,
            documentation_url=documentation_url,
            task_description="Leverandørgjeld (2400)"
        )
    
    async def mark_accruals_complete(
        self,
        client_id: UUID,
        period_year: int,
        period_month: int,
        difference: float,
        documentation_url: str
    ) -> Optional[Task]:
        """Mark accruals/prepayments reconciliation complete"""
        task = await self._find_task(
            client_id=client_id,
            period_year=period_year,
            period_month=period_month,
            task_name_pattern="periodisering"
        )
        
        if not task:
            return None
        
        return await self._mark_reconciliation_task(
            task=task,
            difference=difference,
            documentation_url=documentation_url,
            task_description="Periodiseringer"
        )
    
    async def mark_invoice_booking_complete(
        self,
        client_id: UUID,
        period_year: int,
        period_month: int,
        review_queue_count: int,
        documentation_url: str
    ) -> Optional[Task]:
        """
        Mark invoice booking task as complete
        
        Betingelse: Ingen fakturaer i Review Queue
        """
        task = await self._find_task(
            client_id=client_id,
            period_year=period_year,
            period_month=period_month,
            task_name_pattern="inngående fakturaer"
        )
        
        if not task:
            return None
        
        if review_queue_count == 0:
            result = TaskAuditResult.OK
            status = TaskStatus.COMPLETED
            ai_comment = "Alle inngående fakturaer bokført. Ingen fakturaer i Review Queue."
        else:
            result = TaskAuditResult.DEVIATION
            status = TaskStatus.DEVIATION
            ai_comment = f"Bokføring av inngående fakturaer fullført, men {review_queue_count} fakturaer krever manuell review."
        
        # Update task
        task.status = status
        task.completed_by = "AI"
        task.completed_at = datetime.utcnow()
        task.documentation_url = documentation_url
        task.ai_comment = ai_comment
        task.updated_at = datetime.utcnow()
        
        # Create audit log
        audit_log = TaskAuditLog(
            task_id=task.id,
            action=TaskAuditAction.AUTO_COMPLETED if result == TaskAuditResult.OK else TaskAuditAction.MARKED_DEVIATION,
            performed_by="AI-agent",
            performed_at=datetime.utcnow(),
            result=result,
            result_description=ai_comment,
            documentation_reference=documentation_url
        )
        self.db.add(audit_log)
        
        await self.db.commit()
        await self.db.refresh(task)
        
        return task
    
    async def _find_task(
        self,
        client_id: UUID,
        period_year: int,
        period_month: int,
        task_name_pattern: str
    ) -> Optional[Task]:
        """Find task by client, period, and name pattern"""
        query = select(Task).where(
            Task.client_id == client_id,
            Task.period_year == period_year,
            Task.period_month == period_month,
            Task.name.ilike(f"%{task_name_pattern}%")
        )
        
        result = await self.db.execute(query)
        task = result.scalars().first()
        
        return task
    
    async def _mark_reconciliation_task(
        self,
        task: Task,
        difference: float,
        documentation_url: str,
        task_description: str
    ) -> Task:
        """Generic reconciliation task marking"""
        # Determine result
        if abs(difference) < 0.01:  # Essentially zero
            result = TaskAuditResult.OK
            status = TaskStatus.COMPLETED
            ai_comment = f"{task_description} avstemt. Differanse: kr {difference:.2f} (OK)"
        else:
            result = TaskAuditResult.DEVIATION
            status = TaskStatus.DEVIATION
            ai_comment = f"{task_description} avstemt med avvik. Differanse: kr {difference:.2f}"
        
        # Update task
        task.status = status
        task.completed_by = "AI"
        task.completed_at = datetime.utcnow()
        task.documentation_url = documentation_url
        task.ai_comment = ai_comment
        task.updated_at = datetime.utcnow()
        
        # Create audit log
        audit_log = TaskAuditLog(
            task_id=task.id,
            action=TaskAuditAction.AUTO_COMPLETED if result == TaskAuditResult.OK else TaskAuditAction.MARKED_DEVIATION,
            performed_by="AI-agent",
            performed_at=datetime.utcnow(),
            result=result,
            result_description=ai_comment,
            documentation_reference=documentation_url
        )
        self.db.add(audit_log)
        
        await self.db.commit()
        await self.db.refresh(task)
        
        return task

"""
Orchestrator Agent - Koordinerer alle andre agenter
"""
import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.agents.base import BaseAgent
from app.models.agent_event import AgentEvent
from app.models.agent_task import AgentTask
from app.models.general_ledger import GeneralLedger
from app.models.vendor_invoice import VendorInvoice
from app.models.review_queue import ReviewQueue, ReviewPriority, ReviewStatus, IssueCategory

logger = logging.getLogger(__name__)


class OrchestratorAgent(BaseAgent):
    """
    Orkestrator-agent
    
    Ansvar:
    - Lytte på hendelser i systemet (agent_events tabell)
    - Opprette oppgaver for riktig spesialist-agent
    - Evaluere confidence-score og bestemme om noe trenger review
    - Prioritere Review Queue-elementer
    - Håndtere feil og retries
    """
    
    def __init__(self):
        super().__init__(agent_type="orchestrator")
        self.polling_interval = 30  # seconds
        self.running = False
    
    async def run(self, db: AsyncSession):
        """
        Main event loop - prosesser hendelser kontinuerlig
        
        Args:
            db: Database session
        """
        self.running = True
        logger.info("Orchestrator: Starting event loop")
        
        while self.running:
            try:
                events = await self.fetch_unprocessed_events(db)
                
                logger.info(f"Orchestrator: Found {len(events)} unprocessed events")
                
                for event in events:
                    try:
                        await self.handle_event(db, event)
                        await self.mark_processed(db, event.id)
                    except Exception as e:
                        logger.error(
                            f"Orchestrator: Error handling event {event.id}: {str(e)}",
                            exc_info=True
                        )
                        # Mark as processed to avoid infinite retry
                        await self.mark_processed(db, event.id)
                
                await asyncio.sleep(self.polling_interval)
                
            except Exception as e:
                logger.error(
                    f"Orchestrator: Error in event loop: {str(e)}",
                    exc_info=True
                )
                await asyncio.sleep(5)  # Brief pause before retry
    
    def stop(self):
        """Stop the event loop"""
        logger.info("Orchestrator: Stopping event loop")
        self.running = False
    
    async def fetch_unprocessed_events(
        self,
        db: AsyncSession,
        limit: int = 100
    ) -> list[AgentEvent]:
        """
        Fetch unprocessed events
        
        Args:
            db: Database session
            limit: Max events to fetch
        
        Returns:
            List of unprocessed events
        """
        result = await db.execute(
            select(AgentEvent)
            .where(AgentEvent.processed == False)
            .order_by(AgentEvent.created_at.asc())
            .limit(limit)
        )
        
        return result.scalars().all()
    
    async def mark_processed(self, db: AsyncSession, event_id: str):
        """Mark event as processed"""
        await db.execute(
            update(AgentEvent)
            .where(AgentEvent.id == event_id)
            .values(processed=True)
        )
        await db.commit()
        
        logger.debug(f"Orchestrator: Marked event {event_id} as processed")
    
    async def handle_event(self, db: AsyncSession, event: AgentEvent):
        """
        Handle event based on type
        
        Args:
            db: Database session
            event: Event to handle
        """
        logger.info(
            f"Orchestrator: Handling event {event.id} "
            f"(type={event.event_type}, tenant={event.tenant_id})"
        )
        
        event_type = event.event_type
        
        if event_type == "invoice_received":
            await self.handle_invoice_received(db, event)
        
        elif event_type == "invoice_parsed":
            await self.handle_invoice_parsed(db, event)
        
        elif event_type == "booking_completed":
            await self.handle_booking_completed(db, event)
        
        elif event_type == "correction_received":
            await self.handle_correction_received(db, event)
        
        elif event_type == "period_closing":
            await self.handle_period_closing(db, event)
        
        else:
            logger.warning(
                f"Orchestrator: Unknown event type '{event_type}' "
                f"for event {event.id}"
            )
    
    async def handle_invoice_received(
        self,
        db: AsyncSession,
        event: AgentEvent
    ):
        """
        Handle invoice_received event
        
        Creates task for invoice_parser agent to parse the invoice
        """
        payload = event.payload
        invoice_id = payload.get("invoice_id")
        
        if not invoice_id:
            logger.error(
                f"Orchestrator: invoice_received event {event.id} "
                "missing invoice_id"
            )
            return
        
        # Create parse task
        task = AgentTask(
            tenant_id=event.tenant_id,
            agent_type="invoice_parser",
            task_type="parse_invoice",
            payload={"invoice_id": invoice_id},
            priority=5
        )
        
        db.add(task)
        await db.commit()
        
        logger.info(
            f"Orchestrator: Created parse task {task.id} for invoice {invoice_id}"
        )
        
        await self.log_audit(
            db,
            tenant_id=event.tenant_id,
            action="task_created",
            entity_type="agent_task",
            entity_id=str(task.id),
            details={
                "agent_type": "invoice_parser",
                "task_type": "parse_invoice",
                "invoice_id": invoice_id
            }
        )
    
    async def handle_invoice_parsed(
        self,
        db: AsyncSession,
        event: AgentEvent
    ):
        """
        Handle invoice_parsed event
        
        Creates task for bookkeeper agent to create journal entry
        """
        payload = event.payload
        invoice_id = payload.get("invoice_id")
        
        if not invoice_id:
            logger.error(
                f"Orchestrator: invoice_parsed event {event.id} "
                "missing invoice_id"
            )
            return
        
        # Verify invoice is in parsed state
        result = await db.execute(
            select(VendorInvoice).where(VendorInvoice.id == invoice_id)
        )
        invoice = result.scalar_one_or_none()
        
        if not invoice:
            logger.error(
                f"Orchestrator: Invoice {invoice_id} not found"
            )
            return
        
        # Create booking task
        task = AgentTask(
            tenant_id=event.tenant_id,
            agent_type="bookkeeper",
            task_type="book_invoice",
            payload={"invoice_id": invoice_id},
            priority=5
        )
        
        db.add(task)
        await db.commit()
        
        logger.info(
            f"Orchestrator: Created booking task {task.id} for invoice {invoice_id}"
        )
        
        await self.log_audit(
            db,
            tenant_id=event.tenant_id,
            action="task_created",
            entity_type="agent_task",
            entity_id=str(task.id),
            details={
                "agent_type": "bookkeeper",
                "task_type": "book_invoice",
                "invoice_id": invoice_id
            }
        )
    
    async def handle_booking_completed(
        self,
        db: AsyncSession,
        event: AgentEvent
    ):
        """
        Handle booking_completed event
        
        Evaluates confidence and routes to auto-approve or review queue
        """
        payload = event.payload
        journal_entry_id = payload.get("journal_entry_id")
        
        if not journal_entry_id:
            logger.error(
                f"Orchestrator: booking_completed event {event.id} "
                "missing journal_entry_id"
            )
            return
        
        # Get journal entry
        result = await db.execute(
            select(GeneralLedger).where(GeneralLedger.id == journal_entry_id)
        )
        entry = result.scalar_one_or_none()
        
        if not entry:
            logger.error(
                f"Orchestrator: Journal entry {journal_entry_id} not found"
            )
            return
        
        # Evaluate and route based on confidence
        await self.evaluate_and_route(db, entry)
    
    async def evaluate_and_route(
        self,
        db: AsyncSession,
        entry: GeneralLedger
    ):
        """
        Evaluate confidence and route to auto-approve or review queue
        
        Args:
            db: Database session
            entry: Journal entry to evaluate
        """
        # Get confidence from first line (they should all have same confidence)
        # In real implementation, you'd calculate aggregate confidence
        confidence = 0
        reasoning = ""
        
        if entry.lines and len(entry.lines) > 0:
            confidence = entry.lines[0].ai_confidence_score or 0
            reasoning = entry.lines[0].ai_reasoning or ""
        
        logger.info(
            f"Orchestrator: Evaluating journal entry {entry.id} "
            f"(confidence={confidence}%)"
        )
        
        # Confidence thresholds (configurable per tenant in production)
        AUTO_APPROVE_THRESHOLD = 85
        MEDIUM_THRESHOLD = 60
        
        if confidence >= AUTO_APPROVE_THRESHOLD:
            # Auto-approve
            await self.auto_approve(db, entry)
            
        elif confidence >= MEDIUM_THRESHOLD:
            # Medium priority review
            await self.send_to_review(
                db,
                entry,
                priority=ReviewPriority.MEDIUM,
                confidence=confidence,
                reasoning=reasoning
            )
            
        else:
            # High priority review
            await self.send_to_review(
                db,
                entry,
                priority=ReviewPriority.HIGH,
                confidence=confidence,
                reasoning=reasoning
            )
    
    async def auto_approve(
        self,
        db: AsyncSession,
        entry: GeneralLedger
    ):
        """
        Auto-approve journal entry (high confidence)
        
        Args:
            db: Database session
            entry: Journal entry to approve
        """
        # Update entry status to posted
        await db.execute(
            update(GeneralLedger)
            .where(GeneralLedger.id == entry.id)
            .values(status='posted')
        )
        await db.commit()
        
        logger.info(
            f"Orchestrator: Auto-approved journal entry {entry.id}"
        )
        
        await self.log_audit(
            db,
            tenant_id=str(entry.client_id),
            action="auto_approved",
            entity_type="general_ledger",
            entity_id=str(entry.id),
            details={
                "voucher_number": entry.voucher_number,
                "confidence": entry.lines[0].ai_confidence_score if entry.lines else None
            }
        )
    
    async def send_to_review(
        self,
        db: AsyncSession,
        entry: GeneralLedger,
        priority: ReviewPriority,
        confidence: int,
        reasoning: str
    ):
        """
        Send journal entry to review queue
        
        Args:
            db: Database session
            entry: Journal entry
            priority: Review priority
            confidence: AI confidence score
            reasoning: AI reasoning
        """
        # Determine issue category based on confidence and reasoning
        if confidence < 40:
            issue_category = IssueCategory.LOW_CONFIDENCE
        elif "unknown vendor" in reasoning.lower():
            issue_category = IssueCategory.UNKNOWN_VENDOR
        elif "unusual amount" in reasoning.lower():
            issue_category = IssueCategory.UNUSUAL_AMOUNT
        else:
            issue_category = IssueCategory.LOW_CONFIDENCE
        
        # Create AI summary for accountant
        ai_summary = self._generate_review_summary(entry, confidence, reasoning)
        
        # Create review queue item
        review_item = ReviewQueue(
            client_id=entry.client_id,
            source_type="general_ledger",
            source_id=entry.id,
            priority=priority,
            status=ReviewStatus.PENDING,
            issue_category=issue_category,
            issue_description=f"Confidence {confidence}%: Needs review",
            ai_suggestion={"journal_entry_id": str(entry.id)},
            ai_confidence=confidence,
            ai_reasoning=reasoning
        )
        
        db.add(review_item)
        await db.commit()
        
        logger.info(
            f"Orchestrator: Sent journal entry {entry.id} to review queue "
            f"(priority={priority.value}, confidence={confidence}%)"
        )
        
        await self.log_audit(
            db,
            tenant_id=str(entry.client_id),
            action="sent_to_review",
            entity_type="general_ledger",
            entity_id=str(entry.id),
            details={
                "priority": priority.value,
                "confidence": confidence,
                "review_queue_id": str(review_item.id)
            }
        )
    
    def _generate_review_summary(
        self,
        entry: GeneralLedger,
        confidence: int,
        reasoning: str
    ) -> str:
        """Generate human-readable summary for accountant"""
        return (
            f"AI Confidence: {confidence}%\n\n"
            f"Voucher: {entry.voucher_series}-{entry.voucher_number}\n"
            f"Date: {entry.accounting_date}\n"
            f"Description: {entry.description}\n\n"
            f"AI Reasoning:\n{reasoning}"
        )
    
    async def handle_correction_received(
        self,
        db: AsyncSession,
        event: AgentEvent
    ):
        """
        Handle correction_received event
        
        Creates task for learning mechanism to update patterns
        """
        payload = event.payload
        correction_id = payload.get("correction_id")
        
        if not correction_id:
            logger.error(
                f"Orchestrator: correction_received event {event.id} "
                "missing correction_id"
            )
            return
        
        # Create learning task
        task = AgentTask(
            tenant_id=event.tenant_id,
            agent_type="learning",
            task_type="process_correction",
            payload={"correction_id": correction_id},
            priority=7  # Higher priority
        )
        
        db.add(task)
        await db.commit()
        
        logger.info(
            f"Orchestrator: Created learning task {task.id} "
            f"for correction {correction_id}"
        )
    
    async def handle_period_closing(
        self,
        db: AsyncSession,
        event: AgentEvent
    ):
        """
        Handle period_closing event
        
        Future: Check completeness, trigger reconciliation, etc.
        """
        logger.info(
            f"Orchestrator: Period closing event {event.id} "
            "(not implemented yet)"
        )
        # TODO: Implement period closing logic
        pass

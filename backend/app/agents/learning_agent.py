"""
Learning Agent - Lærer fra korreksjoner
"""
import json
import logging
from typing import Dict, Any, List, Optional
from decimal import Decimal
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.agents.base import BaseAgent
from app.models.agent_task import AgentTask
from app.models.correction import Correction
from app.models.agent_learned_pattern import AgentLearnedPattern
from app.models.general_ledger import GeneralLedger, GeneralLedgerLine
from app.models.vendor_invoice import VendorInvoice

logger = logging.getLogger(__name__)


class LearningAgent(BaseAgent):
    """
    Learning Agent
    
    Ansvar:
    - Prosessere korreksjoner fra regnskapsfører
    - Opprette/oppdatere mønstre basert på korreksjoner
    - Finne lignende feil som kan auto-korrigeres
    - Deaktivere mønstre med lav success rate
    """
    
    def __init__(self):
        super().__init__(agent_type="learning")
    
    async def execute_task(
        self,
        db: AsyncSession,
        task: AgentTask
    ) -> Dict[str, Any]:
        """
        Execute learning task
        
        Args:
            db: Database session
            task: Task to execute
        
        Returns:
            Result dictionary
        """
        task_type = task.task_type
        
        if task_type == "process_correction":
            return await self.process_correction(db, task)
        else:
            raise ValueError(
                f"Unknown task type for learning agent: {task_type}"
            )
    
    async def process_correction(
        self,
        db: AsyncSession,
        task: AgentTask
    ) -> Dict[str, Any]:
        """
        Process correction and learn pattern
        
        Args:
            db: Database session
            task: Task with correction_id in payload
        
        Returns:
            Result with pattern info
        """
        correction_id = task.payload.get("correction_id")
        
        if not correction_id:
            raise ValueError("process_correction task missing correction_id")
        
        # Get correction
        result = await db.execute(
            select(Correction).where(Correction.id == correction_id)
        )
        correction = result.scalar_one_or_none()
        
        if not correction:
            raise ValueError(f"Correction {correction_id} not found")
        
        # Get journal entry and invoice for context
        result = await db.execute(
            select(GeneralLedger).where(
                GeneralLedger.id == correction.journal_entry_id
            )
        )
        journal_entry = result.scalar_one_or_none()
        
        if not journal_entry:
            raise ValueError(
                f"Journal entry {correction.journal_entry_id} not found"
            )
        
        # Get invoice if this was from an invoice
        invoice = None
        if journal_entry.source_type == "ehf_invoice":
            result = await db.execute(
                select(VendorInvoice).where(
                    VendorInvoice.id == journal_entry.source_id
                )
            )
            invoice = result.scalar_one_or_none()
        
        # Analyze correction and create/update pattern
        pattern = await self.learn_pattern(
            db, correction, journal_entry, invoice
        )
        
        # Find similar entries that might have same error
        similar = await self.find_similar_entries(
            db, correction, journal_entry, invoice
        )
        
        logger.info(
            f"Learning: Processed correction {correction_id}, "
            f"found {len(similar)} similar entries"
        )
        
        return {
            "correction_id": str(correction.id),
            "pattern_id": str(pattern.id) if pattern else None,
            "similar_entries_count": len(similar),
            "similar_entry_ids": [str(e.id) for e in similar]
        }
    
    async def learn_pattern(
        self,
        db: AsyncSession,
        correction: Correction,
        journal_entry: GeneralLedger,
        invoice: Optional[VendorInvoice]
    ) -> Optional[AgentLearnedPattern]:
        """
        Create or update learned pattern from correction
        
        Args:
            db: Database session
            correction: Correction
            journal_entry: Journal entry that was corrected
            invoice: Invoice (if applicable)
        
        Returns:
            Created or updated pattern
        """
        # Determine pattern type and trigger
        pattern_type, trigger = self._analyze_correction(
            correction, journal_entry, invoice
        )
        
        if not pattern_type:
            logger.info(
                f"Learning: No pattern identified from correction "
                f"{correction.id}"
            )
            return None
        
        # Extract action from correction
        action = self._extract_action(correction)
        
        # Check if similar pattern exists
        result = await db.execute(
            select(AgentLearnedPattern).where(
                AgentLearnedPattern.pattern_type == pattern_type,
                AgentLearnedPattern.is_active == True
            )
        )
        existing_patterns = result.scalars().all()
        
        # Find matching pattern
        matching_pattern = None
        for p in existing_patterns:
            if self._triggers_match(p.trigger, trigger):
                matching_pattern = p
                break
        
        if matching_pattern:
            # Update existing pattern
            matching_pattern.times_correct += 1
            matching_pattern.times_applied += 1
            matching_pattern.updated_at = datetime.utcnow()
            
            await db.commit()
            await db.refresh(matching_pattern)
            
            logger.info(
                f"Learning: Updated pattern {matching_pattern.id} "
                f"(success_rate={float(matching_pattern.success_rate)*100:.1f}%)"
            )
            
            return matching_pattern
        
        else:
            # Create new pattern
            pattern = AgentLearnedPattern(
                pattern_type=pattern_type,
                pattern_name=self._generate_pattern_name(
                    pattern_type, trigger, action
                ),
                description=correction.correction_reason,
                trigger=trigger,
                action=action,
                applies_to_clients=[correction.tenant_id],
                global_pattern=False,
                success_rate=Decimal("1.0"),  # Start with 100%
                times_applied=1,
                times_correct=1,
                times_incorrect=0,
                confidence_boost=15,  # Default boost
                learned_from_user_id=correction.corrected_by
            )
            
            db.add(pattern)
            await db.commit()
            await db.refresh(pattern)
            
            logger.info(
                f"Learning: Created new pattern {pattern.id} "
                f"(type={pattern_type})"
            )
            
            return pattern
    
    def _analyze_correction(
        self,
        correction: Correction,
        journal_entry: GeneralLedger,
        invoice: Optional[VendorInvoice]
    ) -> tuple[Optional[str], Optional[Dict]]:
        """
        Analyze correction to determine pattern type and trigger
        
        Returns:
            (pattern_type, trigger) or (None, None) if no pattern
        """
        original = correction.original_entry
        corrected = correction.corrected_entry
        
        # If invoice-based, create vendor pattern
        if invoice and invoice.vendor_id:
            return (
                "vendor_account",
                {
                    "vendor_id": str(invoice.vendor_id),
                    "vendor_name": invoice.ai_booking_suggestion.get("vendor_name")
                    if invoice.ai_booking_suggestion else None
                }
            )
        
        # If description-based
        if correction.correction_reason:
            keywords = self._extract_keywords(correction.correction_reason)
            if keywords:
                return (
                    "description_keyword",
                    {
                        "keywords": keywords
                    }
                )
        
        # No clear pattern
        return None, None
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from correction reason"""
        # Simple extraction - could be enhanced with NLP
        words = text.lower().split()
        
        # Filter out common words
        stop_words = {
            "er", "er", "og", "i", "på", "til", "fra", "med", "for",
            "dette", "dette", "den", "det", "en", "et", "ikke"
        }
        
        keywords = [
            w for w in words
            if len(w) > 3 and w not in stop_words
        ]
        
        return keywords[:5]  # Max 5 keywords
    
    def _extract_action(self, correction: Correction) -> Dict:
        """
        Extract action (what to do) from correction
        
        Returns:
            Action dictionary
        """
        corrected = correction.corrected_entry
        
        # Extract account from corrected lines
        # Assumes first expense line is the main account
        account = None
        vat_code = None
        
        if "lines" in corrected:
            for line in corrected["lines"]:
                # Find expense account (not 2xxx)
                if not line.get("account", "").startswith("2"):
                    account = line.get("account")
                    vat_code = line.get("vat_code")
                    break
        
        return {
            "account": account,
            "vat_code": vat_code
        }
    
    def _triggers_match(self, trigger1: Dict, trigger2: Dict) -> bool:
        """Check if two triggers are essentially the same"""
        # Simple equality check - could be enhanced
        return trigger1 == trigger2
    
    def _generate_pattern_name(
        self,
        pattern_type: str,
        trigger: Dict,
        action: Dict
    ) -> str:
        """Generate human-readable pattern name"""
        if pattern_type == "vendor_account":
            vendor_name = trigger.get("vendor_name", "Unknown")
            account = action.get("account", "")
            return f"{vendor_name} → {account}"
        
        elif pattern_type == "description_keyword":
            keywords = trigger.get("keywords", [])
            account = action.get("account", "")
            return f"{', '.join(keywords[:2])} → {account}"
        
        return f"{pattern_type} pattern"
    
    async def find_similar_entries(
        self,
        db: AsyncSession,
        correction: Correction,
        journal_entry: GeneralLedger,
        invoice: Optional[VendorInvoice]
    ) -> List[GeneralLedger]:
        """
        Find similar journal entries that might have the same error
        
        Args:
            db: Database session
            correction: Correction
            journal_entry: Corrected journal entry
            invoice: Invoice (if applicable)
        
        Returns:
            List of similar entries
        """
        # Base query: same client, not reversed, in review
        query = select(GeneralLedger).where(
            GeneralLedger.client_id == correction.tenant_id,
            GeneralLedger.is_reversed == False,
            GeneralLedger.status == "draft"
        )
        
        # If invoice-based, find same vendor
        if invoice and invoice.vendor_id:
            # Find other invoices from same vendor
            result = await db.execute(
                select(VendorInvoice.id).where(
                    VendorInvoice.client_id == invoice.client_id,
                    VendorInvoice.vendor_id == invoice.vendor_id,
                    VendorInvoice.id != invoice.id
                )
            )
            invoice_ids = [row[0] for row in result.all()]
            
            if invoice_ids:
                query = query.where(
                    GeneralLedger.source_type == "ehf_invoice",
                    GeneralLedger.source_id.in_(invoice_ids)
                )
        
        # Limit to prevent processing too many
        query = query.limit(10)
        
        result = await db.execute(query)
        similar = result.scalars().all()
        
        logger.info(
            f"Learning: Found {len(similar)} similar entries for "
            f"correction {correction.id}"
        )
        
        return similar

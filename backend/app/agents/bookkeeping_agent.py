"""
Bookkeeping Agent - AI-ekspert på bokføring
"""
import json
import logging
from typing import Dict, Any, List, Optional
from decimal import Decimal
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.agents.base import BaseAgent
from app.models.agent_task import AgentTask
from app.models.vendor_invoice import VendorInvoice
from app.models.vendor import Vendor
from app.models.general_ledger import GeneralLedger, GeneralLedgerLine
from app.models.agent_learned_pattern import AgentLearnedPattern
from app.models.chart_of_accounts import Account

logger = logging.getLogger(__name__)


class BookkeepingAgent(BaseAgent):
    """
    Bokførings-agent
    
    Ansvar:
    - Lese parsede fakturadata fra DB
    - Sjekke patterns-tabellen for lærte regler
    - Velge debet/kredit-konti basert på leverandør, beskrivelse, beløp
    - Beregne MVA korrekt
    - Opprette journal entry (bilag)
    - Generere confidence-score med begrunnelse
    - Markere usikkerhetsmomenter
    """
    
    def __init__(self):
        super().__init__(agent_type="bookkeeper")
        
        # System prompt for Norwegian accounting
        self.system_prompt = """Du er en ekspert norsk regnskapsfører.

Du bruker norsk kontoplan (NS 4102) og kjenner MVA-regler.

Vanlige utgiftskonti:
- 4000-4099: Varekjøp
- 4005: Kontorrekvisita
- 6000-6099: Varekostnad
- 6100-6199: Lønn og honorarer
- 6300-6399: Kontorkostnader (husleie, strøm, telefon, etc.)
- 6500-6599: Reise
- 6700-6799: Markedsføring
- 6810-6899: Telekommunikasjon

MVA-konti:
- 2740: Inngående MVA (fradragsberettiget)
- 2700: Utgående MVA

Gjeld:
- 2400-2499: Leverandørgjeld

REGLER:
1. Alle bilag MÅ balansere: SUM(debet) = SUM(kredit)
2. MVA-kode 5 = 25%, kode 3 = 15%, kode 0 = fritatt
3. Inngående MVA (2740) er fradragsberettiget MVA på kjøp
4. Leverandørgjeld (2400) er alltid kredit (skylder penger)

Returner ALLTID gyldig JSON."""
    
    async def execute_task(
        self,
        db: AsyncSession,
        task: AgentTask
    ) -> Dict[str, Any]:
        """
        Execute bookkeeping task
        
        Args:
            db: Database session
            task: Task to execute
        
        Returns:
            Result dictionary with journal_entry_id
        """
        task_type = task.task_type
        
        if task_type == "book_invoice":
            return await self.book_invoice(db, task)
        else:
            raise ValueError(
                f"Unknown task type for bookkeeper: {task_type}"
            )
    
    async def book_invoice(
        self,
        db: AsyncSession,
        task: AgentTask
    ) -> Dict[str, Any]:
        """
        Create journal entry for invoice
        
        Args:
            db: Database session
            task: Task with invoice_id in payload
        
        Returns:
            Result with journal_entry_id
        """
        invoice_id = task.payload.get("invoice_id")
        
        if not invoice_id:
            raise ValueError("book_invoice task missing invoice_id")
        
        # Get invoice
        result = await db.execute(
            select(VendorInvoice).where(VendorInvoice.id == invoice_id)
        )
        invoice = result.scalar_one_or_none()
        
        if not invoice:
            raise ValueError(f"Invoice {invoice_id} not found")
        
        # Get vendor
        vendor = None
        if invoice.vendor_id:
            result = await db.execute(
                select(Vendor).where(Vendor.id == invoice.vendor_id)
            )
            vendor = result.scalar_one_or_none()
        
        # Get learned patterns
        patterns = await self.get_applicable_patterns(db, invoice, vendor)
        
        # Generate booking with AI
        booking_data = await self.generate_booking(
            invoice, vendor, patterns
        )
        
        # Create journal entry
        journal_entry = await self.create_journal_entry(
            db, task.tenant_id, invoice, booking_data
        )
        
        # Publish booking_completed event
        await self.publish_event(
            db,
            tenant_id=task.tenant_id,
            event_type="booking_completed",
            payload={
                "journal_entry_id": str(journal_entry.id),
                "invoice_id": str(invoice.id)
            }
        )
        
        # Log audit
        await self.log_audit(
            db,
            tenant_id=task.tenant_id,
            action="booking_created",
            entity_type="general_ledger",
            entity_id=str(journal_entry.id),
            details={
                "invoice_id": str(invoice.id),
                "confidence": booking_data["confidence_score"]
            }
        )
        
        return {
            "journal_entry_id": str(journal_entry.id),
            "confidence": booking_data["confidence_score"]
        }
    
    async def get_applicable_patterns(
        self,
        db: AsyncSession,
        invoice: VendorInvoice,
        vendor: Optional[Vendor]
    ) -> List[AgentLearnedPattern]:
        """
        Get learned patterns that might apply to this invoice
        
        Args:
            db: Database session
            invoice: Invoice to check
            vendor: Vendor (optional)
        
        Returns:
            List of applicable patterns
        """
        # Query active patterns for this client
        query = select(AgentLearnedPattern).where(
            AgentLearnedPattern.is_active == True
        )
        
        # Filter by patterns that apply to this client
        # (global patterns or client-specific)
        query = query.where(
            (AgentLearnedPattern.global_pattern == True) |
            (AgentLearnedPattern.applies_to_clients.contains([invoice.client_id]))
        )
        
        result = await db.execute(query)
        all_patterns = result.scalars().all()
        
        # Filter patterns that match trigger conditions
        applicable = []
        
        for pattern in all_patterns:
            if self._pattern_matches(pattern, invoice, vendor):
                applicable.append(pattern)
        
        logger.info(
            f"Bookkeeper: Found {len(applicable)} applicable patterns "
            f"for invoice {invoice.id}"
        )
        
        return applicable
    
    def _pattern_matches(
        self,
        pattern: AgentLearnedPattern,
        invoice: VendorInvoice,
        vendor: Optional[Vendor]
    ) -> bool:
        """
        Check if pattern trigger matches invoice
        
        Args:
            pattern: Pattern to check
            invoice: Invoice
            vendor: Vendor
        
        Returns:
            True if pattern matches
        """
        trigger = pattern.trigger
        
        # Vendor match
        if "vendor_id" in trigger:
            if not vendor or str(vendor.id) != trigger["vendor_id"]:
                return False
        
        # Description contains
        if "description_contains" in trigger:
            keywords = trigger["description_contains"]
            if isinstance(keywords, str):
                keywords = [keywords]
            
            # Check if any keyword matches
            invoice_desc = (invoice.ai_booking_suggestion or {}).get("description", "")
            if not any(kw.lower() in invoice_desc.lower() for kw in keywords):
                return False
        
        # Amount range
        if "amount_range" in trigger:
            amount_range = trigger["amount_range"]
            amount = float(invoice.amount_excl_vat)
            
            if "min" in amount_range and amount < amount_range["min"]:
                return False
            if "max" in amount_range and amount > amount_range["max"]:
                return False
        
        return True
    
    async def generate_booking(
        self,
        invoice: VendorInvoice,
        vendor: Optional[Vendor],
        patterns: List[AgentLearnedPattern]
    ) -> Dict[str, Any]:
        """
        Generate booking suggestion using AI + patterns
        
        Args:
            invoice: Invoice to book
            vendor: Vendor (optional)
            patterns: Applicable learned patterns
        
        Returns:
            Booking data with lines, confidence, reasoning
        """
        # Build context from patterns
        patterns_context = ""
        if patterns:
            patterns_context = "\n\nLÆRTE MØNSTRE (bruk disse hvis de passer):\n"
            for p in patterns:
                patterns_context += f"""
Mønster: {p.pattern_name or p.pattern_type}
- Success rate: {float(p.success_rate) * 100:.1f}%
- Action: {json.dumps(p.action, ensure_ascii=False)}
"""
        
        # Build prompt
        prompt = f"""Analyser denne leverandørfakturaen og lag bilag (journal entry).

FAKTURA:
- Leverandør: {vendor.name if vendor else 'Ukjent'}
- Fakturanummer: {invoice.invoice_number}
- Beløp eks. MVA: {invoice.amount_excl_vat} NOK
- MVA beløp: {invoice.vat_amount} NOK
- Totalt: {invoice.total_amount} NOK
- Beskrivelse: {invoice.ai_booking_suggestion.get('description') if invoice.ai_booking_suggestion else ''}

{patterns_context}

Lag et balansert bilag (debet = kredit).

Returner JSON:
{{
    "lines": [
        {{
            "account": "6300",
            "account_name": "Kontorkostnader",
            "debit": 1000.00,
            "credit": 0,
            "vat_code": "5",
            "description": "Kontorrekvisita"
        }},
        {{
            "account": "2740",
            "account_name": "Inngående MVA",
            "debit": 250.00,
            "credit": 0,
            "vat_code": null,
            "description": "MVA 25%"
        }},
        {{
            "account": "2400",
            "account_name": "Leverandørgjeld",
            "debit": 0,
            "credit": 1250.00,
            "vat_code": null,
            "description": "{vendor.name if vendor else 'Leverandørgjeld'}"
        }}
    ],
    "confidence_score": 85,
    "reasoning": "Jeg valgte konto 6300 fordi..."
}}

HUSK:
1. Debet = Credit (balansert!)
2. Inngående MVA (2740) = {invoice.vat_amount} NOK
3. Leverandørgjeld (2400) = {invoice.total_amount} NOK (credit)
"""
        
        # Call Claude
        response_text = await self.call_claude(prompt, self.system_prompt)
        
        # Parse JSON response
        try:
            # Extract JSON from response (in case Claude adds explanation)
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            json_str = response_text[json_start:json_end]
            
            booking_data = json.loads(json_str)
            
            # Adjust confidence based on patterns
            if patterns:
                # Boost confidence if high-success pattern matched
                best_pattern = max(patterns, key=lambda p: p.success_rate)
                if best_pattern.success_rate > 0.9:
                    booking_data["confidence_score"] = min(
                        99,
                        booking_data["confidence_score"] + best_pattern.confidence_boost
                    )
                    booking_data["reasoning"] += (
                        f"\n\n[Pattern boost: +{best_pattern.confidence_boost}% "
                        f"fra mønster '{best_pattern.pattern_name}' "
                        f"med {float(best_pattern.success_rate)*100:.0f}% success rate]"
                    )
            
            # Validate balance
            total_debit = sum(
                Decimal(str(line.get("debit", 0)))
                for line in booking_data["lines"]
            )
            total_credit = sum(
                Decimal(str(line.get("credit", 0)))
                for line in booking_data["lines"]
            )
            
            if abs(total_debit - total_credit) > Decimal("0.01"):
                logger.warning(
                    f"Bookkeeper: Unbalanced entry! "
                    f"Debit={total_debit}, Credit={total_credit}"
                )
                booking_data["confidence_score"] = min(
                    booking_data["confidence_score"],
                    40  # Low confidence for unbalanced
                )
                booking_data["reasoning"] += "\n\n[WARNING: Entry is unbalanced!]"
            
            return booking_data
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(
                f"Bookkeeper: Failed to parse AI response: {e}\n"
                f"Response: {response_text}"
            )
            
            # Fallback: simple booking
            return self._generate_fallback_booking(invoice)
    
    def _generate_fallback_booking(
        self,
        invoice: VendorInvoice
    ) -> Dict[str, Any]:
        """
        Generate simple fallback booking when AI fails
        
        Args:
            invoice: Invoice to book
        
        Returns:
            Simple booking data
        """
        logger.warning(
            f"Bookkeeper: Using fallback booking for invoice {invoice.id}"
        )
        
        return {
            "lines": [
                {
                    "account": "6300",
                    "account_name": "Kontorkostnader",
                    "debit": float(invoice.amount_excl_vat),
                    "credit": 0,
                    "vat_code": "5",
                    "description": "Diverse utgifter (automatisk)"
                },
                {
                    "account": "2740",
                    "account_name": "Inngående MVA",
                    "debit": float(invoice.vat_amount),
                    "credit": 0,
                    "vat_code": None,
                    "description": "MVA"
                },
                {
                    "account": "2400",
                    "account_name": "Leverandørgjeld",
                    "debit": 0,
                    "credit": float(invoice.total_amount),
                    "vat_code": None,
                    "description": "Leverandørgjeld"
                }
            ],
            "confidence_score": 30,
            "reasoning": (
                "Automatisk generert fallback-bokføring. "
                "AI kunne ikke analysere fakturaen. "
                "Krever manuell gjennomgang."
            )
        }
    
    async def create_journal_entry(
        self,
        db: AsyncSession,
        tenant_id: str,
        invoice: VendorInvoice,
        booking_data: Dict[str, Any]
    ) -> GeneralLedger:
        """
        Create journal entry in database
        
        Args:
            db: Database session
            tenant_id: Tenant UUID
            invoice: Invoice
            booking_data: Booking data from AI
        
        Returns:
            Created GeneralLedger entry
        """
        # Get next voucher number (simple increment - in production, use sequence)
        result = await db.execute(
            select(GeneralLedger)
            .where(GeneralLedger.client_id == tenant_id)
            .order_by(GeneralLedger.created_at.desc())
            .limit(1)
        )
        last_entry = result.scalar_one_or_none()
        
        if last_entry and last_entry.voucher_number:
            try:
                next_number = int(last_entry.voucher_number) + 1
            except ValueError:
                next_number = 1
        else:
            next_number = 1
        
        # Create journal entry
        entry = GeneralLedger(
            client_id=tenant_id,
            entry_date=datetime.utcnow().date(),
            accounting_date=invoice.invoice_date,
            period=invoice.invoice_date.strftime("%Y-%m"),
            fiscal_year=invoice.invoice_date.year,
            voucher_number=str(next_number),
            voucher_series="A",
            description=f"Faktura {invoice.invoice_number}",
            source_type="ehf_invoice",
            source_id=invoice.id,
            created_by_type="ai_agent",
            created_by_id=None,  # Could store agent session ID
            status="draft"  # Will be posted after review/approval
        )
        
        db.add(entry)
        await db.flush()  # Get entry.id
        
        # Create lines
        confidence = booking_data.get("confidence_score", 0)
        reasoning = booking_data.get("reasoning", "")
        
        for i, line_data in enumerate(booking_data.get("lines", []), start=1):
            line = GeneralLedgerLine(
                general_ledger_id=entry.id,
                line_number=i,
                account_number=line_data.get("account", "6300"),
                debit_amount=Decimal(str(line_data.get("debit", 0))),
                credit_amount=Decimal(str(line_data.get("credit", 0))),
                vat_code=line_data.get("vat_code"),
                vat_amount=Decimal(str(line_data.get("vat_amount", 0))),
                line_description=line_data.get("description", ""),
                ai_confidence_score=confidence,
                ai_reasoning=reasoning if i == 1 else None  # Only first line
            )
            db.add(line)
        
        await db.commit()
        await db.refresh(entry)
        
        logger.info(
            f"Bookkeeper: Created journal entry {entry.id} "
            f"for invoice {invoice.id} (confidence={confidence}%)"
        )
        
        return entry

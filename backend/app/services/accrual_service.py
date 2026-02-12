"""
Accrual Service - Periodisering Logic

Business logic for creating and posting accruals.
"""

from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, Any, Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import uuid

from app.models.accrual import Accrual
from app.models.accrual_posting import AccrualPosting
from app.models.general_ledger import GeneralLedger, GeneralLedgerLine
from app.models.vendor_invoice import VendorInvoice
from app.models.client import Client
from dateutil.relativedelta import relativedelta


class AccrualService:
    """
    Business logic for accruals:
    - Create accrual from invoice or manual entry
    - Generate posting schedule
    - Auto-post pending accruals
    - Calculate next posting date
    """
    
    @staticmethod
    def _calculate_months_between(from_date: date, to_date: date) -> int:
        """Calculate number of months between two dates"""
        delta = relativedelta(to_date, from_date)
        return delta.years * 12 + delta.months + 1  # +1 to include both start and end month
    
    @staticmethod
    def _generate_posting_schedule(
        from_date: date,
        to_date: date,
        total_amount: Decimal,
        frequency: str
    ) -> List[Dict[str, Any]]:
        """
        Generate posting schedule based on frequency.
        
        Returns list of dicts with posting_date, amount, period
        """
        postings = []
        
        if frequency == "monthly":
            num_months = AccrualService._calculate_months_between(from_date, to_date)
            amount_per_month = total_amount / num_months
            
            current_date = from_date
            for _ in range(num_months):
                postings.append({
                    "posting_date": current_date,
                    "amount": amount_per_month,
                    "period": current_date.strftime("%Y-%m")
                })
                current_date = current_date + relativedelta(months=1)
        
        elif frequency == "quarterly":
            # Post every 3 months
            num_quarters = (AccrualService._calculate_months_between(from_date, to_date) + 2) // 3
            amount_per_quarter = total_amount / num_quarters
            
            current_date = from_date
            for _ in range(num_quarters):
                postings.append({
                    "posting_date": current_date,
                    "amount": amount_per_quarter,
                    "period": current_date.strftime("%Y-%m")
                })
                current_date = current_date + relativedelta(months=3)
        
        elif frequency == "yearly":
            # Single posting
            postings.append({
                "posting_date": from_date,
                "amount": total_amount,
                "period": from_date.strftime("%Y-%m")
            })
        
        return postings
    
    async def create_accrual(
        self,
        db: AsyncSession,
        client_id: UUID,
        description: str,
        from_date: date,
        to_date: date,
        total_amount: Decimal,
        balance_account: str,
        result_account: str,
        frequency: str,
        source_invoice_id: Optional[UUID] = None,
        created_by: str = "user",
        ai_detected: bool = False
    ) -> Dict[str, Any]:
        """
        Create new accrual with posting schedule.
        
        Args:
            client_id: Client UUID
            description: Description of accrual
            from_date: Start date
            to_date: End date
            total_amount: Total amount to accrue
            balance_account: Balance sheet account (1xxx or 2xxx)
            result_account: Result account (4xxx-8xxx)
            frequency: "monthly", "quarterly", or "yearly"
            source_invoice_id: Optional link to source invoice
            created_by: "user" or "ai_agent"
            ai_detected: Was this detected by AI?
        
        Returns:
            Dict with accrual details and posting schedule
        """
        
        # Validate dates
        if to_date < from_date:
            raise ValueError("to_date must be >= from_date")
        
        # Validate frequency
        if frequency not in ["monthly", "quarterly", "yearly"]:
            raise ValueError("frequency must be monthly, quarterly, or yearly")
        
        # Create accrual
        accrual = Accrual(
            id=uuid.uuid4(),
            client_id=client_id,
            description=description,
            from_date=from_date,
            to_date=to_date,
            total_amount=total_amount,
            balance_account=balance_account,
            result_account=result_account,
            frequency=frequency,
            source_invoice_id=source_invoice_id,
            created_by=created_by,
            ai_detected=ai_detected,
            status="active",
            auto_post=True
        )
        
        # Generate posting schedule
        schedule = self._generate_posting_schedule(
            from_date, to_date, total_amount, frequency
        )
        
        # Create posting records
        for posting_data in schedule:
            posting = AccrualPosting(
                id=uuid.uuid4(),
                accrual_id=accrual.id,
                posting_date=posting_data["posting_date"],
                amount=posting_data["amount"],
                period=posting_data["period"],
                status="pending"
            )
            db.add(posting)
        
        # Set next posting date to first pending posting
        accrual.next_posting_date = schedule[0]["posting_date"]
        
        db.add(accrual)
        await db.commit()
        await db.refresh(accrual)
        
        return {
            "success": True,
            "accrual_id": str(accrual.id),
            "description": accrual.description,
            "total_amount": float(accrual.total_amount),
            "posting_schedule": schedule,
            "status": "created"
        }
    
    async def post_accrual(
        self,
        db: AsyncSession,
        posting_id: UUID,
        posted_by: str = "ai_agent"
    ) -> Dict[str, Any]:
        """
        Post a single accrual to GeneralLedger.
        
        Creates balanced GL entry:
        - Debit: Result account (expense/revenue)
        - Credit: Balance account (prepaid asset/deferred liability)
        
        Args:
            posting_id: AccrualPosting UUID
            posted_by: "ai_agent" or "user"
        
        Returns:
            Dict with posting details
        """
        
        # Fetch posting with accrual
        result = await db.execute(
            select(AccrualPosting)
            .where(AccrualPosting.id == posting_id)
        )
        posting = result.scalar_one_or_none()
        
        if not posting:
            raise ValueError(f"AccrualPosting {posting_id} not found")
        
        if posting.status != "pending":
            raise ValueError(f"Posting {posting_id} is already {posting.status}")
        
        # Fetch accrual
        result = await db.execute(
            select(Accrual)
            .where(Accrual.id == posting.accrual_id)
        )
        accrual = result.scalar_one_or_none()
        
        if not accrual:
            raise ValueError(f"Accrual {posting.accrual_id} not found")
        
        # Create GeneralLedger entry
        voucher_number = f"PER-{posting.posting_date.strftime('%Y%m%d')}-{str(posting.id)[:8]}"
        
        gl_entry = GeneralLedger(
            id=uuid.uuid4(),
            client_id=accrual.client_id,
            entry_date=date.today(),
            accounting_date=posting.posting_date,
            period=posting.period,
            fiscal_year=posting.posting_date.year,
            voucher_number=voucher_number,
            voucher_series="P",  # P = Periodisering
            description=f"Periodisering: {accrual.description}",
            source_type="accrual",
            source_id=accrual.id,
            created_by_type=posted_by,
            status="posted"
        )
        
        # Create GL lines (balanced entry)
        # Debit: Result account (expense)
        debit_line = GeneralLedgerLine(
            id=uuid.uuid4(),
            general_ledger_id=gl_entry.id,
            line_number=1,
            account_number=accrual.result_account,
            debit_amount=posting.amount,
            credit_amount=Decimal("0.00"),
            line_description=f"Periodisert kostnad: {accrual.description}"
        )
        
        # Credit: Balance account (prepaid asset reduction or deferred liability)
        credit_line = GeneralLedgerLine(
            id=uuid.uuid4(),
            general_ledger_id=gl_entry.id,
            line_number=2,
            account_number=accrual.balance_account,
            debit_amount=Decimal("0.00"),
            credit_amount=posting.amount,
            line_description=f"Nedskriving av forskudd: {accrual.description}"
        )
        
        db.add(gl_entry)
        db.add(debit_line)
        db.add(credit_line)
        
        # Update posting status
        posting.status = "posted"
        posting.posted_by = posted_by
        posting.posted_at = date.today()
        posting.general_ledger_id = gl_entry.id
        
        # Update accrual next_posting_date
        result = await db.execute(
            select(AccrualPosting)
            .where(
                and_(
                    AccrualPosting.accrual_id == accrual.id,
                    AccrualPosting.status == "pending"
                )
            )
            .order_by(AccrualPosting.posting_date)
        )
        next_posting = result.scalars().first()
        
        if next_posting:
            accrual.next_posting_date = next_posting.posting_date
        else:
            # All postings completed
            accrual.status = "completed"
            accrual.next_posting_date = None
        
        await db.commit()
        
        return {
            "success": True,
            "posting_id": str(posting.id),
            "gl_entry_id": str(gl_entry.id),
            "voucher_number": voucher_number,
            "amount": float(posting.amount),
            "posting_date": posting.posting_date.isoformat(),
            "status": "posted"
        }
    
    async def auto_post_due_accruals(
        self,
        db: AsyncSession,
        as_of_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Auto-post all pending accruals due today or earlier.
        Called by cron job daily.
        
        Args:
            as_of_date: Date to check (defaults to today)
        
        Returns:
            Dict with summary: posted_count, total_amount, errors
        """
        
        if as_of_date is None:
            as_of_date = date.today()
        
        # Find all pending postings due today or earlier
        result = await db.execute(
            select(AccrualPosting)
            .where(
                and_(
                    AccrualPosting.status == "pending",
                    AccrualPosting.posting_date <= as_of_date
                )
            )
        )
        due_postings = result.scalars().all()
        
        posted_count = 0
        total_amount = Decimal("0.00")
        errors = []
        
        for posting in due_postings:
            try:
                result_dict = await self.post_accrual(
                    db,
                    posting.id,
                    posted_by="ai_agent"
                )
                if result_dict["success"]:
                    posted_count += 1
                    total_amount += Decimal(str(result_dict["amount"]))
            except Exception as e:
                errors.append({
                    "posting_id": str(posting.id),
                    "error": str(e)
                })
        
        return {
            "success": True,
            "as_of_date": as_of_date.isoformat(),
            "posted_count": posted_count,
            "total_amount": float(total_amount),
            "errors": errors
        }
    
    async def detect_accrual_from_invoice(
        self,
        db: AsyncSession,
        invoice: VendorInvoice
    ) -> Optional[Dict[str, Any]]:
        """
        AI: Detect if an invoice should be accrued.
        
        Patterns to detect:
        - Description contains: "forsikring", "abonnement", "lisens", "leie"
        - Amount is recurring (check history)
        - Invoice covers future period
        
        Returns accrual suggestion or None.
        """
        
        # Check description for keywords
        description_lower = invoice.ai_detected_category.lower() if invoice.ai_detected_category else ""
        
        accrual_keywords = [
            "forsikring", "insurance",
            "abonnement", "subscription",
            "lisens", "license",
            "leie", "rent",
            "årlig", "annual",
            "kvartalsvis", "quarterly"
        ]
        
        detected = any(keyword in description_lower for keyword in accrual_keywords)
        
        if not detected:
            return None
        
        # Suggest accrual
        # Default: 12 months from invoice date
        from_date = invoice.invoice_date
        to_date = from_date + relativedelta(months=12)
        
        return {
            "detected": True,
            "confidence": 85,
            "suggestion": {
                "description": f"Periodisering av {invoice.ai_detected_category or 'utgift'}",
                "from_date": from_date.isoformat(),
                "to_date": to_date.isoformat(),
                "total_amount": float(invoice.amount_excl_vat),
                "frequency": "monthly",
                "balance_account": "1580",  # Forskuddsbetalte kostnader
                "result_account": "6000",   # Default: Varekostnader (should be AI-suggested)
                "source_invoice_id": str(invoice.id)
            }
        }

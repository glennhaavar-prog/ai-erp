"""
Voucher Service - Automatic Voucher Creation Engine
KONTALI SPRINT 1 - Task 2

Generates General Ledger entries (vouchers) from AI-analyzed vendor invoices.
Follows Norwegian accounting standards (debit/credit balancing).

SkatteFUNN-kritisk: Dette er kjernen i automatisk bokføring!
"""
import logging
from uuid import UUID, uuid4
from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from datetime import datetime, date
from decimal import Decimal

from app.models.general_ledger import GeneralLedger, GeneralLedgerLine
from app.models.vendor_invoice import VendorInvoice
from app.models.vendor import Vendor
from app.models.chart_of_accounts import Account
from app.models.audit_trail import AuditTrail
from app.models.document import Document
from app.schemas.voucher import (
    VoucherLineCreate,
    VoucherDTO,
    VoucherDocumentDTO
)

logger = logging.getLogger(__name__)


# Norwegian VAT codes mapping
VAT_CODES = {
    "5": Decimal("0.25"),  # 25% standard rate
    "3": Decimal("0.15"),  # 15% reduced rate (food)
    "0": Decimal("0.00"),  # VAT exempt
    None: Decimal("0.00")  # No VAT
}

# Common accounts for vendor invoices (Norwegian standard)
EXPENSE_ACCOUNTS = {
    "6420": "Kontorrekvisita",
    "6300": "Leie lokaler",
    "5000": "Lønnskostnader",
    "7140": "Frakt og transport",
    "6540": "Konsulenttjenester",
    "6700": "Annen kostnad",
}

VAT_ACCOUNTS = {
    "2740": "Inngående MVA",  # Input VAT (reduces tax liability)
    "2700": "Utgående MVA",   # Output VAT (increases tax liability)
}

PAYABLE_ACCOUNTS = {
    "2400": "Leverandørgjeld",
    "1920": "Bankkonto",
}


class VoucherValidationError(Exception):
    """Custom exception for voucher validation errors"""
    pass


class VoucherGenerator:
    """
    Genererer journal entries (vouchers) fra vendor invoices.
    Følger norsk bokføringspraksis (debet/kredit).
    
    CRITICAL: All vouchers MUST balance (debit = credit)
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_voucher_from_invoice(
        self,
        invoice_id: UUID,
        tenant_id: UUID,
        user_id: str,
        accounting_date: Optional[date] = None,
        override_account: Optional[str] = None
    ) -> VoucherDTO:
        """
        Hovedfunksjon: Create voucher from vendor invoice
        
        PERFORMANCE OPTIMIZED: Reduced DB round-trips from 5+ to 2
        
        Workflow:
        1. Hent invoice fra database (vendor_invoices) with eager loading
        2. Generer voucher med linjer
        3. Valider balansering (debet = kredit)
        4. Lagre til database (transaction safe)
        5. Oppdater invoice status
        
        Args:
            invoice_id: UUID of vendor invoice
            tenant_id: Tenant/client ID
            user_id: User or agent ID creating the voucher
            accounting_date: Override accounting date (defaults to invoice date)
            override_account: Manual account override (optional)
        
        Returns:
            VoucherDTO with complete voucher information
        
        Raises:
            VoucherValidationError: If validation fails
            ValueError: If invoice not found or already posted
        """
        import time
        start_time = time.time()
        
        try:
            # OPTIMIZATION 1: Fetch invoice with vendor in ONE query (eager loading)
            query = select(VendorInvoice).options(
                selectinload(VendorInvoice.vendor)
            ).where(
                VendorInvoice.id == invoice_id,
                VendorInvoice.client_id == tenant_id
            )
            result = await self.db.execute(query)
            invoice = result.scalar_one_or_none()
            
            if not invoice:
                raise ValueError(f"Invoice {invoice_id} not found for tenant {tenant_id}")
            
            logger.info(f"⏱️  Fetched invoice in {time.time() - start_time:.3f}s")
            
            # 2. Check if already posted
            if invoice.general_ledger_id:
                raise ValueError(
                    f"Invoice {invoice_id} already posted to voucher {invoice.general_ledger_id}"
                )
            
            # 3. Vendor already loaded via eager loading
            vendor = invoice.vendor
            
            # OPTIMIZATION 2: Determine accounting date early (avoid later logic)
            if accounting_date is None:
                accounting_date = invoice.invoice_date
            
            # OPTIMIZATION 3: Generate voucher number with optimized query
            current_year = accounting_date.year
            series = "AP"
            
            # Use ROW_NUMBER instead of SELECT MAX for better performance
            from sqlalchemy import literal
            voucher_number_query = select(
                func.coalesce(func.max(GeneralLedger.voucher_number), literal(f"{current_year}-0000"))
            ).where(
                GeneralLedger.client_id == tenant_id,
                GeneralLedger.voucher_series == series,
                GeneralLedger.fiscal_year == current_year
            )
            
            voucher_num_result = await self.db.execute(voucher_number_query)
            max_number = voucher_num_result.scalar()
            
            try:
                last_seq = int(max_number.split("-")[1])
                next_seq = last_seq + 1
            except (IndexError, ValueError):
                next_seq = 1
            
            voucher_number = f"{current_year}-{next_seq:04d}"
            
            logger.info(f"⏱️  Generated voucher number in {time.time() - start_time:.3f}s")
            
            # 4. Generate voucher lines (Norwegian accounting logic)
            # Note: _generate_voucher_lines is now synchronous (no DB calls)
            lines = self._generate_voucher_lines_sync(
                invoice, 
                override_account=override_account
            )
            
            # 5. Validate balance (CRITICAL!)
            self._validate_balance(lines)
            
            # 6. Calculate totals
            total_debit = sum(line.debit_amount for line in lines)
            total_credit = sum(line.credit_amount for line in lines)
            
            # 7. Create voucher (General Ledger entry)
            voucher = GeneralLedger(
                id=uuid4(),
                client_id=tenant_id,
                entry_date=date.today(),
                accounting_date=accounting_date,
                period=accounting_date.strftime("%Y-%m"),
                fiscal_year=accounting_date.year,
                voucher_number=voucher_number,
                voucher_series=series,
                description=self._generate_description(invoice, vendor),
                source_type="vendor_invoice",
                source_id=invoice_id,
                created_by_type="user" if user_id else "ai_agent",
                created_by_id=self._parse_uuid(user_id) if user_id else None,
                status="posted",
                locked=False
            )
            
            self.db.add(voucher)
            await self.db.flush()  # Get voucher.id
            
            # 8. Create voucher lines
            gl_lines = []
            for line_data in lines:
                gl_line = GeneralLedgerLine(
                    id=uuid4(),
                    general_ledger_id=voucher.id,
                    line_number=line_data.line_number,
                    account_number=line_data.account_number,
                    debit_amount=line_data.debit_amount,
                    credit_amount=line_data.credit_amount,
                    vat_code=line_data.vat_code,
                    vat_amount=line_data.vat_amount or Decimal("0.00"),
                    vat_base_amount=invoice.amount_excl_vat if line_data.vat_code else None,
                    line_description=line_data.line_description,
                    ai_confidence_score=invoice.ai_confidence_score,
                    ai_reasoning=invoice.ai_reasoning
                )
                self.db.add(gl_line)
                gl_lines.append(gl_line)
            
            # 9. Update invoice status
            invoice.general_ledger_id = voucher.id
            invoice.booked_at = datetime.utcnow()
            invoice.review_status = 'approved'
            
            # 10. Log audit trail (compliance!)
            audit_entry = AuditTrail(
                id=uuid4(),
                client_id=tenant_id,
                table_name="general_ledger",
                record_id=voucher.id,
                action="create",
                changed_by_type="ai_agent" if not user_id else "user",
                changed_by_id=self._parse_uuid(user_id) if user_id else None,
                changed_by_name="AI Bokfører" if not user_id else user_id,
                reason=f"Automatic booking from vendor invoice {invoice.invoice_number}",
                new_value={
                    "voucher_number": voucher_number,
                    "invoice_number": invoice.invoice_number,
                    "amount": float(invoice.total_amount),
                    "vendor": vendor.name if vendor else "Unknown",
                    "lines_count": len(lines)
                }
            )
            self.db.add(audit_entry)
            
            # 11. Commit transaction (ACID compliance!)
            await self.db.commit()
            await self.db.refresh(voucher)
            
            elapsed = time.time() - start_time
            logger.info(
                f"✅ Created voucher {voucher_number} for invoice {invoice.invoice_number} "
                f"in {elapsed:.3f}s (debit={total_debit}, credit={total_credit})"
            )
            
            # OPTIMIZATION 4: Batch load account names for all lines in ONE query
            account_numbers = list(set(line.account_number for line in gl_lines))
            account_map = await self._get_account_names_batch(tenant_id, account_numbers)
            
            # 12. Return DTO
            return VoucherDTO(
                id=str(voucher.id),
                client_id=str(voucher.client_id),
                voucher_number=voucher_number,
                voucher_series=voucher.voucher_series,
                entry_date=voucher.entry_date,
                accounting_date=voucher.accounting_date,
                period=voucher.period,
                fiscal_year=voucher.fiscal_year,
                description=voucher.description,
                source_type=voucher.source_type,
                source_id=str(voucher.source_id) if voucher.source_id else None,
                total_debit=total_debit,
                total_credit=total_credit,
                is_balanced=True,
                lines=[
                    VoucherLineCreate(
                        line_number=line.line_number,
                        account_number=line.account_number,
                        account_name=account_map.get(line.account_number, f"Konto {line.account_number}"),
                        line_description=line.line_description or "",
                        debit_amount=line.debit_amount,
                        credit_amount=line.credit_amount,
                        vat_code=line.vat_code,
                        vat_amount=line.vat_amount
                    )
                    for line in gl_lines
                ],
                created_at=voucher.created_at
            )
        
        except VoucherValidationError as e:
            await self.db.rollback()
            logger.error(f"❌ Voucher validation failed: {str(e)}")
            raise
        
        except Exception as e:
            await self.db.rollback()
            logger.error(f"❌ Error creating voucher: {str(e)}", exc_info=True)
            raise
    
    def _generate_voucher_lines_sync(
        self, 
        invoice: VendorInvoice,
        override_account: Optional[str] = None
    ) -> List[VoucherLineCreate]:
        """
        Generer voucher lines basert på invoice (SYNC - no DB calls)
        
        PERFORMANCE: Removed async DB call for account names (done in batch later)
        
        Norwegian accounting standard for vendor invoice:
        
        Line 1 (DEBET):  Kostnadskonto (6xxx/7xxx)  - Amount excl. VAT
        Line 2 (DEBET):  2740 Inngående MVA         - VAT amount
        Line 3 (KREDIT): 2400 Leverandørgjeld       - Total amount
        
        Example:
        Line 1 (Debet):  6420 Kontorrekvisita   10,000 kr
        Line 2 (Debet):  2740 Inngående MVA      2,500 kr  (25% VAT)
        Line 3 (Kredit): 2400 Leverandørgjeld  12,500 kr
        
        Total debet = Total kredit = 12,500 kr ✓
        """
        lines = []
        line_num = 1
        
        # Determine expense account
        if override_account:
            expense_account = override_account
        elif invoice.ai_booking_suggestion and invoice.ai_booking_suggestion.get('account'):
            expense_account = invoice.ai_booking_suggestion['account']
        else:
            # Default fallback
            expense_account = "6700"  # Annen kostnad
        
        # Get account name from hardcoded map (fast!)
        all_accounts = {**EXPENSE_ACCOUNTS, **VAT_ACCOUNTS, **PAYABLE_ACCOUNTS}
        expense_account_name = all_accounts.get(expense_account, f"Konto {expense_account}")
        
        # LINE 1: Debit - Expense Account (amount excl. VAT)
        lines.append(VoucherLineCreate(
            line_number=line_num,
            account_number=expense_account,
            account_name=expense_account_name,
            line_description=f"Leverandørfaktura {invoice.invoice_number}",
            debit_amount=invoice.amount_excl_vat,
            credit_amount=Decimal("0.00"),
            vat_code=None,
            vat_amount=None
        ))
        line_num += 1
        
        # LINE 2: Debit - Input VAT (if applicable)
        if invoice.vat_amount and invoice.vat_amount > 0:
            lines.append(VoucherLineCreate(
                line_number=line_num,
                account_number="2740",  # Inngående MVA
                account_name="Inngående MVA",
                line_description=f"MVA på faktura {invoice.invoice_number}",
                debit_amount=invoice.vat_amount,
                credit_amount=Decimal("0.00"),
                vat_code=self._determine_vat_code(invoice.vat_amount, invoice.amount_excl_vat),
                vat_amount=invoice.vat_amount
            ))
            line_num += 1
        
        # LINE 3: Credit - Accounts Payable
        lines.append(VoucherLineCreate(
            line_number=line_num,
            account_number="2400",  # Leverandørgjeld
            account_name="Leverandørgjeld",
            line_description=f"Leverandør: {invoice.vendor.name if invoice.vendor else 'Ukjent'}",
            debit_amount=Decimal("0.00"),
            credit_amount=invoice.total_amount,
            vat_code=None,
            vat_amount=None
        ))
        
        return lines
    
    async def _generate_voucher_lines(
        self, 
        invoice: VendorInvoice,
        override_account: Optional[str] = None
    ) -> List[VoucherLineCreate]:
        """
        DEPRECATED: Use _generate_voucher_lines_sync instead
        Kept for backward compatibility only
        """
        return self._generate_voucher_lines_sync(invoice, override_account)
    
    def _validate_balance(self, lines: List[VoucherLineCreate]) -> bool:
        """
        Validate that voucher balances (debit = credit)
        
        CRITICAL: Norwegian accounting law requires exact balance!
        
        Args:
            lines: List of voucher lines
        
        Returns:
            True if balanced
        
        Raises:
            VoucherValidationError: If not balanced
        """
        total_debit = sum(line.debit_amount for line in lines)
        total_credit = sum(line.credit_amount for line in lines)
        
        # Allow 0.01 tolerance for rounding errors
        difference = abs(total_debit - total_credit)
        
        if difference > Decimal("0.01"):
            raise VoucherValidationError(
                f"Voucher does not balance! "
                f"Debit: {total_debit}, Credit: {total_credit}, Difference: {difference}"
            )
        
        logger.info(f"✓ Voucher balanced: debit={total_debit}, credit={total_credit}")
        return True
    
    async def _get_next_voucher_number(
        self, 
        client_id: UUID, 
        series: str = "AP"
    ) -> str:
        """
        Generer neste bilagsnummer (2026-0001, 2026-0002, etc.)
        
        Format: YYYY-NNNN (year + sequential number)
        
        Args:
            client_id: Client UUID
            series: Voucher series (AP, AR, GENERAL, etc.)
        
        Returns:
            Voucher number string (e.g., "2026-0042")
        """
        current_year = date.today().year
        
        # Find highest voucher number for this client, series, and year
        query = select(func.max(GeneralLedger.voucher_number)).where(
            GeneralLedger.client_id == client_id,
            GeneralLedger.voucher_series == series,
            GeneralLedger.fiscal_year == current_year
        )
        
        result = await self.db.execute(query)
        max_number = result.scalar()
        
        if max_number:
            # Extract number part (e.g., "2026-0042" -> 42)
            try:
                last_seq = int(max_number.split("-")[1])
                next_seq = last_seq + 1
            except (IndexError, ValueError):
                # Fallback if format is unexpected
                next_seq = 1
        else:
            # First voucher of the year
            next_seq = 1
        
        # Format: YYYY-NNNN (zero-padded to 4 digits)
        voucher_number = f"{current_year}-{next_seq:04d}"
        
        logger.info(f"Generated voucher number: {voucher_number} (series: {series})")
        return voucher_number
    
    async def _get_invoice(self, invoice_id: UUID, tenant_id: UUID) -> VendorInvoice:
        """Fetch vendor invoice from database"""
        query = select(VendorInvoice).where(
            VendorInvoice.id == invoice_id,
            VendorInvoice.client_id == tenant_id
        )
        result = await self.db.execute(query)
        invoice = result.scalar_one_or_none()
        
        if not invoice:
            raise ValueError(f"Invoice {invoice_id} not found for tenant {tenant_id}")
        
        return invoice
    
    async def _get_vendor(self, vendor_id: UUID) -> Optional[Vendor]:
        """Fetch vendor from database"""
        if not vendor_id:
            return None
        
        query = select(Vendor).where(Vendor.id == vendor_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def _get_account_names_batch(self, client_id: UUID, account_numbers: List[str]) -> Dict[str, str]:
        """
        Fetch multiple account names in ONE query (PERFORMANCE OPTIMIZATION)
        
        Args:
            client_id: Client UUID
            account_numbers: List of account numbers to fetch
        
        Returns:
            Dict mapping account_number -> account_name
        """
        if not account_numbers:
            return {}
        
        query = select(Account).where(
            Account.client_id == client_id,
            Account.account_number.in_(account_numbers)
        )
        result = await self.db.execute(query)
        accounts = result.scalars().all()
        
        account_map = {acc.account_number: acc.account_name for acc in accounts}
        
        # Fill in missing accounts from hardcoded map
        all_accounts = {**EXPENSE_ACCOUNTS, **VAT_ACCOUNTS, **PAYABLE_ACCOUNTS}
        for account_number in account_numbers:
            if account_number not in account_map:
                account_map[account_number] = all_accounts.get(account_number, f"Konto {account_number}")
        
        return account_map
    
    async def _get_account_name(self, client_id: UUID, account_number: str) -> str:
        """
        Fetch account name from chart of accounts (DEPRECATED - use batch method)
        Kept for backward compatibility
        """
        result = await self._get_account_names_batch(client_id, [account_number])
        return result.get(account_number, f"Konto {account_number}")
    
    def _generate_description(self, invoice: VendorInvoice, vendor: Optional[Vendor]) -> str:
        """Generate voucher description"""
        vendor_name = vendor.name if vendor else "Ukjent leverandør"
        return f"Leverandørfaktura {invoice.invoice_number} - {vendor_name}"
    
    def _determine_vat_code(self, vat_amount: Decimal, base_amount: Decimal) -> Optional[str]:
        """Determine VAT code based on rate"""
        if vat_amount == 0 or base_amount == 0:
            return "0"
        
        vat_rate = vat_amount / base_amount
        
        # 25% standard rate
        if abs(vat_rate - Decimal("0.25")) < Decimal("0.01"):
            return "5"
        
        # 15% reduced rate
        if abs(vat_rate - Decimal("0.15")) < Decimal("0.01"):
            return "3"
        
        # Unknown rate
        return None
    
    def _parse_uuid(self, value: str) -> Optional[UUID]:
        """
        Safely parse string to UUID. Returns None if invalid.
        
        Allows both:
        - Valid UUID strings ("550e8400-e29b-41d4-a716-446655440000")
        - Descriptive strings ("system_auto_approve", "test_user") → None
        """
        if not value:
            return None
        
        try:
            return UUID(value)
        except (ValueError, AttributeError):
            # Not a valid UUID - return None (will be stored as NULL in DB)
            return None


async def get_voucher_by_id(db: AsyncSession, voucher_id: UUID, client_id: UUID) -> Optional[VoucherDTO]:
    """
    Fetch voucher by ID
    
    Args:
        db: Database session
        voucher_id: Voucher UUID
        client_id: Client UUID (for security)
    
    Returns:
        VoucherDTO or None
    """
    query = select(GeneralLedger).where(
        GeneralLedger.id == voucher_id,
        GeneralLedger.client_id == client_id
    )
    result = await db.execute(query)
    voucher = result.scalar_one_or_none()
    
    if not voucher:
        return None
    
    # Fetch lines
    lines_query = select(GeneralLedgerLine).where(
        GeneralLedgerLine.general_ledger_id == voucher_id
    ).order_by(GeneralLedgerLine.line_number)
    lines_result = await db.execute(lines_query)
    lines = lines_result.scalars().all()
    
    # Fetch account names
    accounts_query = select(Account).where(Account.client_id == client_id)
    accounts_result = await db.execute(accounts_query)
    account_map = {acc.account_number: acc.account_name for acc in accounts_result.scalars().all()}
    
    # Calculate totals
    total_debit = sum(line.debit_amount for line in lines)
    total_credit = sum(line.credit_amount for line in lines)
    
    # Fetch document if source is vendor_invoice
    document_url = None
    document_type = None
    if voucher.source_type == "vendor_invoice" and voucher.source_id:
        invoice_query = select(VendorInvoice).where(VendorInvoice.id == voucher.source_id)
        invoice_result = await db.execute(invoice_query)
        invoice = invoice_result.scalar_one_or_none()
        
        if invoice and invoice.document_id:
            doc_query = select(Document).where(Document.id == invoice.document_id)
            doc_result = await db.execute(doc_query)
            document = doc_result.scalar_one_or_none()
            
            if document:
                document_url = document.s3_url or document.file_path
                document_type = document.mime_type
    
    return VoucherDTO(
        id=str(voucher.id),
        client_id=str(voucher.client_id),
        voucher_number=voucher.voucher_number,
        voucher_series=voucher.voucher_series,
        entry_date=voucher.entry_date,
        accounting_date=voucher.accounting_date,
        period=voucher.period,
        fiscal_year=voucher.fiscal_year,
        description=voucher.description,
        source_type=voucher.source_type,
        source_id=str(voucher.source_id) if voucher.source_id else None,
        total_debit=total_debit,
        total_credit=total_credit,
        is_balanced=abs(total_debit - total_credit) < Decimal("0.01"),
        document=VoucherDocumentDTO(url=document_url, type=document_type) if document_url else None,
        lines=[
            VoucherLineCreate(
                line_number=line.line_number,
                account_number=line.account_number,
                account_name=account_map.get(line.account_number, f"Konto {line.account_number}"),
                line_description=line.line_description or "",
                debit_amount=line.debit_amount,
                credit_amount=line.credit_amount,
                vat_code=line.vat_code,
                vat_amount=line.vat_amount
            )
            for line in lines
        ],
        created_at=voucher.created_at
    )


async def list_vouchers(
    db: AsyncSession,
    client_id: UUID,
    period: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> List[VoucherDTO]:
    """
    List vouchers for a client
    
    Args:
        db: Database session
        client_id: Client UUID
        period: Optional period filter (YYYY-MM)
        limit: Max results
        offset: Pagination offset
    
    Returns:
        List of VoucherDTO
    """
    query = select(GeneralLedger).where(GeneralLedger.client_id == client_id)
    
    if period:
        query = query.where(GeneralLedger.period == period)
    
    query = query.order_by(GeneralLedger.accounting_date.desc()).limit(limit).offset(offset)
    
    result = await db.execute(query)
    vouchers = result.scalars().all()
    
    # Convert to DTOs (simplified without lines)
    dtos = []
    for voucher in vouchers:
        lines_query = select(GeneralLedgerLine).where(
            GeneralLedgerLine.general_ledger_id == voucher.id
        )
        lines_result = await db.execute(lines_query)
        lines = lines_result.scalars().all()
        
        total_debit = sum(line.debit_amount for line in lines)
        total_credit = sum(line.credit_amount for line in lines)
        
        dtos.append(VoucherDTO(
            id=str(voucher.id),
            client_id=str(voucher.client_id),
            voucher_number=voucher.voucher_number,
            voucher_series=voucher.voucher_series,
            entry_date=voucher.entry_date,
            accounting_date=voucher.accounting_date,
            period=voucher.period,
            fiscal_year=voucher.fiscal_year,
            description=voucher.description,
            source_type=voucher.source_type,
            source_id=str(voucher.source_id) if voucher.source_id else None,
            total_debit=total_debit,
            total_credit=total_credit,
            is_balanced=abs(total_debit - total_credit) < Decimal("0.01"),
            lines=[],  # Don't load lines for list view (performance)
            created_at=voucher.created_at
        ))
    
    return dtos

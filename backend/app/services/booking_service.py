"""
Booking Service
Creates General Ledger entries from AI suggestions
"""
import logging
from uuid import UUID, uuid4
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from decimal import Decimal

from app.models.general_ledger import GeneralLedger, GeneralLedgerLine
from app.models.vendor_invoice import VendorInvoice
from app.models.vendor import Vendor

logger = logging.getLogger(__name__)


async def book_vendor_invoice(
    db: AsyncSession,
    invoice_id: UUID,
    booking_suggestion: Dict[str, Any],
    created_by_type: str = "ai_agent",
    created_by_id: UUID = None
) -> Dict[str, Any]:
    """
    Create General Ledger entries from a vendor invoice
    
    Args:
        db: Database session
        invoice_id: UUID of VendorInvoice
        booking_suggestion: AI suggestion with 'lines' array
        created_by_type: 'ai_agent' or 'user'
        created_by_id: user_id or agent_session_id
    
    Returns:
        {
            'success': True/False,
            'general_ledger_id': str,
            'voucher_number': str,
            'lines_count': int,
            'error': str (if failed)
        }
    """
    try:
        # 1. Fetch invoice
        query = select(VendorInvoice).where(VendorInvoice.id == invoice_id)
        result = await db.execute(query)
        invoice = result.scalar_one_or_none()
        
        if not invoice:
            logger.error(f"Invoice {invoice_id} not found")
            return {
                'success': False,
                'error': 'Invoice not found'
            }
        
        # 2. Check if already booked
        if invoice.general_ledger_id:
            logger.warning(f"Invoice {invoice_id} already booked to GL {invoice.general_ledger_id}")
            return {
                'success': False,
                'error': 'Invoice already booked'
            }
        
        # 3. Generate voucher number
        voucher_number = await _generate_voucher_number(db, invoice.client_id)
        
        # 4. Extract booking lines
        lines = booking_suggestion.get('lines', [])
        if not lines:
            logger.error(f"No booking lines in suggestion for invoice {invoice_id}")
            return {
                'success': False,
                'error': 'No booking lines in AI suggestion'
            }
        
        # 5. Validate balance (debits = credits)
        total_debit = sum(Decimal(str(line.get('debit', 0))) for line in lines)
        total_credit = sum(Decimal(str(line.get('credit', 0))) for line in lines)
        
        if total_debit != total_credit:
            logger.error(f"Booking not balanced: debit={total_debit}, credit={total_credit}")
            return {
                'success': False,
                'error': f'Booking not balanced: debit {total_debit} != credit {total_credit}'
            }
        
        # 6. Create General Ledger entry
        gl_entry = GeneralLedger(
            id=uuid4(),
            client_id=invoice.client_id,
            entry_date=datetime.now().date(),
            accounting_date=invoice.invoice_date,
            period=invoice.invoice_date.strftime("%Y-%m"),
            fiscal_year=invoice.invoice_date.year,
            voucher_number=voucher_number,
            voucher_series="AP",  # AP = Accounts Payable (Leverandørfaktura)
            description=f"Leverandørfaktura {invoice.invoice_number} - {invoice.vendor.name if invoice.vendor else 'Ukjent leverandør'}",
            source_type="vendor_invoice",
            source_id=invoice.id,
            created_by_type=created_by_type,
            created_by_id=created_by_id,
            status="posted",
            locked=False
        )
        
        db.add(gl_entry)
        
        # 7. Create General Ledger lines
        for idx, line in enumerate(lines, start=1):
            gl_line = GeneralLedgerLine(
                id=uuid4(),
                general_ledger_id=gl_entry.id,
                line_number=idx,
                account_number=str(line.get('account', '')),
                debit_amount=Decimal(str(line.get('debit', 0))),
                credit_amount=Decimal(str(line.get('credit', 0))),
                vat_code=str(line.get('vat_code', '')) if line.get('vat_code') else None,
                vat_amount=Decimal(str(line.get('vat_amount', 0))) if line.get('vat_amount') else Decimal(0),
                line_description=line.get('description', ''),
                ai_confidence_score=booking_suggestion.get('confidence'),
                ai_reasoning=booking_suggestion.get('reasoning')
            )
            db.add(gl_line)
        
        # 8. Link invoice to general ledger
        invoice.general_ledger_id = gl_entry.id
        invoice.booked_at = datetime.utcnow()
        invoice.review_status = 'auto_approved'
        
        await db.commit()
        await db.refresh(gl_entry)
        
        logger.info(f"Successfully booked invoice {invoice_id} to GL {gl_entry.id}, voucher {voucher_number}")
        
        return {
            'success': True,
            'general_ledger_id': str(gl_entry.id),
            'voucher_number': f"{gl_entry.voucher_series}-{voucher_number}",
            'lines_count': len(lines)
        }
    
    except Exception as e:
        logger.error(f"Error booking invoice {invoice_id}: {str(e)}", exc_info=True)
        await db.rollback()
        return {
            'success': False,
            'error': str(e)
        }


async def _generate_voucher_number(db: AsyncSession, client_id: UUID) -> str:
    """
    Generate next voucher number for client
    
    Format: Sequential number per client (1, 2, 3, ...)
    """
    # Find highest existing voucher number for this client
    query = select(GeneralLedger).where(
        GeneralLedger.client_id == client_id,
        GeneralLedger.voucher_series == "AP"
    ).order_by(GeneralLedger.voucher_number.desc()).limit(1)
    
    result = await db.execute(query)
    last_entry = result.scalar_one_or_none()
    
    if last_entry:
        try:
            last_number = int(last_entry.voucher_number)
            next_number = last_number + 1
        except ValueError:
            # Fallback if voucher_number is not numeric
            next_number = 1
    else:
        next_number = 1
    
    return str(next_number).zfill(6)  # Zero-padded to 6 digits: 000001, 000002, etc.


async def reverse_general_ledger_entry(
    db: AsyncSession,
    gl_entry_id: UUID,
    reason: str,
    created_by_type: str = "user",
    created_by_id: UUID = None
) -> Dict[str, Any]:
    """
    Reverse a General Ledger entry (create opposite entry for correction)
    
    Args:
        db: Database session
        gl_entry_id: UUID of GeneralLedger entry to reverse
        reason: Why this is being reversed
        created_by_type: 'user' or 'ai_agent'
        created_by_id: user_id or agent_session_id
    
    Returns:
        {
            'success': True/False,
            'reversal_entry_id': str,
            'error': str (if failed)
        }
    """
    try:
        # 1. Fetch original entry with lines
        query = select(GeneralLedger).where(GeneralLedger.id == gl_entry_id)
        result = await db.execute(query)
        original_entry = result.scalar_one_or_none()
        
        if not original_entry:
            return {'success': False, 'error': 'Original entry not found'}
        
        if original_entry.is_reversed:
            return {'success': False, 'error': 'Entry already reversed'}
        
        if original_entry.locked:
            return {'success': False, 'error': 'Entry is locked (period closed)'}
        
        # 2. Create reversal entry
        reversal_voucher = await _generate_voucher_number(db, original_entry.client_id)
        
        reversal_entry = GeneralLedger(
            id=uuid4(),
            client_id=original_entry.client_id,
            entry_date=datetime.now().date(),
            accounting_date=datetime.now().date(),
            period=datetime.now().strftime("%Y-%m"),
            fiscal_year=datetime.now().year,
            voucher_number=reversal_voucher,
            voucher_series="AP",
            description=f"REVERSERING: {original_entry.description}",
            source_type="reversal",
            source_id=original_entry.id,
            created_by_type=created_by_type,
            created_by_id=created_by_id,
            status="posted"
        )
        
        db.add(reversal_entry)
        
        # 3. Create opposite lines (swap debit/credit)
        for line in original_entry.lines:
            reversal_line = GeneralLedgerLine(
                id=uuid4(),
                general_ledger_id=reversal_entry.id,
                line_number=line.line_number,
                account_number=line.account_number,
                debit_amount=line.credit_amount,  # SWAP
                credit_amount=line.debit_amount,  # SWAP
                vat_code=line.vat_code,
                vat_amount=-line.vat_amount if line.vat_amount else Decimal(0),
                line_description=f"Reversering: {line.line_description}"
            )
            db.add(reversal_line)
        
        # 4. Mark original as reversed
        original_entry.is_reversed = True
        original_entry.reversed_by_entry_id = reversal_entry.id
        original_entry.reversal_reason = reason
        
        await db.commit()
        
        logger.info(f"Reversed GL entry {gl_entry_id}, created reversal {reversal_entry.id}")
        
        return {
            'success': True,
            'reversal_entry_id': str(reversal_entry.id),
            'voucher_number': f"{reversal_entry.voucher_series}-{reversal_voucher}"
        }
    
    except Exception as e:
        logger.error(f"Error reversing GL entry {gl_entry_id}: {str(e)}", exc_info=True)
        await db.rollback()
        return {'success': False, 'error': str(e)}

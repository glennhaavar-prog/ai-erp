"""
Voucher Journal API Routes - Bilagsjournal
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from typing import List, Optional
from datetime import date, datetime
from decimal import Decimal
import uuid

from app.database import get_db
from app.models.general_ledger import GeneralLedger, GeneralLedgerLine

router = APIRouter(prefix="/voucher-journal", tags=["voucher_journal"])


@router.get("/")
async def get_voucher_journal(
    client_id: uuid.UUID,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    voucher_type: Optional[str] = None,
    account_number: Optional[str] = None,
    amount_min: Optional[float] = None,
    amount_max: Optional[float] = None,
    search: Optional[str] = None,
    limit: int = Query(100, le=1000),
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """
    Get voucher journal (bilagsjournal) with comprehensive filters
    
    Returns chronological list of all journal entries (vouchers).
    """
    query = select(GeneralLedger).where(GeneralLedger.client_id == client_id)
    
    # Apply filters
    if date_from:
        query = query.where(GeneralLedger.accounting_date >= date_from)
    
    if date_to:
        query = query.where(GeneralLedger.accounting_date <= date_to)
    
    if voucher_type:
        query = query.where(GeneralLedger.voucher_type == voucher_type)
    
    if account_number:
        # Filter by vouchers that have lines with this account
        query = query.join(GeneralLedgerLine).where(
            GeneralLedgerLine.account_number == account_number
        ).distinct()
    
    if search:
        # Search in description, voucher number, external reference
        search_pattern = f"%{search}%"
        query = query.where(
            or_(
                GeneralLedger.description.ilike(search_pattern),
                GeneralLedger.voucher_number.ilike(search_pattern),
                GeneralLedger.external_reference.ilike(search_pattern)
            )
        )
    
    # Order by accounting_date DESC, then voucher_number DESC (newest first)
    query = query.order_by(
        desc(GeneralLedger.accounting_date),
        desc(GeneralLedger.voucher_number)
    )
    
    # Get total count for pagination
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total_count = total_result.scalar()
    
    # Apply pagination
    query = query.limit(limit).offset(offset)
    
    result = await db.execute(query)
    vouchers = result.scalars().all()
    
    # Build response with summary data
    journal_entries = []
    
    for voucher in vouchers:
        # Get lines for this voucher
        lines_query = (
            select(GeneralLedgerLine)
            .where(GeneralLedgerLine.general_ledger_id == voucher.id)
            .order_by(GeneralLedgerLine.line_number)
        )
        lines_result = await db.execute(lines_query)
        lines = lines_result.scalars().all()
        
        # Calculate totals
        total_debit = sum(line.debit_amount for line in lines)
        total_credit = sum(line.credit_amount for line in lines)
        
        # Apply amount filters if specified
        if amount_min is not None and float(total_debit) < amount_min:
            continue
        if amount_max is not None and float(total_debit) > amount_max:
            continue
        
        voucher_dict = voucher.to_dict()
        voucher_dict["total_debit"] = float(total_debit)
        voucher_dict["total_credit"] = float(total_credit)
        voucher_dict["balanced"] = abs(total_debit - total_credit) < Decimal("0.01")
        voucher_dict["line_count"] = len(lines)
        
        journal_entries.append(voucher_dict)
    
    return {
        "entries": journal_entries,
        "total_count": total_count,
        "returned_count": len(journal_entries),
        "limit": limit,
        "offset": offset,
    }


@router.get("/{voucher_id}")
async def get_voucher_detail(
    voucher_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get full detail of a single voucher including all lines
    """
    # Get voucher
    voucher_query = select(GeneralLedger).where(GeneralLedger.id == voucher_id)
    voucher_result = await db.execute(voucher_query)
    voucher = voucher_result.scalar_one_or_none()
    
    if not voucher:
        raise HTTPException(status_code=404, detail="Voucher not found")
    
    # Get lines
    lines_query = (
        select(GeneralLedgerLine)
        .where(GeneralLedgerLine.general_ledger_id == voucher_id)
        .order_by(GeneralLedgerLine.line_number)
    )
    lines_result = await db.execute(lines_query)
    lines = lines_result.scalars().all()
    
    voucher_dict = voucher.to_dict()
    voucher_dict["lines"] = [line.to_dict() for line in lines]
    
    # Calculate totals
    voucher_dict["total_debit"] = sum(float(line.debit_amount) for line in lines)
    voucher_dict["total_credit"] = sum(float(line.credit_amount) for line in lines)
    voucher_dict["balanced"] = abs(
        Decimal(str(voucher_dict["total_debit"])) - 
        Decimal(str(voucher_dict["total_credit"]))
    ) < Decimal("0.01")
    
    return voucher_dict


@router.get("/stats")
async def get_voucher_journal_stats(
    client_id: uuid.UUID,
    period: Optional[str] = None,  # YYYY-MM format
    db: AsyncSession = Depends(get_db)
):
    """
    Get statistics for voucher journal
    
    Returns counts, totals, and breakdown by type.
    """
    query = select(GeneralLedger).where(GeneralLedger.client_id == client_id)
    
    if period:
        query = query.where(GeneralLedger.period == period)
    
    result = await db.execute(query)
    vouchers = result.scalars().all()
    
    # Calculate stats
    stats = {
        "total_count": len(vouchers),
        "by_type": {},
        "by_posted_by": {},
        "by_status": {},
        "date_range": {
            "earliest": None,
            "latest": None,
        },
    }
    
    if vouchers:
        # Type breakdown
        for voucher in vouchers:
            vtype = voucher.voucher_type or "unknown"
            stats["by_type"][vtype] = stats["by_type"].get(vtype, 0) + 1
            
            posted_by = voucher.posted_by or "unknown"
            stats["by_posted_by"][posted_by] = stats["by_posted_by"].get(posted_by, 0) + 1
            
            status = voucher.status or "unknown"
            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
        
        # Date range
        dates = [v.accounting_date for v in vouchers if v.accounting_date]
        if dates:
            stats["date_range"]["earliest"] = min(dates).isoformat()
            stats["date_range"]["latest"] = max(dates).isoformat()
    
    return stats


@router.get("/types")
async def get_voucher_types(
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of voucher types used in the system
    """
    return {
        "types": [
            {
                "value": "supplier_invoice",
                "label": "Leverandørfaktura",
                "description": "Incoming supplier invoice"
            },
            {
                "value": "customer_invoice",
                "label": "Kundefaktura",
                "description": "Outgoing customer invoice"
            },
            {
                "value": "bank_payment",
                "label": "Bankbetaling",
                "description": "Bank payment transaction"
            },
            {
                "value": "bank_receipt",
                "label": "Bankinnbetaling",
                "description": "Bank receipt transaction"
            },
            {
                "value": "manual_entry",
                "label": "Manuell postering",
                "description": "Manual journal entry"
            },
            {
                "value": "salary",
                "label": "Lønn",
                "description": "Salary/payroll entry"
            },
            {
                "value": "vat_settlement",
                "label": "Mva-oppgjør",
                "description": "VAT settlement"
            },
            {
                "value": "depreciation",
                "label": "Avskrivning",
                "description": "Depreciation entry"
            },
            {
                "value": "accrual",
                "label": "Periodisering",
                "description": "Accrual entry"
            },
            {
                "value": "reversal",
                "label": "Tilbakeføring",
                "description": "Reversal entry"
            },
        ]
    }


@router.get("/export")
async def export_voucher_journal(
    client_id: uuid.UUID,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    format: str = Query("json", regex="^(json|csv)$"),
    db: AsyncSession = Depends(get_db)
):
    """
    Export voucher journal to JSON or CSV
    
    Useful for auditing and external analysis.
    """
    query = select(GeneralLedger).where(GeneralLedger.client_id == client_id)
    
    if date_from:
        query = query.where(GeneralLedger.accounting_date >= date_from)
    if date_to:
        query = query.where(GeneralLedger.accounting_date <= date_to)
    
    query = query.order_by(GeneralLedger.accounting_date, GeneralLedger.voucher_number)
    
    result = await db.execute(query)
    vouchers = result.scalars().all()
    
    export_data = []
    
    for voucher in vouchers:
        # Get lines
        lines_query = (
            select(GeneralLedgerLine)
            .where(GeneralLedgerLine.general_ledger_id == voucher.id)
            .order_by(GeneralLedgerLine.line_number)
        )
        lines_result = await db.execute(lines_query)
        lines = lines_result.scalars().all()
        
        # Create flat structure for each line
        for line in lines:
            export_data.append({
                "accounting_date": voucher.accounting_date.isoformat(),
                "voucher_number": f"{voucher.voucher_series}-{voucher.voucher_number}",
                "voucher_type": voucher.voucher_type,
                "description": voucher.description,
                "account_number": line.account_number,
                "debit": float(line.debit_amount),
                "credit": float(line.credit_amount),
                "vat_code": line.vat_code,
                "vat_amount": float(line.vat_amount) if line.vat_amount else 0.0,
                "line_description": line.line_description,
                "posted_by": voucher.posted_by,
                "created_at": voucher.created_at.isoformat(),
            })
    
    if format == "csv":
        # Convert to CSV format
        import csv
        import io
        
        output = io.StringIO()
        if export_data:
            fieldnames = export_data[0].keys()
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(export_data)
        
        return {
            "format": "csv",
            "data": output.getvalue(),
            "count": len(export_data),
        }
    
    # Return JSON
    return {
        "format": "json",
        "data": export_data,
        "count": len(export_data),
    }

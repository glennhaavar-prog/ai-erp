"""
Supplier Ledger API Routes - Leverandørreskontro
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from typing import List, Optional
from datetime import date, datetime, timedelta
from decimal import Decimal
import uuid

from app.database import get_db
from app.models.supplier_ledger import SupplierLedger, SupplierLedgerTransaction
from app.models.vendor import Vendor
from app.models.client import Client
from app.models.general_ledger import GeneralLedger, GeneralLedgerLine
from app.models.chart_of_accounts import Account
from app.utils.export_utils import (
    generate_pdf_supplier_ledger,
    generate_excel_supplier_ledger,
)

router = APIRouter(prefix="/supplier-ledger", tags=["supplier_ledger"])


@router.get("/")
async def get_supplier_ledger(
    client_id: uuid.UUID,
    status: Optional[str] = Query(None, regex="^(open|partially_paid|paid|all)$"),
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    supplier_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get supplier ledger entries with filters
    
    Returns list of open/paid supplier invoices with remaining balances.
    """
    query = (
        select(SupplierLedger, Vendor)
        .join(Vendor, SupplierLedger.supplier_id == Vendor.id)
        .where(SupplierLedger.client_id == client_id)
    )
    
    # Apply filters
    if status and status != "all":
        query = query.where(SupplierLedger.status == status)
    
    if date_from:
        query = query.where(SupplierLedger.invoice_date >= date_from)
    
    if date_to:
        query = query.where(SupplierLedger.invoice_date <= date_to)
    
    if supplier_id:
        query = query.where(SupplierLedger.supplier_id == supplier_id)
    
    # Order by due date (oldest first)
    query = query.order_by(SupplierLedger.due_date.asc())
    
    result = await db.execute(query)
    entries = result.all()
    
    # Build response
    ledger_list = []
    for ledger_entry, vendor in entries:
        entry_dict = ledger_entry.to_dict()
        entry_dict["supplier_name"] = vendor.name
        entry_dict["supplier_org_number"] = vendor.org_number
        
        # Calculate days overdue
        if ledger_entry.due_date < date.today() and ledger_entry.status in ["open", "partially_paid"]:
            days_overdue = (date.today() - ledger_entry.due_date).days
            entry_dict["days_overdue"] = days_overdue
        else:
            entry_dict["days_overdue"] = 0
        
        ledger_list.append(entry_dict)
    
    return {
        "entries": ledger_list,
        "total_count": len(ledger_list),
        "total_remaining": sum(float(e.remaining_amount) for e, _ in entries),
    }


@router.get("/supplier/{supplier_id}")
async def get_supplier_statement(
    supplier_id: uuid.UUID,
    client_id: uuid.UUID,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get full statement for a specific supplier (Kontoutskrift)
    """
    # Get supplier info
    vendor_query = select(Vendor).where(
        and_(Vendor.id == supplier_id, Vendor.client_id == client_id)
    )
    vendor_result = await db.execute(vendor_query)
    vendor = vendor_result.scalar_one_or_none()
    
    if not vendor:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    # Get all ledger entries for supplier
    query = (
        select(SupplierLedger)
        .where(and_(
            SupplierLedger.supplier_id == supplier_id,
            SupplierLedger.client_id == client_id
        ))
    )
    
    if date_from:
        query = query.where(SupplierLedger.invoice_date >= date_from)
    if date_to:
        query = query.where(SupplierLedger.invoice_date <= date_to)
    
    query = query.order_by(SupplierLedger.invoice_date.asc())
    
    result = await db.execute(query)
    entries = result.scalars().all()
    
    # Build statement with running balance
    statement = []
    running_balance = Decimal("0.00")
    
    for entry in entries:
        # Get transactions for this entry
        trans_query = (
            select(SupplierLedgerTransaction)
            .where(SupplierLedgerTransaction.ledger_id == entry.id)
            .order_by(SupplierLedgerTransaction.transaction_date.asc())
        )
        trans_result = await db.execute(trans_query)
        transactions = trans_result.scalars().all()
        
        # Add invoice line
        running_balance += entry.amount
        statement.append({
            "date": entry.invoice_date.isoformat(),
            "type": "invoice",
            "reference": entry.invoice_number,
            "debit": float(entry.amount),
            "credit": 0.0,
            "balance": float(running_balance),
        })
        
        # Add payment lines
        for trans in transactions:
            if trans.type == "payment":
                running_balance -= trans.amount
                statement.append({
                    "date": trans.transaction_date.isoformat(),
                    "type": "payment",
                    "reference": str(trans.voucher_id),
                    "debit": 0.0,
                    "credit": float(trans.amount),
                    "balance": float(running_balance),
                })
    
    return {
        "supplier": vendor.to_dict(),
        "statement": statement,
        "current_balance": float(running_balance),
    }


@router.get("/aging")
async def get_supplier_aging(
    client_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get aging report for supplier ledger
    
    Breaks down open balances by age:
    - Not due
    - 0-30 days overdue
    - 31-60 days overdue
    - 61-90 days overdue
    - 90+ days overdue
    """
    today = date.today()
    
    # Get all open entries
    query = (
        select(SupplierLedger)
        .where(and_(
            SupplierLedger.client_id == client_id,
            SupplierLedger.status.in_(["open", "partially_paid"])
        ))
    )
    
    result = await db.execute(query)
    entries = result.scalars().all()
    
    # Calculate aging buckets
    aging = {
        "not_due": Decimal("0.00"),
        "0_30": Decimal("0.00"),
        "31_60": Decimal("0.00"),
        "61_90": Decimal("0.00"),
        "90_plus": Decimal("0.00"),
    }
    
    for entry in entries:
        if entry.due_date >= today:
            aging["not_due"] += entry.remaining_amount
        else:
            days_overdue = (today - entry.due_date).days
            if days_overdue <= 30:
                aging["0_30"] += entry.remaining_amount
            elif days_overdue <= 60:
                aging["31_60"] += entry.remaining_amount
            elif days_overdue <= 90:
                aging["61_90"] += entry.remaining_amount
            else:
                aging["90_plus"] += entry.remaining_amount
    
    total = sum(aging.values())
    
    return {
        "aging": {
            "not_due": float(aging["not_due"]),
            "0_30_days": float(aging["0_30"]),
            "31_60_days": float(aging["31_60"]),
            "61_90_days": float(aging["61_90"]),
            "90_plus_days": float(aging["90_plus"]),
        },
        "total": float(total),
        "percentages": {
            "not_due": round((aging["not_due"] / total * 100) if total > 0 else 0, 1),
            "0_30_days": round((aging["0_30"] / total * 100) if total > 0 else 0, 1),
            "31_60_days": round((aging["31_60"] / total * 100) if total > 0 else 0, 1),
            "61_90_days": round((aging["61_90"] / total * 100) if total > 0 else 0, 1),
            "90_plus_days": round((aging["90_plus"] / total * 100) if total > 0 else 0, 1),
        },
    }


@router.get("/reconcile")
async def reconcile_supplier_ledger(
    client_id: uuid.UUID,
    as_of_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Validate that supplier ledger reconciles with account 2400
    
    CRITICAL: Sum of open entries MUST equal account 2400 balance
    """
    if not as_of_date:
        as_of_date = date.today()
    
    # Get sum of open supplier ledger entries
    ledger_query = select(
        func.sum(SupplierLedger.remaining_amount)
    ).where(and_(
        SupplierLedger.client_id == client_id,
        SupplierLedger.status.in_(["open", "partially_paid"]),
        SupplierLedger.invoice_date <= as_of_date
    ))
    
    ledger_result = await db.execute(ledger_query)
    ledger_sum = ledger_result.scalar() or Decimal("0.00")
    
    # Get account 2400 balance from general ledger
    # TODO: This should query account_balances table for performance
    # For now, calculate from general_ledger_lines
    account_query = select(
        func.sum(GeneralLedgerLine.credit_amount - GeneralLedgerLine.debit_amount)
    ).select_from(GeneralLedgerLine).join(
        GeneralLedger,
        GeneralLedgerLine.general_ledger_id == GeneralLedger.id
    ).where(and_(
        GeneralLedger.client_id == client_id,
        GeneralLedgerLine.account_number == "2400",
        GeneralLedger.accounting_date <= as_of_date
    ))
    
    
    account_result = await db.execute(account_query)
    account_balance = account_result.scalar() or Decimal("0.00")
    
    difference = ledger_sum - account_balance
    reconciles = abs(difference) < Decimal("0.01")  # Allow 1 cent rounding difference
    
    return {
        "as_of_date": as_of_date.isoformat(),
        "supplier_ledger_total": float(ledger_sum),
        "account_2400_balance": float(account_balance),
        "difference": float(difference),
        "reconciles": reconciles,
        "status": "OK" if reconciles else "ERROR - Does not reconcile!",
    }





# ==================== EXPORT ENDPOINTS ====================

async def get_client_name_supplier(client_id: uuid.UUID, db: AsyncSession) -> str:
    """Helper function to get client name"""
    result = await db.execute(select(Client).where(Client.id == client_id))
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail=f"Client {client_id} not found")
    return client.name


@router.get("/pdf")
async def export_supplier_ledger_pdf(
    client_id: uuid.UUID,
    status: Optional[str] = Query(None, regex="^(open|partially_paid|paid|all)$"),
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    supplier_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db)
):
    """Export Leverandørreskontro as PDF"""
    data = await get_supplier_ledger(client_id, status, date_from, date_to, supplier_id, db)
    client_name = await get_client_name_supplier(client_id, db)
    
    return generate_pdf_supplier_ledger(data, client_name)


@router.get("/excel")
async def export_supplier_ledger_excel(
    client_id: uuid.UUID,
    status: Optional[str] = Query(None, regex="^(open|partially_paid|paid|all)$"),
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    supplier_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db)
):
    """Export Leverandørreskontro as Excel"""
    data = await get_supplier_ledger(client_id, status, date_from, date_to, supplier_id, db)
    client_name = await get_client_name_supplier(client_id, db)
    
    return generate_excel_supplier_ledger(data, client_name)


@router.get("/{ledger_id}")
async def get_supplier_ledger_entry(
    ledger_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get single supplier ledger entry with full transaction history
    """
    # Get ledger entry
    query = (
        select(SupplierLedger, Vendor)
        .join(Vendor, SupplierLedger.supplier_id == Vendor.id)
        .where(SupplierLedger.id == ledger_id)
    )
    result = await db.execute(query)
    row = result.first()
    
    if not row:
        raise HTTPException(status_code=404, detail="Supplier ledger entry not found")
    
    ledger_entry, vendor = row
    
    # Get transactions
    trans_query = (
        select(SupplierLedgerTransaction)
        .where(SupplierLedgerTransaction.ledger_id == ledger_id)
        .order_by(SupplierLedgerTransaction.transaction_date.asc())
    )
    trans_result = await db.execute(trans_query)
    transactions = trans_result.scalars().all()
    
    entry_dict = ledger_entry.to_dict()
    entry_dict["supplier_name"] = vendor.name
    entry_dict["transactions"] = [t.to_dict() for t in transactions]
    
    return entry_dict



@router.post("/match-payment")
async def match_payment_to_invoice(
    ledger_id: uuid.UUID,
    payment_voucher_id: uuid.UUID,
    amount: Decimal,
    payment_date: date,
    db: AsyncSession = Depends(get_db)
):
    """
    Match a payment to a supplier invoice
    
    Creates a transaction and updates remaining_amount.
    """
    # Get ledger entry
    ledger_query = select(SupplierLedger).where(SupplierLedger.id == ledger_id)
    ledger_result = await db.execute(ledger_query)
    ledger_entry = ledger_result.scalar_one_or_none()
    
    if not ledger_entry:
        raise HTTPException(status_code=404, detail="Supplier ledger entry not found")
    
    if amount > ledger_entry.remaining_amount:
        raise HTTPException(
            status_code=400,
            detail=f"Payment amount ({amount}) exceeds remaining amount ({ledger_entry.remaining_amount})"
        )
    
    # Create transaction
    transaction = SupplierLedgerTransaction(
        id=uuid.uuid4(),
        ledger_id=ledger_id,
        voucher_id=payment_voucher_id,
        transaction_date=payment_date,
        amount=amount,
        type="payment",
        created_at=datetime.utcnow(),
    )
    
    db.add(transaction)
    
    # Update ledger entry
    ledger_entry.remaining_amount -= amount
    ledger_entry.updated_at = datetime.utcnow()
    
    # Update status
    if ledger_entry.remaining_amount == 0:
        ledger_entry.status = "paid"
    elif ledger_entry.remaining_amount < ledger_entry.amount:
        ledger_entry.status = "partially_paid"
    
    await db.commit()
    await db.refresh(ledger_entry)
    
    return {
        "message": "Payment matched successfully",
        "ledger_entry": ledger_entry.to_dict(),
        "transaction": transaction.to_dict(),
    }
"""
Customer Ledger API Routes - Kundereskontro
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from typing import List, Optional
from datetime import date, datetime, timedelta
from decimal import Decimal
import uuid

from app.database import get_db
from app.models.customer_ledger import CustomerLedger, CustomerLedgerTransaction
from app.models.client import Client
from app.models.general_ledger import GeneralLedger
from app.utils.export_utils import (
    generate_pdf_customer_ledger,
    generate_excel_customer_ledger,
)

router = APIRouter(prefix="/customer-ledger", tags=["customer_ledger"])


@router.get("/")
async def get_customer_ledger(
    client_id: uuid.UUID,
    status: Optional[str] = Query(None, regex="^(open|partially_paid|paid|overdue|all)$"),
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    customer_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get customer ledger entries with filters
    
    Returns list of open/paid customer invoices with remaining balances.
    """
    query = select(CustomerLedger).where(CustomerLedger.client_id == client_id)
    
    # Apply filters
    if status and status != "all":
        if status == "overdue":
            # Overdue = due date passed and still has remaining amount
            query = query.where(
                and_(
                    CustomerLedger.due_date < date.today(),
                    CustomerLedger.status.in_(["open", "partially_paid"])
                )
            )
        else:
            query = query.where(CustomerLedger.status == status)
    
    if date_from:
        query = query.where(CustomerLedger.invoice_date >= date_from)
    
    if date_to:
        query = query.where(CustomerLedger.invoice_date <= date_to)
    
    if customer_id:
        query = query.where(CustomerLedger.customer_id == customer_id)
    
    # Order by due date (oldest first)
    query = query.order_by(CustomerLedger.due_date.asc())
    
    result = await db.execute(query)
    entries = result.scalars().all()
    
    # Build response
    ledger_list = []
    today = date.today()
    
    for ledger_entry in entries:
        entry_dict = ledger_entry.to_dict()
        
        # Calculate days overdue
        if ledger_entry.due_date < today and ledger_entry.status in ["open", "partially_paid"]:
            days_overdue = (today - ledger_entry.due_date).days
            entry_dict["days_overdue"] = days_overdue
            
            # Add status label
            if days_overdue > 60:
                entry_dict["status_label"] = "Forfalt (kritisk)"
            elif days_overdue > 30:
                entry_dict["status_label"] = "Forfalt"
            else:
                entry_dict["status_label"] = "Forfaller snart"
        elif ledger_entry.due_date == today:
            entry_dict["days_overdue"] = 0
            entry_dict["status_label"] = "Forfaller i dag"
        elif (ledger_entry.due_date - today).days <= 7:
            entry_dict["days_overdue"] = 0
            entry_dict["status_label"] = "Forfaller snart"
        else:
            entry_dict["days_overdue"] = 0
            entry_dict["status_label"] = "Aktuell"
        
        ledger_list.append(entry_dict)
    
    return {
        "entries": ledger_list,
        "total_count": len(ledger_list),
        "total_remaining": sum(float(e.remaining_amount) for e in entries),
    }


@router.get("/customer/{customer_id}")
async def get_customer_statement(
    customer_id: uuid.UUID,
    client_id: uuid.UUID,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get full statement for a specific customer (Kundekontoutskrift)
    """
    # Get all ledger entries for customer
    query = (
        select(CustomerLedger)
        .where(and_(
            CustomerLedger.customer_id == customer_id,
            CustomerLedger.client_id == client_id
        ))
    )
    
    if date_from:
        query = query.where(CustomerLedger.invoice_date >= date_from)
    if date_to:
        query = query.where(CustomerLedger.invoice_date <= date_to)
    
    query = query.order_by(CustomerLedger.invoice_date.asc())
    
    result = await db.execute(query)
    entries = result.scalars().all()
    
    if not entries:
        raise HTTPException(status_code=404, detail="No entries found for customer")
    
    # Build statement with running balance
    statement = []
    running_balance = Decimal("0.00")
    customer_name = entries[0].customer_name if entries else "Unknown"
    
    for entry in entries:
        # Get transactions for this entry
        trans_query = (
            select(CustomerLedgerTransaction)
            .where(CustomerLedgerTransaction.ledger_id == entry.id)
            .order_by(CustomerLedgerTransaction.transaction_date.asc())
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
                    "reference": entry.kid_number or str(trans.voucher_id),
                    "debit": 0.0,
                    "credit": float(trans.amount),
                    "balance": float(running_balance),
                })
    
    return {
        "customer_id": str(customer_id),
        "customer_name": customer_name,
        "statement": statement,
        "current_balance": float(running_balance),
    }


@router.get("/aging")
async def get_customer_aging(
    client_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get aging report for customer ledger
    
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
        select(CustomerLedger)
        .where(and_(
            CustomerLedger.client_id == client_id,
            CustomerLedger.status.in_(["open", "partially_paid"])
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
async def reconcile_customer_ledger(
    client_id: uuid.UUID,
    as_of_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Validate that customer ledger reconciles with account 1500
    
    CRITICAL: Sum of open entries MUST equal account 1500 balance
    """
    if not as_of_date:
        as_of_date = date.today()
    
    # Get sum of open customer ledger entries
    ledger_query = select(
        func.sum(CustomerLedger.remaining_amount)
    ).where(and_(
        CustomerLedger.client_id == client_id,
        CustomerLedger.status.in_(["open", "partially_paid"]),
        CustomerLedger.invoice_date <= as_of_date
    ))
    
    ledger_result = await db.execute(ledger_query)
    ledger_sum = ledger_result.scalar() or Decimal("0.00")
    
    # Get account 1500 balance from general ledger
    # TODO: This should query account_balances table for performance
    # For now, calculate from general_ledger_lines
    from app.models.general_ledger import GeneralLedgerLine  # Import here to avoid circular
    
    account_query = select(
        func.sum(GeneralLedgerLine.debit_amount - GeneralLedgerLine.credit_amount)
    ).select_from(GeneralLedgerLine).join(
        GeneralLedger,
        GeneralLedgerLine.general_ledger_id == GeneralLedger.id
    ).where(and_(
        GeneralLedger.client_id == client_id,
        GeneralLedgerLine.account_number == "1500",
        GeneralLedger.accounting_date <= as_of_date
    ))
    
    account_result = await db.execute(account_query)
    account_balance = account_result.scalar() or Decimal("0.00")
    
    difference = ledger_sum - account_balance
    reconciles = abs(difference) < Decimal("0.01")  # Allow 1 cent rounding difference
    
    return {
        "as_of_date": as_of_date.isoformat(),
        "customer_ledger_total": float(ledger_sum),
        "account_1500_balance": float(account_balance),
        "difference": float(difference),
        "reconciles": reconciles,
        "status": "OK" if reconciles else "ERROR - Does not reconcile!",
    }





# ==================== EXPORT ENDPOINTS ====================

async def get_client_name_customer(client_id: uuid.UUID, db: AsyncSession) -> str:
    """Helper function to get client name"""
    result = await db.execute(select(Client).where(Client.id == client_id))
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail=f"Client {client_id} not found")
    return client.name


@router.get("/pdf")
async def export_customer_ledger_pdf(
    client_id: uuid.UUID,
    status: Optional[str] = Query(None, regex="^(open|partially_paid|paid|overdue|all)$"),
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    customer_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db)
):
    """Export Kundereskontro as PDF"""
    data = await get_customer_ledger(client_id, status, date_from, date_to, customer_id, db)
    client_name = await get_client_name_customer(client_id, db)
    
    return generate_pdf_customer_ledger(data, client_name)


@router.get("/excel")
async def export_customer_ledger_excel(
    client_id: uuid.UUID,
    status: Optional[str] = Query(None, regex="^(open|partially_paid|paid|overdue|all)$"),
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    customer_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db)
):
    """Export Kundereskontro as Excel"""
    data = await get_customer_ledger(client_id, status, date_from, date_to, customer_id, db)
    client_name = await get_client_name_customer(client_id, db)
    
    return generate_excel_customer_ledger(data, client_name)


@router.get("/{ledger_id}")
async def get_customer_ledger_entry(
    ledger_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get single customer ledger entry with full transaction history
    """
    # Get ledger entry
    query = select(CustomerLedger).where(CustomerLedger.id == ledger_id)
    result = await db.execute(query)
    ledger_entry = result.scalar_one_or_none()
    
    if not ledger_entry:
        raise HTTPException(status_code=404, detail="Customer ledger entry not found")
    
    # Get transactions
    trans_query = (
        select(CustomerLedgerTransaction)
        .where(CustomerLedgerTransaction.ledger_id == ledger_id)
        .order_by(CustomerLedgerTransaction.transaction_date.asc())
    )
    trans_result = await db.execute(trans_query)
    transactions = trans_result.scalars().all()
    
    entry_dict = ledger_entry.to_dict()
    entry_dict["transactions"] = [t.to_dict() for t in transactions]
    
    return entry_dict



@router.post("/match-payment")
async def match_payment_to_invoice(
    ledger_id: Optional[uuid.UUID] = None,
    kid_number: Optional[str] = None,
    payment_voucher_id: uuid.UUID = None,
    amount: Decimal = None,
    payment_date: date = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Match a payment to a customer invoice
    
    Can match by ledger_id OR kid_number.
    Creates a transaction and updates remaining_amount.
    """
    if not ledger_id and not kid_number:
        raise HTTPException(status_code=400, detail="Must provide either ledger_id or kid_number")
    
    # Get ledger entry
    if ledger_id:
        ledger_query = select(CustomerLedger).where(CustomerLedger.id == ledger_id)
    else:
        ledger_query = select(CustomerLedger).where(CustomerLedger.kid_number == kid_number)
    
    ledger_result = await db.execute(ledger_query)
    ledger_entry = ledger_result.scalar_one_or_none()
    
    if not ledger_entry:
        raise HTTPException(status_code=404, detail="Customer ledger entry not found")
    
    if amount > ledger_entry.remaining_amount:
        raise HTTPException(
            status_code=400,
            detail=f"Payment amount ({amount}) exceeds remaining amount ({ledger_entry.remaining_amount})"
        )
    
    # Create transaction
    transaction = CustomerLedgerTransaction(
        id=uuid.uuid4(),
        ledger_id=ledger_entry.id,
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
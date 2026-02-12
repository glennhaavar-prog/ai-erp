"""
Dashboard Metrics API - Kontali ERP Main Dashboard
Comprehensive metrics for the main page dashboard (2B Implementation)
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, cast, String, Integer, extract
from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional
from uuid import UUID
from decimal import Decimal

from app.database import get_db
from app.models.vendor_invoice import VendorInvoice
from app.models.bank_transaction import BankTransaction, TransactionStatus
from app.models.review_queue import ReviewQueue, ReviewStatus, ReviewPriority
from app.models.general_ledger import GeneralLedger, GeneralLedgerLine
from app.models.client import Client

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard Metrics"])


@router.get("/metrics")
async def get_dashboard_metrics(
    tenant_id: Optional[str] = Query(None, description="Filter by tenant_id (optional)"),
    client_id: Optional[str] = Query(None, description="Filter by client_id (optional)"),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    🎯 Dashboard Metrics Endpoint - Main ERP Dashboard (Task 2B)
    
    Returns comprehensive metrics for Kontali ERP main page:
    1. Ubehandlede leverandørfakturaer (unprocessed vendor invoices)
    2. Banktransaksjoner til matching (unmatched bank transactions)
    3. Månedlig resultat inneværende måned (current month P&L)
    4. Månedlig resultat forrige måned (previous month P&L)
    5. Review Queue status (by priority)
    6. Client-level aggregation (if tenant_id provided)
    
    Query params:
    - tenant_id: Filter to specific tenant (regnskapsbyrå)
    - client_id: Filter to specific client (firma)
    """
    
    # Build base filters
    filters = []
    if tenant_id:
        try:
            tenant_uuid = UUID(tenant_id)
            # Will need to join through client for tenant filtering
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid tenant_id format")
    
    if client_id:
        try:
            client_uuid = UUID(client_id)
            filters.append(client_uuid)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid client_id format")
    
    # ===== METRIC 1: Ubehandlede leverandørfakturaer =====
    unprocessed_invoice_query = select(func.count(VendorInvoice.id)).where(
        VendorInvoice.review_status.in_(['pending', 'needs_review'])
    )
    if client_id:
        unprocessed_invoice_query = unprocessed_invoice_query.where(
            VendorInvoice.client_id == UUID(client_id)
        )
    
    unprocessed_result = await db.execute(unprocessed_invoice_query)
    ubehandlede_fakturaer = unprocessed_result.scalar() or 0
    
    # ===== METRIC 2: Banktransaksjoner til matching =====
    unmatched_bank_query = select(func.count(BankTransaction.id)).where(
        cast(BankTransaction.status, String) == 'unmatched'
    )
    if client_id:
        unmatched_bank_query = unmatched_bank_query.where(
            BankTransaction.client_id == UUID(client_id)
        )
    
    unmatched_result = await db.execute(unmatched_bank_query)
    bank_til_matching = unmatched_result.scalar() or 0
    
    # ===== METRIC 3 & 4: Månedlig resultat (P&L) =====
    # Calculate P&L from GeneralLedger
    # Norwegian chart of accounts: Income (3xxx-8xxx), Expenses (4xxx-7xxx)
    # Result = Income - Expenses
    
    today = date.today()
    current_month_start = date(today.year, today.month, 1)
    
    # Previous month
    if today.month == 1:
        prev_month_start = date(today.year - 1, 12, 1)
        prev_month_end = date(today.year - 1, 12, 31)
    else:
        prev_month_start = date(today.year, today.month - 1, 1)
        # Last day of previous month
        prev_month_end = current_month_start - timedelta(days=1)
    
    # Current month P&L
    current_month_result = await calculate_monthly_result(
        db, 
        current_month_start, 
        today,
        UUID(client_id) if client_id else None
    )
    
    # Previous month P&L
    previous_month_result = await calculate_monthly_result(
        db,
        prev_month_start,
        prev_month_end,
        UUID(client_id) if client_id else None
    )
    
    # ===== METRIC 5: Review Queue by Priority =====
    review_queue_stats = await get_review_queue_breakdown(
        db,
        UUID(client_id) if client_id else None
    )
    
    # ===== METRIC 6: Client-level metrics (if tenant_id) =====
    client_metrics = []
    if tenant_id:
        client_metrics = await get_client_level_metrics(db, UUID(tenant_id))
    
    # ===== Additional useful metrics =====
    # Auto-booking success rate (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    total_invoices_query = select(func.count(VendorInvoice.id)).where(
        VendorInvoice.created_at >= thirty_days_ago
    )
    if client_id:
        total_invoices_query = total_invoices_query.where(
            VendorInvoice.client_id == UUID(client_id)
        )
    
    total_invoices_result = await db.execute(total_invoices_query)
    total_recent_invoices = total_invoices_result.scalar() or 0
    
    auto_approved_query = select(func.count(VendorInvoice.id)).where(
        and_(
            VendorInvoice.created_at >= thirty_days_ago,
            VendorInvoice.review_status == 'auto_approved'
        )
    )
    if client_id:
        auto_approved_query = auto_approved_query.where(
            VendorInvoice.client_id == UUID(client_id)
        )
    
    auto_approved_result = await db.execute(auto_approved_query)
    auto_approved_count = auto_approved_result.scalar() or 0
    
    auto_booking_rate = round(
        (auto_approved_count / total_recent_invoices * 100) 
        if total_recent_invoices > 0 else 0,
        1
    )
    
    # ===== Response =====
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "filter": {
            "tenant_id": tenant_id,
            "client_id": client_id
        },
        "metrics": {
            "ubehandlede_fakturaer": {
                "count": ubehandlede_fakturaer,
                "description": "Leverandørfakturaer som venter på behandling",
                "action_url": "/review-queue"
            },
            "bank_til_matching": {
                "count": bank_til_matching,
                "description": "Banktransaksjoner som må matches",
                "action_url": "/bank-reconciliation"
            },
            "maanedlig_resultat": {
                "innevaerende_maaned": {
                    "amount": float(current_month_result),
                    "currency": "NOK",
                    "period": f"{current_month_start.isoformat()} to {today.isoformat()}",
                    "description": f"Resultat {current_month_start.strftime('%B %Y')}"
                },
                "forrige_maaned": {
                    "amount": float(previous_month_result),
                    "currency": "NOK",
                    "period": f"{prev_month_start.isoformat()} to {prev_month_end.isoformat()}",
                    "description": f"Resultat {prev_month_start.strftime('%B %Y')}"
                },
                "change": {
                    "amount": float(current_month_result - previous_month_result),
                    "percentage": round(
                        ((current_month_result - previous_month_result) / abs(previous_month_result) * 100)
                        if previous_month_result != 0 else 0,
                        1
                    )
                },
                "action_url": "/rapporter/resultat"
            },
            "review_queue": {
                "total": review_queue_stats['total'],
                "by_priority": review_queue_stats['by_priority'],
                "by_status": review_queue_stats['by_status'],
                "action_url": "/review-queue"
            },
            "auto_booking_performance": {
                "rate": auto_booking_rate,
                "total_invoices_30d": total_recent_invoices,
                "auto_approved_30d": auto_approved_count,
                "description": "Automatisk bokføring siste 30 dager"
            }
        },
        "client_metrics": client_metrics if client_metrics else None,
        "quick_actions": [
            {
                "label": "Behandle fakturaer",
                "url": "/review-queue",
                "icon": "📄",
                "badge": ubehandlede_fakturaer if ubehandlede_fakturaer > 0 else None
            },
            {
                "label": "Match bank",
                "url": "/bank-reconciliation",
                "icon": "🏦",
                "badge": bank_til_matching if bank_til_matching > 0 else None
            },
            {
                "label": "Se rapporter",
                "url": "/rapporter/resultat",
                "icon": "📊",
                "badge": None
            }
        ]
    }


async def calculate_monthly_result(
    db: AsyncSession,
    start_date: date,
    end_date: date,
    client_id: Optional[UUID] = None
) -> Decimal:
    """
    Calculate P&L (Profit & Loss) for a given period
    
    Norwegian account structure:
    - Income accounts: 3xxx-8xxx (credit increases result)
    - Expense accounts: 4xxx-7xxx (debit decreases result)
    
    Result = Total Income - Total Expenses
    """
    
    # Query for income (credit on income accounts increases result)
    # Account numbers 3000-8999 are income/revenue accounts
    # Using LIKE pattern for account number matching (safer than casting)
    income_query = select(
        func.coalesce(func.sum(GeneralLedgerLine.credit_amount), 0) - 
        func.coalesce(func.sum(GeneralLedgerLine.debit_amount), 0)
    ).select_from(GeneralLedgerLine).join(
        GeneralLedger,
        GeneralLedgerLine.general_ledger_id == GeneralLedger.id
    ).where(
        and_(
            GeneralLedger.accounting_date >= start_date,
            GeneralLedger.accounting_date <= end_date,
            GeneralLedgerLine.account_number.like('3%') | 
            GeneralLedgerLine.account_number.like('4%') |
            GeneralLedgerLine.account_number.like('5%') |
            GeneralLedgerLine.account_number.like('6%') |
            GeneralLedgerLine.account_number.like('7%') |
            GeneralLedgerLine.account_number.like('8%')
        )
    )
    
    if client_id:
        income_query = income_query.where(GeneralLedger.client_id == client_id)
    
    income_result = await db.execute(income_query)
    total_income = income_result.scalar() or Decimal("0.00")
    
    # Query for expenses (debit on expense accounts decreases result)
    # Account numbers 4000-7999 are expense accounts
    expense_query = select(
        func.coalesce(func.sum(GeneralLedgerLine.debit_amount), 0) - 
        func.coalesce(func.sum(GeneralLedgerLine.credit_amount), 0)
    ).select_from(GeneralLedgerLine).join(
        GeneralLedger,
        GeneralLedgerLine.general_ledger_id == GeneralLedger.id
    ).where(
        and_(
            GeneralLedger.accounting_date >= start_date,
            GeneralLedger.accounting_date <= end_date,
            GeneralLedgerLine.account_number.like('4%') |
            GeneralLedgerLine.account_number.like('5%') |
            GeneralLedgerLine.account_number.like('6%') |
            GeneralLedgerLine.account_number.like('7%')
        )
    )
    
    if client_id:
        expense_query = expense_query.where(GeneralLedger.client_id == client_id)
    
    expense_result = await db.execute(expense_query)
    total_expenses = expense_result.scalar() or Decimal("0.00")
    
    # Result = Income - Expenses
    return total_income - total_expenses


async def get_review_queue_breakdown(
    db: AsyncSession,
    client_id: Optional[UUID] = None
) -> Dict[str, Any]:
    """
    Get Review Queue statistics broken down by priority and status
    """
    
    base_query = select(ReviewQueue)
    if client_id:
        base_query = base_query.where(ReviewQueue.client_id == client_id)
    
    # Total count
    total_query = select(func.count(ReviewQueue.id))
    if client_id:
        total_query = total_query.where(ReviewQueue.client_id == client_id)
    
    total_result = await db.execute(total_query)
    total = total_result.scalar() or 0
    
    # By priority
    by_priority = {}
    for priority in ['low', 'medium', 'high', 'urgent']:
        priority_query = select(func.count(ReviewQueue.id)).where(
            cast(ReviewQueue.priority, String) == priority.upper()
        )
        if client_id:
            priority_query = priority_query.where(ReviewQueue.client_id == client_id)
        
        priority_result = await db.execute(priority_query)
        by_priority[priority] = priority_result.scalar() or 0
    
    # By status
    by_status = {}
    for status in ['pending', 'in_progress', 'approved', 'corrected', 'rejected']:
        status_query = select(func.count(ReviewQueue.id)).where(
            cast(ReviewQueue.status, String) == status.upper()
        )
        if client_id:
            status_query = status_query.where(ReviewQueue.client_id == client_id)
        
        status_result = await db.execute(status_query)
        by_status[status] = status_result.scalar() or 0
    
    return {
        "total": total,
        "by_priority": by_priority,
        "by_status": by_status
    }


async def get_client_level_metrics(
    db: AsyncSession,
    tenant_id: UUID
) -> list:
    """
    Get per-client metrics for a tenant (regnskapsbyrå)
    """
    
    # Get all active clients for this tenant
    clients_query = select(Client).where(
        and_(
            Client.tenant_id == tenant_id,
            Client.status == 'active'
        )
    ).order_by(Client.name)
    
    clients_result = await db.execute(clients_query)
    clients = clients_result.scalars().all()
    
    client_metrics = []
    
    for client in clients:
        # Unprocessed invoices for this client
        invoice_count_query = select(func.count(VendorInvoice.id)).where(
            and_(
                VendorInvoice.client_id == client.id,
                VendorInvoice.review_status.in_(['pending', 'needs_review'])
            )
        )
        invoice_count_result = await db.execute(invoice_count_query)
        invoice_count = invoice_count_result.scalar() or 0
        
        # Unmatched bank transactions
        bank_count_query = select(func.count(BankTransaction.id)).where(
            and_(
                BankTransaction.client_id == client.id,
                cast(BankTransaction.status, String) == 'unmatched'
            )
        )
        bank_count_result = await db.execute(bank_count_query)
        bank_count = bank_count_result.scalar() or 0
        
        # Review queue items
        review_count_query = select(func.count(ReviewQueue.id)).where(
            and_(
                ReviewQueue.client_id == client.id,
                cast(ReviewQueue.status, String) == 'PENDING'
            )
        )
        review_count_result = await db.execute(review_count_query)
        review_count = review_count_result.scalar() or 0
        
        # Current month result
        today = date.today()
        current_month_start = date(today.year, today.month, 1)
        monthly_result = await calculate_monthly_result(
            db,
            current_month_start,
            today,
            client.id
        )
        
        client_metrics.append({
            "client_id": str(client.id),
            "client_name": client.name,
            "ubehandlede_fakturaer": invoice_count,
            "bank_til_matching": bank_count,
            "review_queue_pending": review_count,
            "maanedlig_resultat": {
                "amount": float(monthly_result),
                "currency": "NOK"
            },
            "status": "needs_attention" if (invoice_count + bank_count + review_count) > 0 else "ok"
        })
    
    return client_metrics


# Additional utility endpoint for quick stats
@router.get("/metrics/summary")
async def get_metrics_summary(
    client_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Quick summary for mini-widgets (simplified version)
    """
    
    # Pending items count
    pending_query = select(func.count(ReviewQueue.id)).where(
        cast(ReviewQueue.status, String) == 'PENDING'
    )
    if client_id:
        pending_query = pending_query.where(ReviewQueue.client_id == UUID(client_id))
    
    pending_result = await db.execute(pending_query)
    pending_count = pending_result.scalar() or 0
    
    # Unprocessed invoices
    invoice_query = select(func.count(VendorInvoice.id)).where(
        VendorInvoice.review_status.in_(['pending', 'needs_review'])
    )
    if client_id:
        invoice_query = invoice_query.where(VendorInvoice.client_id == UUID(client_id))
    
    invoice_result = await db.execute(invoice_query)
    invoice_count = invoice_result.scalar() or 0
    
    # Bank transactions
    bank_query = select(func.count(BankTransaction.id)).where(
        cast(BankTransaction.status, String) == 'unmatched'
    )
    if client_id:
        bank_query = bank_query.where(BankTransaction.client_id == UUID(client_id))
    
    bank_result = await db.execute(bank_query)
    bank_count = bank_result.scalar() or 0
    
    return {
        "pending_reviews": pending_count,
        "unprocessed_invoices": invoice_count,
        "unmatched_bank": bank_count,
        "total_items": pending_count + invoice_count + bank_count
    }

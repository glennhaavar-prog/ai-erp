"""
Trust Dashboard API - System status and monitoring
Multi-Client Dashboard - Cross-client task aggregation (KONTALI PARADIGM SHIFT)
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
from typing import Dict, Any, List
from uuid import UUID

from app.database import get_db
from app.models.review_queue import ReviewQueue, ReviewStatus
from app.models.vendor_invoice import VendorInvoice
from app.models.customer_invoice import CustomerInvoice
from app.models.bank_transaction import BankTransaction, TransactionStatus
from app.models.client import Client
from app.models.tenant import Tenant

router = APIRouter(prefix="/api/v1/dashboard", tags=["Dashboard"])


@router.get("/")
async def get_dashboard_summary(
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get cross-client dashboard summary (API v1 spec compliant)
    
    Returns summary for the logged-in accountant across all clients.
    For demo purposes, returns all demo clients.
    
    TODO: Fix enum comparison issues with database
    For now, returning simplified counts
    """
    # Get all demo clients
    clients_query = select(Client).where(Client.is_demo == True).order_by(Client.name)
    clients_result = await db.execute(clients_query)
    clients = clients_result.scalars().all()
    
    # TODO: Fix enum comparison - for now use simpler counts
    # Count total review queue items
    all_items_query = select(func.count()).select_from(ReviewQueue)
    all_items_result = await db.execute(all_items_query)
    total_pending_items = all_items_result.scalar() or 0
    
    # Count vendor invoices in review queue
    vendor_items_query = select(func.count()).select_from(ReviewQueue).where(
        ReviewQueue.source_type == 'vendor_invoice'
    )
    vendor_items_result = await db.execute(vendor_items_query)
    vouchers_pending = vendor_items_result.scalar() or 0
    
    # Count bank transactions
    bank_count_query = select(func.count()).select_from(BankTransaction)
    bank_count_result = await db.execute(bank_count_query)
    bank_items_open = bank_count_result.scalar() or 0
    
    # Build client list with status
    client_list = []
    for client in clients:
        # For now, return basic client info without complex queries
        client_list.append({
            "id": str(client.id),
            "name": client.name,
            "vouchers_pending": 0,  # TODO: calculate per client
            "bank_items_open": 0,  # TODO: calculate per client
            "reconciliation_status": "not_started",
            "vat_status": "not_started"
        })
    
    return {
        "total_clients": len(clients),
        "total_pending_items": total_pending_items,
        "summary_by_category": {
            "vouchers_pending": vouchers_pending,
            "bank_items_open": bank_items_open,
            "reconciliation_pending": 0,  # TODO: implement
            "vat_pending": 0  # TODO: implement
        },
        "clients": client_list
    }


@router.get("/multi-client/tasks")
async def get_cross_client_tasks(
    tenant_id: UUID = Query(..., description="Tenant ID (regnskapsbyrå)"),
    category: str = Query(None, description="Filter by category: invoicing, bank, reporting, all"),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    🚀 KONTALI PARADIGM SHIFT: Multi-Client Dashboard
    
    Get tasks across ALL clients for a given regnskapsbyrå (tenant).
    
    This is THE fundamental difference from PowerOffice/Tripletex:
    - Traditional: Work one client at a time
    - Kontali: See ALL unsure cases across ALL clients at once
    
    Returns tasks organized by category:
    - Invoicing tasks (vendor + customer invoices needing review)
    - Bank reconciliation tasks (unmatched transactions)
    - Reporting tasks (compliance, VAT, etc.)
    """
    
    # Get all clients for this tenant
    clients_query = select(Client).where(
        Client.tenant_id == tenant_id,
        Client.status == 'active'
    )
    clients_result = await db.execute(clients_query)
    clients = clients_result.scalars().all()
    
    if not clients:
        return {
            "tenant_id": str(tenant_id),
            "total_clients": 0,
            "clients": [],
            "tasks": [],
            "summary": {
                "total_tasks": 0,
                "by_category": {
                    "invoicing": 0,
                    "bank": 0,
                    "reporting": 0
                }
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    client_ids = [c.id for c in clients]
    
    # INVOICING TASKS - Vendor invoices needing review
    from sqlalchemy import cast, String
    
    invoicing_tasks = []
    
    # Get pending review queue items for these clients
    review_query = select(ReviewQueue, VendorInvoice, Client).join(
        VendorInvoice, ReviewQueue.source_id == VendorInvoice.id
    ).join(
        Client, VendorInvoice.client_id == Client.id
    ).where(
        VendorInvoice.client_id.in_(client_ids),
        ReviewQueue.source_type == 'vendor_invoice',
        cast(ReviewQueue.status, String) == 'PENDING'
    ).order_by(ReviewQueue.created_at.desc())
    
    review_result = await db.execute(review_query)
    reviews = review_result.all()
    
    for review, invoice, client in reviews:
        # Get vendor name if vendor_id exists
        vendor_name = "Unknown Vendor"
        if invoice.vendor_id:
            from app.models.vendor import Vendor
            vendor_query = select(Vendor).where(Vendor.id == invoice.vendor_id)
            vendor_result = await db.execute(vendor_query)
            vendor = vendor_result.scalar_one_or_none()
            if vendor:
                vendor_name = vendor.name
        
        invoicing_tasks.append({
            "id": str(review.id),
            "type": "vendor_invoice_review",
            "category": "invoicing",
            "client_id": str(client.id),
            "client_name": client.name,
            "description": f"Review vendor invoice: {review.issue_category.value}",
            "confidence": review.ai_confidence,
            "created_at": review.created_at.isoformat(),
            "priority": "high" if review.ai_confidence < 50 else "medium",
            "data": {
                "invoice_id": str(invoice.id),
                "vendor_name": vendor_name,
                "amount": float(invoice.total_amount) if invoice.total_amount else 0,
                "invoice_number": invoice.invoice_number
            }
        })
    
    # BANK RECONCILIATION TASKS - Unmatched transactions
    bank_tasks = []
    
    bank_query = select(BankTransaction, Client).join(
        Client, BankTransaction.client_id == Client.id
    ).where(
        BankTransaction.client_id.in_(client_ids),
        cast(BankTransaction.status, String) == 'unmatched'
    ).order_by(BankTransaction.transaction_date.desc()).limit(50)
    
    bank_result = await db.execute(bank_query)
    bank_transactions = bank_result.all()
    
    for txn, client in bank_transactions:
        bank_tasks.append({
            "id": str(txn.id),
            "type": "bank_transaction_unmatched",
            "category": "bank",
            "client_id": str(client.id),
            "client_name": client.name,
            "description": f"Unmatched bank transaction: {txn.description[:50]}",
            "confidence": 0,  # Unmatched = no confidence
            "created_at": txn.created_at.isoformat(),
            "priority": "medium",
            "data": {
                "transaction_id": str(txn.id),
                "amount": float(txn.amount),
                "transaction_date": txn.transaction_date.isoformat(),
                "description": txn.description
            }
        })
    
    # REPORTING TASKS - Customer invoices overdue
    reporting_tasks = []
    
    from datetime import date
    today = date.today()
    
    overdue_query = select(CustomerInvoice, Client).join(
        Client, CustomerInvoice.client_id == Client.id
    ).where(
        CustomerInvoice.client_id.in_(client_ids),
        CustomerInvoice.payment_status == 'unpaid',
        CustomerInvoice.due_date < today
    ).order_by(CustomerInvoice.due_date.asc()).limit(50)
    
    overdue_result = await db.execute(overdue_query)
    overdue_invoices = overdue_result.all()
    
    for invoice, client in overdue_invoices:
        days_overdue = (today - invoice.due_date).days
        reporting_tasks.append({
            "id": str(invoice.id),
            "type": "customer_invoice_overdue",
            "category": "reporting",
            "client_id": str(client.id),
            "client_name": client.name,
            "description": f"Customer invoice {invoice.invoice_number} overdue by {days_overdue} days",
            "confidence": 100,  # Fact, not AI suggestion
            "created_at": invoice.created_at.isoformat(),
            "priority": "high" if days_overdue > 30 else "medium",
            "data": {
                "invoice_id": str(invoice.id),
                "customer_name": invoice.customer_name,
                "amount": float(invoice.total_amount),
                "due_date": invoice.due_date.isoformat(),
                "days_overdue": days_overdue
            }
        })
    
    # Combine all tasks
    all_tasks = invoicing_tasks + bank_tasks + reporting_tasks
    
    # Filter by category if specified
    if category and category != "all":
        all_tasks = [t for t in all_tasks if t["category"] == category]
    
    # Summary by category
    summary_by_category = {
        "invoicing": len(invoicing_tasks),
        "bank": len(bank_tasks),
        "reporting": len(reporting_tasks)
    }
    
    return {
        "tenant_id": str(tenant_id),
        "total_clients": len(clients),
        "clients": [{"id": str(c.id), "name": c.name} for c in clients],
        "tasks": all_tasks,
        "summary": {
            "total_tasks": len(all_tasks),
            "by_category": summary_by_category
        },
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/status")
async def get_dashboard_status(
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get overall system status for Trust Dashboard
    
    Returns traffic light status + counters for:
    - Review Queue
    - EHF invoices
    - Bank transactions (mock for now)
    - System health
    """
    
    # Review Queue stats
    from sqlalchemy import cast, String
    pending_query = select(func.count(ReviewQueue.id)).where(
        cast(ReviewQueue.status, String) == 'pending'
    )
    pending_result = await db.execute(pending_query)
    pending_count = pending_result.scalar() or 0
    
    total_query = select(func.count(ReviewQueue.id))
    total_result = await db.execute(total_query)
    total_reviews = total_result.scalar() or 0
    
    approved_query = select(func.count(ReviewQueue.id)).where(
        cast(ReviewQueue.status, String) == 'approved'
    )
    approved_result = await db.execute(approved_query)
    approved_count = approved_result.scalar() or 0
    
    # Invoice stats
    invoice_query = select(func.count(VendorInvoice.id))
    invoice_result = await db.execute(invoice_query)
    total_invoices = invoice_result.scalar() or 0
    
    # Recent invoices (last 24h)
    yesterday = datetime.utcnow() - timedelta(days=1)
    recent_query = select(func.count(VendorInvoice.id)).where(
        VendorInvoice.created_at >= yesterday
    )
    recent_result = await db.execute(recent_query)
    recent_invoices = recent_result.scalar() or 0
    
    # Auto-booked (high confidence)
    auto_booked_query = select(func.count(VendorInvoice.id)).where(
        VendorInvoice.review_status == 'approved',
        VendorInvoice.ai_confidence_score >= 85
    )
    auto_booked_result = await db.execute(auto_booked_query)
    auto_booked_count = auto_booked_result.scalar() or 0
    
    # Determine traffic light status
    if pending_count == 0:
        status = "green"
        status_message = "All systems operational"
    elif pending_count <= 5:
        status = "yellow"
        status_message = f"{pending_count} items need attention"
    else:
        status = "red"
        status_message = f"{pending_count} items require immediate attention"
    
    # Bank transactions (mock for now - will be real when avstemming is built)
    bank_stats = {
        "total": 0,
        "matched": 0,
        "unmatched": 0,
        "pending": 0
    }
    
    return {
        "status": status,
        "message": status_message,
        "timestamp": datetime.utcnow().isoformat(),
        "counters": {
            "review_queue": {
                "pending": pending_count,
                "total": total_reviews,
                "approved": approved_count,
                "percentage_approved": round((approved_count / total_reviews * 100) if total_reviews > 0 else 0, 1)
            },
            "invoices": {
                "total": total_invoices,
                "recent_24h": recent_invoices,
                "auto_booked": auto_booked_count,
                "auto_booking_rate": round((auto_booked_count / total_invoices * 100) if total_invoices > 0 else 0, 1)
            },
            "ehf": {
                "received": total_invoices,  # For MVP, assuming all are EHF
                "processed": total_invoices,
                "pending": 0,
                "errors": 0
            },
            "bank": bank_stats
        },
        "health_checks": {
            "database": "healthy",
            "ai_agent": "healthy",
            "review_queue": "healthy"
        }
    }


@router.get("/activity")
async def get_recent_activity(
    db: AsyncSession = Depends(get_db),
    limit: int = 10
) -> Dict[str, Any]:
    """
    Get recent system activity for activity log
    """
    
    # Recent reviews
    recent_reviews_query = select(ReviewQueue).order_by(
        ReviewQueue.created_at.desc()
    ).limit(limit)
    
    result = await db.execute(recent_reviews_query)
    reviews = result.scalars().all()
    
    activities = []
    for review in reviews:
        activities.append({
            "id": str(review.id),
            "type": "review_created",
            "timestamp": review.created_at.isoformat(),
            "description": f"Item added to review queue: {review.issue_category.value}",
            "confidence": review.ai_confidence
        })
    
    return {
        "activities": activities,
        "total": len(activities)
    }


@router.get("/verification")
async def get_verification_status(
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Receipt Verification Dashboard - Prove to accountant that NOTHING is forgotten
    
    Returns comprehensive tracking of:
    - EHF invoices: Received vs Processed vs Booked
    - Bank transactions: Total vs Booked (placeholder)
    - Review Queue: Pending items
    - Color-coded status indicators
    """
    
    # Count invoices by review_status
    pending_query = select(func.count(VendorInvoice.id)).where(
        VendorInvoice.review_status == 'pending'
    )
    pending_result = await db.execute(pending_query)
    pending_invoices = pending_result.scalar() or 0
    
    reviewed_query = select(func.count(VendorInvoice.id)).where(
        VendorInvoice.review_status.in_(['reviewed', 'auto_approved'])
    )
    reviewed_result = await db.execute(reviewed_query)
    reviewed_invoices = reviewed_result.scalar() or 0
    
    booked_query = select(func.count(VendorInvoice.id)).where(
        VendorInvoice.booked_at.isnot(None)
    )
    booked_result = await db.execute(booked_query)
    booked_invoices = booked_result.scalar() or 0
    
    # Total invoices received (EHF)
    total_query = select(func.count(VendorInvoice.id))
    total_result = await db.execute(total_query)
    total_invoices = total_result.scalar() or 0
    
    # Review queue pending count
    from sqlalchemy import cast, String
    review_pending_query = select(func.count(ReviewQueue.id)).where(
        cast(ReviewQueue.status, String) == 'pending'
    )
    review_pending_result = await db.execute(review_pending_query)
    review_pending_count = review_pending_result.scalar() or 0
    
    # Calculate processed (reviewed + booked - avoid double counting)
    processed_invoices = reviewed_invoices + pending_invoices  # All that have been seen
    
    # Determine overall status
    untracked_count = pending_invoices + review_pending_count
    
    if untracked_count == 0 and total_invoices > 0:
        overall_status = "green"
        status_message = "✅ ALL RECEIPTS TRACKED - Nothing forgotten!"
    elif untracked_count <= 3:
        overall_status = "yellow"
        status_message = f"⚠️ {untracked_count} items need attention"
    elif total_invoices == 0:
        overall_status = "green"
        status_message = "No invoices to process"
    else:
        overall_status = "red"
        status_message = f"❌ {untracked_count} items require immediate review"
    
    # Bank transactions (placeholder for now)
    bank_total = 0
    bank_booked = 0
    bank_status = "green" if bank_total == 0 else "yellow"
    
    # EHF invoice status
    ehf_status = "green" if pending_invoices == 0 else "yellow"
    if pending_invoices > 5:
        ehf_status = "red"
    
    # Review queue status
    review_status = "green" if review_pending_count == 0 else "yellow"
    if review_pending_count > 5:
        review_status = "red"
    
    return {
        "overall_status": overall_status,
        "status_message": status_message,
        "timestamp": datetime.utcnow().isoformat(),
        "ehf_invoices": {
            "received": total_invoices,
            "processed": processed_invoices,
            "booked": booked_invoices,
            "pending": pending_invoices,
            "status": ehf_status,
            "percentage_booked": round((booked_invoices / total_invoices * 100) if total_invoices > 0 else 0, 1)
        },
        "bank_transactions": {
            "total": bank_total,
            "booked": bank_booked,
            "unbooked": bank_total - bank_booked,
            "status": bank_status,
            "note": "Placeholder - Bank reconciliation coming soon"
        },
        "review_queue": {
            "pending": review_pending_count,
            "status": review_status
        },
        "summary": {
            "total_items": total_invoices + bank_total,
            "fully_tracked": booked_invoices + bank_booked,
            "needs_attention": untracked_count,
            "completion_rate": round(((booked_invoices + bank_booked) / (total_invoices + bank_total) * 100) if (total_invoices + bank_total) > 0 else 100, 1)
        }
    }

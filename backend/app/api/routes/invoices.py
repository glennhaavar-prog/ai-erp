"""
Invoice API routes

Handles invoice payment status, filtering, and management.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from uuid import UUID
from datetime import date
from pydantic import BaseModel

from app.database import get_db
from app.services.payment_status_service import PaymentStatusService
from app.models.vendor_invoice import VendorInvoice
from app.models.customer_invoice import CustomerInvoice
from sqlalchemy import select, and_

router = APIRouter(prefix="/api/invoices", tags=["invoices"])


# === Request/Response Models ===

class MarkPaidRequest(BaseModel):
    """Request to manually mark invoice as paid"""
    paid_date: Optional[str] = None  # ISO date string
    notes: Optional[str] = None


class PaymentStatusResponse(BaseModel):
    """Payment status response"""
    success: bool
    invoice_id: str
    payment_status: str
    paid_amount: float
    total_amount: float
    paid_date: Optional[str]


# === Routes ===

@router.get("/{invoice_id}/payment-status")
async def get_payment_status(
    invoice_id: UUID,
    invoice_type: str = Query("vendor", regex="^(vendor|customer)$"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get payment status for an invoice.
    
    Query params:
    - invoice_type: "vendor" or "customer"
    
    Returns:
    - invoice_id
    - payment_status: unpaid/partially_paid/paid/overdue
    - paid_amount: Amount paid so far
    - total_amount: Total invoice amount
    - paid_date: Date when fully paid (if applicable)
    - due_date: Payment due date
    """
    
    if invoice_type == "vendor":
        result = await db.execute(
            select(VendorInvoice).where(VendorInvoice.id == invoice_id)
        )
        invoice = result.scalar_one_or_none()
    else:
        result = await db.execute(
            select(CustomerInvoice).where(CustomerInvoice.id == invoice_id)
        )
        invoice = result.scalar_one_or_none()
    
    if not invoice:
        raise HTTPException(
            status_code=404,
            detail=f"{invoice_type} invoice not found"
        )
    
    return {
        "success": True,
        "invoice_id": str(invoice.id),
        "invoice_type": invoice_type,
        "invoice_number": invoice.invoice_number,
        "payment_status": invoice.payment_status,
        "paid_amount": float(invoice.paid_amount or 0),
        "total_amount": float(invoice.total_amount),
        "remaining_amount": float(invoice.total_amount - (invoice.paid_amount or 0)),
        "paid_date": invoice.paid_date.isoformat() if hasattr(invoice, 'paid_date') and invoice.paid_date else None,
        "due_date": invoice.due_date.isoformat(),
        "invoice_date": invoice.invoice_date.isoformat()
    }


@router.post("/{invoice_id}/mark-paid")
async def mark_invoice_paid(
    invoice_id: UUID,
    request: MarkPaidRequest,
    invoice_type: str = Query("vendor", regex="^(vendor|customer)$"),
    db: AsyncSession = Depends(get_db)
):
    """
    Manually mark an invoice as paid.
    
    Used for:
    - Cash payments
    - Payments confirmed outside the system
    - Manual corrections
    - Write-offs
    
    Query params:
    - invoice_type: "vendor" or "customer"
    
    Body:
    - paid_date: Optional ISO date (defaults to today)
    - notes: Optional note for audit trail
    """
    
    try:
        paid_date_obj = None
        if request.paid_date:
            paid_date_obj = date.fromisoformat(request.paid_date)
        
        result = await PaymentStatusService.mark_invoice_paid(
            db=db,
            invoice_id=invoice_id,
            invoice_type=invoice_type,
            paid_date=paid_date_obj,
            notes=request.notes
        )
        
        return result
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error marking invoice as paid: {str(e)}")


@router.get("")
async def list_invoices(
    status: Optional[str] = Query(None, regex="^(unpaid|partially_paid|paid|overdue)$"),
    invoice_type: str = Query("vendor", regex="^(vendor|customer)$"),
    client_id: Optional[UUID] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """
    List invoices with optional filtering.
    
    Query params:
    - status: Filter by payment status (unpaid/partially_paid/paid/overdue)
    - invoice_type: "vendor" or "customer"
    - client_id: Filter by client
    - from_date: Filter by invoice_date >= from_date (ISO format)
    - to_date: Filter by invoice_date <= to_date (ISO format)
    - limit: Max results (default 100)
    - offset: Pagination offset
    
    Returns:
    - List of invoices matching criteria
    """
    
    if invoice_type == "vendor":
        InvoiceModel = VendorInvoice
    else:
        InvoiceModel = CustomerInvoice
    
    # Build query
    conditions = []
    
    if status:
        conditions.append(InvoiceModel.payment_status == status)
    
    if client_id:
        conditions.append(InvoiceModel.client_id == client_id)
    
    if from_date:
        from_date_obj = date.fromisoformat(from_date)
        conditions.append(InvoiceModel.invoice_date >= from_date_obj)
    
    if to_date:
        to_date_obj = date.fromisoformat(to_date)
        conditions.append(InvoiceModel.invoice_date <= to_date_obj)
    
    # Execute query
    query = select(InvoiceModel)
    
    if conditions:
        query = query.where(and_(*conditions))
    
    query = query.order_by(InvoiceModel.invoice_date.desc())
    query = query.limit(limit).offset(offset)
    
    result = await db.execute(query)
    invoices = result.scalars().all()
    
    # Convert to dict
    invoice_list = []
    for invoice in invoices:
        invoice_dict = {
            "id": str(invoice.id),
            "invoice_number": invoice.invoice_number,
            "invoice_date": invoice.invoice_date.isoformat(),
            "due_date": invoice.due_date.isoformat(),
            "payment_status": invoice.payment_status,
            "total_amount": float(invoice.total_amount),
            "paid_amount": float(invoice.paid_amount or 0),
            "remaining_amount": float(invoice.total_amount - (invoice.paid_amount or 0)),
            "currency": invoice.currency
        }
        
        # Add type-specific fields
        if invoice_type == "vendor":
            invoice_dict["vendor_id"] = str(invoice.vendor_id) if invoice.vendor_id else None
        else:
            invoice_dict["customer_name"] = invoice.customer_name
        
        invoice_list.append(invoice_dict)
    
    return {
        "success": True,
        "invoice_type": invoice_type,
        "filters": {
            "status": status,
            "client_id": str(client_id) if client_id else None,
            "from_date": from_date,
            "to_date": to_date
        },
        "pagination": {
            "limit": limit,
            "offset": offset,
            "count": len(invoice_list)
        },
        "invoices": invoice_list
    }


@router.get("/summary")
async def get_payment_summary(
    invoice_type: str = Query("vendor", regex="^(vendor|customer)$"),
    client_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Get payment status summary for a client.
    
    Returns counts and totals for each payment status:
    - unpaid
    - partially_paid
    - paid
    - overdue
    
    Query params:
    - invoice_type: "vendor" or "customer"
    - client_id: Client UUID (required)
    """
    
    try:
        result = await PaymentStatusService.get_payment_summary(
            db=db,
            client_id=client_id,
            invoice_type=invoice_type
        )
        
        return result
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting payment summary: {str(e)}"
        )


@router.post("/detect-overdue")
async def detect_overdue(
    client_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Manually trigger overdue detection for a client.
    
    Marks invoices as overdue if:
    - due_date < today
    - payment_status is unpaid or partially_paid
    
    This is normally run daily via background task.
    
    Query params:
    - client_id: Client UUID (required)
    """
    
    try:
        result = await PaymentStatusService.detect_overdue_invoices(
            db=db,
            client_id=client_id
        )
        
        return result
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error detecting overdue invoices: {str(e)}"
        )

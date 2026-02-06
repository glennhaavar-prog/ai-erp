"""
Customer Invoice API - Outgoing invoices (sales)
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, date
from typing import Dict, Any, List
from uuid import UUID
from decimal import Decimal
from pydantic import BaseModel

from app.database import get_db
from app.models.customer_invoice import CustomerInvoice
from app.models.client import Client


router = APIRouter(prefix="/api/customer-invoices", tags=["Customer Invoices"])


class CustomerInvoiceCreate(BaseModel):
    """Request body for creating customer invoice"""
    client_id: UUID
    customer_name: str
    customer_org_number: str | None = None
    customer_email: str | None = None
    invoice_number: str
    invoice_date: date
    due_date: date
    kid_number: str | None = None
    amount_excl_vat: float
    vat_amount: float
    total_amount: float
    description: str | None = None
    line_items: List[Dict[str, Any]] = []


@router.post("/")
async def create_customer_invoice(
    invoice: CustomerInvoiceCreate,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Create a new customer invoice (outgoing/sales invoice)
    """
    
    # Validate client exists
    client_query = select(Client).where(Client.id == invoice.client_id)
    client_result = await db.execute(client_query)
    client = client_result.scalar_one_or_none()
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Create invoice
    new_invoice = CustomerInvoice(
        client_id=invoice.client_id,
        customer_name=invoice.customer_name,
        customer_org_number=invoice.customer_org_number,
        customer_email=invoice.customer_email,
        invoice_number=invoice.invoice_number,
        invoice_date=invoice.invoice_date,
        due_date=invoice.due_date,
        kid_number=invoice.kid_number,
        amount_excl_vat=Decimal(str(invoice.amount_excl_vat)),
        vat_amount=Decimal(str(invoice.vat_amount)),
        total_amount=Decimal(str(invoice.total_amount)),
        description=invoice.description,
        line_items=invoice.line_items
    )
    
    db.add(new_invoice)
    await db.commit()
    await db.refresh(new_invoice)
    
    return {
        "success": True,
        "invoice": new_invoice.to_dict(),
        "message": "Customer invoice created"
    }


@router.get("/")
async def list_customer_invoices(
    client_id: UUID = Query(..., description="Client ID"),
    payment_status: str = Query(None, description="Filter by payment status"),
    limit: int = Query(100, le=500),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    List customer invoices for a client
    """
    
    query = select(CustomerInvoice).where(
        CustomerInvoice.client_id == client_id
    )
    
    if payment_status:
        query = query.where(CustomerInvoice.payment_status == payment_status)
    
    query = query.order_by(CustomerInvoice.invoice_date.desc()).limit(limit)
    
    result = await db.execute(query)
    invoices = result.scalars().all()
    
    return {
        "invoices": [inv.to_dict() for inv in invoices],
        "total": len(invoices)
    }


@router.get("/stats")
async def get_customer_invoice_stats(
    client_id: UUID = Query(..., description="Client ID"),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get customer invoice statistics
    """
    
    # Total count
    total_query = select(func.count(CustomerInvoice.id)).where(
        CustomerInvoice.client_id == client_id
    )
    total_result = await db.execute(total_query)
    total = total_result.scalar() or 0
    
    # Unpaid count
    unpaid_query = select(func.count(CustomerInvoice.id)).where(
        CustomerInvoice.client_id == client_id,
        CustomerInvoice.payment_status == 'unpaid'
    )
    unpaid_result = await db.execute(unpaid_query)
    unpaid = unpaid_result.scalar() or 0
    
    # Paid count
    paid_query = select(func.count(CustomerInvoice.id)).where(
        CustomerInvoice.client_id == client_id,
        CustomerInvoice.payment_status == 'paid'
    )
    paid_result = await db.execute(paid_query)
    paid = paid_result.scalar() or 0
    
    # Total amounts
    total_amount_query = select(func.sum(CustomerInvoice.total_amount)).where(
        CustomerInvoice.client_id == client_id
    )
    total_amount_result = await db.execute(total_amount_query)
    total_amount = float(total_amount_result.scalar() or 0)
    
    unpaid_amount_query = select(func.sum(CustomerInvoice.total_amount)).where(
        CustomerInvoice.client_id == client_id,
        CustomerInvoice.payment_status == 'unpaid'
    )
    unpaid_amount_result = await db.execute(unpaid_amount_query)
    unpaid_amount = float(unpaid_amount_result.scalar() or 0)
    
    return {
        "total_invoices": total,
        "unpaid_invoices": unpaid,
        "paid_invoices": paid,
        "total_amount": total_amount,
        "unpaid_amount": unpaid_amount,
        "collection_rate": round((paid / total * 100) if total > 0 else 0, 1)
    }


@router.get("/{invoice_id}")
async def get_customer_invoice(
    invoice_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get a specific customer invoice
    """
    
    query = select(CustomerInvoice).where(CustomerInvoice.id == invoice_id)
    result = await db.execute(query)
    invoice = result.scalar_one_or_none()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    return invoice.to_dict()


@router.patch("/{invoice_id}/payment")
async def mark_invoice_paid(
    invoice_id: UUID,
    paid_amount: float = Query(...),
    payment_date: date = Query(...),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Mark invoice as paid (full or partial)
    """
    
    query = select(CustomerInvoice).where(CustomerInvoice.id == invoice_id)
    result = await db.execute(query)
    invoice = result.scalar_one_or_none()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    invoice.paid_amount = Decimal(str(paid_amount))
    invoice.payment_date = payment_date
    
    # Update status
    if paid_amount >= float(invoice.total_amount):
        invoice.payment_status = 'paid'
    elif paid_amount > 0:
        invoice.payment_status = 'partial'
    
    await db.commit()
    
    return {
        "success": True,
        "invoice": invoice.to_dict(),
        "message": f"Payment of {paid_amount} NOK registered"
    }

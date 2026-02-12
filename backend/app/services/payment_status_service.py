"""
Payment Status Service

Handles automatic payment status updates for vendor and customer invoices.

Features:
- Auto-update on bank transaction matching
- Partial payment tracking
- Overdue detection
- Payment history tracking for audit compliance (Norwegian accounting)
"""

from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, update
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal
import logging

from app.models.vendor_invoice import VendorInvoice
from app.models.customer_invoice import CustomerInvoice
from app.models.bank_transaction import BankTransaction

logger = logging.getLogger(__name__)


class PaymentStatusService:
    """Service for managing invoice payment status"""
    
    @staticmethod
    async def update_vendor_invoice_payment(
        db: AsyncSession,
        invoice_id: UUID,
        payment_amount: Decimal,
        payment_date: date,
        transaction_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Update vendor invoice payment status based on payment transaction.
        
        Logic:
        - If payment_amount >= total_amount → status = 'paid', set paid_date
        - If payment_amount < total_amount → status = 'partially_paid'
        - Accumulate paid_amount from all matched transactions
        
        Args:
            invoice_id: Vendor invoice UUID
            payment_amount: Amount paid in this transaction
            payment_date: Date of payment
            transaction_id: Optional bank transaction ID for audit trail
        
        Returns:
            Dict with updated status information
        """
        
        # Get invoice
        result = await db.execute(
            select(VendorInvoice).where(VendorInvoice.id == invoice_id)
        )
        invoice = result.scalar_one_or_none()
        
        if not invoice:
            raise ValueError(f"Vendor invoice {invoice_id} not found")
        
        # Calculate new paid amount
        previous_paid = invoice.paid_amount or Decimal("0.00")
        new_paid_amount = previous_paid + payment_amount
        
        # Determine new status
        total_amount = invoice.total_amount
        
        if new_paid_amount >= total_amount:
            new_status = "paid"
            paid_date = payment_date
        elif new_paid_amount > Decimal("0.00"):
            new_status = "partially_paid"
            paid_date = None
        else:
            new_status = "unpaid"
            paid_date = None
        
        # Update invoice
        invoice.paid_amount = new_paid_amount
        invoice.payment_status = new_status
        
        if paid_date:
            invoice.paid_date = paid_date
        
        invoice.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(invoice)
        
        logger.info(
            f"Updated vendor invoice {invoice_id}: "
            f"paid_amount={new_paid_amount}, status={new_status}"
        )
        
        return {
            "success": True,
            "invoice_id": str(invoice_id),
            "previous_paid": float(previous_paid),
            "payment_amount": float(payment_amount),
            "new_paid_amount": float(new_paid_amount),
            "total_amount": float(total_amount),
            "previous_status": invoice.payment_status,
            "new_status": new_status,
            "paid_date": paid_date.isoformat() if paid_date else None,
            "transaction_id": str(transaction_id) if transaction_id else None
        }
    
    @staticmethod
    async def update_customer_invoice_payment(
        db: AsyncSession,
        invoice_id: UUID,
        payment_amount: Decimal,
        payment_date: date,
        transaction_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Update customer invoice payment status based on payment transaction.
        
        Same logic as vendor invoices but for outgoing invoices.
        
        Args:
            invoice_id: Customer invoice UUID
            payment_amount: Amount received in this transaction
            payment_date: Date of payment
            transaction_id: Optional bank transaction ID for audit trail
        
        Returns:
            Dict with updated status information
        """
        
        # Get invoice
        result = await db.execute(
            select(CustomerInvoice).where(CustomerInvoice.id == invoice_id)
        )
        invoice = result.scalar_one_or_none()
        
        if not invoice:
            raise ValueError(f"Customer invoice {invoice_id} not found")
        
        # Calculate new paid amount
        previous_paid = invoice.paid_amount or Decimal("0.00")
        new_paid_amount = previous_paid + payment_amount
        
        # Determine new status
        total_amount = invoice.total_amount
        
        if new_paid_amount >= total_amount:
            new_status = "paid"
            paid_date = payment_date
        elif new_paid_amount > Decimal("0.00"):
            new_status = "partially_paid"
            paid_date = None
        else:
            new_status = "unpaid"
            paid_date = None
        
        # Update invoice
        invoice.paid_amount = new_paid_amount
        invoice.payment_status = new_status
        
        if paid_date:
            invoice.paid_date = paid_date
        
        invoice.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(invoice)
        
        logger.info(
            f"Updated customer invoice {invoice_id}: "
            f"paid_amount={new_paid_amount}, status={new_status}"
        )
        
        return {
            "success": True,
            "invoice_id": str(invoice_id),
            "previous_paid": float(previous_paid),
            "payment_amount": float(payment_amount),
            "new_paid_amount": float(new_paid_amount),
            "total_amount": float(total_amount),
            "previous_status": invoice.payment_status,
            "new_status": new_status,
            "paid_date": paid_date.isoformat() if paid_date else None,
            "transaction_id": str(transaction_id) if transaction_id else None
        }
    
    @staticmethod
    async def mark_invoice_paid(
        db: AsyncSession,
        invoice_id: UUID,
        invoice_type: str,
        paid_date: Optional[date] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Manually mark an invoice as paid (override).
        
        Used when payment is confirmed outside bank transaction matching
        (e.g., cash payment, correction, write-off).
        
        Args:
            invoice_id: Invoice UUID
            invoice_type: "vendor" or "customer"
            paid_date: Date invoice was paid (defaults to today)
            notes: Optional note for audit trail
        
        Returns:
            Dict with updated status
        """
        
        if not paid_date:
            paid_date = date.today()
        
        if invoice_type == "vendor":
            result = await db.execute(
                select(VendorInvoice).where(VendorInvoice.id == invoice_id)
            )
            invoice = result.scalar_one_or_none()
        elif invoice_type == "customer":
            result = await db.execute(
                select(CustomerInvoice).where(CustomerInvoice.id == invoice_id)
            )
            invoice = result.scalar_one_or_none()
        else:
            raise ValueError(f"Invalid invoice_type: {invoice_type}")
        
        if not invoice:
            raise ValueError(f"{invoice_type} invoice {invoice_id} not found")
        
        # Set to fully paid
        invoice.payment_status = "paid"
        invoice.paid_amount = invoice.total_amount
        invoice.paid_date = paid_date
        invoice.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(invoice)
        
        logger.info(
            f"Manually marked {invoice_type} invoice {invoice_id} as paid "
            f"(date: {paid_date}, notes: {notes})"
        )
        
        return {
            "success": True,
            "invoice_id": str(invoice_id),
            "invoice_type": invoice_type,
            "status": "paid",
            "paid_amount": float(invoice.total_amount),
            "paid_date": paid_date.isoformat(),
            "notes": notes
        }
    
    @staticmethod
    async def detect_overdue_invoices(
        db: AsyncSession,
        client_id: UUID
    ) -> Dict[str, Any]:
        """
        Detect and mark overdue invoices.
        
        Logic:
        - If due_date < today AND payment_status != 'paid' → mark as 'overdue'
        
        Should be run daily via background task.
        
        Args:
            client_id: Client UUID
        
        Returns:
            Dict with count of invoices marked overdue
        """
        
        today = date.today()
        
        # Update overdue vendor invoices
        vendor_result = await db.execute(
            update(VendorInvoice)
            .where(
                and_(
                    VendorInvoice.client_id == client_id,
                    VendorInvoice.due_date < today,
                    VendorInvoice.payment_status.in_(['unpaid', 'partially_paid'])
                )
            )
            .values(payment_status='overdue', updated_at=datetime.utcnow())
            .execution_options(synchronize_session=False)
        )
        
        vendor_count = vendor_result.rowcount
        
        # Update overdue customer invoices
        customer_result = await db.execute(
            update(CustomerInvoice)
            .where(
                and_(
                    CustomerInvoice.client_id == client_id,
                    CustomerInvoice.due_date < today,
                    CustomerInvoice.payment_status.in_(['unpaid', 'partially_paid'])
                )
            )
            .values(payment_status='overdue', updated_at=datetime.utcnow())
            .execution_options(synchronize_session=False)
        )
        
        customer_count = customer_result.rowcount
        
        await db.commit()
        
        logger.info(
            f"Overdue detection: marked {vendor_count} vendor invoices "
            f"and {customer_count} customer invoices as overdue"
        )
        
        return {
            "success": True,
            "client_id": str(client_id),
            "vendor_invoices_overdue": vendor_count,
            "customer_invoices_overdue": customer_count,
            "total_overdue": vendor_count + customer_count,
            "check_date": today.isoformat()
        }
    
    @staticmethod
    async def get_payment_summary(
        db: AsyncSession,
        client_id: UUID,
        invoice_type: str = "vendor"
    ) -> Dict[str, Any]:
        """
        Get payment status summary for a client.
        
        Args:
            client_id: Client UUID
            invoice_type: "vendor" or "customer"
        
        Returns:
            Dict with payment status counts and amounts
        """
        
        if invoice_type == "vendor":
            InvoiceModel = VendorInvoice
        else:
            InvoiceModel = CustomerInvoice
        
        # Get all invoices for client
        result = await db.execute(
            select(InvoiceModel).where(InvoiceModel.client_id == client_id)
        )
        invoices = result.scalars().all()
        
        # Calculate summary
        summary = {
            "unpaid": {"count": 0, "total_amount": Decimal("0.00")},
            "partially_paid": {"count": 0, "total_amount": Decimal("0.00"), "paid_amount": Decimal("0.00")},
            "paid": {"count": 0, "total_amount": Decimal("0.00")},
            "overdue": {"count": 0, "total_amount": Decimal("0.00")}
        }
        
        for invoice in invoices:
            status = invoice.payment_status
            if status in summary:
                summary[status]["count"] += 1
                summary[status]["total_amount"] += invoice.total_amount
                
                if status == "partially_paid":
                    summary[status]["paid_amount"] += (invoice.paid_amount or Decimal("0.00"))
        
        # Convert Decimal to float for JSON serialization
        for status in summary:
            for key in summary[status]:
                if isinstance(summary[status][key], Decimal):
                    summary[status][key] = float(summary[status][key])
        
        return {
            "success": True,
            "client_id": str(client_id),
            "invoice_type": invoice_type,
            "summary": summary
        }

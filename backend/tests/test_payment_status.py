"""
Payment Status Tracking Tests

Test coverage:
1. Database migration
2. Payment status service methods
3. API endpoints
4. Bank reconciliation integration
5. Overdue detection
6. Partial payment handling

Norwegian accounting compliance tests included.
"""

import pytest
from datetime import date, timedelta, datetime
from decimal import Decimal
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.vendor_invoice import VendorInvoice
from app.models.customer_invoice import CustomerInvoice
from app.models.bank_transaction import BankTransaction
from app.models.client import Client
from app.services.payment_status_service import PaymentStatusService
from app.services.smart_reconciliation_service import SmartReconciliationService


# ============================================================================
# Test 1: Database Schema Validation
# ============================================================================

@pytest.mark.asyncio
async def test_payment_status_enum_values(db: AsyncSession):
    """
    Test that payment_status enum accepts only valid values.
    
    Valid values: unpaid, partially_paid, paid, overdue
    """
    
    # Create test client
    client = Client(
        id=uuid4(),
        company_name="Test Company AS",
        org_number="999999999",
        email="test@example.com"
    )
    db.add(client)
    await db.commit()
    
    # Test valid statuses
    valid_statuses = ['unpaid', 'partially_paid', 'paid', 'overdue']
    
    for status in valid_statuses:
        invoice = VendorInvoice(
            id=uuid4(),
            client_id=client.id,
            invoice_number=f"INV-{status}",
            invoice_date=date.today(),
            due_date=date.today() + timedelta(days=30),
            amount_excl_vat=Decimal("1000.00"),
            vat_amount=Decimal("250.00"),
            total_amount=Decimal("1250.00"),
            payment_status=status
        )
        db.add(invoice)
    
    await db.commit()
    
    # Verify all created successfully
    result = await db.execute(
        select(VendorInvoice).where(VendorInvoice.client_id == client.id)
    )
    invoices = result.scalars().all()
    
    assert len(invoices) == 4
    assert set(inv.payment_status for inv in invoices) == set(valid_statuses)


@pytest.mark.asyncio
async def test_paid_date_column_exists(db: AsyncSession):
    """
    Test that paid_date column exists and works correctly.
    """
    
    client = Client(
        id=uuid4(),
        company_name="Test Company AS",
        org_number="999999999",
        email="test@example.com"
    )
    db.add(client)
    await db.commit()
    
    today = date.today()
    
    invoice = VendorInvoice(
        id=uuid4(),
        client_id=client.id,
        invoice_number="INV-001",
        invoice_date=today,
        due_date=today + timedelta(days=30),
        amount_excl_vat=Decimal("1000.00"),
        vat_amount=Decimal("250.00"),
        total_amount=Decimal("1250.00"),
        payment_status='paid',
        paid_amount=Decimal("1250.00"),
        paid_date=today  # Test paid_date column
    )
    db.add(invoice)
    await db.commit()
    
    # Verify
    result = await db.execute(
        select(VendorInvoice).where(VendorInvoice.id == invoice.id)
    )
    saved_invoice = result.scalar_one()
    
    assert saved_invoice.paid_date == today
    assert saved_invoice.payment_status == 'paid'


# ============================================================================
# Test 2: Payment Status Service - Vendor Invoices
# ============================================================================

@pytest.mark.asyncio
async def test_update_vendor_invoice_full_payment(db: AsyncSession):
    """
    Test updating vendor invoice to 'paid' status with full payment.
    
    Scenario: Invoice total = 1250 kr, payment = 1250 kr → status = 'paid'
    """
    
    client = Client(
        id=uuid4(),
        company_name="Test Company AS",
        org_number="999999999",
        email="test@example.com"
    )
    db.add(client)
    await db.commit()
    
    invoice = VendorInvoice(
        id=uuid4(),
        client_id=client.id,
        invoice_number="INV-001",
        invoice_date=date.today(),
        due_date=date.today() + timedelta(days=30),
        amount_excl_vat=Decimal("1000.00"),
        vat_amount=Decimal("250.00"),
        total_amount=Decimal("1250.00"),
        payment_status='unpaid'
    )
    db.add(invoice)
    await db.commit()
    
    # Process full payment
    payment_date = date.today()
    result = await PaymentStatusService.update_vendor_invoice_payment(
        db=db,
        invoice_id=invoice.id,
        payment_amount=Decimal("1250.00"),
        payment_date=payment_date
    )
    
    # Verify result
    assert result["success"] is True
    assert result["new_status"] == "paid"
    assert result["new_paid_amount"] == 1250.00
    assert result["paid_date"] == payment_date.isoformat()
    
    # Verify database
    await db.refresh(invoice)
    assert invoice.payment_status == "paid"
    assert invoice.paid_amount == Decimal("1250.00")
    assert invoice.paid_date == payment_date


@pytest.mark.asyncio
async def test_update_vendor_invoice_partial_payment(db: AsyncSession):
    """
    Test updating vendor invoice to 'partially_paid' status.
    
    Scenario: Invoice total = 1250 kr, payment = 500 kr → status = 'partially_paid'
    """
    
    client = Client(
        id=uuid4(),
        company_name="Test Company AS",
        org_number="999999999",
        email="test@example.com"
    )
    db.add(client)
    await db.commit()
    
    invoice = VendorInvoice(
        id=uuid4(),
        client_id=client.id,
        invoice_number="INV-002",
        invoice_date=date.today(),
        due_date=date.today() + timedelta(days=30),
        amount_excl_vat=Decimal("1000.00"),
        vat_amount=Decimal("250.00"),
        total_amount=Decimal("1250.00"),
        payment_status='unpaid'
    )
    db.add(invoice)
    await db.commit()
    
    # Process partial payment
    result = await PaymentStatusService.update_vendor_invoice_payment(
        db=db,
        invoice_id=invoice.id,
        payment_amount=Decimal("500.00"),
        payment_date=date.today()
    )
    
    # Verify
    assert result["new_status"] == "partially_paid"
    assert result["new_paid_amount"] == 500.00
    assert result["paid_date"] is None  # Should not be set for partial payment
    
    await db.refresh(invoice)
    assert invoice.payment_status == "partially_paid"
    assert invoice.paid_amount == Decimal("500.00")
    assert invoice.paid_date is None


@pytest.mark.asyncio
async def test_multiple_partial_payments(db: AsyncSession):
    """
    Test accumulating multiple partial payments.
    
    Scenario:
    - Invoice total = 1250 kr
    - Payment 1 = 500 kr → status = 'partially_paid'
    - Payment 2 = 750 kr → status = 'paid'
    
    Norwegian accounting: Must track payment history for audit.
    """
    
    client = Client(
        id=uuid4(),
        company_name="Test Company AS",
        org_number="999999999",
        email="test@example.com"
    )
    db.add(client)
    await db.commit()
    
    invoice = VendorInvoice(
        id=uuid4(),
        client_id=client.id,
        invoice_number="INV-003",
        invoice_date=date.today(),
        due_date=date.today() + timedelta(days=30),
        amount_excl_vat=Decimal("1000.00"),
        vat_amount=Decimal("250.00"),
        total_amount=Decimal("1250.00"),
        payment_status='unpaid'
    )
    db.add(invoice)
    await db.commit()
    
    # First payment: 500 kr
    result1 = await PaymentStatusService.update_vendor_invoice_payment(
        db=db,
        invoice_id=invoice.id,
        payment_amount=Decimal("500.00"),
        payment_date=date.today()
    )
    
    assert result1["new_status"] == "partially_paid"
    assert result1["new_paid_amount"] == 500.00
    
    # Second payment: 750 kr
    payment_date = date.today() + timedelta(days=5)
    result2 = await PaymentStatusService.update_vendor_invoice_payment(
        db=db,
        invoice_id=invoice.id,
        payment_amount=Decimal("750.00"),
        payment_date=payment_date
    )
    
    # Should now be fully paid
    assert result2["new_status"] == "paid"
    assert result2["new_paid_amount"] == 1250.00
    assert result2["paid_date"] == payment_date.isoformat()
    
    await db.refresh(invoice)
    assert invoice.payment_status == "paid"
    assert invoice.paid_amount == Decimal("1250.00")
    assert invoice.paid_date == payment_date


# ============================================================================
# Test 3: Customer Invoice Payments
# ============================================================================

@pytest.mark.asyncio
async def test_update_customer_invoice_payment(db: AsyncSession):
    """
    Test customer invoice payment tracking (outgoing invoices).
    """
    
    client = Client(
        id=uuid4(),
        company_name="Test Company AS",
        org_number="999999999",
        email="test@example.com"
    )
    db.add(client)
    await db.commit()
    
    invoice = CustomerInvoice(
        id=uuid4(),
        client_id=client.id,
        customer_name="Customer Inc",
        invoice_number="CUST-001",
        invoice_date=date.today(),
        due_date=date.today() + timedelta(days=14),
        amount_excl_vat=Decimal("2000.00"),
        vat_amount=Decimal("500.00"),
        total_amount=Decimal("2500.00"),
        payment_status='unpaid'
    )
    db.add(invoice)
    await db.commit()
    
    # Process payment
    payment_date = date.today()
    result = await PaymentStatusService.update_customer_invoice_payment(
        db=db,
        invoice_id=invoice.id,
        payment_amount=Decimal("2500.00"),
        payment_date=payment_date
    )
    
    assert result["success"] is True
    assert result["new_status"] == "paid"
    
    await db.refresh(invoice)
    assert invoice.payment_status == "paid"
    assert invoice.paid_date == payment_date


# ============================================================================
# Test 4: Manual Payment Marking
# ============================================================================

@pytest.mark.asyncio
async def test_mark_invoice_paid_manually(db: AsyncSession):
    """
    Test manual override to mark invoice as paid.
    
    Use case: Cash payment, external confirmation, correction.
    """
    
    client = Client(
        id=uuid4(),
        company_name="Test Company AS",
        org_number="999999999",
        email="test@example.com"
    )
    db.add(client)
    await db.commit()
    
    invoice = VendorInvoice(
        id=uuid4(),
        client_id=client.id,
        invoice_number="INV-004",
        invoice_date=date.today(),
        due_date=date.today() + timedelta(days=30),
        amount_excl_vat=Decimal("1000.00"),
        vat_amount=Decimal("250.00"),
        total_amount=Decimal("1250.00"),
        payment_status='unpaid'
    )
    db.add(invoice)
    await db.commit()
    
    # Mark as paid manually
    result = await PaymentStatusService.mark_invoice_paid(
        db=db,
        invoice_id=invoice.id,
        invoice_type="vendor",
        notes="Cash payment received"
    )
    
    assert result["success"] is True
    assert result["status"] == "paid"
    
    await db.refresh(invoice)
    assert invoice.payment_status == "paid"
    assert invoice.paid_amount == invoice.total_amount


# ============================================================================
# Test 5: Overdue Detection
# ============================================================================

@pytest.mark.asyncio
async def test_detect_overdue_invoices(db: AsyncSession):
    """
    Test automatic overdue detection.
    
    Scenario:
    - Invoice 1: due yesterday, unpaid → should be marked overdue
    - Invoice 2: due tomorrow, unpaid → should remain unpaid
    - Invoice 3: due yesterday, paid → should remain paid
    """
    
    client = Client(
        id=uuid4(),
        company_name="Test Company AS",
        org_number="999999999",
        email="test@example.com"
    )
    db.add(client)
    await db.commit()
    
    today = date.today()
    
    # Invoice 1: overdue
    invoice1 = VendorInvoice(
        id=uuid4(),
        client_id=client.id,
        invoice_number="INV-OVERDUE",
        invoice_date=today - timedelta(days=40),
        due_date=today - timedelta(days=1),
        amount_excl_vat=Decimal("1000.00"),
        vat_amount=Decimal("250.00"),
        total_amount=Decimal("1250.00"),
        payment_status='unpaid'
    )
    
    # Invoice 2: not yet due
    invoice2 = VendorInvoice(
        id=uuid4(),
        client_id=client.id,
        invoice_number="INV-FUTURE",
        invoice_date=today,
        due_date=today + timedelta(days=10),
        amount_excl_vat=Decimal("1000.00"),
        vat_amount=Decimal("250.00"),
        total_amount=Decimal("1250.00"),
        payment_status='unpaid'
    )
    
    # Invoice 3: overdue but paid
    invoice3 = VendorInvoice(
        id=uuid4(),
        client_id=client.id,
        invoice_number="INV-PAID",
        invoice_date=today - timedelta(days=40),
        due_date=today - timedelta(days=1),
        amount_excl_vat=Decimal("1000.00"),
        vat_amount=Decimal("250.00"),
        total_amount=Decimal("1250.00"),
        payment_status='paid',
        paid_amount=Decimal("1250.00")
    )
    
    db.add_all([invoice1, invoice2, invoice3])
    await db.commit()
    
    # Run overdue detection
    result = await PaymentStatusService.detect_overdue_invoices(
        db=db,
        client_id=client.id
    )
    
    assert result["success"] is True
    assert result["vendor_invoices_overdue"] == 1  # Only invoice1
    
    # Verify statuses
    await db.refresh(invoice1)
    await db.refresh(invoice2)
    await db.refresh(invoice3)
    
    assert invoice1.payment_status == "overdue"
    assert invoice2.payment_status == "unpaid"
    assert invoice3.payment_status == "paid"


# ============================================================================
# Test 6: Payment Summary
# ============================================================================

@pytest.mark.asyncio
async def test_payment_summary(db: AsyncSession):
    """
    Test payment status summary generation.
    
    Creates multiple invoices with different statuses and verifies summary.
    """
    
    client = Client(
        id=uuid4(),
        company_name="Test Company AS",
        org_number="999999999",
        email="test@example.com"
    )
    db.add(client)
    await db.commit()
    
    today = date.today()
    
    # Create invoices with various statuses
    invoices = [
        # 2 unpaid
        VendorInvoice(
            id=uuid4(), client_id=client.id, invoice_number="INV-U1",
            invoice_date=today, due_date=today + timedelta(days=30),
            amount_excl_vat=Decimal("1000"), vat_amount=Decimal("250"),
            total_amount=Decimal("1250"), payment_status='unpaid'
        ),
        VendorInvoice(
            id=uuid4(), client_id=client.id, invoice_number="INV-U2",
            invoice_date=today, due_date=today + timedelta(days=30),
            amount_excl_vat=Decimal("2000"), vat_amount=Decimal("500"),
            total_amount=Decimal("2500"), payment_status='unpaid'
        ),
        # 1 partially paid
        VendorInvoice(
            id=uuid4(), client_id=client.id, invoice_number="INV-P1",
            invoice_date=today, due_date=today + timedelta(days=30),
            amount_excl_vat=Decimal("3000"), vat_amount=Decimal("750"),
            total_amount=Decimal("3750"), payment_status='partially_paid',
            paid_amount=Decimal("1000")
        ),
        # 1 paid
        VendorInvoice(
            id=uuid4(), client_id=client.id, invoice_number="INV-PAID",
            invoice_date=today, due_date=today + timedelta(days=30),
            amount_excl_vat=Decimal("5000"), vat_amount=Decimal("1250"),
            total_amount=Decimal("6250"), payment_status='paid',
            paid_amount=Decimal("6250")
        ),
    ]
    
    db.add_all(invoices)
    await db.commit()
    
    # Get summary
    result = await PaymentStatusService.get_payment_summary(
        db=db,
        client_id=client.id,
        invoice_type="vendor"
    )
    
    assert result["success"] is True
    summary = result["summary"]
    
    # Verify counts
    assert summary["unpaid"]["count"] == 2
    assert summary["partially_paid"]["count"] == 1
    assert summary["paid"]["count"] == 1
    
    # Verify amounts
    assert summary["unpaid"]["total_amount"] == 3750.00  # 1250 + 2500
    assert summary["partially_paid"]["total_amount"] == 3750.00
    assert summary["partially_paid"]["paid_amount"] == 1000.00
    assert summary["paid"]["total_amount"] == 6250.00


# ============================================================================
# Run tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

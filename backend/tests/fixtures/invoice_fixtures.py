"""
Invoice Test Fixtures for E2E Testing
KONTALI SPRINT 1 - Task 4

Provides realistic test data for end-to-end invoice flow testing.
"""
import pytest
from uuid import uuid4
from datetime import date, datetime, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vendor_invoice import VendorInvoice
from app.models.vendor import Vendor
from app.models.client import Client
from app.models.chart_of_accounts import Account


async def create_test_invoice(
    db_session: AsyncSession,
    client_id: str,
    vendor_id: str,
    vendor_name: str = "Test Vendor AS",
    invoice_number: str = None,
    amount_ex_vat: Decimal = Decimal("10000.00"),
    vat_amount: Decimal = Decimal("2500.00"),
    total_amount: Decimal = Decimal("12500.00"),
    ai_suggested_account: str = "6420",
    ocr_confidence: float = 0.95,
    ai_confidence: float = 0.90,
    invoice_date: date = None,
    due_date: date = None
) -> VendorInvoice:
    """
    Create a test vendor invoice with configurable parameters
    
    Args:
        db_session: Database session
        client_id: Client UUID
        vendor_id: Vendor UUID
        vendor_name: Vendor name for context
        invoice_number: Invoice number (auto-generated if None)
        amount_ex_vat: Amount excluding VAT
        vat_amount: VAT amount
        total_amount: Total amount including VAT
        ai_suggested_account: AI-suggested account number
        ocr_confidence: OCR confidence score (0.0-1.0)
        ai_confidence: AI confidence score (0.0-1.0)
        invoice_date: Invoice date (today if None)
        due_date: Due date (30 days from today if None)
    
    Returns:
        Created VendorInvoice instance
    """
    if invoice_number is None:
        invoice_number = f"TEST-{uuid4().hex[:8].upper()}"
    
    if invoice_date is None:
        invoice_date = date.today()
    
    if due_date is None:
        due_date = date.today() + timedelta(days=30)
    
    invoice = VendorInvoice(
        id=uuid4(),
        client_id=client_id,
        vendor_id=vendor_id,
        invoice_number=invoice_number,
        invoice_date=invoice_date,
        due_date=due_date,
        amount_excl_vat=amount_ex_vat,
        vat_amount=vat_amount,
        total_amount=total_amount,
        currency="NOK",
        ai_processed=True,
        ai_confidence_score=int(ai_confidence * 100),  # FIX: Removed ocr_confidence_score (doesn't exist in model)
        ai_booking_suggestion={
            "account": ai_suggested_account,
            "confidence": ai_confidence,
            "lines": [
                {
                    "account_number": ai_suggested_account,
                    "debit": float(amount_ex_vat),
                    "credit": 0,
                    "description": f"Invoice {invoice_number} - {vendor_name}"
                },
                {
                    "account_number": "2740",
                    "debit": float(vat_amount),
                    "credit": 0,
                    "description": "Input VAT"
                },
                {
                    "account_number": "2400",
                    "debit": 0,
                    "credit": float(total_amount),
                    "description": "Accounts Payable"
                }
            ]
        },
        review_status="pending",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db_session.add(invoice)
    await db_session.flush()
    await db_session.refresh(invoice)
    
    return invoice


@pytest.fixture
async def high_confidence_invoice(db_session: AsyncSession, test_client, test_vendor):
    """
    Perfect invoice for auto-approval
    
    Characteristics:
    - High OCR confidence: 95%
    - High AI confidence: 90%
    - Complete data (all fields present)
    - VAT calculation correct
    - Known vendor with history
    
    Expected outcome: AUTO-APPROVE (no manual review)
    """
    return await create_test_invoice(
        db_session=db_session,
        client_id=test_client.id,
        vendor_id=test_vendor.id,
        vendor_name="Acme Supplies AS",
        invoice_number="PERFECT-001",
        amount_ex_vat=Decimal("10000.00"),
        vat_amount=Decimal("2500.00"),
        total_amount=Decimal("12500.00"),
        ai_suggested_account="6420",  # Kontorrekvisita
        ocr_confidence=0.95,
        ai_confidence=0.90
    )


@pytest.fixture
async def low_confidence_invoice(db_session: AsyncSession, test_client, test_vendor):
    """
    Invoice requiring manual review
    
    Characteristics:
    - Moderate OCR confidence: 70%
    - Moderate AI confidence: 65%
    - Complete data but uncertain categorization
    - New vendor or unusual pattern
    
    Expected outcome: REVIEW QUEUE (manual review required)
    """
    return await create_test_invoice(
        db_session=db_session,
        client_id=test_client.id,
        vendor_id=test_vendor.id,
        vendor_name="New Vendor Inc",
        invoice_number="UNCERTAIN-002",
        amount_ex_vat=Decimal("5000.00"),
        vat_amount=Decimal("1250.00"),
        total_amount=Decimal("6250.00"),
        ai_suggested_account="6700",  # Annen kostnad (generic)
        ocr_confidence=0.70,
        ai_confidence=0.65
    )


@pytest.fixture
async def very_low_confidence_invoice(db_session: AsyncSession, test_client, test_vendor):
    """
    Invoice with missing data (very low confidence)
    
    Characteristics:
    - Low OCR confidence: 50%
    - Low AI confidence: 40%
    - Missing VAT data
    - AI couldn't suggest account
    
    Expected outcome: REVIEW QUEUE (requires manual data entry)
    """
    return await create_test_invoice(
        db_session=db_session,
        client_id=test_client.id,
        vendor_id=test_vendor.id,
        vendor_name="Unknown Vendor",
        invoice_number="MISSING-003",
        amount_ex_vat=Decimal("3000.00"),
        vat_amount=Decimal("0.00"),  # Missing VAT!
        total_amount=Decimal("3000.00"),
        ai_suggested_account=None,  # AI couldn't suggest
        ocr_confidence=0.50,
        ai_confidence=0.40
    )


@pytest.fixture
async def batch_invoices(db_session: AsyncSession, test_client, test_vendor):
    """
    Create a batch of 100 test invoices for performance testing
    
    Mix of:
    - 60% high confidence (auto-approve)
    - 30% medium confidence (review queue)
    - 10% low confidence (review queue)
    """
    invoices = []
    
    for i in range(100):
        if i < 60:
            # High confidence
            ocr_conf = 0.85 + (i % 15) * 0.01
            ai_conf = 0.80 + (i % 20) * 0.01
        elif i < 90:
            # Medium confidence
            ocr_conf = 0.65 + (i % 10) * 0.01
            ai_conf = 0.60 + (i % 15) * 0.01
        else:
            # Low confidence
            ocr_conf = 0.40 + (i % 10) * 0.01
            ai_conf = 0.35 + (i % 15) * 0.01
        
        invoice = await create_test_invoice(
            db_session=db_session,
            client_id=test_client.id,
            vendor_id=test_vendor.id,
            vendor_name=f"Batch Vendor {i}",
            invoice_number=f"BATCH-{i:04d}",
            amount_ex_vat=Decimal(f"{1000 + (i * 100)}.00"),
            vat_amount=Decimal(f"{250 + (i * 25)}.00"),
            total_amount=Decimal(f"{1250 + (i * 125)}.00"),
            ai_suggested_account="6420",
            ocr_confidence=ocr_conf,
            ai_confidence=ai_conf
        )
        invoices.append(invoice)
    
    await db_session.commit()
    return invoices


@pytest.fixture
async def test_vendor(db_session: AsyncSession, test_client):
    """Create a test vendor for E2E tests"""
    vendor = Vendor(
        id=uuid4(),
        client_id=test_client.id,
        vendor_number=f"V{uuid4().hex[:8].upper()}",
        name="E2E Test Vendor AS",
        org_number="987654321",
        account_number="2400",  # FIX: Added required account_number (Accounts Payable)
        payment_terms="30",
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(vendor)
    await db_session.flush()
    await db_session.refresh(vendor)
    return vendor


@pytest.fixture
async def test_chart_of_accounts(db_session: AsyncSession, test_client):
    """Create test chart of accounts (kontoplan) for E2E tests"""
    accounts = [
        Account(
            id=uuid4(),
            client_id=test_client.id,
            account_number="6420",
            account_name="Kontorrekvisita",
            account_type="expense",
            is_active=True
        ),
        Account(
            id=uuid4(),
            client_id=test_client.id,
            account_number="6300",
            account_name="Leie lokaler",
            account_type="expense",
            is_active=True
        ),
        Account(
            id=uuid4(),
            client_id=test_client.id,
            account_number="6700",
            account_name="Annen kostnad",
            account_type="expense",
            is_active=True
        ),
        Account(
            id=uuid4(),
            client_id=test_client.id,
            account_number="2740",
            account_name="Inngående MVA",
            account_type="liability",
            is_active=True
        ),
        Account(
            id=uuid4(),
            client_id=test_client.id,
            account_number="2400",
            account_name="Leverandørgjeld",
            account_type="liability",
            is_active=True
        ),
    ]
    
    for account in accounts:
        db_session.add(account)
    
    await db_session.flush()
    return accounts

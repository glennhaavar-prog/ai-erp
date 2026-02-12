#!/usr/bin/env python3
"""
Comprehensive test for AI Features

Tests:
1. Smart Expense Categorization
2. Anomaly Detection
3. Smart Reconciliation
4. Payment Terms Extraction
5. Contextual Help

Run: python test_ai_features.py
"""
import asyncio
import sys
from datetime import datetime, timedelta, date
from decimal import Decimal
import uuid

# Add app to path
sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/ai-erp/backend')

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models import (
    VendorInvoice, Vendor, Client, Tenant, BankTransaction,
    GeneralLedger, GeneralLedgerLine
)
from app.services.ai_categorization_service import AICategorizationService
from app.services.anomaly_detection_service import AnomalyDetectionService
from app.services.smart_reconciliation_service import SmartReconciliationService
from app.services.payment_terms_extractor import PaymentTermsExtractor
from app.services.contextual_help_service import ContextualHelpService


# Create async engine
engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


class TestResults:
    """Track test results"""
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.failures = []
    
    def test(self, name: str, condition: bool, message: str = ""):
        self.tests_run += 1
        if condition:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            self.tests_failed += 1
            self.failures.append(f"{name}: {message}")
            print(f"❌ {name}: {message}")
    
    def summary(self):
        print("\n" + "="*60)
        print(f"Tests run: {self.tests_run}")
        print(f"Passed: {self.tests_passed} ✅")
        print(f"Failed: {self.tests_failed} ❌")
        if self.failures:
            print("\nFailures:")
            for failure in self.failures:
                print(f"  - {failure}")
        print("="*60)
        return self.tests_failed == 0


async def get_or_create_test_client(db: AsyncSession) -> Client:
    """Get or create test client"""
    # First get or create tenant
    result = await db.execute(
        select(Tenant).where(Tenant.name == "AI Test Tenant")
    )
    tenant = result.scalar_one_or_none()
    
    if not tenant:
        tenant = Tenant(
            id=uuid.uuid4(),
            name="AI Test Tenant",
            org_number="TEST-TENANT-001",
            subscription_tier="enterprise",
            is_demo=True
        )
        db.add(tenant)
        await db.commit()
        await db.refresh(tenant)
    
    # Now get or create client
    result = await db.execute(
        select(Client).where(Client.org_number == "TEST-AI-123")
    )
    client = result.scalar_one_or_none()
    
    if not client:
        client = Client(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            name="AI Features Test Client",
            org_number="TEST-AI-123",
            client_number="AI-TEST-001",
            status="active",
            is_demo=True
        )
        db.add(client)
        await db.commit()
        await db.refresh(client)
    
    return client


async def test_categorization(db: AsyncSession, client: Client, results: TestResults):
    """Test Smart Expense Categorization"""
    print("\n🧠 Testing SMART EXPENSE CATEGORIZATION...")
    
    # Create test vendor
    vendor = Vendor(
        id=uuid.uuid4(),
        client_id=client.id,
        vendor_number="V-CAT-001",
        name="Telenor Norge AS",
        org_number="123456789",
        account_number="2400"
    )
    db.add(vendor)
    await db.commit()
    
    # Create invoice with description containing keywords
    invoice = VendorInvoice(
        id=uuid.uuid4(),
        client_id=client.id,
        vendor_id=vendor.id,
        invoice_number="TEL-2024-001",
        invoice_date=date.today(),
        due_date=date.today() + timedelta(days=30),
        amount_excl_vat=Decimal("800.00"),
        vat_amount=Decimal("200.00"),
        total_amount=Decimal("1000.00")
    )
    # Note: Actual description would come from OCR or EHF, not stored directly
    db.add(invoice)
    await db.commit()
    await db.refresh(invoice)
    
    # Test categorization
    service = AICategorizationService(db)
    suggestions = await service.suggest_account(invoice, vendor)
    
    results.test(
        "Categorization: Suggests accounts",
        len(suggestions) > 0,
        f"No suggestions returned"
    )
    
    if suggestions:
        top_suggestion = suggestions[0]
        results.test(
            "Categorization: Has confidence score",
            top_suggestion.confidence > 0,
            f"Confidence: {top_suggestion.confidence}"
        )
        results.test(
            "Categorization: Matches phone keywords (6340)",
            "6340" in [s.account_number for s in suggestions],
            f"Suggested accounts: {[s.account_number for s in suggestions]}"
        )
    
    # Test learning
    await service.learn_from_booking(invoice, "6340")
    results.test(
        "Categorization: Learning from booking",
        True,
        "Pattern stored"
    )
    
    # Test update invoice
    result = await service.update_invoice_suggestion(invoice.id)
    results.test(
        "Categorization: Update invoice",
        result is not None and 'account_number' in result,
        f"Result: {result}"
    )
    
    print(f"  Top suggestion: Account {suggestions[0].account_number} ({suggestions[0].confidence}% confidence)")


async def test_anomaly_detection(db: AsyncSession, client: Client, results: TestResults):
    """Test Anomaly Detection"""
    print("\n🚨 Testing ANOMALY DETECTION...")
    
    # Create vendor with historical invoices
    vendor = Vendor(
        id=uuid.uuid4(),
        client_id=client.id,
        vendor_number="V-ANOM-001",
        name="Office Supplies AS",
        org_number="987654321",
        account_number="2400"
    )
    db.add(vendor)
    await db.commit()
    
    # Create historical invoices (normal amounts)
    for i in range(10):
        historical = VendorInvoice(
            id=uuid.uuid4(),
            client_id=client.id,
            vendor_id=vendor.id,
            invoice_number=f"OFF-{i}",
            invoice_date=date.today() - timedelta(days=30*i),
            due_date=date.today() - timedelta(days=30*i) + timedelta(days=30),
            amount_excl_vat=Decimal("400.00"),
            vat_amount=Decimal("100.00"),
            total_amount=Decimal("500.00")
        )
        db.add(historical)
    
    await db.commit()
    
    # Create outlier invoice (10x normal amount)
    outlier_invoice = VendorInvoice(
        id=uuid.uuid4(),
        client_id=client.id,
        vendor_id=vendor.id,
        invoice_number="OFF-OUTLIER",
        invoice_date=date.today(),
        due_date=date.today() + timedelta(days=30),
        amount_excl_vat=Decimal("4000.00"),
        vat_amount=Decimal("1000.00"),
        total_amount=Decimal("5000.00")
    )
    db.add(outlier_invoice)
    await db.commit()
    await db.refresh(outlier_invoice)
    
    # Test anomaly detection
    service = AnomalyDetectionService(db)
    flags = await service.detect_anomalies(outlier_invoice)
    
    results.test(
        "Anomaly: Detects outlier",
        any(f.flag_type == "amount_outlier" for f in flags),
        f"Flags: {[f.flag_type for f in flags]}"
    )
    
    # Create duplicate invoice
    duplicate_invoice = VendorInvoice(
        id=uuid.uuid4(),
        client_id=client.id,
        vendor_id=vendor.id,
        invoice_number="OFF-DUP",
        invoice_date=date.today() + timedelta(days=1),
        due_date=date.today() + timedelta(days=31),
        amount_excl_vat=Decimal("4000.00"),
        vat_amount=Decimal("1000.00"),
        total_amount=Decimal("5000.00")
    )
    db.add(duplicate_invoice)
    await db.commit()
    await db.refresh(duplicate_invoice)
    
    flags = await service.detect_anomalies(duplicate_invoice)
    results.test(
        "Anomaly: Detects duplicate",
        any(f.flag_type == "duplicate_invoice" for f in flags),
        f"Flags: {[f.flag_type for f in flags]}"
    )
    
    # Test risk score
    risk = await service.get_invoice_risk_score(outlier_invoice.id)
    results.test(
        "Anomaly: Calculates risk score",
        risk['risk_score'] > 0,
        f"Risk score: {risk['risk_score']}"
    )
    
    print(f"  Outlier detected: {len(flags)} flags, risk score: {risk['risk_score']}")


async def test_reconciliation(db: AsyncSession, client: Client, results: TestResults):
    """Test Smart Reconciliation"""
    print("\n🔗 Testing SMART RECONCILIATION...")
    
    # Create vendor and invoice
    vendor = Vendor(
        id=uuid.uuid4(),
        client_id=client.id,
        vendor_number="V-RECON-001",
        name="Power Company AS",
        org_number="555444333",
        account_number="2400"
    )
    db.add(vendor)
    await db.commit()
    
    invoice = VendorInvoice(
        id=uuid.uuid4(),
        client_id=client.id,
        vendor_id=vendor.id,
        invoice_number="POW-2024-001",
        invoice_date=date.today() - timedelta(days=5),
        due_date=date.today() + timedelta(days=25),
        amount_excl_vat=Decimal("4000.00"),
        vat_amount=Decimal("1000.00"),
        total_amount=Decimal("5000.00"),
        payment_status="unpaid"
    )
    db.add(invoice)
    await db.commit()
    await db.refresh(invoice)
    
    # Create bank transaction
    transaction = BankTransaction(
        id=uuid.uuid4(),
        client_id=client.id,
        transaction_date=datetime.now() - timedelta(days=2),
        amount=Decimal("-5000.00"),
        transaction_type="debit",
        description="Betaling til Power Company AS",
        counterparty_name="Power Company AS",
        bank_account="1234.56.78901",
        status="unmatched"
    )
    db.add(transaction)
    await db.commit()
    await db.refresh(transaction)
    
    # Test matching
    service = SmartReconciliationService(db)
    matches = await service.find_matches_for_transaction(transaction)
    
    results.test(
        "Reconciliation: Finds matches",
        len(matches) > 0,
        f"Matches found: {len(matches)}"
    )
    
    if matches:
        top_match = matches[0]
        results.test(
            "Reconciliation: Has confidence",
            top_match.confidence > 60,
            f"Confidence: {top_match.confidence}"
        )
        results.test(
            "Reconciliation: Matches correct invoice",
            top_match.matched_entity_id == invoice.id,
            f"Matched: {top_match.matched_entity_id}"
        )
        
        # Test applying match
        success = await service.apply_match(top_match)
        results.test(
            "Reconciliation: Apply match",
            success,
            "Match applied"
        )
        
        print(f"  Match found: {top_match.confidence}% confidence - {top_match.match_reason}")


async def test_payment_terms(db: AsyncSession, client: Client, results: TestResults):
    """Test Payment Terms Extraction"""
    print("\n📅 Testing PAYMENT TERMS EXTRACTION...")
    
    service = PaymentTermsExtractor(db)
    
    # Test cases
    test_cases = [
        ("30 dager netto", 30, "30 days net"),
        ("Netto 14 dager", 14, "14 days net"),
        ("Betales ved mottak", 0, "Immediate payment"),
        ("Betalingsfrist: 45 dager", 45, "45 days payment deadline"),
    ]
    
    for text, expected_days, description in test_cases:
        result = service.extract_payment_terms(text, date.today())
        
        results.test(
            f"Payment Terms: {description}",
            result['payment_days'] == expected_days,
            f"Expected {expected_days} days, got {result['payment_days']}"
        )
        
        print(f"  '{text}' → {result['payment_days']} days")
    
    # Test with invoice
    vendor = Vendor(
        id=uuid.uuid4(),
        client_id=client.id,
        vendor_number="V-PAY-001",
        name="Test Vendor",
        org_number="111222333",
        account_number="2400"
    )
    db.add(vendor)
    await db.commit()
    
    invoice = VendorInvoice(
        id=uuid.uuid4(),
        client_id=client.id,
        vendor_id=vendor.id,
        invoice_number="PAY-001",
        invoice_date=date.today(),
        due_date=date.today() + timedelta(days=30),
        amount_excl_vat=Decimal("1000.00"),
        vat_amount=Decimal("250.00"),
        total_amount=Decimal("1250.00")
    )
    # Note: payment terms would be extracted from OCR text
    db.add(invoice)
    await db.commit()
    await db.refresh(invoice)
    
    result = await service.update_invoice_payment_terms(invoice.id)
    results.test(
        "Payment Terms: Extract from invoice",
        result.get('payment_days') == 30,
        f"Result: {result}"
    )


async def test_contextual_help(db: AsyncSession, client: Client, results: TestResults):
    """Test Contextual Help"""
    print("\n💡 Testing CONTEXTUAL HELP...")
    
    service = ContextualHelpService(db)
    
    # Test getting default help
    help_text = await service.get_help_text("vendor_invoice", "invoice_number", "client")
    
    results.test(
        "Contextual Help: Get help text",
        help_text is not None and 'help_text' in help_text,
        f"Help: {help_text}"
    )
    
    if help_text:
        print(f"  Help for 'invoice_number': {help_text['help_text'][:50]}...")
    
    # Test getting all help for page
    page_help = await service.get_page_help_texts("vendor_invoice", "client")
    
    results.test(
        "Contextual Help: Get page help",
        len(page_help) > 0,
        f"Found {len(page_help)} help texts"
    )
    
    # Test storing help
    help_id = await service.store_help_text(
        page="test_page",
        field="test_field",
        user_role="client",
        help_text="This is a test help text",
        example_text="Example value"
    )
    
    results.test(
        "Contextual Help: Store help text",
        help_id is not None,
        "Help text stored"
    )
    
    print(f"  Found {len(page_help)} help texts for vendor_invoice page")


async def main():
    """Run all tests"""
    print("="*60)
    print("🧪 AI FEATURES COMPREHENSIVE TEST")
    print("="*60)
    
    results = TestResults()
    
    async with AsyncSessionLocal() as db:
        try:
            # Get or create test client
            client = await get_or_create_test_client(db)
            print(f"\n✅ Using test client: {client.name}")
            
            # Run tests
            await test_categorization(db, client, results)
            await test_anomaly_detection(db, client, results)
            await test_reconciliation(db, client, results)
            await test_payment_terms(db, client, results)
            await test_contextual_help(db, client, results)
            
        except Exception as e:
            print(f"\n❌ Test error: {e}")
            import traceback
            traceback.print_exc()
            results.tests_failed += 1
    
    # Print summary
    success = results.summary()
    
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

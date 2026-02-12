"""
Test script to create a vendor invoice and process it through the AI flow
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4, UUID

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models.tenant import Tenant
from app.models.client import Client
from app.models.vendor import Vendor
from app.models.vendor_invoice import VendorInvoice
from app.services.invoice_processing import process_vendor_invoice


async def create_test_data(db: AsyncSession):
    """Create test tenant, client, vendor"""
    
    # Check if tenant exists
    tenant = await db.get(Tenant, UUID("00000000-0000-0000-0000-000000000001"))
    
    if not tenant:
        print("Creating test tenant...")
        tenant = Tenant(
            id=UUID("00000000-0000-0000-0000-000000000001"),
            name="Test Regnskapsbyrå AS",
            org_number="999999999"
        )
        db.add(tenant)
        await db.commit()
    
    # Check if client exists
    client = await db.get(Client, UUID("00000000-0000-0000-0000-000000000002"))
    
    if not client:
        print("Creating test client...")
        client = Client(
            id=UUID("00000000-0000-0000-0000-000000000002"),
            tenant_id=tenant.id,
            name="Test Bedrift AS",
            org_number="888888888"
        )
        db.add(client)
        await db.commit()
    
    # Check if vendor exists
    vendor = await db.get(Vendor, UUID("00000000-0000-0000-0000-000000000003"))
    
    if not vendor:
        print("Creating test vendor...")
        vendor = Vendor(
            id=UUID("00000000-0000-0000-0000-000000000003"),
            client_id=client.id,
            name="Kontorrekvisita AS",
            org_number="777777777"
        )
        db.add(vendor)
        await db.commit()
    
    return tenant, client, vendor


async def create_test_invoice(db: AsyncSession, client_id, vendor_id):
    """Create a test invoice"""
    
    print("\n📄 Creating test invoice...")
    
    invoice = VendorInvoice(
        client_id=client_id,
        vendor_id=vendor_id,
        invoice_number="INV-2024-001",
        invoice_date=datetime.now().date(),
        due_date=(datetime.now() + timedelta(days=14)).date(),
        currency="NOK",
        amount_excl_vat=Decimal("1200.00"),
        vat_amount=Decimal("300.00"),
        total_amount=Decimal("1500.00"),
        description="Kontorrekvisita - blyanter, papir, tusjer",
        payment_status="unpaid",
        review_status="pending"
    )
    
    db.add(invoice)
    await db.commit()
    await db.refresh(invoice)
    
    print(f"✅ Invoice created: {invoice.id}")
    print(f"   Vendor: {invoice.vendor.name if invoice.vendor else 'Unknown'}")
    print(f"   Amount: {invoice.total_amount} NOK")
    
    return invoice


async def test_invoice_processing():
    """Test the full invoice processing flow"""
    
    print("=" * 60)
    print("KONTALI ERP - Invoice Processing Test")
    print("=" * 60)
    
    # Create async engine
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False
    )
    
    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session() as db:
        # Create test data
        tenant, client, vendor = await create_test_data(db)
        
        # Create test invoice
        invoice = await create_test_invoice(db, client.id, vendor.id)
        
        # Process through AI
        print("\n🤖 Processing invoice through AI Agent...")
        print(f"   Using model: {settings.CLAUDE_MODEL}")
        
        if not settings.ANTHROPIC_API_KEY:
            print("\n❌ ERROR: ANTHROPIC_API_KEY not set in .env")
            print("   Please add ANTHROPIC_API_KEY to backend/.env")
            return
        
        result = await process_vendor_invoice(db, invoice.id)
        
        # Display results
        print("\n" + "=" * 60)
        print("RESULTS")
        print("=" * 60)
        print(f"Success: {result['success']}")
        print(f"Confidence: {result.get('confidence', 'N/A')}%")
        print(f"Action: {result.get('action', 'N/A')}")
        
        if result.get('review_queue_id'):
            print(f"\n📋 Sent to Review Queue: {result['review_queue_id']}")
            print("\nNext steps:")
            print("1. Open frontend: http://localhost:3000")
            print("2. Check Review Queue to see the invoice")
            print("3. Use chat to approve: 'approve [id]'")
        elif result.get('action') == 'auto_booked':
            print(f"\n✅ Auto-booked (high confidence)")
            suggested = result.get('suggested_booking', [])
            if suggested:
                print("\nSuggested booking:")
                for entry in suggested:
                    print(f"  {entry.get('account')}: {entry.get('description')} - "
                          f"Debit: {entry.get('debit', 0)}, Credit: {entry.get('credit', 0)}")
        
        if result.get('error'):
            print(f"\n❌ Error: {result['error']}")
        
        print("\n" + "=" * 60)
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(test_invoice_processing())

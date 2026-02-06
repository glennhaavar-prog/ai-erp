#!/usr/bin/env python3
"""Process invoice PDF and save results to database"""

import asyncio
import sys
import os
import uuid
from pathlib import Path
from datetime import datetime, date
from decimal import Decimal

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / 'backend'))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load env
load_dotenv('/home/ubuntu/.openclaw/workspace/ai-erp/backend/.env')

# Import models
from app.models import Tenant, Client, Vendor, VendorInvoice, ReviewQueue
from app.models.review_queue import ReviewStatus, ReviewPriority, IssueCategory
from app.database import get_db
from app.config import settings

# Import processing function
from process_invoice_pdf import extract_text_from_pdf
from app.agents.invoice_agent import InvoiceAgent


async def create_test_tenant_and_client(db: AsyncSession):
    """Create test tenant and client if they don't exist"""
    
    from sqlalchemy import select
    
    # Check if test tenant exists
    result = await db.execute(
        select(Tenant).where(Tenant.name == "Test Regnskapsbyrå")
    )
    tenant = result.scalar_one_or_none()
    
    if not tenant:
        print("📝 Creating test tenant...")
        from app.models.tenant import SubscriptionTier
        tenant = Tenant(
            id=uuid.uuid4(),
            name="Test Regnskapsbyrå",
            org_number="999999999",
            subscription_tier=SubscriptionTier.PROFESSIONAL
        )
        db.add(tenant)
        await db.flush()
        print(f"✅ Tenant created: {tenant.name}")
    else:
        print(f"✅ Using existing tenant: {tenant.name}")
    
    # Check if test client exists
    result = await db.execute(
        select(Client).where(
            Client.tenant_id == tenant.id,
            Client.name == "GHB AS Test"
        )
    )
    client = result.scalar_one_or_none()
    
    if not client:
        print("📝 Creating test client...")
        from app.models.client import AutomationLevel
        client = Client(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            client_number="TEST001",
            name="GHB AS Test",
            org_number="123456789",
            ai_confidence_threshold=85,
            ai_automation_level=AutomationLevel.ASSISTED
        )
        db.add(client)
        await db.flush()
        print(f"✅ Client created: {client.name}")
    else:
        print(f"✅ Using existing client: {client.name}")
    
    await db.commit()
    
    return tenant, client


async def save_invoice_to_db(
    db: AsyncSession,
    client: Client,
    pdf_path: str,
    ocr_text: str,
    analysis_result: dict
):
    """Save invoice analysis to database"""
    
    from sqlalchemy import select
    
    print("\n💾 Saving to database...")
    print("-" * 70)
    
    # 1. Create or get vendor
    vendor_data = analysis_result.get('vendor', {})
    vendor_name = vendor_data.get('name', 'Unknown Vendor')
    vendor_org_nr = vendor_data.get('org_number', '')
    
    result = await db.execute(
        select(Vendor).where(
            Vendor.client_id == client.id,
            Vendor.name == vendor_name
        )
    )
    vendor = result.scalar_one_or_none()
    
    if not vendor:
        print(f"📝 Creating vendor: {vendor_name}")
        
        # Generate vendor number (simple sequential)
        result_count = await db.execute(
            select(Vendor).where(Vendor.client_id == client.id)
        )
        vendor_count = len(result_count.all())
        vendor_number = f"V{vendor_count + 1:04d}"
        
        vendor = Vendor(
            id=uuid.uuid4(),
            client_id=client.id,
            vendor_number=vendor_number,
            name=vendor_name,
            org_number=vendor_org_nr
        )
        db.add(vendor)
        await db.flush()
    else:
        print(f"✅ Using existing vendor: {vendor_name}")
    
    # 2. Create invoice
    invoice_number = analysis_result.get('invoice_number', 'UNKNOWN')
    invoice_date_str = analysis_result.get('invoice_date')
    due_date_str = analysis_result.get('due_date')
    
    # Parse dates
    invoice_date = None
    if invoice_date_str:
        try:
            invoice_date = datetime.strptime(invoice_date_str, '%Y-%m-%d').date()
        except:
            pass
    
    due_date = None
    if due_date_str:
        try:
            due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
        except:
            pass
    
    print(f"📝 Creating invoice: {invoice_number}")
    
    invoice = VendorInvoice(
        id=uuid.uuid4(),
        client_id=client.id,
        vendor_id=vendor.id,
        invoice_number=invoice_number,
        invoice_date=invoice_date or date.today(),
        due_date=due_date,
        amount_excl_vat=Decimal(str(analysis_result.get('amount_excl_vat', 0))),
        vat_amount=Decimal(str(analysis_result.get('vat_amount', 0))),
        total_amount=Decimal(str(analysis_result.get('total_amount', 0))),
        currency=analysis_result.get('currency', 'NOK'),
        ocr_text=ocr_text[:5000],  # Limit length
        ai_confidence=analysis_result.get('confidence_score', 0),
        ai_suggested_booking=analysis_result.get('suggested_booking', []),
        ai_reasoning=analysis_result.get('reasoning', ''),
        status='pending'
    )
    db.add(invoice)
    await db.flush()
    print(f"✅ Invoice created with ID: {invoice.id}")
    
    # 3. Determine if it needs review
    confidence = analysis_result.get('confidence_score', 0)
    threshold = client.ai_confidence_threshold
    
    if confidence < threshold:
        print(f"⚠️  Confidence {confidence}% < threshold {threshold}%")
        print("📝 Adding to review queue...")
        
        # Determine priority
        if confidence < 50:
            priority = ReviewPriority.HIGH
        elif confidence < 70:
            priority = ReviewPriority.MEDIUM
        else:
            priority = ReviewPriority.LOW
        
        review_item = ReviewQueue(
            id=uuid.uuid4(),
            client_id=client.id,
            invoice_id=invoice.id,
            status=ReviewStatus.PENDING,
            priority=priority,
            issue_category=IssueCategory.LOW_CONFIDENCE,
            issue_description=f"AI confidence {confidence}% below threshold {threshold}%",
            ai_suggestion=analysis_result.get('suggested_booking', [])
        )
        db.add(review_item)
        print(f"✅ Added to review queue with {priority.value} priority")
    else:
        print(f"✅ Confidence {confidence}% >= threshold {threshold}%")
        print("✅ Would auto-approve (not creating review item)")
    
    await db.commit()
    print("✅ All data saved to database!")
    
    return invoice


async def main():
    """Main processing function"""
    
    if len(sys.argv) < 2:
        print("Usage: python process_and_save_invoice.py <path-to-pdf>")
        print("\nAvailable test invoices:")
        test_dir = Path(__file__).parent / 'test-invoices'
        for pdf in sorted(test_dir.glob('*.pdf')):
            print(f"  - {pdf.name}")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    if not os.path.exists(pdf_path):
        print(f"❌ File not found: {pdf_path}")
        sys.exit(1)
    
    print("="*70)
    print(f"🧾 PROCESSING & SAVING: {Path(pdf_path).name}")
    print("="*70)
    
    # Step 1: Extract text
    print("\n📄 STEP 1: OCR Extraction")
    print("-"*70)
    
    try:
        ocr_text = extract_text_from_pdf(pdf_path)
        print(f"✅ Extracted {len(ocr_text)} characters")
    except Exception as e:
        print(f"❌ OCR failed: {e}")
        return
    
    # Step 2: Analyze with AI
    print("\n🤖 STEP 2: AI Analysis")
    print("-"*70)
    
    try:
        agent = InvoiceAgent()
        test_client_id = uuid.uuid4()
        
        result = await agent.analyze_invoice(
            client_id=test_client_id,
            ocr_text=ocr_text,
            vendor_history=None,
            learned_patterns=None
        )
        
        if 'error' in result:
            print(f"❌ Analysis failed: {result.get('error')}")
            return
        
        print(f"✅ Analysis complete!")
        print(f"   Vendor: {result.get('vendor', {}).get('name')}")
        print(f"   Amount: {result.get('total_amount')} {result.get('currency')}")
        print(f"   Confidence: {result.get('confidence_score')}%")
        
    except Exception as e:
        print(f"❌ AI analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 3: Save to database
    print("\n💾 STEP 3: Save to Database")
    print("-"*70)
    
    try:
        # Create database session
        engine = create_async_engine(settings.DATABASE_URL, echo=False)
        async_session = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        
        async with async_session() as db:
            # Create test tenant/client if needed
            tenant, client = await create_test_tenant_and_client(db)
            
            # Save invoice
            invoice = await save_invoice_to_db(
                db, client, pdf_path, ocr_text, result
            )
            
            print("\n" + "="*70)
            print("✅ SUCCESS! Invoice saved to database")
            print("="*70)
            print(f"\n📊 Summary:")
            print(f"  Tenant: {tenant.name}")
            print(f"  Client: {client.name}")
            print(f"  Vendor: {invoice.vendor.name}")
            print(f"  Invoice: {invoice.invoice_number}")
            print(f"  Amount: {invoice.total_amount} {invoice.currency}")
            print(f"  Confidence: {invoice.ai_confidence}%")
            print(f"  Status: {invoice.status}")
            
            confidence = invoice.ai_confidence
            threshold = client.ai_confidence_threshold
            
            if confidence >= threshold:
                print(f"\n✅ Would AUTO-APPROVE (confidence {confidence}% >= {threshold}%)")
            else:
                print(f"\n⚠️  Sent to REVIEW QUEUE (confidence {confidence}% < {threshold}%)")
            
            print("\n🌐 View in frontend:")
            print(f"  http://localhost:3000")
            print("="*70)
        
        await engine.dispose()
        
    except Exception as e:
        print(f"❌ Database save failed: {e}")
        import traceback
        traceback.print_exc()
        return

if __name__ == "__main__":
    asyncio.run(main())

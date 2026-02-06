#!/usr/bin/env python3
"""Quick script to create a test invoice and process it"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Load .env file before importing app modules
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), 'backend', '.env'))

import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import UUID
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.models.vendor_invoice import VendorInvoice
from app.models.client import Client
from app.models.vendor import Vendor
from app.services.invoice_processing import process_vendor_invoice
from sqlalchemy import select

async def main():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        # Get first client and vendor
        client_query = select(Client).limit(1)
        client_result = await db.execute(client_query)
        client = client_result.scalar_one_or_none()
        
        vendor_query = select(Vendor).limit(1)
        vendor_result = await db.execute(vendor_query)
        vendor = vendor_result.scalar_one_or_none()
        
        if not client or not vendor:
            print("❌ No client or vendor found! Run setup first.")
            return
        
        print(f"Using client: {client.name}")
        print(f"Using vendor: {vendor.name}\n")
        
        # Create invoice
        invoice = VendorInvoice(
            client_id=client.id,
            vendor_id=vendor.id,
            invoice_number=f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            invoice_date=datetime.now().date(),
            due_date=(datetime.now() + timedelta(days=14)).date(),
            currency="NOK",
            amount_excl_vat=Decimal("1200.00"),
            vat_amount=Decimal("300.00"),
            total_amount=Decimal("1500.00"),
            payment_status="unpaid",
            review_status="pending"
        )
        db.add(invoice)
        await db.commit()
        await db.refresh(invoice)
        
        print(f"✅ Invoice created: {invoice.id}")
        print(f"   Invoice number: {invoice.invoice_number}")
        print(f"   Amount: {invoice.total_amount} NOK\n")
        
        # Process
        print("🤖 Processing through AI Agent...")
        try:
            result = await process_vendor_invoice(db, invoice.id)
        except Exception as e:
            print(f"\n❌ Exception during processing:")
            import traceback
            traceback.print_exc()
            result = {'success': False, 'error': str(e)}
        
        print("\n" + "="*60)
        print("RESULTS")
        print("="*60)
        print(f"Success: {result['success']}")
        print(f"Confidence: {result.get('confidence', 'N/A')}%")
        print(f"Action: {result.get('action', 'N/A')}")
        
        if result.get('review_queue_id'):
            print(f"\n📋 Sent to Review Queue!")
            print(f"Review Queue ID: {result['review_queue_id']}")
            print("\nNext steps:")
            print("1. Open: http://localhost:3000")
            print(f"2. Use chat: 'show reviews'")
            print(f"3. Approve: 'approve {result['review_queue_id'][:8]}'")
        
        if result.get('error'):
            print(f"\n❌ Error: {result['error']}")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""
Smoke Test: Create 5 Test Vendor Invoices

Creates simple vendor invoices for testing the booking workflow.
"""

import asyncio
import sys
from pathlib import Path
from uuid import UUID, uuid4
from datetime import date, timedelta
from decimal import Decimal

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import ENUM
from app.database import get_db
from app.models.vendor_invoice import VendorInvoice
from app.models.vendor import Vendor
from app.models.client import Client

# Define the payment_status enum
PaymentStatusEnum = ENUM('unpaid', 'partially_paid', 'paid', 'overdue', name='payment_status_enum', create_type=False)


async def create_test_invoices():
    """Create 5 test vendor invoices for smoke test"""
    
    # Client ID from smoke test
    client_id = UUID('09409ccf-d23e-45e5-93b9-68add0b96277')  # GHB AS Test
    
    # Get database session
    db_gen = get_db()
    db = await anext(db_gen)
    
    try:
        # Verify client exists
        result = await db.execute(select(Client).where(Client.id == client_id))
        client = result.scalar_one_or_none()
        
        if not client:
            print(f"❌ Client {client_id} not found!")
            return
        
        print(f"✅ Client found: {client.name}")
        
        # Create or find 5 test vendors
        test_vendors = [
            {"name": "Kontorrekvisita AS", "org": "987654321"},
            {"name": "Strømleverandøren", "org": "876543210"},
            {"name": "IT-Utstyr Norge", "org": "765432109"},
            {"name": "Møbel & Inventar", "org": "654321098"},
            {"name": "Revisjon & Rådgivning", "org": "543210987"},
        ]
        
        created_invoices = []
        
        for idx, vendor_data in enumerate(test_vendors, 1):
            # Find or create vendor
            result = await db.execute(
                select(Vendor).where(
                    Vendor.client_id == client_id,
                    Vendor.org_number == vendor_data["org"]
                ).limit(1)
            )
            vendor = result.scalars().first()
            
            if not vendor:
                vendor = Vendor(
                    id=uuid4(),
                    client_id=client_id,
                    name=vendor_data["name"],
                    org_number=vendor_data["org"],
                    is_active=True
                )
                db.add(vendor)
                await db.flush()
                print(f"✅ Created vendor: {vendor.name}")
            else:
                print(f"✅ Found existing vendor: {vendor.name}")
            
            # Create invoice
            invoice_date = date.today() - timedelta(days=idx)
            due_date = invoice_date + timedelta(days=30)
            
            # Simple amounts (excluding VAT)
            amount_excl_vat = Decimal(1000 * idx)  # 1000, 2000, 3000, 4000, 5000
            vat_amount = amount_excl_vat * Decimal("0.25")  # 25% VAT
            total_amount = amount_excl_vat + vat_amount
            
            invoice = VendorInvoice(
                id=uuid4(),
                client_id=client_id,
                vendor_id=vendor.id,
                invoice_number=f"TEST-{idx:03d}",
                invoice_date=invoice_date,
                due_date=due_date,
                currency="NOK",
                amount_excl_vat=amount_excl_vat,
                vat_amount=vat_amount,
                total_amount=total_amount
                # payment_status defaults to "unpaid"
                # review_status defaults to "pending"
            )
            
            db.add(invoice)
            await db.flush()
            
            created_invoices.append({
                "id": str(invoice.id),
                "number": invoice.invoice_number,
                "vendor": vendor.name,
                "amount": float(total_amount),
                "date": invoice_date.isoformat()
            })
            
            print(f"✅ Created invoice {invoice.invoice_number}: {vendor.name} - {total_amount} NOK")
        
        # Commit all
        await db.commit()
        
        print(f"\n🎉 Successfully created {len(created_invoices)} test invoices!")
        print("\nInvoice IDs for processing:")
        for inv in created_invoices:
            print(f"  - {inv['id']} ({inv['number']})")
        
        return created_invoices
        
    except Exception as e:
        await db.rollback()
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        await db.close()


if __name__ == "__main__":
    result = asyncio.run(create_test_invoices())

#!/usr/bin/env python3
"""
Generate realistic demo data for Kontali ERP demo
Creates invoices with mix of auto-booked and review queue items
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from datetime import datetime, timedelta
import random
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.client import Client
from app.models.vendor import Vendor
from app.models.vendor_invoice import VendorInvoice
from app.models.review_queue import ReviewQueue, ReviewStatus
from app.services.invoice_processing import process_vendor_invoice
import uuid

# Realistic Norwegian vendors with typical purchases
DEMO_VENDORS = [
    {
        "name": "Kontorrekvisita AS",
        "org_number": "998877665",
        "invoice_types": [
            ("Kontorrekvisita - blyanter, notatblokker", 850, "6100", 5),
            ("Kopipapir og konvolupper", 1250, "6100", 5),
            ("Kontormateriell diverse", 450, "6100", 5),
        ]
    },
    {
        "name": "Strømleverandøren AS",
        "org_number": "998877666",
        "invoice_types": [
            ("Strøm kontorlokaler januar 2026", 4500, "6340", 5),
            ("Strøm kontorlokaler februar 2026", 4800, "6340", 5),
        ]
    },
    {
        "name": "Telenor Norge AS",
        "org_number": "998877667",
        "invoice_types": [
            ("Mobilabonnement ansatte", 2400, "6900", 5),
            ("Fasttelefon og internett", 1200, "6900", 5),
        ]
    },
    {
        "name": "Rema 1000 Næringskunder",
        "org_number": "998877668",
        "invoice_types": [
            ("Kaffe, melk, kjeks til pauserom", 950, "6100", 3),
            ("Rengjøringsmidler", 480, "6100", 5),
        ]
    },
    {
        "name": "IT-Partner Norge AS",
        "org_number": "998877669",
        "invoice_types": [
            ("Microsoft 365 Business Premium - 5 lisenser", 3500, "6900", 5),
            ("Support og vedlikehold IT-systemer", 8500, "6900", 5),
            ("Nytt tastatur og mus", 1200, "6100", 5),
        ]
    },
    {
        "name": "Advokatfirmaet Brottveit & Co",
        "org_number": "998877670",
        "invoice_types": [
            ("Juridisk rådgivning kundekontrakt", 15000, "6700", 5),
            ("Gjennomgang av leieavtale", 8500, "6700", 5),
        ]
    },
    {
        "name": "Revisjon Nord AS",
        "org_number": "998877671",
        "invoice_types": [
            ("Årsregnskap og revisjon 2025", 25000, "6700", 5),
        ]
    },
    {
        "name": "Kontorlokaler Bodø AS",
        "org_number": "998877672",
        "invoice_types": [
            ("Husleie kontorlokaler januar 2026", 18000, "6200", 0),
            ("Husleie kontorlokaler februar 2026", 18000, "6200", 0),
        ]
    },
    {
        "name": "Staples Norge AS",
        "org_number": "998877673",
        "invoice_types": [
            ("Skrivebord og kontorstol", 8500, "1220", 5),  # Equipment (asset)
            ("Arkivskap", 3200, "1220", 5),
        ]
    },
    {
        "name": "Widerøe Ground Handling",
        "org_number": "998877674",
        "invoice_types": [
            ("Reise Oslo-Bodø tur/retur - møte kunde", 2800, "6800", 3),
            ("Reise Bergen møte - tur/retur", 3200, "6800", 3),
        ]
    },
    {
        "name": "Clarion Hotel Bodø",
        "org_number": "998877675",
        "invoice_types": [
            ("Hotellopphold Oslo 2 netter - kundemøte", 3400, "6800", 3),
        ]
    },
    {
        "name": "Circle K Næringskunder",
        "org_number": "998877676",
        "invoice_types": [
            ("Drivstoff firmabil januar", 2200, "6800", 5),
        ]
    },
]

async def create_vendor_if_not_exists(db: AsyncSession, client_id: str, vendor_data: dict, vendor_number: int) -> Vendor:
    """Create vendor if it doesn't exist"""
    result = await db.execute(
        select(Vendor).filter(
            Vendor.client_id == client_id,
            Vendor.org_number == vendor_data["org_number"]
        )
    )
    vendor = result.scalars().first()
    
    if not vendor:
        vendor = Vendor(
            id=str(uuid.uuid4()),
            client_id=client_id,
            vendor_number=str(vendor_number),
            name=vendor_data["name"],
            org_number=vendor_data["org_number"],
            email=f"faktura@{vendor_data['name'].lower().replace(' ', '').replace('æ','ae').replace('ø','o').replace('å','a')}.no",
            account_number="2400",  # Standard Leverandørgjeld account
            payment_terms="30",
        )
        db.add(vendor)
        await db.commit()
        await db.refresh(vendor)
        print(f"✓ Created vendor: {vendor.name}")
    
    return vendor

def generate_invoice_number() -> str:
    """Generate realistic invoice number"""
    return f"{random.randint(2026001, 2026999)}"

def generate_ocr_text(vendor_name: str, description: str, amount: float, invoice_number: str) -> str:
    """Generate realistic OCR text"""
    date_str = (datetime.now() - timedelta(days=random.randint(1, 30))).strftime("%d.%m.%Y")
    due_date_str = (datetime.now() + timedelta(days=14)).strftime("%d.%m.%Y")
    
    return f"""FAKTURA

{vendor_name}
Org.nr: MVA

Fakturanummer: {invoice_number}
Fakturadato: {date_str}
Forfallsdato: {due_date_str}

{description}

Sum eks. mva: {amount:.2f} kr
MVA 25%: {amount * 0.25:.2f} kr
------------------------
Totalt å betale: {amount * 1.25:.2f} kr

Vennligst betal til: 1234 56 78901
KID: {invoice_number}
"""

async def create_invoice(
    db: AsyncSession,
    client_id: str,
    vendor: Vendor,
    description: str,
    amount: float,
    account: str,
    mva_code: int,
    confidence_override: int = None
) -> VendorInvoice:
    """Create a vendor invoice"""
    from decimal import Decimal
    
    invoice_number = generate_invoice_number()
    ocr_text = generate_ocr_text(vendor.name, description, amount, invoice_number)
    
    # Calculate VAT based on mva_code
    if mva_code == 5:  # 25% VAT
        vat_rate = 0.25
    elif mva_code == 3:  # 15% VAT
        vat_rate = 0.15
    else:  # 0% VAT
        vat_rate = 0.0
    
    amount_excl_vat = Decimal(str(amount))
    vat_amount = amount_excl_vat * Decimal(str(vat_rate))
    total_amount = amount_excl_vat + vat_amount
    
    invoice = VendorInvoice(
        id=str(uuid.uuid4()),
        client_id=client_id,
        vendor_id=vendor.id,
        invoice_number=invoice_number,
        invoice_date=(datetime.now() - timedelta(days=random.randint(1, 30))).date(),
        due_date=(datetime.now() + timedelta(days=14)).date(),
        amount_excl_vat=amount_excl_vat,
        vat_amount=vat_amount,
        total_amount=total_amount,
        currency="NOK",
        review_status="pending",
        ai_processed=False,
    )
    
    db.add(invoice)
    await db.commit()
    await db.refresh(invoice)
    
    return invoice

async def main():
    print("🚀 Generating demo data for Kontali ERP...")
    print()
    
    async with AsyncSessionLocal() as db:
        try:
            # Get GHB AS Test client
            result = await db.execute(select(Client).filter(Client.name.like("%GHB AS%")))
            client = result.scalars().first()
            
            if not client:
                print("❌ Error: GHB AS Test client not found!")
                print("Please create test client first.")
                return
            
            print(f"✓ Using client: {client.name} (ID: {client.id})")
            print()
            
            # Statistics
            total_invoices = 0
            auto_booked = 0
            in_review = 0
            
            # Create invoices from each vendor
            for idx, vendor_data in enumerate(DEMO_VENDORS, start=1000):
                vendor = await create_vendor_if_not_exists(db, client.id, vendor_data, idx)
                
                # Create 1-2 invoices per vendor
                num_invoices = random.randint(1, 2)
                
                for _ in range(num_invoices):
                    # Pick random invoice type
                    invoice_type = random.choice(vendor_data["invoice_types"])
                    description, amount, account, mva_code = invoice_type
                    
                    # Create invoice
                    invoice = await create_invoice(
                        db, client.id, vendor,
                        description, amount, account, mva_code
                    )
                    
                    # Process through AI (will auto-book or send to review queue)
                    result = await process_vendor_invoice(db, invoice.id)
                    
                    total_invoices += 1
                    
                    if result["action"] == "auto_booked":
                        auto_booked += 1
                        print(f"  ✓ Auto-booked: {vendor.name} - {description} ({float(invoice.total_amount):.0f} kr)")
                    else:
                        in_review += 1
                        print(f"  ⚠ Review queue: {vendor.name} - {description} ({float(invoice.total_amount):.0f} kr)")
            
            print()
            print("=" * 70)
            print("📊 DEMO DATA GENERATION COMPLETE")
            print("=" * 70)
            print(f"Total invoices created: {total_invoices}")
            print(f"Auto-booked: {auto_booked} ({auto_booked/total_invoices*100:.1f}%)")
            print(f"In review queue: {in_review} ({in_review/total_invoices*100:.1f}%)")
            print()
            print("🎯 Demo ready! Visit:")
            print("  - Dashboard: http://localhost:3000/dashboard")
            print("  - Review Queue: http://localhost:3000/review-queue (use ReviewQueue component)")
            print()
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            await db.rollback()

if __name__ == "__main__":
    asyncio.run(main())

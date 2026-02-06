#!/usr/bin/env python3
"""
Generate realistic demo data for Kontali ERP demo (SIMPLIFIED - no AI processing)
Creates invoices and review queue items directly
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from datetime import datetime, timedelta
import random
import asyncio
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.client import Client
from app.models.vendor import Vendor
from app.models.vendor_invoice import VendorInvoice
from app.models.review_queue import ReviewQueue, ReviewStatus, ReviewPriority, IssueCategory
import uuid

# Realistic Norwegian vendors with typical purchases
DEMO_VENDORS = [
    {
        "name": "Kontorrekvisita AS",
        "org_number": "998877665",
        "invoices": [
            ("Kontorrekvisita - blyanter, notatblokker", 850, "6100", 5, 95),
            ("Kopipapir og konvolupper", 1250, "6100", 5, 92),
        ]
    },
    {
        "name": "Strømleverandøren AS",
        "org_number": "998877666",
        "invoices": [
            ("Strøm kontorlokaler januar 2026", 4500, "6340", 5, 88),
        ]
    },
    {
        "name": "Telenor Norge AS",
        "org_number": "998877667",
        "invoices": [
            ("Mobilabonnement ansatte", 2400, "6900", 5, 96),
            ("Fasttelefon og internett", 1200, "6900", 5, 94),
        ]
    },
    {
        "name": "Rema 1000 Næringskunder",
        "org_number": "998877668",
        "invoices": [
            ("Kaffe, melk, kjeks til pauserom", 950, "6100", 3, 65),  # Low confidence → review queue
        ]
    },
    {
        "name": "IT-Partner Norge AS",
        "org_number": "998877669",
        "invoices": [
            ("Microsoft 365 Business Premium - 5 lisenser", 3500, "6900", 5, 98),
            ("Support og vedlikehold IT-systemer", 8500, "6900", 5, 72),  # Lower confidence
        ]
    },
    {
        "name": "Advokatfirmaet Brottveit & Co",
        "org_number": "998877670",
        "invoices": [
            ("Juridisk rådgivning kundekontrakt", 15000, "6700", 5, 55),  # Low confidence → review
        ]
    },
    {
        "name": "Kontorlokaler Bodø AS",
        "org_number": "998877672",
        "invoices": [
            ("Husleie kontorlokaler januar 2026", 18000, "6200", 0, 99),
        ]
    },
    {
        "name": "Staples Norge AS",
        "org_number": "998877673",
        "invoices": [
            ("Skrivebord og kontorstol", 8500, "1220", 5, 48),  # Asset - low confidence
        ]
    },
    {
        "name": "Widerøe Ground Handling",
        "org_number": "998877674",
        "invoices": [
            ("Reise Oslo-Bodø tur/retur - møte kunde", 2800, "6800", 3, 89),
        ]
    },
    {
        "name": "Clarion Hotel Bodø",
        "org_number": "998877675",
        "invoices": [
            ("Hotellopphold Oslo 2 netter - kundemøte", 3400, "6800", 3, 60),  # → review
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

def calculate_vat(amount: Decimal, mva_code: int) -> tuple[Decimal, Decimal]:
    """Calculate VAT amount and total"""
    if mva_code == 5:  # 25% VAT
        vat_rate = Decimal("0.25")
    elif mva_code == 3:  # 15% VAT
        vat_rate = Decimal("0.15")
    else:  # 0% VAT
        vat_rate = Decimal("0")
    
    vat_amount = amount * vat_rate
    total_amount = amount + vat_amount
    return vat_amount, total_amount

async def create_invoice_with_status(
    db: AsyncSession,
    client_id: str,
    vendor: Vendor,
    description: str,
    amount: float,
    account: str,
    mva_code: int,
    confidence: int
) -> tuple[VendorInvoice, bool]:
    """Create invoice and optionally add to review queue"""
    invoice_number = f"2026{random.randint(100, 999)}"
    
    amount_excl_vat = Decimal(str(amount))
    vat_amount, total_amount = calculate_vat(amount_excl_vat, mva_code)
    
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
        review_status="auto_approved" if confidence >= 85 else "needs_review",
        ai_processed=True,
        ai_confidence_score=confidence,
        ai_booking_suggestion={
            "lines": [
                {
                    "account": account,
                    "description": description,
                    "debit": float(amount_excl_vat),
                    "credit": 0,
                    "vat_code": mva_code
                },
                {
                    "account": "2740" if mva_code > 0 else "2400",
                    "description": "Inngående MVA" if mva_code > 0 else "Leverandørgjeld",
                    "debit": float(vat_amount),
                    "credit": 0,
                    "vat_code": 0
                },
                {
                    "account": "2400",
                    "description": f"Leverandør: {vendor.name}",
                    "debit": 0,
                    "credit": float(total_amount),
                    "vat_code": 0
                }
            ],
            "confidence": confidence,
            "reasoning": f"Standard booking for {description}"
        },
        ai_detected_category="office_supplies" if "6100" in account else "other",
    )
    
    db.add(invoice)
    await db.commit()
    await db.refresh(invoice)
    
    # If low confidence, add to review queue
    needs_review = confidence < 85
    if needs_review:
        review_item = ReviewQueue(
            id=str(uuid.uuid4()),
            client_id=client_id,
            source_type="vendor_invoice",
            source_id=invoice.id,
            priority=ReviewPriority.MEDIUM if confidence > 60 else ReviewPriority.HIGH,
            status=ReviewStatus.PENDING,
            issue_category=IssueCategory.LOW_CONFIDENCE,
            issue_description=f"AI confidence score {confidence}% is below threshold (85%). Please review and approve or correct the booking suggestion.",
            ai_suggestion=invoice.ai_booking_suggestion,
            ai_confidence=confidence,
            ai_reasoning=f"Low confidence due to: {description}",
            created_at=datetime.now(),
        )
        db.add(review_item)
        await db.commit()
    
    return invoice, needs_review

async def main():
    print("🚀 Generating demo data for Kontali ERP (SIMPLIFIED)...")
    print()
    
    async with AsyncSessionLocal() as db:
        try:
            # Get GHB AS Test client
            result = await db.execute(select(Client).filter(Client.name.like("%GHB AS%")))
            client = result.scalars().first()
            
            if not client:
                print("❌ Error: GHB AS Test client not found!")
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
                
                for invoice_data in vendor_data["invoices"]:
                    description, amount, account, mva_code, confidence = invoice_data
                    
                    invoice, needs_review = await create_invoice_with_status(
                        db, client.id, vendor,
                        description, amount, account, mva_code, confidence
                    )
                    
                    total_invoices += 1
                    
                    if needs_review:
                        in_review += 1
                        print(f"  ⚠ Review ({confidence}%): {vendor.name} - {description} ({float(invoice.total_amount):.0f} kr)")
                    else:
                        auto_booked += 1
                        print(f"  ✓ Auto ({confidence}%): {vendor.name} - {description} ({float(invoice.total_amount):.0f} kr)")
            
            print()
            print("=" * 70)
            print("📊 DEMO DATA GENERATION COMPLETE")
            print("=" * 70)
            print(f"Total invoices created: {total_invoices}")
            print(f"Auto-booked (≥85%): {auto_booked} ({auto_booked/total_invoices*100:.1f}%)")
            print(f"In review queue (<85%): {in_review} ({in_review/total_invoices*100:.1f}%)")
            print()
            print("🎯 Demo ready! Visit:")
            print("  - Dashboard: http://localhost:3000/dashboard")
            print("  - Review Queue component (needs route setup)")
            print()
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            await db.rollback()

if __name__ == "__main__":
    asyncio.run(main())

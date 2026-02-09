#!/usr/bin/env python3
"""
Populate Review Queue with 20 new vendor invoices + AI analysis

Creates realistic Norwegian vendor invoices with varied confidence scores
for demo purposes.
"""
import asyncio
import random
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import Client, VendorInvoice, ReviewQueue, Account

# Norwegian vendors
VENDORS = [
    "Telenor Norge AS", "Elkjøp Nordic AS", "Rema 1000 AS",
    "Circle K Norge AS", "Posten Norge AS", "DHL Express Norway AS",
    "Staples Norge AS", "Office Partner AS", "ISS Facility Services AS",
    "DNB Bank ASA", "Nordea Bank Norge ASA", "BDO Norge AS",
    "Strømberg Elektro AS", "VVS Nord AS", "Malermester Hansen AS",
    "IT-Support Nord AS", "CloudNorge AS", "Kontorrekvisita AS",
    "Trykkservice Bodø AS", "Datasikkerhet Norge AS"
]

# Account mappings (NS 4102) with VAT codes
EXPENSE_MAPPINGS = [
    (6540, 5, 85, "Kontorrekvisita"),  # account, vat_code, confidence, description
    (6900, 5, 90, "Telefon/data"),
    (6300, 0, 95, "Leie lokaler"),
    (4300, 5, 88, "Elektrisitet"),
    (7140, 5, 82, "Reisekostnader"),
    (6700, 0, 92, "Regnskapsføring"),
    (7700, 0, 87, "Bank- og kortgebyr"),
    (6100, 5, 78, "Vedlikehold"),
    (7500, 0, 91, "Forsikringer"),
    (7320, 5, 75, "Reklamekostnader"),
]


async def get_demo_clients(session: AsyncSession):
    """Get all demo clients"""
    result = await session.execute(
        select(Client).where(Client.is_demo == True).limit(20)
    )
    return result.scalars().all()


async def create_vendor_invoice_with_ai_analysis(
    session: AsyncSession,
    client: Client,
    vendor_name: str,
    amount: Decimal,
    account: int,
    vat_code: int,
    confidence: int,
    description: str
):
    """Create a vendor invoice and corresponding review queue item"""
    
    invoice_date = datetime.now() - timedelta(days=random.randint(1, 30))
    due_date = invoice_date + timedelta(days=14)
    
    # Calculate amounts
    vat_rate = Decimal("0.25") if vat_code == 5 else Decimal("0")
    vat_amt = amount * vat_rate
    total_amt = amount + vat_amt
    
    # Create vendor invoice
    invoice = VendorInvoice(
        id=uuid4(),
        client_id=client.id,
        vendor_id=None,  # Demo: no vendor entity needed
        invoice_number=f"INV-{random.randint(10000, 99999)}",
        invoice_date=invoice_date.date(),
        due_date=due_date.date(),
        amount_excl_vat=amount,
        vat_amount=vat_amt,
        total_amount=total_amt,
        currency="NOK",
        payment_status="UNPAID",
        review_status="PENDING_REVIEW",
        ai_processed=True,
        ai_confidence_score=confidence,
        ai_detected_category=description,
        ai_reasoning=f"AI suggests account {account} ({description}) based on pattern matching with {vendor_name}"
    )
    session.add(invoice)
    await session.flush()
    
    # Determine issue category based on confidence
    if confidence >= 85:
        issue_cat = "manual_review_required"  # High confidence, just needs approval
        issue_desc = f"High confidence ({confidence}%) - Ready for approval"
    elif confidence >= 60:
        issue_cat = "low_confidence"
        issue_desc = f"Medium confidence ({confidence}%) - Please review suggestion"
    else:
        issue_cat = "low_confidence"
        issue_desc = f"Low confidence ({confidence}%) - Manual booking recommended"
    
    # Create review queue item (AI suggestion)
    review_item = ReviewQueue(
        id=uuid4(),
        client_id=client.id,
        source_type="vendor_invoice",
        source_id=invoice.id,
        priority="high" if confidence >= 85 else "medium" if confidence >= 60 else "low",
        status="pending",
        issue_category=issue_cat,
        issue_description=issue_desc,
        ai_suggestion={
            "account": account,
            "vat_code": vat_code,
            "description": description,
            "vendor": vendor_name
        },
        ai_confidence=confidence,
        ai_reasoning=f"AI suggests account {account} ({description}) based on pattern matching with {vendor_name}"
    )
    session.add(review_item)
    
    return invoice, review_item


async def main():
    """Generate 20 vendor invoices with AI analysis"""
    
    print("=" * 60)
    print("🎯 Populating Review Queue with 20 new items")
    print("=" * 60)
    
    async with AsyncSessionLocal() as session:
        try:
            # Get demo clients
            clients = await get_demo_clients(session)
            if not clients:
                print("❌ No demo clients found!")
                return
            
            print(f"✅ Found {len(clients)} demo clients")
            
            # Confidence distribution
            # 14 high (85-95%), 4 medium (60-84%), 2 low (40-59%)
            confidence_targets = (
                [random.randint(85, 95) for _ in range(14)] +
                [random.randint(60, 84) for _ in range(4)] +
                [random.randint(40, 59) for _ in range(2)]
            )
            random.shuffle(confidence_targets)
            
            created_count = 0
            
            for i in range(20):
                # Pick random client, vendor, and expense mapping
                client = random.choice(clients)
                vendor = random.choice(VENDORS)
                account, vat_code, base_confidence, description = random.choice(EXPENSE_MAPPINGS)
                
                # Use target confidence (override base)
                confidence = confidence_targets[i]
                
                # Generate realistic amount
                amount = Decimal(random.randint(500, 50000))
                
                # Create invoice + review queue item
                invoice, review_item = await create_vendor_invoice_with_ai_analysis(
                    session, client, vendor, amount, account, vat_code,
                    confidence, description
                )
                
                created_count += 1
                
                if (i + 1) % 5 == 0:
                    print(f"  Created {i + 1}/20 invoices...")
            
            # Commit all
            await session.commit()
            
            print(f"\n✅ Successfully created {created_count} vendor invoices")
            print("✅ Review queue populated with AI suggestions")
            
            # Verify
            result = await session.execute(select(func.count(ReviewQueue.id)))
            total_queue_size = result.scalar()
            
            print(f"\n📊 Total Review Queue size: {total_queue_size}")
            
            # Confidence distribution
            result = await session.execute(
                select(
                    func.count(ReviewQueue.id),
                    func.min(ReviewQueue.confidence_score),
                    func.max(ReviewQueue.confidence_score),
                    func.avg(ReviewQueue.confidence_score)
                ).where(ReviewQueue.status == "PENDING")
            )
            count, min_conf, max_conf, avg_conf = result.first()
            
            print(f"📊 Pending items: {count}")
            print(f"📊 Confidence range: {min_conf}% - {max_conf}% (avg: {avg_conf:.1f}%)")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            await session.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(main())

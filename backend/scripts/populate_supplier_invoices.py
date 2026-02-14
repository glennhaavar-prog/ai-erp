#!/usr/bin/env python3
"""
Populate 10 supplier invoices for end-to-end testing
Client: 09409ccf-d23e-45e5-93b9-68add0b96277

Distribution:
- 3 high confidence (85-95%) - auto-approve candidates
- 4 medium confidence (60-75%) - needs review
- 3 low confidence (30-50%) - needs manual handling
"""
import asyncio
import random
import sys
import os
from pathlib import Path
from uuid import UUID, uuid4
from datetime import datetime, timedelta
from decimal import Decimal

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import AsyncSessionLocal
from app.models.vendor_invoice import VendorInvoice
from app.models.review_queue import (
    ReviewQueue,
    ReviewStatus,
    ReviewPriority,
    IssueCategory,
    VoucherType
)
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy import text

# Test client ID
TEST_CLIENT_ID = UUID("09409ccf-d23e-45e5-93b9-68add0b96277")

# Norwegian suppliers with realistic data
SUPPLIERS = [
    {"name": "Elkjøp Nordic AS", "org_no": "990 633 374", "account": 6540, "desc": "IT-utstyr og elektronikk"},
    {"name": "Coop Norge SA", "org_no": "980 478 851", "account": 6700, "desc": "Kontorrekvisita"},
    {"name": "Circle K Norge AS", "org_no": "922 588 307", "account": 7160, "desc": "Drivstoff"},
    {"name": "Telenor Norge AS", "org_no": "978 130 619", "account": 6900, "desc": "Telefoni og internett"},
    {"name": "Posten Norge AS", "org_no": "984 661 185", "account": 6840, "desc": "Porto og frakt"},
    {"name": "ISS Facility Services AS", "org_no": "913 251 918", "account": 6100, "desc": "Renhold og vaktmester"},
    {"name": "DNB Bank ASA", "org_no": "984 851 006", "account": 7700, "desc": "Bankgebyrer"},
    {"name": "BDO Norge AS", "org_no": "993 160 787", "account": 7500, "desc": "Regnskapstjenester"},
    {"name": "Strømberg Elektro AS", "org_no": "987 654 321", "account": 6300, "desc": "Strøm og oppvarming"},
    {"name": "CloudNorge AS", "org_no": "923 456 789", "account": 6940, "desc": "Sky-tjenester"},
]


async def create_supplier_invoice(db, supplier: dict, confidence: int, index: int):
    """Create a single supplier invoice with review queue item"""
    
    # Generate invoice details
    invoice_date = datetime.now() - timedelta(days=random.randint(5, 30))
    due_date = invoice_date + timedelta(days=random.choice([14, 30]))
    
    # Amount based on confidence (vary between 500 and 50,000 NOK)
    if confidence >= 85:
        amount_excl_vat = Decimal(random.randint(5000, 50000))
    elif confidence >= 60:
        amount_excl_vat = Decimal(random.randint(2000, 30000))
    else:
        amount_excl_vat = Decimal(random.randint(500, 15000))
    
    # VAT calculation (25% for most, 0% for some services)
    vat_exempt = supplier["account"] in [7500, 7700, 6300]  # Accounting, bank, rent
    vat_rate = Decimal("0") if vat_exempt else Decimal("0.25")
    vat_code = 0 if vat_exempt else 3
    vat_amount = (amount_excl_vat * vat_rate).quantize(Decimal("0.01"))
    total_amount = amount_excl_vat + vat_amount
    
    # Generate KID number for some invoices (Norwegian payment reference)
    kid_number = None
    if random.random() > 0.4:  # 60% have KID
        kid_number = f"{random.randint(1000000, 9999999):07d}{random.randint(10, 99)}"
    
    # Create vendor invoice
    invoice = VendorInvoice(
        id=uuid4(),
        client_id=TEST_CLIENT_ID,
        vendor_id=None,  # Not linking to vendor table for demo
        invoice_number=f"INV-{random.randint(100000, 999999)}",
        invoice_date=invoice_date.date(),
        due_date=due_date.date(),
        amount_excl_vat=amount_excl_vat,
        vat_amount=vat_amount,
        total_amount=total_amount,
        currency="NOK",
        review_status="pending",  # Explicitly set
        ai_processed=True,
        ai_confidence_score=confidence,
        ai_detected_category=supplier["desc"],
        ai_reasoning=f"AI matched to {supplier['name']} based on invoice content. Suggested account {supplier['account']} ({supplier['desc']})."
        # payment_status uses database default ("unpaid")
    )
    db.add(invoice)
    await db.flush()
    
    # Determine issue category and priority based on confidence
    if confidence >= 85:
        priority = ReviewPriority.LOW
        issue_category = IssueCategory.LOW_CONFIDENCE if confidence < 90 else IssueCategory.MANUAL_REVIEW_REQUIRED
        issue_desc = f"High confidence ({confidence}%) - Auto-approve candidate"
    elif confidence >= 60:
        priority = ReviewPriority.MEDIUM
        issue_category = IssueCategory.LOW_CONFIDENCE
        issue_desc = f"Medium confidence ({confidence}%) - Please review AI suggestion"
    else:
        priority = ReviewPriority.HIGH
        issue_category = IssueCategory.LOW_CONFIDENCE
        issue_desc = f"Low confidence ({confidence}%) - Manual handling required"
    
    # Add variation to some items
    if confidence < 50 and random.random() > 0.5:
        issue_category = IssueCategory.UNCLEAR_DESCRIPTION
        issue_desc += " - Invoice description unclear"
    
    if not kid_number and confidence < 70:
        issue_desc += " - Missing KID number"
    
    # Create review queue item
    review_item = ReviewQueue(
        id=uuid4(),
        client_id=TEST_CLIENT_ID,
        source_type="vendor_invoice",
        source_id=invoice.id,
        type=VoucherType.SUPPLIER_INVOICE,
        priority=priority,
        status=ReviewStatus.PENDING,
        issue_category=issue_category,
        issue_description=issue_desc,
        ai_confidence=confidence,
        ai_reasoning=f"Matched {supplier['name']} (org: {supplier['org_no']}). Suggested posting: Debit {supplier['account']} ({supplier['desc']}), Credit 2400 (Leverandørgjeld). VAT code: {vat_code}.",
        ai_suggestion={
            "supplier_name": supplier["name"],
            "org_number": supplier["org_no"],
            "account": supplier["account"],
            "account_name": supplier["desc"],
            "vat_code": vat_code,
            "amount_excl_vat": float(amount_excl_vat),
            "vat_amount": float(vat_amount),
            "total_amount": float(total_amount),
            "kid": kid_number,
            "posting": {
                "debit": [{"account": supplier["account"], "amount": float(amount_excl_vat)}],
                "credit": [{"account": 2400, "amount": float(total_amount)}],
                "vat": [{"account": 2700, "amount": float(vat_amount)}] if vat_amount > 0 else []
            }
        },
        created_at=datetime.utcnow() - timedelta(minutes=index * 5)
    )
    db.add(review_item)
    
    return invoice, review_item


async def main():
    """Main function to populate supplier invoices"""
    print("=" * 70)
    print("POPULATING SUPPLIER INVOICES FOR E2E TESTING")
    print("=" * 70)
    print(f"Client ID: {TEST_CLIENT_ID}")
    print()
    
    # Confidence distribution
    confidence_levels = [
        # 3 high confidence (85-95%)
        random.randint(85, 90),
        random.randint(88, 93),
        random.randint(90, 95),
        # 4 medium confidence (60-75%)
        random.randint(60, 68),
        random.randint(65, 72),
        random.randint(68, 73),
        random.randint(70, 75),
        # 3 low confidence (30-50%)
        random.randint(30, 40),
        random.randint(35, 45),
        random.randint(40, 50),
    ]
    
    random.shuffle(confidence_levels)
    
    async with AsyncSessionLocal() as db:
        created_invoices = []
        created_reviews = []
        
        for idx, (supplier, confidence) in enumerate(zip(SUPPLIERS, confidence_levels)):
            invoice, review = await create_supplier_invoice(db, supplier, confidence, idx)
            created_invoices.append(invoice)
            created_reviews.append(review)
            
            conf_label = "HIGH" if confidence >= 85 else "MED" if confidence >= 60 else "LOW"
            print(f"  [{conf_label:4}] {supplier['name']:30} {confidence:2}% - {float(invoice.total_amount):>10,.2f} NOK")
        
        await db.commit()
        
        print()
        print("=" * 70)
        print("✅ SUPPLIER INVOICES CREATED SUCCESSFULLY")
        print("=" * 70)
        print(f"Total invoices: {len(created_invoices)}")
        print(f"  - High confidence (85-95%): {sum(1 for r in created_reviews if r.ai_confidence >= 85)}")
        print(f"  - Medium confidence (60-75%): {sum(1 for r in created_reviews if 60 <= r.ai_confidence < 85)}")
        print(f"  - Low confidence (30-50%): {sum(1 for r in created_reviews if r.ai_confidence < 60)}")
        print()
        total_value = sum(float(inv.total_amount) for inv in created_invoices)
        print(f"Total value: {total_value:,.2f} NOK")
        print()
        print("Test with:")
        print(f'  curl "http://localhost:8000/api/review-queue/pending?client_id={TEST_CLIENT_ID}&type=supplier_invoice"')


if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""
Create test data for other voucher types (non-supplier-invoice)
- Employee expenses (ansatteutlegg)
- Inventory adjustments (lagerjusteringer)
- Manual corrections (manuelle korreksjoner)
"""
import asyncio
import sys
import os
from uuid import UUID, uuid4
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import AsyncSessionLocal
from app.models.review_queue import (
    ReviewQueue,
    ReviewStatus,
    ReviewPriority,
    IssueCategory,
    VoucherType
)
from sqlalchemy import select


async def create_employee_expenses(db, client_id: UUID):
    """Create 5 employee expense test items"""
    print("Creating employee expense test data...")
    
    expenses = [
        {
            "description": "Utlegg for reise Oslo-Bergen - mangler kvittering",
            "priority": ReviewPriority.HIGH,
            "category": IssueCategory.MISSING_VAT,
            "ai_confidence": 45,
            "ai_reasoning": "Missing receipt for train ticket. Manually verify with employee.",
            "ai_suggestion": {
                "account_number": "7140",
                "account_name": "Reisekostnader",
                "vat_code": "0",
                "amount": 890.00
            }
        },
        {
            "description": "Hotellovernatting - manuell godkjenning nødvendig",
            "priority": ReviewPriority.MEDIUM,
            "category": IssueCategory.MANUAL_REVIEW_REQUIRED,
            "ai_confidence": 65,
            "ai_reasoning": "Hotel expense within policy limits. Verify business purpose.",
            "ai_suggestion": {
                "account_number": "7145",
                "account_name": "Hotell og overnatting",
                "vat_code": "3",
                "amount": 1250.00,
                "vat_amount": 250.00
            }
        },
        {
            "description": "Drivstoff - uvanlig høyt beløp",
            "priority": ReviewPriority.HIGH,
            "category": IssueCategory.UNUSUAL_AMOUNT,
            "ai_confidence": 50,
            "ai_reasoning": "Fuel expense of 2500 NOK is 3x higher than average. Verify distance.",
            "ai_suggestion": {
                "account_number": "7160",
                "account_name": "Drivstoffkostnader",
                "vat_code": "3",
                "amount": 2500.00,
                "vat_amount": 500.00
            }
        },
        {
            "description": "Representasjon - lav tillit på kategorisering",
            "priority": ReviewPriority.MEDIUM,
            "category": IssueCategory.LOW_CONFIDENCE,
            "ai_confidence": 40,
            "ai_reasoning": "Receipt unclear. Could be representation or office supplies. Review needed.",
            "ai_suggestion": {
                "account_number": "7600",
                "account_name": "Representasjon",
                "vat_code": "0",
                "amount": 845.00
            }
        },
        {
            "description": "Kontorrekvisita - mulig duplikat",
            "priority": ReviewPriority.LOW,
            "category": IssueCategory.DUPLICATE_INVOICE,
            "ai_confidence": 55,
            "ai_reasoning": "Similar expense from same vendor 3 days ago. Verify not duplicate.",
            "ai_suggestion": {
                "account_number": "6940",
                "account_name": "Kontorrekvisita",
                "vat_code": "3",
                "amount": 345.00,
                "vat_amount": 69.00
            }
        }
    ]
    
    for i, expense in enumerate(expenses):
        # Create a synthetic source_id (would normally be from employee_expenses table)
        source_id = uuid4()
        
        item = ReviewQueue(
            id=uuid4(),
            client_id=client_id,
            source_type="employee_expense",
            source_id=source_id,
            type=VoucherType.EMPLOYEE_EXPENSE,
            priority=expense["priority"],
            status=ReviewStatus.PENDING,
            issue_category=expense["category"],
            issue_description=expense["description"],
            ai_suggestion=expense["ai_suggestion"],
            ai_confidence=expense["ai_confidence"],
            ai_reasoning=expense["ai_reasoning"],
            created_at=datetime.utcnow() - timedelta(hours=i)
        )
        db.add(item)
        print(f"  ✅ Created employee expense: {expense['description'][:50]}")
    
    await db.commit()
    print(f"✅ Created 5 employee expenses")


async def create_inventory_adjustments(db, client_id: UUID):
    """Create 3 inventory adjustment test items"""
    print("Creating inventory adjustment test data...")
    
    adjustments = [
        {
            "description": "Lagerjustering - uklar årsak til differanse",
            "priority": ReviewPriority.URGENT,
            "category": IssueCategory.UNCLEAR_DESCRIPTION,
            "ai_confidence": 35,
            "ai_reasoning": "Inventory count differs by 15% from system. Requires manual verification of cause.",
            "ai_suggestion": {
                "account_number": "1400",
                "account_name": "Varebeholdning",
                "vat_code": "0",
                "amount": -4500.00,
                "debit_account": "6100",
                "credit_account": "1400"
            }
        },
        {
            "description": "Svinn - manuell godkjenning påkrevd",
            "priority": ReviewPriority.HIGH,
            "category": IssueCategory.MANUAL_REVIEW_REQUIRED,
            "ai_confidence": 60,
            "ai_reasoning": "Product write-off exceeds threshold. Manager approval required.",
            "ai_suggestion": {
                "account_number": "6390",
                "account_name": "Svinn",
                "vat_code": "0",
                "amount": 2300.00
            }
        },
        {
            "description": "Varetelling - uvanlig stort avvik",
            "priority": ReviewPriority.MEDIUM,
            "category": IssueCategory.UNUSUAL_AMOUNT,
            "ai_confidence": 45,
            "ai_reasoning": "Physical count shows 8% discrepancy. Verify counting process.",
            "ai_suggestion": {
                "account_number": "1400",
                "account_name": "Varebeholdning",
                "vat_code": "0",
                "amount": -1850.00
            }
        }
    ]
    
    for i, adj in enumerate(adjustments):
        source_id = uuid4()
        
        item = ReviewQueue(
            id=uuid4(),
            client_id=client_id,
            source_type="inventory_adjustment",
            source_id=source_id,
            type=VoucherType.INVENTORY_ADJUSTMENT,
            priority=adj["priority"],
            status=ReviewStatus.PENDING,
            issue_category=adj["category"],
            issue_description=adj["description"],
            ai_suggestion=adj["ai_suggestion"],
            ai_confidence=adj["ai_confidence"],
            ai_reasoning=adj["ai_reasoning"],
            created_at=datetime.utcnow() - timedelta(hours=i * 2)
        )
        db.add(item)
        print(f"  ✅ Created inventory adjustment: {adj['description'][:50]}")
    
    await db.commit()
    print(f"✅ Created 3 inventory adjustments")


async def create_manual_corrections(db, client_id: UUID):
    """Create 2 manual correction test items"""
    print("Creating manual correction test data...")
    
    corrections = [
        {
            "description": "Korreksjon av tidligere føring - krever verifisering",
            "priority": ReviewPriority.HIGH,
            "category": IssueCategory.MANUAL_REVIEW_REQUIRED,
            "ai_confidence": 30,
            "ai_reasoning": "Correction to voucher from previous period. Verify with accountant before posting.",
            "ai_suggestion": {
                "account_number": "3000",
                "account_name": "Egenkapital",
                "vat_code": "0",
                "amount": -1200.00,
                "debit_account": "3000",
                "credit_account": "6800",
                "description": "Correction of accounting error from Q1"
            }
        },
        {
            "description": "Periodeavgrensingskorreksjon - lav tillit",
            "priority": ReviewPriority.MEDIUM,
            "category": IssueCategory.LOW_CONFIDENCE,
            "ai_confidence": 40,
            "ai_reasoning": "Accrual correction. AI unsure about correct period allocation. Human review needed.",
            "ai_suggestion": {
                "account_number": "2920",
                "account_name": "Påløpte kostnader",
                "vat_code": "0",
                "amount": 3400.00,
                "debit_account": "6800",
                "credit_account": "2920"
            }
        }
    ]
    
    for i, corr in enumerate(corrections):
        source_id = uuid4()
        
        item = ReviewQueue(
            id=uuid4(),
            client_id=client_id,
            source_type="manual_correction",
            source_id=source_id,
            type=VoucherType.MANUAL_CORRECTION,
            priority=corr["priority"],
            status=ReviewStatus.PENDING,
            issue_category=corr["category"],
            issue_description=corr["description"],
            ai_suggestion=corr["ai_suggestion"],
            ai_confidence=corr["ai_confidence"],
            ai_reasoning=corr["ai_reasoning"],
            created_at=datetime.utcnow() - timedelta(hours=i * 3)
        )
        db.add(item)
        print(f"  ✅ Created manual correction: {corr['description'][:50]}")
    
    await db.commit()
    print(f"✅ Created 2 manual corrections")


async def main():
    """Main function to create test data"""
    # Test client ID from task description
    client_id = UUID("09409ccf-d23e-45e5-93b9-68add0b96277")
    
    print("=" * 70)
    print("CREATING OTHER VOUCHERS TEST DATA")
    print("=" * 70)
    print(f"Client ID: {client_id}")
    print()
    
    async with AsyncSessionLocal() as db:
        # Verify client exists (optional check)
        from app.models.client import Client
        query = select(Client).where(Client.id == client_id)
        result = await db.execute(query)
        client = result.scalar_one_or_none()
        
        if not client:
            print(f"⚠️  Warning: Client {client_id} not found in database")
            print("    Test data will still be created, but may not be visible")
            print()
        else:
            print(f"✅ Client found: {client.name}")
            print()
        
        # Create test data
        await create_employee_expenses(db, client_id)
        print()
        await create_inventory_adjustments(db, client_id)
        print()
        await create_manual_corrections(db, client_id)
        print()
        
        print("=" * 70)
        print("✅ TEST DATA CREATION COMPLETE")
        print("=" * 70)
        print()
        print("Summary:")
        print("  - 5 employee expenses (ansatteutlegg)")
        print("  - 3 inventory adjustments (lagerjusteringer)")
        print("  - 2 manual corrections")
        print("  - Total: 10 items")
        print()
        print("Test with:")
        print(f"  GET /api/other-vouchers/pending?client_id={client_id}")


if __name__ == "__main__":
    asyncio.run(main())

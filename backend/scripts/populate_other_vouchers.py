#!/usr/bin/env python3
"""
Populate 8 other vouchers for end-to-end testing
Client: 09409ccf-d23e-45e5-93b9-68add0b96277

Distribution:
- 3 employee expenses (ansatteutlegg)
- 3 inventory adjustments (lagerjusteringer)
- 2 manual corrections (manuelle korreksjoner)
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
from app.models.review_queue import (
    ReviewQueue,
    ReviewStatus,
    ReviewPriority,
    IssueCategory,
    VoucherType
)

# Test client ID
TEST_CLIENT_ID = UUID("09409ccf-d23e-45e5-93b9-68add0b96277")


async def create_employee_expenses(db):
    """Create 3 employee expense items"""
    print("Creating employee expenses...")
    
    expenses = [
        {
            "description": "Bensinutlegg - tur Bodø-Tromsø",
            "priority": ReviewPriority.MEDIUM,
            "category": IssueCategory.LOW_CONFIDENCE,
            "confidence": 72,
            "reasoning": "Fuel expense for business trip. Distance matches expense amount.",
            "suggestion": {
                "employee": "Kari Nordmann",
                "account": 7160,
                "account_name": "Drivstoffkostnader",
                "amount_excl_vat": 1600.00,
                "vat_code": 3,
                "vat_amount": 400.00,
                "total": 2000.00,
                "note": "Business trip: Bodø-Tromsø-Bodø, 850 km"
            }
        },
        {
            "description": "Reiseutgifter - konferanse Oslo",
            "priority": ReviewPriority.MEDIUM,
            "category": IssueCategory.MANUAL_REVIEW_REQUIRED,
            "confidence": 68,
            "reasoning": "Conference expenses including train and hotel. Verify receipts.",
            "suggestion": {
                "employee": "Ola Hansen",
                "account": 7140,
                "account_name": "Reisekostnader",
                "amount_excl_vat": 3200.00,
                "vat_code": 0,
                "vat_amount": 0.00,
                "total": 3200.00,
                "note": "Conference: Norwegian Accounting Summit 2026"
            }
        },
        {
            "description": "Kontorrekvisita - kjøp av skrivesaker",
            "priority": ReviewPriority.LOW,
            "category": IssueCategory.LOW_CONFIDENCE,
            "confidence": 55,
            "reasoning": "Office supplies purchase. Receipt somewhat unclear.",
            "suggestion": {
                "employee": "Per Olsen",
                "account": 6940,
                "account_name": "Kontorrekvisita",
                "amount_excl_vat": 240.00,
                "vat_code": 3,
                "vat_amount": 60.00,
                "total": 300.00,
                "note": "Pens, notebooks, and folders"
            }
        }
    ]
    
    created_items = []
    for idx, expense in enumerate(expenses):
        source_id = uuid4()  # Simulated employee_expense ID
        
        item = ReviewQueue(
            id=uuid4(),
            client_id=TEST_CLIENT_ID,
            source_type="employee_expense",
            source_id=source_id,
            type=VoucherType.EMPLOYEE_EXPENSE,
            priority=expense["priority"],
            status=ReviewStatus.PENDING,
            issue_category=expense["category"],
            issue_description=expense["description"],
            ai_confidence=expense["confidence"],
            ai_reasoning=expense["reasoning"],
            ai_suggestion=expense["suggestion"],
            created_at=datetime.utcnow() - timedelta(hours=idx * 2)
        )
        db.add(item)
        created_items.append(item)
        print(f"  ✅ [{expense['confidence']:2}%] {expense['description']}")
    
    return created_items


async def create_inventory_adjustments(db):
    """Create 3 inventory adjustment items"""
    print("\nCreating inventory adjustments...")
    
    adjustments = [
        {
            "description": "Varetelling Q1 2026 - mindre avvik",
            "priority": ReviewPriority.MEDIUM,
            "category": IssueCategory.UNUSUAL_AMOUNT,
            "confidence": 65,
            "reasoning": "Physical count shows 3% discrepancy. Within acceptable range.",
            "suggestion": {
                "type": "physical_count",
                "account": 1400,
                "account_name": "Varebeholdning",
                "adjustment_amount": -2340.00,
                "vat_code": 0,
                "debit_account": 6100,
                "credit_account": 1400,
                "note": "Quarterly inventory count adjustment"
            }
        },
        {
            "description": "Svinn - defekte varer",
            "priority": ReviewPriority.HIGH,
            "category": IssueCategory.MANUAL_REVIEW_REQUIRED,
            "confidence": 58,
            "reasoning": "Product write-off due to damage. Requires manager approval.",
            "suggestion": {
                "type": "write_off",
                "account": 6390,
                "account_name": "Annen kostnad (svinn)",
                "adjustment_amount": 8750.00,
                "vat_code": 0,
                "debit_account": 6390,
                "credit_account": 1400,
                "note": "Write-off of damaged inventory items"
            }
        },
        {
            "description": "Lagerjustering - råvarer",
            "priority": ReviewPriority.MEDIUM,
            "category": IssueCategory.LOW_CONFIDENCE,
            "confidence": 48,
            "reasoning": "Raw materials adjustment. Unclear if due to theft, damage or counting error.",
            "suggestion": {
                "type": "adjustment",
                "account": 1400,
                "account_name": "Varebeholdning",
                "adjustment_amount": -1250.00,
                "vat_code": 0,
                "note": "Raw materials inventory adjustment - cause unclear"
            }
        }
    ]
    
    created_items = []
    for idx, adj in enumerate(adjustments):
        source_id = uuid4()  # Simulated inventory_adjustment ID
        
        item = ReviewQueue(
            id=uuid4(),
            client_id=TEST_CLIENT_ID,
            source_type="inventory_adjustment",
            source_id=source_id,
            type=VoucherType.INVENTORY_ADJUSTMENT,
            priority=adj["priority"],
            status=ReviewStatus.PENDING,
            issue_category=adj["category"],
            issue_description=adj["description"],
            ai_confidence=adj["confidence"],
            ai_reasoning=adj["reasoning"],
            ai_suggestion=adj["suggestion"],
            created_at=datetime.utcnow() - timedelta(hours=(idx + 3) * 2)
        )
        db.add(item)
        created_items.append(item)
        print(f"  ✅ [{adj['confidence']:2}%] {adj['description']}")
    
    return created_items


async def create_manual_corrections(db):
    """Create 2 manual correction items"""
    print("\nCreating manual corrections...")
    
    corrections = [
        {
            "description": "Korrigering av feilført bilag #1234",
            "priority": ReviewPriority.HIGH,
            "category": IssueCategory.PROCESSING_ERROR,
            "confidence": 42,
            "reasoning": "Correction needed for voucher posted to wrong account. Verify correct allocation.",
            "suggestion": {
                "type": "correction",
                "original_voucher": "1234",
                "debit_account": 6800,
                "debit_account_name": "Kontorkostnader",
                "credit_account": 6940,
                "credit_account_name": "Kontorrekvisita",
                "amount": 4500.00,
                "vat_code": 0,
                "note": "Move expense from general office to office supplies"
            }
        },
        {
            "description": "Periodisering - forsikring Q1",
            "priority": ReviewPriority.MEDIUM,
            "category": IssueCategory.MANUAL_REVIEW_REQUIRED,
            "confidence": 52,
            "reasoning": "Accrual adjustment for insurance. AI unsure about correct period allocation.",
            "suggestion": {
                "type": "accrual",
                "debit_account": 7500,
                "debit_account_name": "Forsikringer",
                "credit_account": 2920,
                "credit_account_name": "Påløpte kostnader",
                "amount": 12000.00,
                "vat_code": 0,
                "period": "2026-Q1",
                "note": "Accrual for annual insurance premium (3/12)"
            }
        }
    ]
    
    created_items = []
    for idx, corr in enumerate(corrections):
        source_id = uuid4()  # Simulated manual_correction ID
        
        item = ReviewQueue(
            id=uuid4(),
            client_id=TEST_CLIENT_ID,
            source_type="manual_correction",
            source_id=source_id,
            type=VoucherType.MANUAL_CORRECTION,
            priority=corr["priority"],
            status=ReviewStatus.PENDING,
            issue_category=corr["category"],
            issue_description=corr["description"],
            ai_confidence=corr["confidence"],
            ai_reasoning=corr["reasoning"],
            ai_suggestion=corr["suggestion"],
            created_at=datetime.utcnow() - timedelta(hours=(idx + 6) * 2)
        )
        db.add(item)
        created_items.append(item)
        print(f"  ✅ [{corr['confidence']:2}%] {corr['description']}")
    
    return created_items


async def main():
    """Main function to populate other vouchers"""
    print("=" * 70)
    print("POPULATING OTHER VOUCHERS FOR E2E TESTING")
    print("=" * 70)
    print(f"Client ID: {TEST_CLIENT_ID}")
    print()
    
    async with AsyncSessionLocal() as db:
        # Create all voucher types
        expenses = await create_employee_expenses(db)
        adjustments = await create_inventory_adjustments(db)
        corrections = await create_manual_corrections(db)
        
        all_items = expenses + adjustments + corrections
        
        await db.commit()
        
        print()
        print("=" * 70)
        print("✅ OTHER VOUCHERS CREATED SUCCESSFULLY")
        print("=" * 70)
        print(f"Total vouchers: {len(all_items)}")
        print(f"  - Employee expenses: {len(expenses)}")
        print(f"  - Inventory adjustments: {len(adjustments)}")
        print(f"  - Manual corrections: {len(corrections)}")
        print()
        
        # Calculate confidence distribution
        high_conf = sum(1 for item in all_items if item.ai_confidence >= 70)
        med_conf = sum(1 for item in all_items if 50 <= item.ai_confidence < 70)
        low_conf = sum(1 for item in all_items if item.ai_confidence < 50)
        
        print(f"Confidence distribution:")
        print(f"  - High (70%+): {high_conf}")
        print(f"  - Medium (50-69%): {med_conf}")
        print(f"  - Low (<50%): {low_conf}")
        print()
        print("Test with:")
        print(f'  curl "http://localhost:8000/api/other-vouchers/pending?client_id={TEST_CLIENT_ID}"')


if __name__ == "__main__":
    asyncio.run(main())

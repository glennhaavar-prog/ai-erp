"""
Test Bank Reconciliation System
Tests import, matching algorithm, and API endpoints
"""
import asyncio
import sys
import uuid
from datetime import datetime, date
from decimal import Decimal

# Add backend to path
sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/ai-erp/backend')

from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import Client, Vendor, VendorInvoice, BankTransaction, BankReconciliation
from app.services.bank_import import BankImportService
from app.services.bank_reconciliation import BankReconciliationService


async def setup_test_data(db):
    """Create test client, vendor, and invoices"""
    
    # Check if test client already exists
    stmt = select(Client).where(Client.org_number == "999888777")
    result = await db.execute(stmt)
    client = result.scalar_one_or_none()
    
    if not client:
        # Create test client
        client = Client(
            id=uuid.uuid4(),
            tenant_id=uuid.UUID('00000000-0000-0000-0000-000000000001'),
            client_number=f"TEST{uuid.uuid4().hex[:6]}",
            name="Test Bank Reconciliation Client",
            org_number="999888777",
            ai_automation_level="FULL",
            status="active",
            is_demo=True
        )
        db.add(client)
    
    # Create test vendors
    vendor1 = Vendor(
        id=uuid.uuid4(),
        client_id=client.id,
        vendor_number="V001",
        name="ABC Leverandører AS",
        org_number="123456789",
        email="post@abc.no"
    )
    db.add(vendor1)
    
    vendor2 = Vendor(
        id=uuid.uuid4(),
        client_id=client.id,
        vendor_number="V002",
        name="XYZ Norge AS",
        org_number="987654321",
        email="faktura@xyz.no"
    )
    db.add(vendor2)
    
    # Create test invoices that match bank transactions
    # Invoice 1: Should match transaction from 15.01.2026 (5000 NOK)
    invoice1 = VendorInvoice(
        id=uuid.uuid4(),
        client_id=client.id,
        vendor_id=vendor1.id,
        invoice_number="2001",
        invoice_date=date(2026, 1, 10),
        due_date=date(2026, 1, 15),
        amount_excl_vat=Decimal("4000.00"),
        vat_amount=Decimal("1000.00"),
        total_amount=Decimal("5000.00"),
        currency="NOK",
        payment_status="unpaid",
        review_status="approved"
    )
    db.add(invoice1)
    
    # Invoice 2: Should match transaction from 25.01.2026 (8000 NOK)
    invoice2 = VendorInvoice(
        id=uuid.uuid4(),
        client_id=client.id,
        vendor_id=vendor2.id,
        invoice_number="INV-2026-001",
        invoice_date=date(2026, 1, 20),
        due_date=date(2026, 1, 25),
        amount_excl_vat=Decimal("6400.00"),
        vat_amount=Decimal("1600.00"),
        total_amount=Decimal("8000.00"),
        currency="NOK",
        payment_status="unpaid",
        review_status="approved"
    )
    db.add(invoice2)
    
    await db.commit()
    
    return client.id, {
        'vendor1': vendor1.id,
        'vendor2': vendor2.id,
        'invoice1': invoice1.id,
        'invoice2': invoice2.id
    }


async def test_csv_import(db, client_id):
    """Test CSV import"""
    print("\n=== TEST 1: CSV Import ===")
    
    # Read test CSV
    with open('/home/ubuntu/.openclaw/workspace/ai-erp/backend/test_bank_statement.csv', 'r') as f:
        csv_content = f.read()
    
    # Parse CSV
    batch_id = uuid.uuid4()
    transactions = BankImportService.parse_norwegian_csv(
        csv_content,
        client_id,
        batch_id,
        "test_bank_statement.csv"
    )
    
    print(f"✓ Parsed {len(transactions)} transactions from CSV")
    
    # Import to database
    imported_count = await BankImportService.import_transactions(db, transactions)
    print(f"✓ Imported {imported_count} transactions to database")
    
    # Verify
    stmt = select(BankTransaction).where(BankTransaction.upload_batch_id == batch_id)
    result = await db.execute(stmt)
    db_transactions = result.scalars().all()
    
    print(f"✓ Verified {len(db_transactions)} transactions in database")
    
    # Sample output
    if db_transactions:
        txn = db_transactions[0]
        print(f"  Sample: {txn.transaction_date.date()} | {txn.description[:40]} | {txn.amount} NOK")
    
    return db_transactions


async def test_matching_algorithm(db, client_id, transactions):
    """Test automatic matching algorithm"""
    print("\n=== TEST 2: Automatic Matching Algorithm ===")
    
    matched_count = 0
    suggestions_count = 0
    
    for txn in transactions:
        # Find matches
        matches = await BankReconciliationService.find_matches(db, txn.id, client_id)
        
        if matches:
            suggestions_count += 1
            best_match = matches[0]
            
            print(f"\nTransaction: {txn.description[:40]}")
            print(f"  Amount: {txn.amount} NOK, Date: {txn.transaction_date.date()}")
            print(f"  Best match: Invoice #{best_match['invoice']['invoice_number']}")
            print(f"  Confidence: {best_match['confidence']:.1f}%")
            print(f"  Reason: {best_match['reason']}")
            
            # Auto-match if confidence is high enough
            if best_match['confidence'] >= BankReconciliationService.CONFIDENCE_AUTO_MATCH:
                match_result = await BankReconciliationService.auto_match_transaction(
                    db, txn.id, client_id
                )
                if match_result:
                    matched_count += 1
                    print(f"  ✓ AUTO-MATCHED (confidence {best_match['confidence']:.1f}%)")
    
    print(f"\n✓ Found suggestions for {suggestions_count} transactions")
    print(f"✓ Auto-matched {matched_count} transactions")
    
    # Calculate match rate
    match_rate = (matched_count / len(transactions) * 100) if transactions else 0
    print(f"✓ Match rate: {match_rate:.1f}%")
    
    return matched_count, match_rate


async def test_manual_matching(db, client_id, transactions, test_data):
    """Test manual matching"""
    print("\n=== TEST 3: Manual Matching ===")
    
    # Find an unmatched transaction
    stmt = select(BankTransaction).where(
        BankTransaction.client_id == client_id,
        BankTransaction.status == "unmatched"
    ).limit(1)
    result = await db.execute(stmt)
    unmatched_txn = result.scalar_one_or_none()
    
    if unmatched_txn:
        print(f"Unmatched transaction: {unmatched_txn.description[:40]}")
        print(f"  Amount: {unmatched_txn.amount} NOK")
        
        # Get suggestions
        matches = await BankReconciliationService.find_matches(db, unmatched_txn.id, client_id)
        
        if matches:
            # Create manual match
            best_match = matches[0]
            mock_user_id = uuid.uuid4()
            
            reconciliation = await BankReconciliationService.create_manual_match(
                db,
                unmatched_txn.id,
                uuid.UUID(best_match['invoice_id']),
                'vendor' if best_match['type'] == 'vendor_invoice' else 'customer',
                client_id,
                mock_user_id
            )
            
            print(f"✓ Manual match created: {reconciliation['id']}")
            print(f"  Confidence: {reconciliation['confidence_score']}%")
        else:
            print("  No suggestions available for manual match")
    else:
        print("✗ No unmatched transactions available")


async def test_statistics(db, client_id):
    """Test statistics endpoint"""
    print("\n=== TEST 4: Statistics ===")
    
    stats = await BankReconciliationService.get_reconciliation_stats(db, client_id)
    
    print(f"Total transactions: {stats['total_transactions']}")
    print(f"Matched: {stats['matched']}")
    print(f"Unmatched: {stats['unmatched']}")
    print(f"Auto-match count: {stats['auto_match_count']}")
    print(f"Manual match count: {stats['manual_match_count']}")
    print(f"Auto-match rate: {stats['auto_match_rate']}%")
    
    # Verify auto-match rate goal (>80%)
    if stats['auto_match_rate'] >= 80:
        print(f"✓ AUTO-MATCH RATE GOAL ACHIEVED: {stats['auto_match_rate']}% >= 80%")
    else:
        print(f"⚠ Auto-match rate: {stats['auto_match_rate']}% (goal: 80%)")
    
    return stats


async def cleanup_test_data(db, client_id):
    """Clean up test data"""
    print("\n=== Cleanup ===")
    
    # Delete in correct order due to foreign keys
    await db.execute(sa.text(f"DELETE FROM bank_reconciliations WHERE client_id = '{client_id}'"))
    await db.execute(sa.text(f"DELETE FROM bank_transactions WHERE client_id = '{client_id}'"))
    await db.execute(sa.text(f"DELETE FROM vendor_invoices WHERE client_id = '{client_id}'"))
    await db.execute(sa.text(f"DELETE FROM vendors WHERE client_id = '{client_id}'"))
    await db.execute(sa.text(f"DELETE FROM clients WHERE id = '{client_id}'"))
    await db.commit()
    
    print("✓ Test data cleaned up")


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("BANK RECONCILIATION SYSTEM TEST")
    print("="*60)
    
    async with AsyncSessionLocal() as db:
        try:
            # Setup
            client_id, test_data = await setup_test_data(db)
            print(f"\n✓ Test data created (Client ID: {client_id})")
            
            # Test 1: CSV Import
            transactions = await test_csv_import(db, client_id)
            
            # Test 2: Matching Algorithm
            matched_count, match_rate = await test_matching_algorithm(db, client_id, transactions)
            
            # Test 3: Manual Matching
            await test_manual_matching(db, client_id, transactions, test_data)
            
            # Test 4: Statistics
            stats = await test_statistics(db, client_id)
            
            # Final Summary
            print("\n" + "="*60)
            print("TEST SUMMARY")
            print("="*60)
            print(f"✓ CSV Import: {len(transactions)} transactions")
            print(f"✓ Auto-matched: {matched_count} transactions ({match_rate:.1f}%)")
            print(f"✓ Total matched: {stats['matched']}")
            print(f"✓ Auto-match rate: {stats['auto_match_rate']}%")
            
            if stats['auto_match_rate'] >= 80:
                print("\n🎉 SUCCESS: Auto-match rate goal achieved (>80%)!")
            else:
                print(f"\n⚠ Warning: Auto-match rate {stats['auto_match_rate']}% below goal (80%)")
            
            # Cleanup
            # await cleanup_test_data(db, client_id)
            print("\n✓ Test completed successfully!")
            
        except Exception as e:
            print(f"\n❌ Test failed: {str(e)}")
            import traceback
            traceback.print_exc()
            raise


if __name__ == "__main__":
    import sqlalchemy as sa
    asyncio.run(main())

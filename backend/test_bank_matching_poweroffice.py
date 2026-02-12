#!/usr/bin/env python3
"""
Test Bank Matching Service - PowerOffice Design

Tests all 4 matching algorithms with Norwegian KID numbers and realistic data.
"""

import asyncio
from decimal import Decimal
from datetime import date, timedelta
from app.services.bank_matching_service import BankMatchingService


# Mock BankTransaction class for testing
class MockBankTransaction:
    def __init__(self, txn_id, txn_date, amount, description, reference=""):
        self.id = txn_id
        self.transaction_date = txn_date
        self.amount = Decimal(str(amount))
        self.description = description
        self.reference = reference


# Mock Voucher class for testing
class MockVoucher:
    def __init__(self, voucher_id, voucher_num, voucher_date, amount, description, reference=""):
        self.id = voucher_id
        self.voucher_number = voucher_num
        self.date = voucher_date
        self.amount = Decimal(str(amount))
        self.description = description
        self.reference = reference


async def test_kid_matching():
    """Test KID-based matching with Norwegian KID numbers"""
    
    print("\n" + "="*70)
    print("TEST 1: KID MATCHING (Norwegian Payment ID)")
    print("="*70)
    
    service = BankMatchingService()
    
    # Test Case 1a: Exact KID match (highest priority)
    print("\n[1a] Exact KID Match - 100% Confidence")
    print("-" * 50)
    
    bank_txn = MockBankTransaction(
        "txn_001",
        date(2026, 2, 5),
        -5250.00,
        "Invoice INV-2024-001, KID: 12345678901",
        ""
    )
    
    voucher = MockVoucher(
        "v_001",
        "INV-2024-001",
        date(2026, 2, 5),
        5250.00,
        "Customer invoice",
        "KID12345678901"
    )
    
    result = await service.match_by_kid(bank_txn, [voucher])
    
    print(f"Bank Transaction: {bank_txn.description}")
    print(f"Bank Amount: {bank_txn.amount} NOK")
    print(f"Bank KID: 12345678901")
    print(f"")
    print(f"Voucher: {voucher.reference}")
    print(f"Voucher Amount: {voucher.amount} NOK")
    print(f"")
    print(f"Result:")
    print(f"  Category: {result.category}")
    print(f"  Confidence: {result.confidence}%")
    print(f"  Reason: {result.reason}")
    print(f"  Matched: {'✓ YES' if result.matched_voucher_id else '✗ NO'}")
    
    # Test Case 1b: No KID in transaction
    print("\n[1b] No KID Found - 0% Confidence")
    print("-" * 50)
    
    bank_txn2 = MockBankTransaction(
        "txn_002",
        date(2026, 2, 6),
        -3500.00,
        "Payment reference unclear",
        ""
    )
    
    result2 = await service.match_by_kid(bank_txn2, [voucher])
    
    print(f"Bank Transaction: {bank_txn2.description}")
    print(f"Result:")
    print(f"  Confidence: {result2.confidence}%")
    print(f"  Reason: {result2.reason}")


async def test_voucher_matching():
    """Test voucher number matching"""
    
    print("\n" + "="*70)
    print("TEST 2: VOUCHER NUMBER MATCHING (Bilagsnummer)")
    print("="*70)
    
    service = BankMatchingService()
    
    # Test Case 2a: Exact voucher number match
    print("\n[2a] Exact Voucher Number Match - 95% Confidence")
    print("-" * 50)
    
    bank_txn = MockBankTransaction(
        "txn_003",
        date(2026, 2, 6),
        -3500.00,
        "Payment REF#8765",
        ""
    )
    
    voucher = MockVoucher(
        "v_002",
        "8765",
        date(2026, 2, 5),
        3500.00,
        "Supplier payment",
        ""
    )
    
    result = await service.match_by_voucher(bank_txn, [voucher])
    
    print(f"Bank Transaction: {bank_txn.description}")
    print(f"Bank Amount: {bank_txn.amount} NOK")
    print(f"")
    print(f"Voucher Number: {voucher.voucher_number}")
    print(f"Voucher Amount: {voucher.amount} NOK")
    print(f"")
    print(f"Result:")
    print(f"  Confidence: {result.confidence}%")
    print(f"  Reason: {result.reason}")
    print(f"  Matched: {'✓ YES' if result.matched_voucher_id else '✗ NO'}")


async def test_amount_matching():
    """Test amount-based matching with date tolerance"""
    
    print("\n" + "="*70)
    print("TEST 3: AMOUNT MATCHING (Beløp) with Date Tolerance")
    print("="*70)
    
    service = BankMatchingService()
    
    # Test Case 3a: Exact amount, 2 days difference
    print("\n[3a] Exact Amount, 2 Days Difference - ~85% Confidence")
    print("-" * 50)
    
    bank_txn = MockBankTransaction(
        "txn_004",
        date(2026, 2, 10),
        12500.00,
        "Bank deposit from customer ABC",
        ""
    )
    
    vouchers = [
        MockVoucher(
            "v_003",
            "INV-2024-002",
            date(2026, 2, 8),  # 2 days earlier
            12500.00,
            "Customer ABC invoice",
            ""
        ),
        MockVoucher(
            "v_004",
            "INV-2024-003",
            date(2026, 2, 11),
            12500.00,
            "Customer ABC payment",
            ""
        ),
    ]
    
    result = await service.match_by_amount(bank_txn, vouchers)
    
    print(f"Bank Transaction: {bank_txn.description}")
    print(f"Bank Date: {bank_txn.transaction_date}")
    print(f"Bank Amount: {bank_txn.amount} NOK")
    print(f"")
    print(f"Candidate Vouchers:")
    for v in vouchers:
        print(f"  • {v.voucher_number}: {v.amount} NOK, {v.date} ({abs((bank_txn.transaction_date - v.date).days)} days diff)")
    print(f"")
    print(f"Result:")
    print(f"  Primary Match: {result.suggested_entries[0]['voucher_number'] if result.suggested_entries else 'None'}")
    print(f"  Confidence: {result.confidence}%")
    print(f"  Reason: {result.reason}")
    
    # Test Case 3b: Amount outside tolerance
    print("\n[3b] Amount Outside ±1 NOK Tolerance - 0% Confidence")
    print("-" * 50)
    
    bank_txn2 = MockBankTransaction(
        "txn_005",
        date(2026, 2, 12),
        5000.00,
        "Large payment",
        ""
    )
    
    voucher_wrong = MockVoucher(
        "v_005",
        "INV-2024-004",
        date(2026, 2, 12),
        4990.00,  # 10 NOK difference
        "Invoice",
        ""
    )
    
    result2 = await service.match_by_amount(bank_txn2, [voucher_wrong])
    
    print(f"Bank Amount: {bank_txn2.amount} NOK")
    print(f"Voucher Amount: {voucher_wrong.amount} NOK")
    print(f"Difference: {abs(bank_txn2.amount - voucher_wrong.amount)} NOK (outside ±1 tolerance)")
    print(f"Result:")
    print(f"  Confidence: {result2.confidence}%")
    print(f"  Reason: {result2.reason}")


async def test_combination_matching():
    """Test combination matching with weighted scoring"""
    
    print("\n" + "="*70)
    print("TEST 4: COMBINATION MATCHING (Multiple Criteria)")
    print("="*70)
    
    service = BankMatchingService()
    
    # Test Case 4a: High combination score
    print("\n[4a] Multiple Matching Criteria - ~80% Confidence")
    print("-" * 50)
    
    bank_txn = MockBankTransaction(
        "txn_006",
        date(2026, 2, 12),
        -750.00,
        "Office supplies payment ABC Ltd",
        ""
    )
    
    vouchers = [
        MockVoucher(
            "v_006",
            "9001",
            date(2026, 2, 10),
            750.00,
            "Office supplies for ABC",
            ""
        ),
        MockVoucher(
            "v_007",
            "9002",
            date(2026, 2, 15),
            745.00,
            "Miscellaneous expenses",
            ""
        ),
    ]
    
    result = await service.match_by_combination(bank_txn, vouchers)
    
    print(f"Bank Transaction: {bank_txn.description}")
    print(f"Bank Date: {bank_txn.transaction_date}")
    print(f"Bank Amount: {abs(bank_txn.amount)} NOK")
    print(f"")
    print(f"Candidate Vouchers:")
    for v in vouchers:
        print(f"  • {v.voucher_number}: '{v.description}' ({v.amount} NOK, {v.date})")
    print(f"")
    print(f"Result:")
    print(f"  Confidence: {result.confidence}%")
    print(f"  Reason: {result.reason}")
    print(f"  Scoring Breakdown:")
    print(f"    - Amount similarity: 40%")
    print(f"    - Description text match: 30%")
    print(f"    - Date proximity: 20%")
    print(f"    - Counterparty match: 10%")


async def test_auto_match():
    """Test the complete auto-matching algorithm"""
    
    print("\n" + "="*70)
    print("TEST 5: AUTO-MATCH (All 4 Algorithms in Priority Order)")
    print("="*70)
    
    service = BankMatchingService()
    
    # Test Case 5: Real-world scenario with multiple transactions
    print("\n[5] Complete Auto-Match Workflow")
    print("-" * 50)
    
    bank_transactions = [
        MockBankTransaction(
            "txn_001",
            date(2026, 2, 5),
            -5250.00,
            "Invoice INV-2024-001, KID: 12345678901",
            ""
        ),
        MockBankTransaction(
            "txn_002",
            date(2026, 2, 6),
            -3500.00,
            "Payment REF#8765",
            ""
        ),
        MockBankTransaction(
            "txn_003",
            date(2026, 2, 10),
            12500.00,
            "Bank deposit",
            ""
        ),
        MockBankTransaction(
            "txn_004",
            date(2026, 2, 12),
            -750.00,
            "Office supplies payment",
            ""
        ),
    ]
    
    vouchers = [
        MockVoucher("v_001", "INV-2024-001", date(2026, 2, 5), 5250.00, "Customer invoice", "KID12345678901"),
        MockVoucher("v_002", "8765", date(2026, 2, 5), 3500.00, "Supplier payment", ""),
        MockVoucher("v_003", "INV-2024-002", date(2026, 2, 8), 12500.00, "Customer ABC invoice", ""),
        MockVoucher("v_004", "9001", date(2026, 2, 10), 750.00, "Office supplies", ""),
    ]
    
    print("Processing 4 bank transactions with auto-match algorithm...")
    print()
    
    results = []
    for bank_txn in bank_transactions:
        result = await service.auto_match(bank_txn, vouchers)
        results.append(result)
        
        # Print result summary
        status_emoji = "✓" if result.confidence >= 90 else "⚠" if result.confidence >= 70 else "✗" if result.confidence > 0 else "❌"
        confidence_label = "HIGH" if result.confidence >= 90 else "MEDIUM" if result.confidence >= 70 else "LOW" if result.confidence > 0 else "NONE"
        
        print(f"{status_emoji} Transaction: {bank_txn.id}")
        print(f"  Amount: {bank_txn.amount} NOK")
        print(f"  Matched: {result.matched_voucher_id if result.matched_voucher_id else 'No match'}")
        print(f"  Algorithm: {result.category.upper()}")
        print(f"  Confidence: {result.confidence}% ({confidence_label})")
        print()
    
    # Summary statistics
    print("="*50)
    print("SUMMARY STATISTICS")
    print("="*50)
    high_conf = sum(1 for r in results if r.confidence >= 90)
    med_conf = sum(1 for r in results if 70 <= r.confidence < 90)
    low_conf = sum(1 for r in results if 0 < r.confidence < 70)
    no_match = sum(1 for r in results if r.confidence == 0)
    
    print(f"Total Processed: {len(results)}")
    print(f"High Confidence (≥90%): {high_conf}")
    print(f"Medium Confidence (70-90%): {med_conf}")
    print(f"Low Confidence (<70%): {low_conf}")
    print(f"No Match (0%): {no_match}")
    print()
    print(f"Success Rate: {((high_conf + med_conf) / len(results) * 100):.1f}%")
    print(f"Auto-Match Rate (≥90%): {(high_conf / len(results) * 100):.1f}%")


async def main():
    """Run all tests"""
    
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "  BANK MATCHING SERVICE - PowerOffice Design  ".center(68) + "║")
    print("║" + "  Complete Test Suite with Norwegian KID Numbers  ".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "=" * 68 + "╝")
    
    try:
        await test_kid_matching()
        await test_voucher_matching()
        await test_amount_matching()
        await test_combination_matching()
        await test_auto_match()
        
        print("\n" + "="*70)
        print("ALL TESTS COMPLETED SUCCESSFULLY ✓")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

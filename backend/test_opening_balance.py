#!/usr/bin/env python3
"""
Opening Balance API Test Script

Tests all critical validations:
1. Balance check: SUM(debit) = SUM(credit)
2. Bank balance match: Bank accounts must match actual balance
3. Account existence: All accounts must exist in chart of accounts

Test with tenant: b3776033-40e5-42e2-ab7b-b1df97062d0c
"""
import asyncio
import httpx
from decimal import Decimal
from datetime import date
import json

BASE_URL = "http://localhost:8000"
TEST_CLIENT_ID = "b3776033-40e5-42e2-ab7b-b1df97062d0c"


async def test_opening_balance_workflow():
    """Test complete opening balance workflow"""
    print("=" * 80)
    print("OPENING BALANCE API TEST")
    print("=" * 80)
    print()
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Test 1: Import BALANCED opening balance
        print("Test 1: Import BALANCED opening balance")
        print("-" * 80)
        
        balanced_import = {
            "client_id": TEST_CLIENT_ID,
            "import_date": "2024-01-01",
            "fiscal_year": "2024",
            "description": "Åpningsbalanse 2024 - Balanced Test",
            "lines": [
                {"account_number": "1920", "account_name": "Bank Account", "debit": "100000.00", "credit": "0.00"},
                {"account_number": "1500", "account_name": "Maskiner", "debit": "50000.00", "credit": "0.00"},
                {"account_number": "2000", "account_name": "Egenkapital", "debit": "0.00", "credit": "150000.00"},
            ]
        }
        
        response = await client.post(
            f"{BASE_URL}/api/opening-balance/import",
            json=balanced_import
        )
        
        if response.status_code == 201:
            ob = response.json()
            opening_balance_id = ob["id"]
            print(f"✓ Import successful! ID: {opening_balance_id}")
            print(f"  Status: {ob['status']}")
            print(f"  Total Debit: {ob['total_debit']} NOK")
            print(f"  Total Credit: {ob['total_credit']} NOK")
            print(f"  Difference: {ob['balance_difference']} NOK")
            print()
        else:
            print(f"✗ Import failed: {response.status_code}")
            print(f"  {response.text}")
            return
        
        # Test 2: Validate with bank balance verification
        print("Test 2: Validate opening balance (with bank verification)")
        print("-" * 80)
        
        validate_request = {
            "opening_balance_id": opening_balance_id,
            "bank_balances": [
                {
                    "account_number": "1920",
                    "actual_balance": "100000.00"  # Matches opening balance
                }
            ]
        }
        
        response = await client.post(
            f"{BASE_URL}/api/opening-balance/validate",
            json=validate_request
        )
        
        if response.status_code == 200:
            validation = response.json()
            print(f"✓ Validation complete!")
            print(f"  Status: {validation['status']}")
            print(f"  Is Balanced: {validation['is_balanced']}")
            print(f"  Bank Balance Verified: {validation['bank_balance_verified']}")
            
            if validation.get('validation_errors'):
                print(f"\n  Validation Errors:")
                for err in validation['validation_errors']:
                    print(f"    - {err['message']}")
            
            if validation.get('bank_balance_errors'):
                print(f"\n  Bank Balance Errors:")
                for err in validation['bank_balance_errors']:
                    print(f"    - {err['message']}")
            
            print()
        else:
            print(f"✗ Validation failed: {response.status_code}")
            print(f"  {response.text}")
            return
        
        # Test 3: Preview before import
        print("Test 3: Preview opening balance")
        print("-" * 80)
        
        response = await client.get(
            f"{BASE_URL}/api/opening-balance/preview/{opening_balance_id}"
        )
        
        if response.status_code == 200:
            preview = response.json()
            print(f"✓ Preview loaded!")
            print(f"  Can Import: {preview['can_import']}")
            print(f"  Validation Summary:")
            for key, value in preview['validation_summary'].items():
                print(f"    {key}: {value}")
            
            if preview['errors']:
                print(f"\n  Errors:")
                for err in preview['errors']:
                    print(f"    [{err['severity']}] {err['message']}")
            
            if preview['warnings']:
                print(f"\n  Warnings:")
                for warn in preview['warnings']:
                    print(f"    [{warn['severity']}] {warn['message']}")
            
            print()
        else:
            print(f"✗ Preview failed: {response.status_code}")
            print(f"  {response.text}")
            return
        
        # Test 4: Import to ledger (if validation passed)
        if preview['can_import']:
            print("Test 4: Import to general ledger")
            print("-" * 80)
            
            response = await client.post(
                f"{BASE_URL}/api/opening-balance/import-to-ledger/{opening_balance_id}"
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✓ Import successful!")
                print(f"  Voucher Number: {result['voucher_number']}")
                print(f"  Journal Entry ID: {result['journal_entry_id']}")
                print(f"  Message: {result['message']}")
                print()
            else:
                print(f"✗ Import to ledger failed: {response.status_code}")
                print(f"  {response.text}")
        
        # Test 5: NOT BALANCED (should fail)
        print("\nTest 5: Import UNBALANCED opening balance (should fail validation)")
        print("-" * 80)
        
        unbalanced_import = {
            "client_id": TEST_CLIENT_ID,
            "import_date": "2024-01-01",
            "fiscal_year": "2024",
            "description": "Unbalanced Test - Should Fail",
            "lines": [
                {"account_number": "1920", "account_name": "Bank", "debit": "100000.00", "credit": "0.00"},
                {"account_number": "2000", "account_name": "Egenkapital", "debit": "0.00", "credit": "95000.00"},  # NOT BALANCED!
            ]
        }
        
        response = await client.post(
            f"{BASE_URL}/api/opening-balance/import",
            json=unbalanced_import
        )
        
        if response.status_code == 201:
            ob = response.json()
            unbalanced_id = ob["id"]
            print(f"✓ Import created (status: {ob['status']})")
            print(f"  Difference: {ob['balance_difference']} NOK (NOT ZERO!)")
            
            # Try to validate
            validate_request = {"opening_balance_id": unbalanced_id}
            response = await client.post(
                f"{BASE_URL}/api/opening-balance/validate",
                json=validate_request
            )
            
            if response.status_code == 200:
                validation = response.json()
                print(f"\n  Validation Status: {validation['status']}")
                if validation.get('validation_errors'):
                    print(f"  ✗ Validation Errors (expected):")
                    for err in validation['validation_errors']:
                        print(f"    - {err['message']}")
                
                # Try to import (should fail)
                response = await client.post(
                    f"{BASE_URL}/api/opening-balance/import-to-ledger/{unbalanced_id}"
                )
                
                if response.status_code != 200:
                    print(f"\n  ✓ Import blocked (as expected): {response.status_code}")
                    error_detail = response.json().get("detail", "")
                    print(f"    {error_detail}")
                else:
                    print(f"\n  ✗ ERROR: Import should have been blocked!")
            
            print()
        
        # Test 6: Bank balance mismatch (should fail)
        print("\nTest 6: Bank balance MISMATCH (should fail validation)")
        print("-" * 80)
        
        bank_mismatch_import = {
            "client_id": TEST_CLIENT_ID,
            "import_date": "2024-01-01",
            "fiscal_year": "2024",
            "description": "Bank Mismatch Test - Should Fail",
            "lines": [
                {"account_number": "1920", "account_name": "Bank", "debit": "50000.00", "credit": "0.00"},
                {"account_number": "2000", "account_name": "Egenkapital", "debit": "0.00", "credit": "50000.00"},
            ]
        }
        
        response = await client.post(
            f"{BASE_URL}/api/opening-balance/import",
            json=bank_mismatch_import
        )
        
        if response.status_code == 201:
            ob = response.json()
            bank_mismatch_id = ob["id"]
            print(f"✓ Import created")
            
            # Validate with WRONG bank balance
            validate_request = {
                "opening_balance_id": bank_mismatch_id,
                "bank_balances": [
                    {
                        "account_number": "1920",
                        "actual_balance": "75000.00"  # MISMATCH! (should be 50000)
                    }
                ]
            }
            
            response = await client.post(
                f"{BASE_URL}/api/opening-balance/validate",
                json=validate_request
            )
            
            if response.status_code == 200:
                validation = response.json()
                print(f"  Validation Status: {validation['status']}")
                
                if validation.get('bank_balance_errors'):
                    print(f"  ✓ Bank Balance Errors (expected):")
                    for err in validation['bank_balance_errors']:
                        print(f"    - {err['message']}")
                
                # Try to import (should fail)
                response = await client.post(
                    f"{BASE_URL}/api/opening-balance/import-to-ledger/{bank_mismatch_id}"
                )
                
                if response.status_code != 200:
                    print(f"\n  ✓ Import blocked due to bank mismatch (as expected)")
                else:
                    print(f"\n  ✗ ERROR: Import should have been blocked!")
            
            print()
        
        # Test 7: List all opening balances
        print("\nTest 7: List all opening balances for client")
        print("-" * 80)
        
        response = await client.get(
            f"{BASE_URL}/api/opening-balance/list/{TEST_CLIENT_ID}"
        )
        
        if response.status_code == 200:
            opening_balances = response.json()
            print(f"✓ Found {len(opening_balances)} opening balance(s)")
            for ob in opening_balances:
                print(f"\n  ID: {ob['id']}")
                print(f"  Fiscal Year: {ob['fiscal_year']}")
                print(f"  Status: {ob['status']}")
                print(f"  Balanced: {ob['is_balanced']}")
                print(f"  Description: {ob['description']}")
            print()
        else:
            print(f"✗ List failed: {response.status_code}")
    
    print("=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_opening_balance_workflow())

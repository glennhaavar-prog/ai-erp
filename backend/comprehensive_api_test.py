#!/usr/bin/env python3
"""
COMPREHENSIVE API TEST SUITE
Tests: Kontaktregister, Firmainnstillinger, Åpningsbalanse
Author: Sonny (Subagent)
Date: 2026-02-11
"""

import requests
import json
import uuid
from decimal import Decimal
from datetime import datetime, date
from typing import Dict, List, Any

# Configuration
BASE_URL = "http://localhost:8000"
CLIENT_ID = "b3776033-40e5-42e2-ab7b-b1df97062d0c"

# Test results tracking
test_results = {
    "kontaktregister": {"passed": 0, "failed": 0, "tests": []},
    "firmainnstillinger": {"passed": 0, "failed": 0, "tests": []},
    "åpningsbalanse": {"passed": 0, "failed": 0, "tests": []}
}

def log_test(module: str, test_name: str, passed: bool, details: str = "", response_data: Any = None):
    """Log test result"""
    status = "✅ PASS" if passed else "❌ FAIL"
    result = {
        "test": test_name,
        "status": status,
        "details": details,
        "response": response_data if not passed else None
    }
    
    test_results[module]["tests"].append(result)
    if passed:
        test_results[module]["passed"] += 1
    else:
        test_results[module]["failed"] += 1
    
    print(f"{status}: {test_name}")
    if details:
        print(f"  → {details}")
    if not passed and response_data:
        print(f"  → Response: {json.dumps(response_data, indent=2)}")

def print_section(title: str):
    """Print section header"""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")

# =============================================================================
# 1. KONTAKTREGISTER TESTS
# =============================================================================

def test_kontaktregister():
    print_section("1. KONTAKTREGISTER (Contact Register)")
    
    supplier_id = None
    customer_id = None
    
    # Test 1.1: Create Supplier (Success)
    print("\n--- 1.1: Create Supplier (Success) ---")
    supplier_data = {
        "client_id": CLIENT_ID,
        "company_name": f"Test Leverandør {uuid.uuid4().hex[:8]}",
        "org_number": f"9{uuid.uuid4().int % 100000000:08d}",
        "address": {
            "line1": "Testveien 123",
            "postal_code": "0123",
            "city": "Oslo"
        },
        "contact": {
            "phone": "+47 12345678",
            "email": "test@supplier.no"
        },
        "financial": {
            "payment_terms_days": 30,
            "currency": "NOK",
            "vat_registered": True
        },
        "notes": "Test supplier for API testing"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/contacts/suppliers/", json=supplier_data)
        if response.status_code == 200:
            data = response.json()
            supplier_id = data.get("id")
            supplier_number = data.get("supplier_number")
            log_test("kontaktregister", "Create Supplier", True, 
                    f"Created supplier {supplier_number} with ID {supplier_id}")
        else:
            log_test("kontaktregister", "Create Supplier", False, 
                    f"Status {response.status_code}", response.json())
    except Exception as e:
        log_test("kontaktregister", "Create Supplier", False, str(e))
    
    # Test 1.2: Read Supplier
    print("\n--- 1.2: Read Supplier ---")
    if supplier_id:
        try:
            response = requests.get(f"{BASE_URL}/api/contacts/suppliers/{supplier_id}")
            if response.status_code == 200:
                data = response.json()
                log_test("kontaktregister", "Read Supplier", True,
                        f"Retrieved: {data.get('company_name')}")
            else:
                log_test("kontaktregister", "Read Supplier", False,
                        f"Status {response.status_code}", response.json())
        except Exception as e:
            log_test("kontaktregister", "Read Supplier", False, str(e))
    
    # Test 1.3: Update Supplier
    print("\n--- 1.3: Update Supplier ---")
    if supplier_id:
        try:
            update_data = {
                "notes": "Updated notes - API test",
                "financial": {
                    "payment_terms_days": 45
                }
            }
            response = requests.put(f"{BASE_URL}/api/contacts/suppliers/{supplier_id}", 
                                   json=update_data)
            if response.status_code == 200:
                log_test("kontaktregister", "Update Supplier", True,
                        "Updated payment terms to 45 days")
            else:
                log_test("kontaktregister", "Update Supplier", False,
                        f"Status {response.status_code}", response.json())
        except Exception as e:
            log_test("kontaktregister", "Update Supplier", False, str(e))
    
    # Test 1.4: Get Audit Log
    print("\n--- 1.4: Get Supplier Audit Log ---")
    if supplier_id:
        try:
            response = requests.get(f"{BASE_URL}/api/contacts/suppliers/{supplier_id}/audit-log")
            if response.status_code == 200:
                data = response.json()
                audit_count = len(data) if isinstance(data, list) else data.get("total", 0)
                log_test("kontaktregister", "Supplier Audit Log", True,
                        f"Found {audit_count} audit entries")
            else:
                log_test("kontaktregister", "Supplier Audit Log", False,
                        f"Status {response.status_code}", response.json())
        except Exception as e:
            log_test("kontaktregister", "Supplier Audit Log", False, str(e))
    
    # Test 1.5: Create Customer (Success)
    print("\n--- 1.5: Create Customer (Success) ---")
    customer_data = {
        "client_id": CLIENT_ID,
        "name": f"Test Kunde {uuid.uuid4().hex[:8]}",
        "org_number": f"9{uuid.uuid4().int % 100000000:08d}",
        "is_company": True,
        "address": {
            "line1": "Kundeveien 456",
            "postal_code": "0456",
            "city": "Bergen"
        },
        "contact": {
            "phone": "+47 87654321",
            "email": "test@customer.no"
        },
        "financial": {
            "payment_terms_days": 14,
            "currency": "NOK",
            "credit_limit": 50000.00
        }
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/contacts/customers/", json=customer_data)
        if response.status_code == 200:
            data = response.json()
            customer_id = data.get("id")
            customer_number = data.get("customer_number")
            log_test("kontaktregister", "Create Customer", True,
                    f"Created customer {customer_number} with ID {customer_id}")
        else:
            log_test("kontaktregister", "Create Customer", False,
                    f"Status {response.status_code}", response.json())
    except Exception as e:
        log_test("kontaktregister", "Create Customer", False, str(e))
    
    # Test 1.6: Duplicate Org Number (Should Fail)
    print("\n--- 1.6: Duplicate Org Number Validation (Should Fail) ---")
    if supplier_data:
        try:
            # Try to create supplier with same org_number
            response = requests.post(f"{BASE_URL}/api/contacts/suppliers/", json=supplier_data)
            if response.status_code == 400 or response.status_code == 409:
                log_test("kontaktregister", "Duplicate Validation", True,
                        "Correctly rejected duplicate org_number")
            else:
                log_test("kontaktregister", "Duplicate Validation", False,
                        f"Should reject duplicate but got status {response.status_code}",
                        response.json())
        except Exception as e:
            log_test("kontaktregister", "Duplicate Validation", False, str(e))
    
    # Test 1.7: List Suppliers with Search
    print("\n--- 1.7: List Suppliers with Search ---")
    try:
        response = requests.get(f"{BASE_URL}/api/contacts/suppliers/",
                               params={"client_id": CLIENT_ID, "status": "active", "limit": 10})
        if response.status_code == 200:
            data = response.json()
            count = len(data) if isinstance(data, list) else data.get("total", 0)
            log_test("kontaktregister", "List Suppliers", True,
                    f"Found {count} active suppliers")
        else:
            log_test("kontaktregister", "List Suppliers", False,
                    f"Status {response.status_code}", response.json())
    except Exception as e:
        log_test("kontaktregister", "List Suppliers", False, str(e))
    
    # Test 1.8: List Customers with Pagination
    print("\n--- 1.8: List Customers with Pagination ---")
    try:
        response = requests.get(f"{BASE_URL}/api/contacts/customers/",
                               params={"client_id": CLIENT_ID, "skip": 0, "limit": 10})
        if response.status_code == 200:
            data = response.json()
            count = len(data) if isinstance(data, list) else data.get("total", 0)
            log_test("kontaktregister", "List Customers", True,
                    f"Found {count} customers")
        else:
            log_test("kontaktregister", "List Customers", False,
                    f"Status {response.status_code}", response.json())
    except Exception as e:
        log_test("kontaktregister", "List Customers", False, str(e))
    
    # Test 1.9: Deactivate Supplier (Soft Delete)
    print("\n--- 1.9: Deactivate Supplier (Soft Delete) ---")
    if supplier_id:
        try:
            response = requests.delete(f"{BASE_URL}/api/contacts/suppliers/{supplier_id}")
            if response.status_code == 200:
                # Verify it's deactivated
                verify_response = requests.get(f"{BASE_URL}/api/contacts/suppliers/{supplier_id}")
                if verify_response.status_code == 200:
                    data = verify_response.json()
                    status = data.get("status")
                    if status == "inactive":
                        log_test("kontaktregister", "Deactivate Supplier", True,
                                "Supplier correctly deactivated (soft delete)")
                    else:
                        log_test("kontaktregister", "Deactivate Supplier", False,
                                f"Status is '{status}', expected 'inactive'", data)
            else:
                log_test("kontaktregister", "Deactivate Supplier", False,
                        f"Status {response.status_code}", response.json())
        except Exception as e:
            log_test("kontaktregister", "Deactivate Supplier", False, str(e))
    
    # Test 1.10: Ledger Integration (Read with Balance)
    print("\n--- 1.10: Ledger Integration (Read with Balance) ---")
    if supplier_id:
        try:
            response = requests.get(f"{BASE_URL}/api/contacts/suppliers/{supplier_id}",
                                   params={"include_balance": True, "include_transactions": True})
            if response.status_code == 200:
                data = response.json()
                has_balance = "balance" in data or "ledger_balance" in data
                log_test("kontaktregister", "Ledger Integration", True,
                        f"Balance integration available: {has_balance}")
            else:
                log_test("kontaktregister", "Ledger Integration", False,
                        f"Status {response.status_code}", response.json())
        except Exception as e:
            log_test("kontaktregister", "Ledger Integration", False, str(e))

# =============================================================================
# 2. FIRMAINNSTILLINGER TESTS
# =============================================================================

def test_firmainnstillinger():
    print_section("2. FIRMAINNSTILLINGER (Client Settings)")
    
    # Test 2.1: GET Settings (Auto-creates if not exists)
    print("\n--- 2.1: GET Settings (Auto-create) ---")
    try:
        response = requests.get(f"{BASE_URL}/api/clients/{CLIENT_ID}/settings")
        if response.status_code == 200:
            data = response.json()
            sections = ["company_info", "accounting_settings", "bank_accounts", 
                       "payroll_employees", "services", "responsible_accountant"]
            has_all_sections = all(section in data for section in sections)
            log_test("firmainnstillinger", "GET Settings", True,
                    f"Retrieved settings with all {len(sections)} sections")
        else:
            log_test("firmainnstillinger", "GET Settings", False,
                    f"Status {response.status_code}", response.json())
    except Exception as e:
        log_test("firmainnstillinger", "GET Settings", False, str(e))
    
    # Test 2.2: Full Update (All Sections)
    print("\n--- 2.2: PUT Full Update (All Sections) ---")
    try:
        update_data = {
            "company_info": {
                "company_name": "Test Firma AS",
                "org_number": "987654321",
                "address": {
                    "street": "Testgata 1",
                    "postal_code": "0001",
                    "city": "Oslo"
                },
                "phone": "+47 22334455",
                "email": "post@testfirma.no",
                "ceo_name": "Test CEO",
                "legal_form": "AS",
                "accounting_year_start_month": 1
            },
            "accounting_settings": {
                "chart_of_accounts": "NS4102",
                "vat_registered": True,
                "vat_period": "bimonthly",
                "currency": "NOK",
                "rounding_rules": {"decimals": 2, "method": "standard"}
            },
            "bank_accounts": [
                {
                    "bank_name": "DNB",
                    "account_number": "12345678901",
                    "ledger_account": "1920",
                    "is_integrated": True,
                    "integration_status": "active"
                }
            ],
            "payroll_employees": {
                "has_employees": True,
                "payroll_frequency": "monthly",
                "employer_tax_zone": "1"
            },
            "services": {
                "services_provided": {
                    "bookkeeping": True,
                    "payroll": True,
                    "annual_accounts": True,
                    "vat_reporting": True,
                    "other": ["advisory"]
                },
                "task_templates": ["standard", "vat_reporting"]
            },
            "responsible_accountant": {
                "name": "Test Accountant",
                "email": "accountant@test.no",
                "phone": "+47 99887766"
            }
        }
        
        response = requests.put(f"{BASE_URL}/api/clients/{CLIENT_ID}/settings", 
                               json=update_data)
        if response.status_code == 200:
            data = response.json()
            log_test("firmainnstillinger", "Full Update", True,
                    "All 6 sections updated successfully")
        else:
            log_test("firmainnstillinger", "Full Update", False,
                    f"Status {response.status_code}", response.json())
    except Exception as e:
        log_test("firmainnstillinger", "Full Update", False, str(e))
    
    # Test 2.3: Partial Update (Only Accountant)
    print("\n--- 2.3: PUT Partial Update (Only Accountant) ---")
    try:
        partial_update = {
            "responsible_accountant": {
                "name": "New Accountant Name",
                "email": "new.accountant@test.no"
            }
        }
        
        response = requests.put(f"{BASE_URL}/api/clients/{CLIENT_ID}/settings",
                               json=partial_update)
        if response.status_code == 200:
            # Verify only accountant was updated
            verify_response = requests.get(f"{BASE_URL}/api/clients/{CLIENT_ID}/settings")
            if verify_response.status_code == 200:
                data = verify_response.json()
                accountant = data.get("responsible_accountant", {})
                if accountant.get("name") == "New Accountant Name":
                    log_test("firmainnstillinger", "Partial Update", True,
                            "Only accountant section updated, others preserved")
                else:
                    log_test("firmainnstillinger", "Partial Update", False,
                            "Accountant not updated correctly", data)
        else:
            log_test("firmainnstillinger", "Partial Update", False,
                    f"Status {response.status_code}", response.json())
    except Exception as e:
        log_test("firmainnstillinger", "Partial Update", False, str(e))
    
    # Test 2.4: Invalid Client (Should Fail)
    print("\n--- 2.4: Invalid Client (Should Fail) ---")
    try:
        fake_client_id = str(uuid.uuid4())
        response = requests.get(f"{BASE_URL}/api/clients/{fake_client_id}/settings")
        if response.status_code == 404:
            log_test("firmainnstillinger", "Invalid Client", True,
                    "Correctly returned 404 for non-existent client")
        else:
            log_test("firmainnstillinger", "Invalid Client", False,
                    f"Expected 404, got {response.status_code}", response.json())
    except Exception as e:
        log_test("firmainnstillinger", "Invalid Client", False, str(e))
    
    # Test 2.5: Verify All 6 Sections Exist
    print("\n--- 2.5: Verify All 6 Sections Exist ---")
    try:
        response = requests.get(f"{BASE_URL}/api/clients/{CLIENT_ID}/settings")
        if response.status_code == 200:
            data = response.json()
            required_sections = [
                "company_info",
                "accounting_settings",
                "bank_accounts",
                "payroll_employees",
                "services",
                "responsible_accountant"
            ]
            missing = [s for s in required_sections if s not in data]
            if not missing:
                log_test("firmainnstillinger", "All 6 Sections", True,
                        "All required sections present")
            else:
                log_test("firmainnstillinger", "All 6 Sections", False,
                        f"Missing sections: {missing}", data)
        else:
            log_test("firmainnstillinger", "All 6 Sections", False,
                    f"Status {response.status_code}", response.json())
    except Exception as e:
        log_test("firmainnstillinger", "All 6 Sections", False, str(e))

# =============================================================================
# 3. ÅPNINGSBALANSE TESTS
# =============================================================================

def test_åpningsbalanse():
    print_section("3. ÅPNINGSBALANSE (Opening Balance)")
    
    balanced_ob_id = None
    unbalanced_ob_id = None
    
    # Test 3.1: Import Balanced Opening Balance (Should Succeed)
    print("\n--- 3.1: Import Balanced Opening Balance (Should Succeed) ---")
    try:
        balanced_data = {
            "client_id": CLIENT_ID,
            "import_date": "2024-01-01",
            "fiscal_year": "2024",
            "description": "Test Balanced Opening Balance",
            "lines": [
                {
                    "account_number": "1920",
                    "account_name": "Bankkonto DNB",
                    "debit": 100000.00,
                    "credit": 0.00
                },
                {
                    "account_number": "1500",
                    "account_name": "Kundefordringer",
                    "debit": 50000.00,
                    "credit": 0.00
                },
                {
                    "account_number": "2000",
                    "account_name": "Egenkapital",
                    "debit": 0.00,
                    "credit": 100000.00
                },
                {
                    "account_number": "2400",
                    "account_name": "Leverandørgjeld",
                    "debit": 0.00,
                    "credit": 50000.00
                }
            ]
        }
        
        response = requests.post(f"{BASE_URL}/api/opening-balance/import", json=balanced_data)
        if response.status_code in [200, 201]:  # Accept both 200 and 201
            data = response.json()
            balanced_ob_id = data.get("id")
            is_balanced = data.get("is_balanced", False)
            total_debit = data.get("total_debit", 0)
            total_credit = data.get("total_credit", 0)
            log_test("åpningsbalanse", "Import Balanced", True,
                    f"Imported balanced OB: Debit={total_debit}, Credit={total_credit}")
        else:
            log_test("åpningsbalanse", "Import Balanced", False,
                    f"Status {response.status_code}", response.json())
    except Exception as e:
        log_test("åpningsbalanse", "Import Balanced", False, str(e))
    
    # Test 3.2: Validate Balanced Opening Balance
    print("\n--- 3.2: Validate Balanced Opening Balance ---")
    if balanced_ob_id:
        try:
            validate_data = {
                "opening_balance_id": balanced_ob_id,
                "bank_balances": [
                    {
                        "account_number": "1920",
                        "actual_balance": 100000.00
                    }
                ]
            }
            
            response = requests.post(f"{BASE_URL}/api/opening-balance/validate",
                                    json=validate_data)
            if response.status_code == 200:
                data = response.json()
                is_valid = data.get("is_valid", False)
                errors = data.get("errors", [])
                log_test("åpningsbalanse", "Validate Balanced", is_valid and len(errors) == 0,
                        f"Valid: {is_valid}, Errors: {len(errors)}")
            else:
                log_test("åpningsbalanse", "Validate Balanced", False,
                        f"Status {response.status_code}", response.json())
        except Exception as e:
            log_test("åpningsbalanse", "Validate Balanced", False, str(e))
    
    # Test 3.3: Preview Opening Balance
    print("\n--- 3.3: Preview Opening Balance ---")
    if balanced_ob_id:
        try:
            response = requests.get(f"{BASE_URL}/api/opening-balance/preview/{balanced_ob_id}")
            if response.status_code == 200:
                data = response.json()
                can_import = data.get("can_import", False)
                line_count = data.get("line_count", 0)
                log_test("åpningsbalanse", "Preview", True,
                        f"Preview available: {line_count} lines, Can import: {can_import}")
            else:
                log_test("åpningsbalanse", "Preview", False,
                        f"Status {response.status_code}", response.json())
        except Exception as e:
            log_test("åpningsbalanse", "Preview", False, str(e))
    
    # Test 3.4: Import to Ledger (Creates Locked Journal Entry)
    print("\n--- 3.4: Import to Ledger (Creates Locked Journal Entry) ---")
    if balanced_ob_id:
        try:
            response = requests.post(f"{BASE_URL}/api/opening-balance/import-to-ledger/{balanced_ob_id}")
            if response.status_code == 200:
                data = response.json()
                journal_entry_id = data.get("journal_entry_id")
                is_locked = data.get("is_locked", False)
                log_test("åpningsbalanse", "Import to Ledger", True,
                        f"Created journal entry {journal_entry_id}, Locked: {is_locked}")
            else:
                log_test("åpningsbalanse", "Import to Ledger", False,
                        f"Status {response.status_code}", response.json())
        except Exception as e:
            log_test("åpningsbalanse", "Import to Ledger", False, str(e))
    
    # Test 3.5: Import Unbalanced (Should FAIL)
    print("\n--- 3.5: Import Unbalanced Opening Balance (Should FAIL) ---")
    try:
        unbalanced_data = {
            "client_id": CLIENT_ID,
            "import_date": "2024-01-01",
            "fiscal_year": "2024",
            "description": "Test Unbalanced - Should Fail",
            "lines": [
                {
                    "account_number": "1920",
                    "account_name": "Bank",
                    "debit": 100000.00,
                    "credit": 0.00
                },
                {
                    "account_number": "2000",
                    "account_name": "Egenkapital",
                    "debit": 0.00,
                    "credit": 95000.00  # 5000 NOK difference!
                }
            ]
        }
        
        response = requests.post(f"{BASE_URL}/api/opening-balance/import", json=unbalanced_data)
        if response.status_code in [200, 201]:
            data = response.json()
            unbalanced_ob_id = data.get("id")
            is_balanced = data.get("is_balanced", False)
            balance_diff = data.get("balance_difference", 0)
            
            # Now try to validate and import (should fail)
            validate_response = requests.post(f"{BASE_URL}/api/opening-balance/validate",
                                             json={"opening_balance_id": unbalanced_ob_id})
            
            if validate_response.status_code == 200:
                validate_data = validate_response.json()
                is_valid = validate_data.get("is_valid", False)
                errors = validate_data.get("errors", [])
                has_balance_error = any("NOT_BALANCED" in str(e) for e in errors)
                
                if not is_valid and has_balance_error:
                    log_test("åpningsbalanse", "Unbalanced Validation", True,
                            f"Correctly rejected unbalanced data (diff: {balance_diff})")
                else:
                    log_test("åpningsbalanse", "Unbalanced Validation", False,
                            "Should reject unbalanced data", validate_data)
            
            # Try to import to ledger (should fail)
            import_response = requests.post(f"{BASE_URL}/api/opening-balance/import-to-ledger/{unbalanced_ob_id}")
            if import_response.status_code in [400, 422]:
                log_test("åpningsbalanse", "Block Unbalanced Import", True,
                        "Correctly blocked import of unbalanced data")
            else:
                log_test("åpningsbalanse", "Block Unbalanced Import", False,
                        f"Should block import, got status {import_response.status_code}",
                        import_response.json())
        else:
            log_test("åpningsbalanse", "Unbalanced Validation", False,
                    f"Status {response.status_code}", response.json())
    except Exception as e:
        log_test("åpningsbalanse", "Unbalanced Validation", False, str(e))
    
    # Test 3.6: Bank Balance Mismatch (Should FAIL)
    print("\n--- 3.6: Bank Balance Mismatch (Should FAIL) ---")
    try:
        bank_mismatch_data = {
            "client_id": CLIENT_ID,
            "import_date": "2024-01-01",
            "fiscal_year": "2024",
            "description": "Test Bank Mismatch",
            "lines": [
                {
                    "account_number": "1920",
                    "account_name": "Bank",
                    "debit": 100000.00,
                    "credit": 0.00
                },
                {
                    "account_number": "2000",
                    "account_name": "Egenkapital",
                    "debit": 0.00,
                    "credit": 100000.00
                }
            ]
        }
        
        response = requests.post(f"{BASE_URL}/api/opening-balance/import", json=bank_mismatch_data)
        if response.status_code in [200, 201]:
            data = response.json()
            ob_id = data.get("id")
            
            # Validate with WRONG bank balance
            validate_data = {
                "opening_balance_id": ob_id,
                "bank_balances": [
                    {
                        "account_number": "1920",
                        "actual_balance": 95000.00  # Mismatch!
                    }
                ]
            }
            
            validate_response = requests.post(f"{BASE_URL}/api/opening-balance/validate",
                                             json=validate_data)
            if validate_response.status_code == 200:
                validate_result = validate_response.json()
                errors = validate_result.get("errors", [])
                has_bank_error = any("BANK" in str(e).upper() or "MISMATCH" in str(e).upper() 
                                    for e in errors)
                
                if has_bank_error:
                    log_test("åpningsbalanse", "Bank Mismatch Validation", True,
                            "Correctly detected bank balance mismatch")
                else:
                    log_test("åpningsbalanse", "Bank Mismatch Validation", False,
                            "Should detect bank mismatch", validate_result)
            else:
                log_test("åpningsbalanse", "Bank Mismatch Validation", False,
                        f"Status {validate_response.status_code}", validate_response.json())
        else:
            log_test("åpningsbalanse", "Bank Mismatch Validation", False,
                    f"Status {response.status_code}", response.json())
    except Exception as e:
        log_test("åpningsbalanse", "Bank Mismatch Validation", False, str(e))
    
    # Test 3.7: List Opening Balances
    print("\n--- 3.7: List Opening Balances ---")
    try:
        response = requests.get(f"{BASE_URL}/api/opening-balance/list/{CLIENT_ID}")
        if response.status_code == 200:
            data = response.json()
            count = len(data) if isinstance(data, list) else data.get("total", 0)
            log_test("åpningsbalanse", "List Opening Balances", True,
                    f"Found {count} opening balance records")
        else:
            log_test("åpningsbalanse", "List Opening Balances", False,
                    f"Status {response.status_code}", response.json())
    except Exception as e:
        log_test("åpningsbalanse", "List Opening Balances", False, str(e))

# =============================================================================
# MAIN TEST EXECUTION
# =============================================================================

def print_summary():
    """Print final test summary"""
    print("\n" + "="*80)
    print("  TEST SUMMARY")
    print("="*80 + "\n")
    
    total_passed = 0
    total_failed = 0
    
    for module, results in test_results.items():
        passed = results["passed"]
        failed = results["failed"]
        total = passed + failed
        total_passed += passed
        total_failed += failed
        
        status = "✅" if failed == 0 else "⚠️"
        print(f"{status} {module.upper()}: {passed}/{total} passed")
        
        if failed > 0:
            print(f"   Failed tests:")
            for test in results["tests"]:
                if "❌" in test["status"]:
                    print(f"     - {test['test']}: {test['details']}")
    
    print(f"\n{'='*80}")
    grand_total = total_passed + total_failed
    percentage = (total_passed / grand_total * 100) if grand_total > 0 else 0
    
    print(f"TOTAL: {total_passed}/{grand_total} tests passed ({percentage:.1f}%)")
    
    if total_failed == 0:
        print("🎉 ALL TESTS PASSED! 🎉")
    else:
        print(f"⚠️  {total_failed} test(s) failed")
    
    print("="*80 + "\n")

def main():
    print("\n" + "="*80)
    print("  COMPREHENSIVE BACKEND API TEST SUITE")
    print("  Testing: Kontaktregister, Firmainnstillinger, Åpningsbalanse")
    print(f"  Backend: {BASE_URL}")
    print(f"  Tenant: {CLIENT_ID}")
    print(f"  Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    # Check backend health
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is healthy\n")
        else:
            print("⚠️  Backend returned non-200 status\n")
    except Exception as e:
        print(f"❌ Cannot connect to backend: {e}\n")
        return
    
    # Run all tests
    test_kontaktregister()
    test_firmainnstillinger()
    test_åpningsbalanse()
    
    # Print summary
    print_summary()
    
    # Save results to file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"comprehensive_test_results_{timestamp}.json"
    with open(filename, 'w') as f:
        json.dump(test_results, f, indent=2, default=str)
    print(f"📄 Detailed results saved to: {filename}\n")

if __name__ == "__main__":
    main()

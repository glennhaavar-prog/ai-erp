#!/usr/bin/env python3
"""
Test script for Client Settings (FIRMAINNSTILLINGER) API
"""
import requests
import json
from datetime import date

BASE_URL = "http://localhost:8000"
TEST_CLIENT_ID = "b3776033-40e5-42e2-ab7b-b1df97062d0c"


def test_get_settings():
    """Test GET /api/clients/{client_id}/settings"""
    print("=" * 60)
    print("TEST 1: GET Client Settings")
    print("=" * 60)
    
    url = f"{BASE_URL}/api/clients/{TEST_CLIENT_ID}/settings"
    response = requests.get(url)
    
    print(f"Status Code: {response.status_code}")
    assert response.status_code == 200, "GET should return 200 OK"
    
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2)}")
    
    # Validate structure
    assert "company_info" in data
    assert "accounting_settings" in data
    assert "bank_accounts" in data
    assert "payroll_employees" in data
    assert "services" in data
    assert "responsible_accountant" in data
    
    print("✅ GET test passed\n")
    return data


def test_update_settings():
    """Test PUT /api/clients/{client_id}/settings"""
    print("=" * 60)
    print("TEST 2: PUT Update Client Settings")
    print("=" * 60)
    
    url = f"{BASE_URL}/api/clients/{TEST_CLIENT_ID}/settings"
    
    update_data = {
        "company_info": {
            "company_name": "Test AS (Updated)",
            "org_number": "99986e7f5",
            "address": {
                "street": "Ny Testveien 456",
                "postal_code": "0456",
                "city": "Bergen"
            },
            "phone": "+47 99887766",
            "email": "kontakt@test.no",
            "ceo_name": "Anne Hansen",
            "chairman_name": "Per Olsen",
            "industry": "Software Development",
            "nace_code": "62.011",
            "accounting_year_start_month": 7,
            "incorporation_date": "2019-06-15",
            "legal_form": "AS"
        },
        "accounting_settings": {
            "chart_of_accounts": "NS4102",
            "vat_registered": True,
            "vat_period": "annual",
            "currency": "NOK",
            "rounding_rules": {
                "decimals": 2,
                "method": "round_half_up"
            }
        },
        "bank_accounts": [
            {
                "bank_name": "DNB",
                "account_number": "12001234567",
                "ledger_account": "1920",
                "is_integrated": True,
                "integration_status": "active"
            },
            {
                "bank_name": "Sparebank 1",
                "account_number": "12007654321",
                "ledger_account": "1921",
                "is_integrated": False,
                "integration_status": "inactive"
            }
        ],
        "payroll_employees": {
            "has_employees": True,
            "payroll_frequency": "monthly",
            "employer_tax_zone": "zone3"
        },
        "services": {
            "services_provided": {
                "bookkeeping": True,
                "payroll": True,
                "annual_accounts": True,
                "vat_reporting": True,
                "other": ["advisory", "tax_planning", "budgeting"]
            },
            "task_templates": ["monthly_closing", "vat_reporting", "payroll_processing"]
        },
        "responsible_accountant": {
            "name": "Glenn Fossen",
            "email": "glenn@kontali.no",
            "phone": "+47 98765432"
        }
    }
    
    response = requests.put(url, json=update_data)
    
    print(f"Status Code: {response.status_code}")
    assert response.status_code == 200, "PUT should return 200 OK"
    
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2)}")
    
    # Validate updated values
    assert data["company_info"]["company_name"] == "Test AS (Updated)"
    assert data["company_info"]["address"]["city"] == "Bergen"
    assert data["accounting_settings"]["vat_period"] == "annual"
    assert len(data["bank_accounts"]) == 2
    assert data["payroll_employees"]["has_employees"] is True
    assert data["responsible_accountant"]["name"] == "Glenn Fossen"
    
    print("✅ PUT test passed\n")
    return data


def test_partial_update():
    """Test partial update - only updating one section"""
    print("=" * 60)
    print("TEST 3: Partial Update (Only Responsible Accountant)")
    print("=" * 60)
    
    url = f"{BASE_URL}/api/clients/{TEST_CLIENT_ID}/settings"
    
    partial_update = {
        "responsible_accountant": {
            "name": "Nikoline Agent",
            "email": "nikoline@kontali.no",
            "phone": "+47 11223344"
        }
    }
    
    response = requests.put(url, json=partial_update)
    
    print(f"Status Code: {response.status_code}")
    assert response.status_code == 200, "Partial PUT should return 200 OK"
    
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2)}")
    
    # Validate only the updated field changed
    assert data["responsible_accountant"]["name"] == "Nikoline Agent"
    assert data["responsible_accountant"]["email"] == "nikoline@kontali.no"
    
    # Other fields should remain unchanged
    assert data["company_info"]["company_name"] == "Test AS (Updated)"
    
    print("✅ Partial update test passed\n")
    return data


def test_invalid_client():
    """Test GET with invalid client ID"""
    print("=" * 60)
    print("TEST 4: Invalid Client ID")
    print("=" * 60)
    
    url = f"{BASE_URL}/api/clients/00000000-0000-0000-0000-000000000000/settings"
    response = requests.get(url)
    
    print(f"Status Code: {response.status_code}")
    assert response.status_code == 404, "Invalid client should return 404"
    
    print("✅ Invalid client test passed\n")


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("CLIENT SETTINGS API TEST SUITE")
    print("=" * 60 + "\n")
    
    try:
        # Test 1: GET settings
        settings = test_get_settings()
        
        # Test 2: Full update
        updated_settings = test_update_settings()
        
        # Test 3: Partial update
        partial_settings = test_partial_update()
        
        # Test 4: Invalid client
        test_invalid_client()
        
        print("=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())

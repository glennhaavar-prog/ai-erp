#!/usr/bin/env python3
"""
Generate test data for Bank Reconciliation (Bankavstemming) feature.

Creates sample bank accounts and transactions in the 4 PowerOffice categories:
1. Uttak postert - ikke inkludert i kontoutskrift (Withdrawals posted, not in statement)
2. Innskudd postert - ikke inkludert i kontoutskrift (Deposits posted, not in statement)
3. Uttak ikke postert - inkludert i kontoutskrift (Withdrawals not posted, in statement)
4. Innskudd ikke postert - inkludert i kontoutskrift (Deposits not posted, in statement)

This demonstrates the reconciliation between:
- Saldo i Go (System balance)
- Saldo i kontoutskrift (Bank statement balance)
- Korreksjoner (Adjustments from categories 1 & 2)
- Differanse (Difference that should be 0 when balanced)
"""

import json
from datetime import datetime, date, timedelta
from decimal import Decimal
from uuid import uuid4


def generate_test_data():
    """Generate comprehensive test data for bankavstemming."""

    # Test client ID
    client_id = str(uuid4())

    # Account 1: Main bank account with some unmatched items
    account_1 = {
        "account_id": "acc_001",
        "account_number": "1920",
        "account_name": "Hovedkonto - Bank",
        "saldo_i_bank": 125450.50,
        "saldo_i_go": 125200.25,
        "differanse": 250.25,
        "poster_a_avstemme": 3,
        "currency": "NOK",
    }

    # Account 2: Savings account (balanced)
    account_2 = {
        "account_id": "acc_002",
        "account_number": "1921",
        "account_name": "Sparekonto",
        "saldo_i_bank": 50000.00,
        "saldo_i_go": 50000.00,
        "differanse": 0.0,
        "poster_a_avstemme": 0,
        "currency": "NOK",
    }

    # Detailed reconciliation for Account 1
    today = date.today()
    period_start = f"{today.year}-{today.month:02d}-01"
    period_end = today.isoformat()

    # Category 1: Uttak postert - ikke inkludert i kontoutskrift
    # (Withdrawals posted in system but not yet in bank statement)
    category_1_txns = [
        {
            "id": "t001",
            "date": "2026-02-05",
            "description": "Lønn utbetaling februar",
            "beløp": -45000.00,
            "valutakode": "NOK",
            "voucher_number": "V001",
            "status": "posted",
        },
        {
            "id": "t002",
            "date": "2026-02-08",
            "description": "Leverandør betaling - Acme AS",
            "beløp": -12500.00,
            "valutakode": "NOK",
            "voucher_number": "V002",
            "status": "posted",
        },
    ]

    # Category 2: Innskudd postert - ikke inkludert i kontoutskrift
    # (Deposits posted in system but not yet in bank statement)
    category_2_txns = [
        {
            "id": "t003",
            "date": "2026-02-10",
            "description": "Kundebetalinger - invoices",
            "beløp": 35250.00,
            "valutakode": "NOK",
            "voucher_number": "V003",
            "status": "posted",
        },
    ]

    # Category 3: Uttak ikke postert - inkludert i kontoutskrift
    # (Withdrawals in bank statement but not yet posted in system)
    category_3_txns = [
        {
            "id": "t004",
            "date": "2026-02-11",
            "description": "Gebyr fra bank",
            "beløp": -500.00,
            "valutakode": "NOK",
            "status": "in_statement",
        },
    ]

    # Category 4: Innskudd ikke postert - inkludert i kontoutskrift
    # (Deposits in bank statement but not yet posted in system)
    category_4_txns = []

    reconciliation_detail = {
        "account_id": "acc_001",
        "account_number": "1920",
        "account_name": "Hovedkonto - Bank",
        "period_start": period_start,
        "period_end": period_end,
        "categories": [
            {
                "category_key": "uttak_postert_ikke_statement",
                "category_name": "Uttak postert - ikke inkludert i kontoutskrift",
                "transactions": category_1_txns,
                "total_beløp": sum(t["beløp"] for t in category_1_txns),
            },
            {
                "category_key": "innskudd_postert_ikke_statement",
                "category_name": "Innskudd postert - ikke inkludert i kontoutskrift",
                "transactions": category_2_txns,
                "total_beløp": sum(t["beløp"] for t in category_2_txns),
            },
            {
                "category_key": "uttak_ikke_postert_i_statement",
                "category_name": "Uttak ikke postert - inkludert i kontoutskrift",
                "transactions": category_3_txns,
                "total_beløp": sum(t["beløp"] for t in category_3_txns),
            },
            {
                "category_key": "innskudd_ikke_postert_i_statement",
                "category_name": "Innskudd ikke postert - inkludert i kontoutskrift",
                "transactions": category_4_txns,
                "total_beløp": sum(t["beløp"] for t in category_4_txns),
            },
        ],
        "saldo_i_go": 125200.25,
        "korreksjoner_total": -22250.00,  # -57500 + 35250
        "saldo_etter_korreksjoner": 102950.25,  # 125200 - 22250
        "kontoutskrift_saldo": 102450.25,  # Actual bank statement
        "differanse": 500.00,  # Should be 0 if perfectly balanced
        "is_balanced": False,
        "currency": "NOK",
    }

    # Test case: Balanced account
    balanced_reconciliation = {
        "account_id": "acc_002",
        "account_number": "1921",
        "account_name": "Sparekonto",
        "period_start": period_start,
        "period_end": period_end,
        "categories": [
            {
                "category_key": "uttak_postert_ikke_statement",
                "category_name": "Uttak postert - ikke inkludert i kontoutskrift",
                "transactions": [],
                "total_beløp": 0.0,
            },
            {
                "category_key": "innskudd_postert_ikke_statement",
                "category_name": "Innskudd postert - ikke inkludert i kontoutskrift",
                "transactions": [],
                "total_beløp": 0.0,
            },
            {
                "category_key": "uttak_ikke_postert_i_statement",
                "category_name": "Uttak ikke postert - inkludert i kontoutskrift",
                "transactions": [],
                "total_beløp": 0.0,
            },
            {
                "category_key": "innskudd_ikke_postert_i_statement",
                "category_name": "Innskudd ikke postert - inkludert i kontoutskrift",
                "transactions": [],
                "total_beløp": 0.0,
            },
        ],
        "saldo_i_go": 50000.00,
        "korreksjoner_total": 0.0,
        "saldo_etter_korreksjoner": 50000.00,
        "kontoutskrift_saldo": 50000.00,
        "differanse": 0.0,
        "is_balanced": True,
        "currency": "NOK",
    }

    return {
        "client_id": client_id,
        "timestamp": datetime.now().isoformat(),
        "accounts": [account_1, account_2],
        "reconciliation_details": [reconciliation_detail, balanced_reconciliation],
        "test_scenarios": {
            "scenario_1_unmatched_withdrawals": {
                "description": "Shows withdrawals posted in system but not yet in bank statement",
                "category": "Uttak postert - ikke inkludert i kontoutskrift",
                "example_amount": -57500.00,
                "example_transactions": [
                    {"date": "2026-02-05", "description": "Salary payment", "amount": -45000},
                    {
                        "date": "2026-02-08",
                        "description": "Vendor payment",
                        "amount": -12500,
                    },
                ],
            },
            "scenario_2_unmatched_deposits": {
                "description": "Shows deposits posted in system but not yet in bank statement",
                "category": "Innskudd postert - ikke inkludert i kontoutskrift",
                "example_amount": 35250.00,
                "example_transactions": [
                    {
                        "date": "2026-02-10",
                        "description": "Customer invoice payments",
                        "amount": 35250,
                    }
                ],
            },
            "scenario_3_bank_fees": {
                "description": "Shows bank charges in statement but not yet posted in system",
                "category": "Uttak ikke postert - inkludert i kontoutskrift",
                "example_amount": -500.00,
                "example_transactions": [
                    {"date": "2026-02-11", "description": "Bank fee", "amount": -500}
                ],
            },
            "scenario_4_balanced": {
                "description": "Perfectly reconciled account with no differences",
                "category": "All categories",
                "difference": 0.00,
                "is_balanced": True,
            },
        },
    }


def main():
    test_data = generate_test_data()

    # Save to file
    filename = "bank_reconciliation_test_data.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(test_data, f, indent=2, ensure_ascii=False)

    print(f"✓ Test data generated: {filename}")
    print(f"\nTest Scenarios:")
    print("=" * 60)

    for scenario_key, scenario in test_data["test_scenarios"].items():
        print(f"\n{scenario_key.upper()}")
        print(f"Description: {scenario['description']}")
        if "category" in scenario:
            print(f"Category: {scenario['category']}")
        if "example_amount" in scenario:
            print(f"Total Amount: {scenario['example_amount']:.2f} NOK")
        if "difference" in scenario:
            print(f"Difference: {scenario['difference']:.2f} NOK")
        if "is_balanced" in scenario:
            print(f"Is Balanced: {scenario['is_balanced']}")

    print("\n" + "=" * 60)
    print(f"Client ID for testing: {test_data['client_id']}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Quick verification script for Ledger Sync

Run this to verify the ledger sync is working correctly.
"""
import asyncio
from sqlalchemy import text
from app.database import AsyncSessionLocal
from datetime import datetime

async def verify_sync():
    print("\n" + "="*80)
    print("🔍 LEDGER SYNC VERIFICATION")
    print("="*80)
    
    async with AsyncSessionLocal() as db:
        tenant_id = 'b3776033-40e5-42e2-ab7b-b1df97062d0c'
        
        # 1. Check journal entries with 2400/1500
        print("\n📋 Step 1: Journal entries with accounts 2400/1500 (last 7 days)")
        print("-" * 80)
        result = await db.execute(text("""
            SELECT 
                gl.voucher_number,
                gl.accounting_date,
                gl.description,
                gl.source_type,
                COUNT(CASE WHEN gll.account_number = '2400' THEN 1 END) as has_2400,
                COUNT(CASE WHEN gll.account_number = '1500' THEN 1 END) as has_1500
            FROM general_ledger gl
            JOIN general_ledger_lines gll ON gll.general_ledger_id = gl.id
            WHERE gl.client_id = :tenant_id
                AND gl.accounting_date >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY gl.id, gl.voucher_number, gl.accounting_date, gl.description, gl.source_type
            HAVING COUNT(CASE WHEN gll.account_number IN ('2400', '1500') THEN 1 END) > 0
            ORDER BY gl.accounting_date DESC
            LIMIT 10
        """), {"tenant_id": tenant_id})
        
        entries = result.fetchall()
        for entry in entries:
            marker = ""
            if entry[4] > 0:
                marker += "📤 Supplier"
            if entry[5] > 0:
                marker += "📥 Customer" if marker else "📥 Customer"
            print(f"  {marker} | {entry[0]} | {entry[1]} | {entry[3]}")
        
        # 2. Check supplier ledger entries
        print("\n" + "-" * 80)
        print("📤 Step 2: Supplier Ledger Entries (last 7 days)")
        print("-" * 80)
        result = await db.execute(text("""
            SELECT 
                sl.created_at::date as date,
                gl.voucher_number,
                s.company_name,
                sl.invoice_number,
                sl.amount,
                sl.status
            FROM supplier_ledger sl
            JOIN general_ledger gl ON gl.id = sl.voucher_id
            LEFT JOIN suppliers s ON s.id = sl.supplier_id
            WHERE sl.client_id = :tenant_id
                AND sl.created_at >= CURRENT_DATE - INTERVAL '7 days'
            ORDER BY sl.created_at DESC
            LIMIT 10
        """), {"tenant_id": tenant_id})
        
        supplier_entries = result.fetchall()
        if supplier_entries:
            for entry in supplier_entries:
                print(f"  ✅ {entry[0]} | {entry[1]} | {entry[2] or 'No supplier'} | "
                      f"{entry[3] or 'N/A'} | {entry[4]:,.2f} | {entry[5]}")
        else:
            print("  ⚠️ No supplier ledger entries in last 7 days")
        
        # 3. Check customer ledger entries
        print("\n" + "-" * 80)
        print("📥 Step 3: Customer Ledger Entries (last 7 days)")
        print("-" * 80)
        result = await db.execute(text("""
            SELECT 
                cl.created_at::date as date,
                gl.voucher_number,
                cl.customer_name,
                cl.invoice_number,
                cl.amount,
                cl.status
            FROM customer_ledger cl
            JOIN general_ledger gl ON gl.id = cl.voucher_id
            WHERE cl.client_id = :tenant_id
                AND cl.created_at >= CURRENT_DATE - INTERVAL '7 days'
            ORDER BY cl.created_at DESC
            LIMIT 10
        """), {"tenant_id": tenant_id})
        
        customer_entries = result.fetchall()
        if customer_entries:
            for entry in customer_entries:
                print(f"  ✅ {entry[0]} | {entry[1]} | {entry[2]} | "
                      f"{entry[3] or 'N/A'} | {entry[4]:,.2f} | {entry[5]}")
        else:
            print("  ⚠️ No customer ledger entries in last 7 days")
        
        # 4. Balance check
        print("\n" + "-" * 80)
        print("💰 Step 4: Balance Verification")
        print("-" * 80)
        
        # Supplier balance: GL account 2400 vs supplier_ledger total
        result = await db.execute(text("""
            SELECT 
                COALESCE(SUM(gll.credit_amount - gll.debit_amount), 0) as gl_balance,
                (SELECT COALESCE(SUM(remaining_amount), 0) 
                 FROM supplier_ledger 
                 WHERE client_id = :tenant_id) as ledger_balance
            FROM general_ledger_lines gll
            JOIN general_ledger gl ON gl.id = gll.general_ledger_id
            WHERE gl.client_id = :tenant_id
                AND gll.account_number = '2400'
                AND gl.status = 'posted'
        """), {"tenant_id": tenant_id})
        
        supplier_bal = result.fetchone()
        supplier_diff = abs(float(supplier_bal[0]) - float(supplier_bal[1]))
        
        print(f"  📤 Account 2400 (Supplier Debt):")
        print(f"     GL Balance:     {supplier_bal[0]:>15,.2f} NOK")
        print(f"     Ledger Balance: {supplier_bal[1]:>15,.2f} NOK")
        if supplier_diff < 0.01:
            print(f"     ✅ BALANCED! (diff: {supplier_diff:.2f})")
        else:
            print(f"     ⚠️ DIFFERENCE: {supplier_diff:,.2f} NOK")
        
        # Customer balance: GL account 1500 vs customer_ledger total
        result = await db.execute(text("""
            SELECT 
                COALESCE(SUM(gll.debit_amount - gll.credit_amount), 0) as gl_balance,
                (SELECT COALESCE(SUM(remaining_amount), 0) 
                 FROM customer_ledger 
                 WHERE client_id = :tenant_id) as ledger_balance
            FROM general_ledger_lines gll
            JOIN general_ledger gl ON gl.id = gll.general_ledger_id
            WHERE gl.client_id = :tenant_id
                AND gll.account_number = '1500'
                AND gl.status = 'posted'
        """), {"tenant_id": tenant_id})
        
        customer_bal = result.fetchone()
        customer_diff = abs(float(customer_bal[0]) - float(customer_bal[1]))
        
        print(f"\n  📥 Account 1500 (Customer Receivables):")
        print(f"     GL Balance:     {customer_bal[0]:>15,.2f} NOK")
        print(f"     Ledger Balance: {customer_bal[1]:>15,.2f} NOK")
        if customer_diff < 0.01:
            print(f"     ✅ BALANCED! (diff: {customer_diff:.2f})")
        else:
            print(f"     ⚠️ DIFFERENCE: {customer_diff:,.2f} NOK")
        
        # 5. Summary
        print("\n" + "="*80)
        print("📊 SUMMARY")
        print("="*80)
        
        all_good = (
            len(entries) > 0 and
            (len(supplier_entries) > 0 or len(customer_entries) > 0) and
            supplier_diff < 0.01 and
            customer_diff < 0.01
        )
        
        if all_good:
            print("✅ Ledger sync is WORKING PERFECTLY!")
            print("   - Journal entries with 2400/1500 found")
            print("   - Ledger entries created automatically")
            print("   - Balances match between GL and ledgers")
        else:
            print("⚠️ Some issues detected:")
            if len(entries) == 0:
                print("   - No recent journal entries with 2400/1500")
            if len(supplier_entries) == 0 and len(customer_entries) == 0:
                print("   - No ledger entries created in last 7 days")
            if supplier_diff >= 0.01:
                print(f"   - Supplier ledger balance off by {supplier_diff:,.2f}")
            if customer_diff >= 0.01:
                print(f"   - Customer ledger balance off by {customer_diff:,.2f}")
        
        print("\n" + "="*80)

if __name__ == "__main__":
    asyncio.run(verify_sync())

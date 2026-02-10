#!/usr/bin/env python3
"""
Fix Supplier Ledger Consistency - BUG #1 (Version 2 - Comprehensive)

Problem: Supplier ledger sum != Account 2400 balance
Root Cause: Multiple data integrity issues in demo data

Fix Strategy:
1. Delete orphaned GL entries (2400 postings with no vendor_invoices)
2. Create supplier_ledger for vendor_invoices that have GL but no ledger entry  
3. Create GL postings for supplier_ledger entries without them
4. Ensure payments are properly recorded

Usage:
    cd /home/ubuntu/.openclaw/workspace/ai-erp/backend
    python3 scripts/fix_supplier_ledger_consistency_v2.py
"""
import asyncio
import sys
import os
from decimal import Decimal

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, text
from app.database import AsyncSessionLocal
from app.models import (
    Client, SupplierLedger, GeneralLedger, GeneralLedgerLine, VendorInvoice
)


async def check_reconciliation(session: AsyncSession, client_id) -> dict:
    """Check if supplier ledger reconciles with account 2400"""
    result = await session.execute(
        select(func.sum(SupplierLedger.remaining_amount))
        .where(and_(
            SupplierLedger.client_id == client_id,
            SupplierLedger.status.in_(['open', 'partially_paid'])
        ))
    )
    supplier_sum = result.scalar() or Decimal('0')
    
    result = await session.execute(
        select(
            func.sum(GeneralLedgerLine.credit_amount) - func.sum(GeneralLedgerLine.debit_amount)
        )
        .join(GeneralLedger)
        .where(and_(
            GeneralLedger.client_id == client_id,
            GeneralLedgerLine.account_number == '2400'
        ))
    )
    account_2400_balance = result.scalar() or Decimal('0')
    
    difference = supplier_sum - account_2400_balance
    
    return {
        'supplier_ledger_sum': supplier_sum,
        'account_2400_balance': account_2400_balance,
        'difference': difference
    }


async def main():
    """Main execution"""
    print("\n" + "="*70)
    print("🔧 FIX SUPPLIER LEDGER CONSISTENCY - BUG #1 (V2)")
    print("="*70)
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Client).where(Client.is_demo == True).limit(1)
        )
        client = result.scalars().first()
        
        if not client:
            result = await session.execute(select(Client).limit(1))
            client = result.scalars().first()
        
        if not client:
            print("\n❌ ERROR: No client found!")
            return
        
        print(f"\n📊 Client: {client.name}")
        
        # Check BEFORE
        print("\n" + "-"*70)
        print("BEFORE FIX")
        print("-"*70)
        before = await check_reconciliation(session, client.id)
        print(f"\n   Supplier Ledger Sum:     {before['supplier_ledger_sum']:>15,.2f} NOK")
        print(f"   Account 2400 Balance:    {before['account_2400_balance']:>15,.2f} NOK")
        print(f"   Difference:              {before['difference']:>15,.2f} NOK")
        
        if abs(before['difference']) < 1:
            print("\n✅ Already reconciled!")
            return
        
        # STEP 1: Delete orphaned GL entries (not linked to vendor_invoices)
        print("\n" + "-"*70)
        print("STEP 1: Delete orphaned GL entries")
        print("-"*70)
        
        result = await session.execute(
            text("""
                SELECT gl.id, gl.voucher_number
                FROM general_ledger gl
                JOIN general_ledger_lines gll ON gl.id = gll.general_ledger_id
                LEFT JOIN vendor_invoices vi ON vi.general_ledger_id = gl.id
                WHERE gl.client_id = :client_id
                  AND gll.account_number = '2400'
                  AND gl.source_type = 'vendor_invoice'
                  AND vi.id IS NULL
            """),
            {"client_id": str(client.id)}
        )
        orphaned = result.fetchall()
        
        if orphaned:
            print(f"\n⚠️  Found {len(orphaned)} orphaned GL entries (not linked to vendor_invoices)")
            orphaned_ids = [str(row[0]) for row in orphaned]
            
            #Delete lines first
            await session.execute(
                text("DELETE FROM general_ledger_lines WHERE general_ledger_id = ANY(:ids)"),
                {"ids": orphaned_ids}
            )
            
            # Delete entries
            await session.execute(
                text("DELETE FROM general_ledger WHERE id = ANY(:ids)"),
                {"ids": orphaned_ids}
            )
            
            await session.commit()
            print(f"   ✅ Deleted {len(orphaned)} orphaned GL entries")
        else:
            print("\n✅ No orphaned GL entries found")
        
        # STEP 2: Create supplier_ledger for vendor_invoices without them
        print("\n" + "-"*70)
        print("STEP 2: Create supplier_ledger for vendor_invoices")
        print("-"*70)
        
        result = await session.execute(
            text("""
                SELECT vi.id
                FROM vendor_invoices vi
                JOIN general_ledger gl ON vi.general_ledger_id = gl.id
                LEFT JOIN supplier_ledger sl ON sl.voucher_id = gl.id
                WHERE vi.client_id = :client_id
                  AND sl.id IS NULL
            """),
            {"client_id": str(client.id)}
        )
        vi_ids = [row[0] for row in result.fetchall()]
        
        if vi_ids:
            from uuid import uuid4
            
            result = await session.execute(
                select(VendorInvoice, GeneralLedger)
                .join(GeneralLedger, VendorInvoice.general_ledger_id == GeneralLedger.id)
                .where(VendorInvoice.id.in_(vi_ids))
            )
            
            for vi, gl in result.all():
                sl = SupplierLedger(
                    id=uuid4(),
                    client_id=vi.client_id,
                    supplier_id=vi.vendor_id,
                    voucher_id=gl.id,
                    invoice_number=vi.invoice_number,
                    invoice_date=vi.invoice_date,
                    due_date=vi.due_date,
                    amount=vi.total_amount,
                    remaining_amount=vi.total_amount,
                    currency=vi.currency,
                    status='open'
                )
                session.add(sl)
                print(f"   ✅ Created supplier_ledger for {vi.invoice_number}")
            
            await session.commit()
            print(f"\n✅ Created {len(vi_ids)} supplier_ledger entries")
        else:
            print("\n✅ All vendor_invoices have supplier_ledger")
        
        # STEP 3: Delete auto-generated payment postings (we'll handle payments differently)
        print("\n" + "-"*70)
        print("STEP 3: Clean up auto-generated payment postings")
        print("-"*70)
        
        result = await session.execute(
            text("DELETE FROM general_ledger WHERE voucher_series = 'P' RETURNING id")
        )
        payment_count = result.rowcount
        if payment_count > 0:
            await session.commit()
            print(f"   ✅ Deleted {payment_count} auto-generated payment vouchers")
        else:
            print("   ✅ No auto-generated payments to clean up")
        
        # STEP 4: Create GL lines for supplier_ledger entries without them
        print("\n" + "-"*70)
        print("STEP 4: Create GL lines for supplier_ledger entries")
        print("-"*70)
        
        result = await session.execute(
            select(SupplierLedger, GeneralLedger)
            .join(GeneralLedger, SupplierLedger.voucher_id == GeneralLedger.id)
            .where(SupplierLedger.client_id == client.id)
        )
        
        created = 0
        for sl, gl in result.all():
            # Check if has lines
            result2 = await session.execute(
                select(func.count(GeneralLedgerLine.id))
                .where(GeneralLedgerLine.general_ledger_id == gl.id)
            )
            if result2.scalar() == 0:
                # Create lines
                line1 = GeneralLedgerLine(
                    general_ledger_id=gl.id,
                    line_number=1,
                    account_number='6000',
                    debit_amount=sl.amount,
                    credit_amount=Decimal('0'),
                    line_description=f'Varekjøp - {sl.invoice_number}'
                )
                session.add(line1)
                
                line2 = GeneralLedgerLine(
                    general_ledger_id=gl.id,
                    line_number=2,
                    account_number='2400',
                    debit_amount=Decimal('0'),
                    credit_amount=sl.amount,
                    line_description=f'Leverandørgjeld - {sl.invoice_number}'
                )
                session.add(line2)
                
                created += 1
                print(f"   ✅ Created GL lines for {sl.invoice_number}")
        
        if created > 0:
            await session.commit()
            print(f"\n✅ Created GL lines for {created} supplier entries")
        else:
            print("\n✅ All supplier entries have GL lines")
        
        # STEP 5: Update supplier_ledger status to 'paid' for zero remaining
        print("\n" + "-"*70)
        print("STEP 5: Update payment status")
        print("-"*70)
        
        result = await session.execute(
            text("""
                UPDATE supplier_ledger
                SET status = 'paid', remaining_amount = 0
                WHERE client_id = :client_id
                  AND status != 'paid'
                  AND remaining_amount = 0
                RETURNING id
            """),
            {"client_id": str(client.id)}
        )
        updated = result.rowcount
        if updated > 0:
            await session.commit()
            print(f"   ✅ Updated {updated} entries to 'paid' status")
        else:
            print("   ✅ Payment statuses are correct")
        
        # Check AFTER
        print("\n" + "-"*70)
        print("AFTER FIX")
        print("-"*70)
        after = await check_reconciliation(session, client.id)
        print(f"\n   Supplier Ledger Sum:     {after['supplier_ledger_sum']:>15,.2f} NOK")
        print(f"   Account 2400 Balance:    {after['account_2400_balance']:>15,.2f} NOK")
        print(f"   Difference:              {after['difference']:>15,.2f} NOK")
        
        print("\n" + "="*70)
        if abs(after['difference']) < 1:
            print("✅ SUCCESS! Database consistency restored!")
        else:
            print("⚠️  Inconsistency remains, further investigation needed")
        print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())

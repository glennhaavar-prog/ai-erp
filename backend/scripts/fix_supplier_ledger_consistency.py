#!/usr/bin/env python3
"""
Fix Supplier Ledger Consistency - BUG #1

Problem: Supplier ledger entries exist without corresponding GL postings to account 2400.
This script creates the missing GeneralLedgerLine entries for each supplier invoice.

Strategy:
1. Find all supplier_ledger entries
2. Check if their GL voucher has proper debit/credit lines
3. Create missing lines: Debit 6000 (expenses), Credit 2400 (accounts payable)
4. Verify reconciliation after fix

Usage:
    cd /home/ubuntu/.openclaw/workspace/ai-erp/backend
    python3 scripts/fix_supplier_ledger_consistency.py
"""
import asyncio
import sys
import os
from decimal import Decimal
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.database import AsyncSessionLocal
from app.models import (
    Client, SupplierLedger, GeneralLedger, GeneralLedgerLine
)


async def check_reconciliation(session: AsyncSession, client_id) -> dict:
    """
    Check if supplier ledger reconciles with account 2400
    Returns: {
        'supplier_ledger_sum': Decimal,
        'account_2400_balance': Decimal,
        'difference': Decimal
    }
    """
    # Sum of supplier ledger remaining amounts (only open and partially_paid)
    result = await session.execute(
        select(func.sum(SupplierLedger.remaining_amount))
        .where(and_(
            SupplierLedger.client_id == client_id,
            SupplierLedger.status.in_(['open', 'partially_paid'])
        ))
    )
    supplier_sum = result.scalar() or Decimal('0')
    
    # Account 2400 balance (credit - debit)
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


async def find_missing_gl_lines(session: AsyncSession, client_id) -> list:
    """
    Find supplier_ledger entries that lack proper GL postings
    Returns list of (supplier_ledger, general_ledger) tuples needing fix
    """
    # Get all supplier ledger entries with their GL vouchers
    result = await session.execute(
        select(SupplierLedger, GeneralLedger)
        .join(GeneralLedger, SupplierLedger.voucher_id == GeneralLedger.id)
        .where(SupplierLedger.client_id == client_id)
    )
    entries = result.all()
    
    missing = []
    
    for supplier_entry, gl_entry in entries:
        # Check if GL entry has any lines
        result = await session.execute(
            select(func.count(GeneralLedgerLine.id))
            .where(GeneralLedgerLine.general_ledger_id == gl_entry.id)
        )
        line_count = result.scalar()
        
        if line_count == 0:
            missing.append((supplier_entry, gl_entry))
    
    return missing


async def find_vendor_invoices_without_supplier_ledger(session: AsyncSession, client_id) -> list:
    """
    Find vendor_invoices that have GL postings but no supplier_ledger entries.
    These need supplier_ledger entries created.
    Returns list of (vendor_invoice, general_ledger) tuples.
    """
    from sqlalchemy import text
    from app.models import VendorInvoice
    
    # Find vendor_invoices with GL entries but no supplier_ledger
    result = await session.execute(
        text("""
            SELECT vi.id
            FROM vendor_invoices vi
            JOIN general_ledger gl ON vi.general_ledger_id = gl.id
            LEFT JOIN supplier_ledger sl ON sl.voucher_id = gl.id
            WHERE vi.client_id = :client_id
              AND sl.id IS NULL
        """),
        {"client_id": str(client_id)}
    )
    vendor_invoice_ids = [row[0] for row in result.fetchall()]
    
    if not vendor_invoice_ids:
        return []
    
    # Get full VendorInvoice and GeneralLedger objects
    result = await session.execute(
        select(VendorInvoice, GeneralLedger)
        .join(GeneralLedger, VendorInvoice.general_ledger_id == GeneralLedger.id)
        .where(VendorInvoice.id.in_(vendor_invoice_ids))
    )
    
    return result.all()


async def create_supplier_ledger_from_vendor_invoice(
    session: AsyncSession,
    vendor_invoice,
    gl_entry: GeneralLedger
):
    """
    Create a SupplierLedger entry from a VendorInvoice.
    Assumes the invoice is fully unpaid.
    """
    from uuid import uuid4
    
    supplier_ledger = SupplierLedger(
        id=uuid4(),
        client_id=vendor_invoice.client_id,
        supplier_id=vendor_invoice.vendor_id,
        voucher_id=gl_entry.id,
        invoice_number=vendor_invoice.invoice_number,
        invoice_date=vendor_invoice.invoice_date,
        due_date=vendor_invoice.due_date,
        amount=vendor_invoice.total_amount,
        remaining_amount=vendor_invoice.total_amount,  # Assume unpaid
        currency=vendor_invoice.currency,
        status='open'
    )
    session.add(supplier_ledger)
    return supplier_ledger


async def create_gl_lines_for_supplier_entry(
    session: AsyncSession,
    supplier_entry: SupplierLedger,
    gl_entry: GeneralLedger
):
    """
    Create proper GL lines for a supplier invoice:
    - Line 1: Debit 6000 (Varekjøp/expenses) for invoice amount
    - Line 2: Credit 2400 (Leverandørgjeld/accounts payable) for invoice amount
    
    If invoice is paid/partially_paid, also create payment lines:
    - Line 3: Debit 2400 (reduce payable) for paid amount
    - Line 4: Credit 1920 (bank) for paid amount
    """
    from uuid import uuid4
    amount = supplier_entry.amount
    paid_amount = amount - supplier_entry.remaining_amount
    
    # Line 1: Debit expenses (account 6000)
    line1 = GeneralLedgerLine(
        general_ledger_id=gl_entry.id,
        line_number=1,
        account_number='6000',
        debit_amount=amount,
        credit_amount=Decimal('0'),
        line_description=f'Varekjøp - {supplier_entry.invoice_number}',
        ai_confidence_score=95,
        ai_reasoning='Auto-generated: Expense posting for supplier invoice'
    )
    session.add(line1)
    
    # Line 2: Credit accounts payable (account 2400)
    line2 = GeneralLedgerLine(
        general_ledger_id=gl_entry.id,
        line_number=2,
        account_number='2400',
        debit_amount=Decimal('0'),
        credit_amount=amount,
        line_description=f'Leverandørgjeld - {supplier_entry.invoice_number}',
        ai_confidence_score=95,
        ai_reasoning='Auto-generated: Accounts payable posting for supplier invoice'
    )
    session.add(line2)
    
    lines_created = [line1, line2]
    
    # If invoice is paid or partially paid, create payment GL entry
    if paid_amount > 0:
        # Create a separate payment voucher
        payment_voucher = GeneralLedger(
            id=uuid4(),
            client_id=gl_entry.client_id,
            entry_date=gl_entry.entry_date,
            accounting_date=gl_entry.accounting_date,
            period=gl_entry.period,
            fiscal_year=gl_entry.fiscal_year,
            voucher_number=f"P{gl_entry.voucher_number[1:]}",  # P for payment
            voucher_series="P",
            description=f"Betaling {supplier_entry.invoice_number}",
            source_type="supplier_payment",
            created_by_type="ai_agent",
            status="posted"
        )
        session.add(payment_voucher)
        
        # Line 1: Debit 2400 (reduce payable)
        payment_line1 = GeneralLedgerLine(
            general_ledger_id=payment_voucher.id,
            line_number=1,
            account_number='2400',
            debit_amount=paid_amount,
            credit_amount=Decimal('0'),
            line_description=f'Betaling leverandør - {supplier_entry.invoice_number}',
            ai_confidence_score=95,
            ai_reasoning='Auto-generated: Payment reduces accounts payable'
        )
        session.add(payment_line1)
        
        # Line 2: Credit 1920 (bank out)
        payment_line2 = GeneralLedgerLine(
            general_ledger_id=payment_voucher.id,
            line_number=2,
            account_number='1920',
            debit_amount=Decimal('0'),
            credit_amount=paid_amount,
            line_description=f'Bankutbetaling - {supplier_entry.invoice_number}',
            ai_confidence_score=95,
            ai_reasoning='Auto-generated: Bank payment'
        )
        session.add(payment_line2)
        
        lines_created.extend([payment_line1, payment_line2])
    
    return lines_created


async def main():
    """
    Main execution: Fix supplier ledger consistency
    """
    print("\n" + "="*70)
    print("🔧 FIX SUPPLIER LEDGER CONSISTENCY - BUG #1")
    print("="*70)
    
    async with AsyncSessionLocal() as session:
        # Get first demo client
        result = await session.execute(
            select(Client)
            .where(Client.is_demo == True)
            .limit(1)
        )
        client = result.scalars().first()
        
        if not client:
            # Try any client
            result = await session.execute(select(Client).limit(1))
            client = result.scalars().first()
        
        if not client:
            print("\n❌ ERROR: No client found in database!")
            return
        
        print(f"\n📊 Client: {client.name} (ID: {client.id})")
        
        # STEP 1: Check reconciliation BEFORE fix
        print("\n" + "-"*70)
        print("STEP 1: Check reconciliation BEFORE fix")
        print("-"*70)
        
        before_recon = await check_reconciliation(session, client.id)
        
        print(f"\n📋 Reconciliation Status (BEFORE):")
        print(f"   Supplier Ledger Sum:     {before_recon['supplier_ledger_sum']:>15,.2f} NOK")
        print(f"   Account 2400 Balance:    {before_recon['account_2400_balance']:>15,.2f} NOK")
        print(f"   Difference:              {before_recon['difference']:>15,.2f} NOK")
        
        if abs(before_recon['difference']) < 1:
            print("\n✅ Already reconciled! No fix needed.")
            return
        
        print(f"\n⚠️  INCONSISTENCY DETECTED: {abs(before_recon['difference']):,.2f} NOK")
        
        # STEP 2: Clean up orphaned GL entries
        print("\n" + "-"*70)
        print("STEP 2: Clean up orphaned GL entries (no supplier_ledger)")
        print("-"*70)
        
        orphaned_ids = await find_orphaned_gl_entries(session, client.id)
        
        if len(orphaned_ids) > 0:
            print(f"\n⚠️  Found {len(orphaned_ids)} orphaned GL entries with account 2400")
            print("   These have GL postings but no supplier_ledger entries")
            print("   Deleting them...")
            
            from sqlalchemy import delete, text
            
            # Delete GL lines first (cascade should handle it, but be explicit)
            result = await session.execute(
                text("""
                    DELETE FROM general_ledger_lines
                    WHERE general_ledger_id = ANY(:gl_ids)
                """),
                {"gl_ids": orphaned_ids}
            )
            lines_deleted = result.rowcount
            
            # Delete GL entries
            result = await session.execute(
                text("""
                    DELETE FROM general_ledger
                    WHERE id = ANY(:gl_ids)
                """),
                {"gl_ids": orphaned_ids}
            )
            entries_deleted = result.rowcount
            
            await session.commit()
            
            print(f"   ✅ Deleted {entries_deleted} orphaned GL entries")
            print(f"   ✅ Deleted {lines_deleted} orphaned GL lines")
        else:
            print("\n✅ No orphaned GL entries found")
        
        # STEP 3: Find supplier ledger entries without GL lines
        print("\n" + "-"*70)
        print("STEP 3: Find supplier entries without GL postings")
        print("-"*70)
        
        missing = await find_missing_gl_lines(session, client.id)
        
        print(f"\n🔍 Found {len(missing)} supplier entries without GL lines")
        
        if len(missing) == 0:
            print("\n✅ All supplier ledger entries have GL postings!")
            # Still check reconciliation
            after_recon = await check_reconciliation(session, client.id)
            
            if abs(after_recon['difference']) < 1:
                print("\n✅ Reconciliation already correct!")
                return
            else:
                print(f"\n⚠️  But reconciliation still off by {abs(after_recon['difference']):,.2f} NOK")
                print("   Further investigation needed.")
                return
        
        # STEP 4: Create missing GL lines
        print("\n" + "-"*70)
        print("STEP 4: Create missing GL lines for supplier entries")
        print("-"*70)
        
        lines_created = 0
        total_amount_fixed = Decimal('0')
        total_invoice_amount = Decimal('0')
        total_payment_amount = Decimal('0')
        
        for supplier_entry, gl_entry in missing:
            paid_amount = supplier_entry.amount - supplier_entry.remaining_amount
            
            print(f"\n   Processing: {supplier_entry.invoice_number}")
            print(f"      Status:  {supplier_entry.status}")
            print(f"      Voucher: {gl_entry.voucher_series}-{gl_entry.voucher_number}")
            print(f"      Amount:  {supplier_entry.amount:,.2f} NOK")
            if paid_amount > 0:
                print(f"      Paid:    {paid_amount:,.2f} NOK")
                print(f"      Remaining: {supplier_entry.remaining_amount:,.2f} NOK")
            
            lines = await create_gl_lines_for_supplier_entry(
                session, supplier_entry, gl_entry
            )
            
            print(f"      ✅ Created invoice posting: Debit 6000 / Credit 2400 = {supplier_entry.amount:,.2f} NOK")
            
            if paid_amount > 0:
                print(f"      ✅ Created payment posting: Debit 2400 / Credit 1920 = {paid_amount:,.2f} NOK")
            
            lines_created += len(lines)
            total_invoice_amount += supplier_entry.amount
            total_payment_amount += paid_amount
            total_amount_fixed += supplier_entry.remaining_amount
        
        # Commit changes
        await session.commit()
        
        print(f"\n✅ Created {lines_created} GL lines for {len(missing)} supplier entries")
        print(f"   Total invoice amount posted to 2400: {total_invoice_amount:,.2f} NOK")
        print(f"   Total payment amount (reduced 2400): {total_payment_amount:,.2f} NOK")
        print(f"   Net effect on 2400 balance:          {total_amount_fixed:,.2f} NOK")
        
        # STEP 5: Verify reconciliation AFTER fix
        print("\n" + "-"*70)
        print("STEP 5: Verify reconciliation AFTER fix")
        print("-"*70)
        
        after_recon = await check_reconciliation(session, client.id)
        
        print(f"\n📋 Reconciliation Status (AFTER):")
        print(f"   Supplier Ledger Sum:     {after_recon['supplier_ledger_sum']:>15,.2f} NOK")
        print(f"   Account 2400 Balance:    {after_recon['account_2400_balance']:>15,.2f} NOK")
        print(f"   Difference:              {after_recon['difference']:>15,.2f} NOK")
        
        # Success check
        print("\n" + "="*70)
        if abs(after_recon['difference']) < 1:
            print("✅ SUCCESS! Reconciliation complete!")
            print("="*70)
            print("\n🎉 Database consistency restored:")
            print(f"   • Fixed {len(missing)} supplier entries")
            print(f"   • Created {lines_created} GL lines")
            print(f"   • Posted invoices to account 2400: {total_invoice_amount:,.2f} NOK")
            print(f"   • Posted payments (reduced 2400):  {total_payment_amount:,.2f} NOK")
            print(f"   • Net remaining balance in 2400:   {total_amount_fixed:,.2f} NOK")
            print(f"   • Final reconciliation difference:  {abs(after_recon['difference']):.2f} NOK")
        else:
            print("⚠️  WARNING! Inconsistency still exists!")
            print("="*70)
            print(f"\n   Remaining difference: {abs(after_recon['difference']):,.2f} NOK")
            print("   Further investigation needed.")
        
        print("\n" + "="*70)


if __name__ == "__main__":
    asyncio.run(main())

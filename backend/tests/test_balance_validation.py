"""
Balance Validation Tests - Ensure accounting integrity

Tests:
1. Every GeneralLedger entry must balance (debit = credit)
2. Account classes match account numbers
3. Trial balance = 0 (total debits = total credits)
4. Sequential voucher numbers
"""
import pytest
from decimal import Decimal
from datetime import datetime, date
from uuid import uuid4
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.general_ledger import GeneralLedger, GeneralLedgerLine
from app.models.client import Client


@pytest.mark.asyncio
async def test_general_ledger_entry_must_balance(db_session: AsyncSession, test_client: Client):
    """
    Test: Every GeneralLedger entry must balance (SUM(debits) = SUM(credits))
    
    Norwegian accounting rule: Balansekravet
    """
    client = test_client
    
    # Create balanced GL entry
    gl_entry = GeneralLedger(
        id=uuid4(),
        client_id=client.id,
        entry_date=date.today(),
        accounting_date=date.today(),
        period="2026-02",
        fiscal_year=2026,
        voucher_number="000001",
        voucher_series="TEST",
        description="Test entry - balanced",
        source_type="manual",
        created_by_type="test",
        status="posted"
    )
    db_session.add(gl_entry)
    
    # Add lines that balance
    line1 = GeneralLedgerLine(
        id=uuid4(),
        general_ledger_id=gl_entry.id,
        line_number=1,
        account_number="6300",  # Debit expense
        debit_amount=Decimal("1000.00"),
        credit_amount=Decimal("0.00")
    )
    line2 = GeneralLedgerLine(
        id=uuid4(),
        general_ledger_id=gl_entry.id,
        line_number=2,
        account_number="2400",  # Credit payable
        debit_amount=Decimal("0.00"),
        credit_amount=Decimal("1000.00")
    )
    db_session.add(line1)
    db_session.add(line2)
    
    await db_session.commit()
    
    # Verify balance
    query = select(
        func.sum(GeneralLedgerLine.debit_amount).label('total_debit'),
        func.sum(GeneralLedgerLine.credit_amount).label('total_credit')
    ).where(GeneralLedgerLine.general_ledger_id == gl_entry.id)
    
    result = await db_session.execute(query)
    row = result.first()
    
    assert row.total_debit == row.total_credit, f"Entry not balanced: debit={row.total_debit}, credit={row.total_credit}"


@pytest.mark.asyncio
async def test_unbalanced_entry_should_fail_in_application(db_session: AsyncSession, test_client: Client):
    """
    Test: Application should reject unbalanced entries
    
    This test verifies that booking_service validates balance before posting.
    """
    from app.services.booking_service import book_vendor_invoice
    from app.models.vendor_invoice import VendorInvoice
    from app.models.vendor import Vendor
    
    client = test_client
    
    # Create test vendor
    vendor = Vendor(
        id=uuid4(),
        client_id=client.id,
        vendor_number="V001",
        name="Test Vendor",
        org_number="888777666",
        account_number="2400"  # Leverandørgjeld
    )
    db_session.add(vendor)
    
    # Create invoice
    invoice = VendorInvoice(
        id=uuid4(),
        client_id=client.id,
        vendor_id=vendor.id,
        invoice_number="INV-001",
        invoice_date=date.today(),
        due_date=date.today(),
        amount_excl_vat=Decimal("1000.00"),
        vat_amount=Decimal("250.00"),
        total_amount=Decimal("1250.00")
    )
    db_session.add(invoice)
    await db_session.commit()
    
    # Try to book with unbalanced suggestion
    unbalanced_suggestion = {
        'lines': [
            {'account': '6300', 'debit': 1000.00, 'credit': 0.00, 'description': 'Expense'},
            {'account': '2740', 'debit': 250.00, 'credit': 0.00, 'description': 'VAT'},
            # Missing credit line! Total debit=1250, credit=0
        ],
        'confidence': 100
    }
    
    result = await book_vendor_invoice(
        db=db_session,
        invoice_id=invoice.id,
        booking_suggestion=unbalanced_suggestion
    )
    
    assert result['success'] is False, "Unbalanced entry should be rejected"
    assert 'not balanced' in result['error'].lower(), f"Expected balance error, got: {result['error']}"


@pytest.mark.asyncio
async def test_account_classes_match_account_numbers(db_session: AsyncSession, test_client: Client):
    """
    Test: Account types match account numbers (Norwegian chart of accounts NS 4102)
    
    Rules:
    - 1xxx = Assets (Eiendeler)
    - 2xxx = Liabilities (Gjeld)
    - 3xxx = Equity (Egenkapital)
    - 4xxx-8xxx = Income/Expenses (Inntekt/Kostnad)
    """
    from app.models.chart_of_accounts import Account
    
    client = test_client
    
    # Create accounts with correct classification
    test_accounts = [
        ("1920", "Bank", "asset"),
        ("2400", "Leverandørgjeld", "liability"),
        ("2000", "Egenkapital", "equity"),
        ("3000", "Salgsinntekt", "revenue"),
        ("6300", "Kontorkostnader", "expense"),
    ]
    
    for account_number, name, account_type in test_accounts:
        account = Account(
            id=uuid4(),
            client_id=client.id,
            account_number=account_number,
            account_name=name,
            account_type=account_type,
            is_active=True
        )
        db_session.add(account)
    
    await db_session.commit()
    
    # Verify classification matches account number ranges
    query = select(Account).where(Account.client_id == client.id)
    result = await db_session.execute(query)
    accounts = result.scalars().all()
    
    for account in accounts:
        first_digit = int(account.account_number[0])
        
        if first_digit == 1:
            assert account.account_type == "asset"
        elif first_digit == 2:
            assert account.account_type in ["liability", "equity"]
        elif first_digit == 3:
            assert account.account_type in ["equity", "revenue"]
        elif first_digit in [4, 5, 6, 7, 8]:
            assert account.account_type in ["revenue", "expense"]


@pytest.mark.asyncio
async def test_trial_balance_must_be_zero(db_session: AsyncSession, test_client: Client):
    """
    Test: Trial balance must equal zero (total debits = total credits)
    
    Norwegian: Kontrollbalansen
    """
    client = test_client
    
    # Create multiple balanced entries
    for i in range(3):
        gl_entry = GeneralLedger(
            id=uuid4(),
            client_id=client.id,
            entry_date=date.today(),
            accounting_date=date.today(),
            period="2026-02",
            fiscal_year=2026,
            voucher_number=f"{i+1:06d}",
            voucher_series="TEST",
            description=f"Test entry {i+1}",
            source_type="manual",
            created_by_type="test",
            status="posted"
        )
        db_session.add(gl_entry)
        
        # Each entry: debit=credit
        amount = Decimal((i + 1) * 1000)
        line1 = GeneralLedgerLine(
            id=uuid4(),
            general_ledger_id=gl_entry.id,
            line_number=1,
            account_number="6300",
            debit_amount=amount,
            credit_amount=Decimal("0.00")
        )
        line2 = GeneralLedgerLine(
            id=uuid4(),
            general_ledger_id=gl_entry.id,
            line_number=2,
            account_number="2400",
            debit_amount=Decimal("0.00"),
            credit_amount=amount
        )
        db_session.add(line1)
        db_session.add(line2)
    
    await db_session.commit()
    
    # Calculate trial balance
    query = select(
        func.sum(GeneralLedgerLine.debit_amount).label('total_debit'),
        func.sum(GeneralLedgerLine.credit_amount).label('total_credit')
    ).join(
        GeneralLedger
    ).where(
        GeneralLedger.client_id == client.id,
        GeneralLedger.status == 'posted'
    )
    
    result = await db_session.execute(query)
    row = result.first()
    
    trial_balance = row.total_debit - row.total_credit
    
    assert trial_balance == 0, f"Trial balance not zero: {trial_balance} (debit={row.total_debit}, credit={row.total_credit})"


@pytest.mark.asyncio
async def test_voucher_numbers_are_sequential(db_session: AsyncSession, test_client: Client):
    """
    Test: Voucher numbers should be sequential per client/series
    
    Norwegian: Bilagsnummer må være løpende
    """
    client = test_client
    
    # Create entries with sequential voucher numbers
    for i in range(1, 6):  # 1, 2, 3, 4, 5
        gl_entry = GeneralLedger(
            id=uuid4(),
            client_id=client.id,
            entry_date=date.today(),
            accounting_date=date.today(),
            period="2026-02",
            fiscal_year=2026,
            voucher_number=f"{i:06d}",
            voucher_series="AP",
            description=f"Entry {i}",
            source_type="manual",
            created_by_type="test",
            status="posted"
        )
        db_session.add(gl_entry)
    
    await db_session.commit()
    
    # Verify sequence
    query = select(GeneralLedger).where(
        GeneralLedger.client_id == client.id,
        GeneralLedger.voucher_series == "AP"
    ).order_by(GeneralLedger.voucher_number)
    
    result = await db_session.execute(query)
    entries = result.scalars().all()
    
    # Check no gaps in sequence
    for i, entry in enumerate(entries, start=1):
        expected = f"{i:06d}"
        assert entry.voucher_number == expected, f"Gap in sequence: expected {expected}, got {entry.voucher_number}"


@pytest.mark.asyncio
async def test_locked_entries_cannot_be_modified(db_session: AsyncSession, test_client: Client):
    """
    Test: Locked entries (period closed) cannot be modified or reversed
    
    Norwegian: Låste bilag (etter periodestenging) kan ikke endres
    """
    from app.services.booking_service import reverse_general_ledger_entry
    
    client = test_client
    
    # Create locked entry
    gl_entry = GeneralLedger(
        id=uuid4(),
        client_id=client.id,
        entry_date=date.today(),
        accounting_date=date.today(),
        period="2026-01",
        fiscal_year=2026,
        voucher_number="000001",
        voucher_series="AP",
        description="Locked entry",
        source_type="manual",
        created_by_type="test",
        status="posted",
        locked=True  # Period closed
    )
    db_session.add(gl_entry)
    
    # Add lines
    line1 = GeneralLedgerLine(
        id=uuid4(),
        general_ledger_id=gl_entry.id,
        line_number=1,
        account_number="6300",
        debit_amount=Decimal("1000.00"),
        credit_amount=Decimal("0.00")
    )
    line2 = GeneralLedgerLine(
        id=uuid4(),
        general_ledger_id=gl_entry.id,
        line_number=2,
        account_number="2400",
        debit_amount=Decimal("0.00"),
        credit_amount=Decimal("1000.00")
    )
    db_session.add(line1)
    db_session.add(line2)
    
    await db_session.commit()
    
    # Try to reverse locked entry
    result = await reverse_general_ledger_entry(
        db=db_session,
        gl_entry_id=gl_entry.id,
        reason="Test reversal"
    )
    
    assert result['success'] is False, "Locked entry should not be reversible"
    assert 'locked' in result['error'].lower(), f"Expected lock error, got: {result['error']}"

"""
Test Voucher Creation Engine
KONTALI SPRINT 1 - Task 2

Tests automatic voucher (General Ledger) creation from vendor invoices.
Validates Norwegian accounting standards (debit/credit balancing).

SkatteFUNN-kritisk: Disse testene beviser automatisk bokføring!
"""
import pytest
from uuid import uuid4, UUID
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vendor_invoice import VendorInvoice
from app.models.vendor import Vendor
from app.models.client import Client
from app.models.chart_of_accounts import Account
from app.models.general_ledger import GeneralLedger, GeneralLedgerLine
from app.services.voucher_service import (
    VoucherGenerator,
    VoucherValidationError,
    get_voucher_by_id,
    list_vouchers
)
from app.schemas.voucher import VoucherLineCreate


# Note: Using fixtures from conftest.py (test_client) where possible
# Custom fixtures below are specific to voucher tests


@pytest.fixture
async def test_vendor_voucher(db_session: AsyncSession, test_client):
    """Create test vendor for voucher tests"""
    vendor = Vendor(
        id=uuid4(),
        client_id=test_client.id,
        name="Leverandør AS",
        org_number="987654321",
        is_active=True
    )
    db_session.add(vendor)
    await db_session.flush()
    return vendor


@pytest.fixture
async def test_chart_of_accounts_voucher(db_session: AsyncSession, test_client):
    """Create test chart of accounts (kontoplan)"""
    accounts = [
        Account(
            id=uuid4(),
            client_id=test_client.id,
            account_number="6420",
            account_name="Kontorrekvisita",
            account_type="expense",
            is_active=True
        ),
        Account(
            id=uuid4(),
            client_id=test_client.id,
            account_number="2740",
            account_name="Inngående MVA",
            account_type="liability",
            is_active=True
        ),
        Account(
            id=uuid4(),
            client_id=test_client.id,
            account_number="2400",
            account_name="Leverandørgjeld",
            account_type="liability",
            is_active=True
        ),
        Account(
            id=uuid4(),
            client_id=test_client.id,
            account_number="6300",
            account_name="Leie lokaler",
            account_type="expense",
            is_active=True
        ),
    ]
    
    for account in accounts:
        db_session.add(account)
    
    await db_session.flush()
    return accounts


@pytest.fixture
async def test_invoice_voucher(db_session: AsyncSession, test_client, test_vendor_voucher):
    """Create test vendor invoice for voucher tests"""
    invoice = VendorInvoice(
        id=uuid4(),
        client_id=test_client.id,
        vendor_id=test_vendor_voucher.id,
        invoice_number=f"INV-{uuid4().hex[:8]}",
        invoice_date=date(2026, 2, 9),
        due_date=date(2026, 3, 9),
        amount_excl_vat=Decimal("10000.00"),
        vat_amount=Decimal("2500.00"),
        total_amount=Decimal("12500.00"),
        currency="NOK",
        ai_processed=True,
        ai_confidence_score=95,
        ai_booking_suggestion={"account": "6420", "confidence": 95},
        review_status="pending"
    )
    db_session.add(invoice)
    await db_session.flush()
    return invoice


class TestVoucherCreation:
    """Test suite for voucher creation"""
    
    @pytest.mark.asyncio
    async def test_create_voucher_from_invoice_success(
        self, 
        db_session: AsyncSession,
        test_client,
        test_vendor_voucher,
        test_invoice_voucher,
        test_chart_of_accounts_voucher
    ):
        """
        Test successful voucher creation from vendor invoice
        
        Expected result:
        - Voucher created with 3 lines
        - Line 1 (Debit): 6420 Kontorrekvisita  10,000 kr
        - Line 2 (Debit): 2740 Inngående MVA    2,500 kr
        - Line 3 (Credit): 2400 Leverandørgjeld 12,500 kr
        - Total debit = Total credit = 12,500 kr ✓
        """
        # Arrange
        generator = VoucherGenerator(db_session)
        
        # Act
        voucher_dto = await generator.create_voucher_from_invoice(
            invoice_id=test_invoice.id,
            tenant_id=test_client.id,
            user_id="test_user_123",
            accounting_date=None,
            override_account=None
        )
        
        # Assert - Voucher properties
        assert voucher_dto.id is not None
        assert voucher_dto.client_id == str(test_client.id)
        assert voucher_dto.voucher_number.startswith("2026-")
        assert voucher_dto.voucher_series == "AP"
        assert voucher_dto.is_balanced is True
        assert voucher_dto.total_debit == voucher_dto.total_credit
        assert voucher_dto.total_debit == Decimal("12500.00")
        
        # Assert - Lines
        assert len(voucher_dto.lines) == 3
        
        # Line 1: Debit - Expense account
        expense_line = voucher_dto.lines[0]
        assert expense_line.line_number == 1
        assert expense_line.account_number == "6420"
        assert expense_line.account_name == "Kontorrekvisita"
        assert expense_line.debit_amount == Decimal("10000.00")
        assert expense_line.credit_amount == Decimal("0.00")
        
        # Line 2: Debit - Input VAT
        vat_line = voucher_dto.lines[1]
        assert vat_line.line_number == 2
        assert vat_line.account_number == "2740"
        assert vat_line.account_name == "Inngående MVA"
        assert vat_line.debit_amount == Decimal("2500.00")
        assert vat_line.credit_amount == Decimal("0.00")
        assert vat_line.vat_code in ["5", None]  # 25% VAT code
        assert vat_line.vat_amount == Decimal("2500.00")
        
        # Line 3: Credit - Accounts Payable
        payable_line = voucher_dto.lines[2]
        assert payable_line.line_number == 3
        assert payable_line.account_number == "2400"
        assert payable_line.account_name == "Leverandørgjeld"
        assert payable_line.debit_amount == Decimal("0.00")
        assert payable_line.credit_amount == Decimal("12500.00")
        
        # Assert - Invoice updated
        await db_session.refresh(test_invoice)
        assert test_invoice.general_ledger_id is not None
        assert test_invoice.booked_at is not None
        assert test_invoice.review_status == "approved"
    
    @pytest.mark.asyncio
    async def test_create_voucher_already_posted(
        self,
        db_session: AsyncSession,
        test_client,
        test_invoice_voucher,
        test_chart_of_accounts_voucher
    ):
        """Test that creating voucher for already posted invoice fails"""
        # Arrange - Mark invoice as already posted
        test_invoice.general_ledger_id = uuid4()
        test_invoice.booked_at = datetime.utcnow()
        await db_session.commit()
        
        generator = VoucherGenerator(db_session)
        
        # Act & Assert
        with pytest.raises(ValueError, match="already posted"):
            await generator.create_voucher_from_invoice(
                invoice_id=test_invoice.id,
                tenant_id=test_client.id,
                user_id="test_user_123"
            )
    
    @pytest.mark.asyncio
    async def test_create_voucher_invoice_not_found(
        self,
        db_session: AsyncSession,
        test_client
    ):
        """Test that creating voucher for non-existent invoice fails"""
        generator = VoucherGenerator(db_session)
        
        with pytest.raises(ValueError, match="not found"):
            await generator.create_voucher_from_invoice(
                invoice_id=uuid4(),  # Random non-existent ID
                tenant_id=test_client.id,
                user_id="test_user_123"
            )
    
    @pytest.mark.asyncio
    async def test_voucher_balance_validation(self, db_session: AsyncSession):
        """Test that unbalanced vouchers are rejected"""
        generator = VoucherGenerator(db_session)
        
        # Create unbalanced lines (debit != credit)
        unbalanced_lines = [
            VoucherLineCreate(
                line_number=1,
                account_number="6420",
                account_name="Kontorrekvisita",
                line_description="Test",
                debit_amount=Decimal("10000.00"),
                credit_amount=Decimal("0.00")
            ),
            VoucherLineCreate(
                line_number=2,
                account_number="2400",
                account_name="Leverandørgjeld",
                line_description="Test",
                debit_amount=Decimal("0.00"),
                credit_amount=Decimal("9999.00")  # Doesn't match debit!
            ),
        ]
        
        # Should raise VoucherValidationError
        with pytest.raises(VoucherValidationError, match="does not balance"):
            generator._validate_balance(unbalanced_lines)
    
    @pytest.mark.asyncio
    async def test_voucher_balance_with_rounding(self, db_session: AsyncSession):
        """Test that small rounding differences are tolerated (0.01 tolerance)"""
        generator = VoucherGenerator(db_session)
        
        # Create lines with tiny rounding difference
        lines = [
            VoucherLineCreate(
                line_number=1,
                account_number="6420",
                account_name="Kontorrekvisita",
                line_description="Test",
                debit_amount=Decimal("10000.00"),
                credit_amount=Decimal("0.00")
            ),
            VoucherLineCreate(
                line_number=2,
                account_number="2400",
                account_name="Leverandørgjeld",
                line_description="Test",
                debit_amount=Decimal("0.00"),
                credit_amount=Decimal("10000.01")  # 0.01 difference (OK)
            ),
        ]
        
        # Should NOT raise error (within tolerance)
        result = generator._validate_balance(lines)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_voucher_number_generation(
        self,
        db_session: AsyncSession,
        test_client,
        test_vendor_voucher,
        test_chart_of_accounts_voucher
    ):
        """Test that voucher numbers are generated sequentially"""
        generator = VoucherGenerator(db_session)
        
        # Create multiple invoices and vouchers
        voucher_numbers = []
        
        for i in range(3):
            invoice = VendorInvoice(
                id=uuid4(),
                client_id=test_client.id,
                vendor_id=test_vendor.id,
                invoice_number=f"INV-{i}",
                invoice_date=date.today(),
                due_date=date.today(),
                amount_excl_vat=Decimal("1000.00"),
                vat_amount=Decimal("250.00"),
                total_amount=Decimal("1250.00"),
                currency="NOK",
                ai_booking_suggestion={"account": "6420"},
                review_status="pending"
            )
            db_session.add(invoice)
            await db_session.commit()
            
            voucher_dto = await generator.create_voucher_from_invoice(
                invoice_id=invoice.id,
                tenant_id=test_client.id,
                user_id="test_user"
            )
            
            voucher_numbers.append(voucher_dto.voucher_number)
        
        # Assert sequential numbering (2026-0001, 2026-0002, 2026-0003)
        assert len(voucher_numbers) == 3
        assert all(num.startswith("2026-") for num in voucher_numbers)
        
        # Extract sequence numbers
        seq_nums = [int(num.split("-")[1]) for num in voucher_numbers]
        assert seq_nums[1] == seq_nums[0] + 1
        assert seq_nums[2] == seq_nums[1] + 1
    
    @pytest.mark.asyncio
    async def test_create_voucher_with_override_account(
        self,
        db_session: AsyncSession,
        test_client,
        test_vendor_voucher,
        test_invoice_voucher,
        test_chart_of_accounts_voucher
    ):
        """Test that override_account parameter works"""
        # Add another account
        override_account = Account(
            id=uuid4(),
            client_id=test_client.id,
            account_number="6300",
            account_name="Leie lokaler",
            account_type="expense",
            is_active=True
        )
        db_session.add(override_account)
        await db_session.commit()
        
        generator = VoucherGenerator(db_session)
        
        voucher_dto = await generator.create_voucher_from_invoice(
            invoice_id=test_invoice.id,
            tenant_id=test_client.id,
            user_id="test_user",
            override_account="6300"  # Override to "Leie lokaler"
        )
        
        # Assert that first line uses override account
        expense_line = voucher_dto.lines[0]
        assert expense_line.account_number == "6300"
        assert expense_line.account_name == "Leie lokaler"
    
    @pytest.mark.asyncio
    async def test_create_voucher_no_vat(
        self,
        db_session: AsyncSession,
        test_client,
        test_vendor_voucher,
        test_chart_of_accounts_voucher
    ):
        """Test voucher creation for invoice without VAT"""
        # Create invoice without VAT
        invoice_no_vat = VendorInvoice(
            id=uuid4(),
            client_id=test_client.id,
            vendor_id=test_vendor.id,
            invoice_number="INV-NO-VAT",
            invoice_date=date.today(),
            due_date=date.today(),
            amount_excl_vat=Decimal("5000.00"),
            vat_amount=Decimal("0.00"),
            total_amount=Decimal("5000.00"),
            currency="NOK",
            ai_booking_suggestion={"account": "6420"},
            review_status="pending"
        )
        db_session.add(invoice_no_vat)
        await db_session.commit()
        
        generator = VoucherGenerator(db_session)
        
        voucher_dto = await generator.create_voucher_from_invoice(
            invoice_id=invoice_no_vat.id,
            tenant_id=test_client.id,
            user_id="test_user"
        )
        
        # Should only have 2 lines (no VAT line)
        assert len(voucher_dto.lines) == 2
        assert voucher_dto.lines[0].account_number == "6420"  # Expense
        assert voucher_dto.lines[1].account_number == "2400"  # Payable
        assert voucher_dto.is_balanced is True
        assert voucher_dto.total_debit == Decimal("5000.00")
    
    @pytest.mark.asyncio
    async def test_get_voucher_by_id(
        self,
        db_session: AsyncSession,
        test_client,
        test_invoice_voucher,
        test_chart_of_accounts_voucher
    ):
        """Test retrieving voucher by ID"""
        # Create voucher
        generator = VoucherGenerator(db_session)
        voucher_dto = await generator.create_voucher_from_invoice(
            invoice_id=test_invoice.id,
            tenant_id=test_client.id,
            user_id="test_user"
        )
        
        # Retrieve voucher
        retrieved = await get_voucher_by_id(
            db=db_session,
            voucher_id=UUID(voucher_dto.id),
            client_id=test_client.id
        )
        
        assert retrieved is not None
        assert retrieved.id == voucher_dto.id
        assert retrieved.voucher_number == voucher_dto.voucher_number
        assert len(retrieved.lines) == len(voucher_dto.lines)
    
    @pytest.mark.asyncio
    async def test_list_vouchers(
        self,
        db_session: AsyncSession,
        test_client,
        test_vendor_voucher,
        test_chart_of_accounts_voucher
    ):
        """Test listing vouchers for a client"""
        # Create multiple vouchers
        generator = VoucherGenerator(db_session)
        
        for i in range(5):
            invoice = VendorInvoice(
                id=uuid4(),
                client_id=test_client.id,
                vendor_id=test_vendor.id,
                invoice_number=f"LIST-{i}",
                invoice_date=date(2026, 2, i + 1),
                due_date=date(2026, 3, i + 1),
                amount_excl_vat=Decimal("1000.00"),
                vat_amount=Decimal("250.00"),
                total_amount=Decimal("1250.00"),
                currency="NOK",
                ai_booking_suggestion={"account": "6420"},
                review_status="pending"
            )
            db_session.add(invoice)
            await db_session.commit()
            
            await generator.create_voucher_from_invoice(
                invoice_id=invoice.id,
                tenant_id=test_client.id,
                user_id="test_user"
            )
        
        # List vouchers
        vouchers = await list_vouchers(
            db=db_session,
            client_id=test_client.id,
            period="2026-02",
            limit=10,
            offset=0
        )
        
        assert len(vouchers) >= 5
        assert all(v.period == "2026-02" for v in vouchers)
        assert all(v.client_id == str(test_client.id) for v in vouchers)


class TestNorwegianAccountingLogic:
    """Test Norwegian accounting standards compliance"""
    
    @pytest.mark.asyncio
    async def test_vendor_invoice_accounting_entries(
        self,
        db_session: AsyncSession,
        test_client,
        test_vendor_voucher,
        test_invoice_voucher,
        test_chart_of_accounts_voucher
    ):
        """
        Test that vendor invoice creates correct accounting entries
        per Norwegian standard:
        
        DEBET:  Kostnadskonto (6xxx)    - Beløp eks MVA
        DEBET:  2740 Inngående MVA      - MVA-beløp
        KREDIT: 2400 Leverandørgjeld    - Totalbeløp
        """
        generator = VoucherGenerator(db_session)
        
        voucher_dto = await generator.create_voucher_from_invoice(
            invoice_id=test_invoice.id,
            tenant_id=test_client.id,
            user_id="test_user"
        )
        
        # Verify debit entries
        debit_lines = [line for line in voucher_dto.lines if line.debit_amount > 0]
        assert len(debit_lines) == 2
        
        # Expense account (6xxx)
        expense = next(line for line in debit_lines if line.account_number.startswith("6"))
        assert expense.debit_amount == test_invoice.amount_excl_vat
        
        # Input VAT (2740)
        vat = next(line for line in debit_lines if line.account_number == "2740")
        assert vat.debit_amount == test_invoice.vat_amount
        
        # Verify credit entry
        credit_lines = [line for line in voucher_dto.lines if line.credit_amount > 0]
        assert len(credit_lines) == 1
        
        # Accounts Payable (2400)
        payable = credit_lines[0]
        assert payable.account_number == "2400"
        assert payable.credit_amount == test_invoice.total_amount
        
        # Verify balance
        total_debit = sum(line.debit_amount for line in voucher_dto.lines)
        total_credit = sum(line.credit_amount for line in voucher_dto.lines)
        assert total_debit == total_credit == test_invoice.total_amount
    
    @pytest.mark.asyncio
    async def test_vat_calculation_25_percent(
        self,
        db_session: AsyncSession,
        test_client,
        test_vendor_voucher,
        test_chart_of_accounts_voucher
    ):
        """Test correct VAT handling for 25% standard rate"""
        # Create invoice with 25% VAT
        invoice = VendorInvoice(
            id=uuid4(),
            client_id=test_client.id,
            vendor_id=test_vendor.id,
            invoice_number="VAT-25",
            invoice_date=date.today(),
            due_date=date.today(),
            amount_excl_vat=Decimal("8000.00"),
            vat_amount=Decimal("2000.00"),  # 25% of 8000
            total_amount=Decimal("10000.00"),
            currency="NOK",
            ai_booking_suggestion={"account": "6420"},
            review_status="pending"
        )
        db_session.add(invoice)
        await db_session.commit()
        
        generator = VoucherGenerator(db_session)
        voucher_dto = await generator.create_voucher_from_invoice(
            invoice_id=invoice.id,
            tenant_id=test_client.id,
            user_id="test_user"
        )
        
        # Find VAT line
        vat_line = next(line for line in voucher_dto.lines if line.account_number == "2740")
        
        assert vat_line.vat_amount == Decimal("2000.00")
        assert vat_line.debit_amount == Decimal("2000.00")
        
        # VAT code should be "5" for 25%
        assert vat_line.vat_code in ["5", None]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

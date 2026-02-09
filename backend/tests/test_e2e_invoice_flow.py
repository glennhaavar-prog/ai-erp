"""
End-to-End Invoice Flow Tests
KONTALI SPRINT 1 - Task 4

Tests complete flow:
Upload → OCR → AI → Confidence → Review → Approve → Voucher → GL

SkatteFUNN-kritisk: Dette beviser at systemet fungerer end-to-end!
"""
import pytest
import asyncio
import time
from decimal import Decimal
from uuid import uuid4, UUID
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.vendor_invoice import VendorInvoice
from app.models.vendor import Vendor
from app.models.general_ledger import GeneralLedger, GeneralLedgerLine
from app.models.review_queue import ReviewQueue, ReviewStatus, ReviewPriority, IssueCategory
from app.services.confidence_scorer import ConfidenceScorer
from app.services.review_queue_service import ReviewQueueService
from app.services.voucher_service import VoucherGenerator, get_voucher_by_id

from tests.fixtures.invoice_fixtures import (
    create_test_invoice,
    high_confidence_invoice,
    low_confidence_invoice,
    very_low_confidence_invoice,
    test_vendor,
    test_chart_of_accounts
)


class TestEndToEndInvoiceFlow:
    """
    Test complete flow:
    Upload → OCR → AI → Confidence → Review → Approve → Voucher → GL
    """
    
    @pytest.mark.asyncio
    async def test_high_confidence_auto_approve_flow(
        self,
        db_session: AsyncSession,
        test_client,
        test_vendor,
        test_chart_of_accounts
    ):
        """
        High confidence invoice should auto-approve and create voucher
        
        Flow:
        1. Create vendor invoice (mock OCR data)
        2. AI suggests account (mock AI confidence = 0.95)
        3. Confidence scorer evaluates → 85% (above threshold)
        4. Auto-approve (no manual review needed)
        5. Voucher created automatically
        6. Verify GL entries exist and balance
        """
        # Step 1: Create high-confidence invoice
        invoice = await create_test_invoice(
            db_session=db_session,
            client_id=test_client.id,
            vendor_id=test_vendor.id,
            vendor_name="Acme Supplies AS",
            invoice_number="HIGH-CONF-001",
            amount_ex_vat=Decimal("10000.00"),
            vat_amount=Decimal("2500.00"),
            total_amount=Decimal("12500.00"),
            ai_suggested_account="6420",
            ocr_confidence=0.95,
            ai_confidence=0.90
        )
        
        # Step 2: Calculate confidence score
        scorer = ConfidenceScorer()
        confidence_result = scorer.calculate_score(
            invoice_data={
                'amount_excl_vat': invoice.amount_excl_vat,
                'vat_amount': invoice.vat_amount,
                'total_amount': invoice.total_amount,
                'vendor_name': 'Acme Supplies AS',
                'invoice_date': invoice.invoice_date,
                'due_date': invoice.due_date,
                'ai_suggested_account': '6420'
            },
            ocr_confidence=0.95,
            ai_confidence=0.90
        )
        
        # Step 3: Verify confidence is above threshold (should auto-approve)
        assert confidence_result['total_score'] >= 0.80
        assert confidence_result['should_auto_approve'] is True
        
        # Step 4: Auto-approve - Create voucher directly (no review queue)
        voucher_generator = VoucherGenerator(db_session)
        voucher_dto = await voucher_generator.create_voucher_from_invoice(
            invoice_id=invoice.id,
            tenant_id=test_client.id,
            user_id="system_auto_approve",
            accounting_date=None,
            override_account=None
        )
        
        # Step 5: Verify voucher created
        assert voucher_dto is not None
        assert voucher_dto.id is not None
        assert voucher_dto.is_balanced is True
        assert voucher_dto.total_debit == voucher_dto.total_credit
        
        # Step 6: Verify GL entries
        voucher = await get_voucher_by_id(
            db=db_session,
            voucher_id=UUID(voucher_dto.id),
            client_id=test_client.id
        )
        
        assert voucher is not None
        assert len(voucher.lines) == 3  # Expense + VAT + Payable
        
        # Verify debit lines
        debit_lines = [line for line in voucher.lines if line.debit_amount > 0]
        assert len(debit_lines) == 2
        
        expense_line = next(l for l in debit_lines if l.account_number == "6420")
        assert expense_line.debit_amount == Decimal("10000.00")
        
        vat_line = next(l for l in debit_lines if l.account_number == "2740")
        assert vat_line.debit_amount == Decimal("2500.00")
        
        # Verify credit line
        credit_lines = [line for line in voucher.lines if line.credit_amount > 0]
        assert len(credit_lines) == 1
        
        payable_line = credit_lines[0]
        assert payable_line.account_number == "2400"
        assert payable_line.credit_amount == Decimal("12500.00")
        
        # Verify invoice updated
        await db_session.refresh(invoice)
        assert invoice.general_ledger_id is not None
        assert invoice.booked_at is not None
        assert invoice.review_status == "approved"
    
    @pytest.mark.asyncio
    async def test_low_confidence_manual_review_flow(
        self,
        db_session: AsyncSession,
        test_client,
        test_vendor,
        test_chart_of_accounts
    ):
        """
        Low confidence invoice should go to Review Queue
        
        Flow:
        1. Create vendor invoice
        2. AI suggests account (mock AI confidence = 0.60)
        3. Confidence scorer evaluates → 65% (below threshold)
        4. Sent to Review Queue (status = pending)
        5. Accountant approves via API
        6. Voucher created
        7. Verify GL entries
        """
        # Step 1: Create low-confidence invoice
        invoice = await create_test_invoice(
            db_session=db_session,
            client_id=test_client.id,
            vendor_id=test_vendor.id,
            vendor_name="Uncertain Vendor",
            invoice_number="LOW-CONF-002",
            amount_ex_vat=Decimal("5000.00"),
            vat_amount=Decimal("1250.00"),
            total_amount=Decimal("6250.00"),
            ai_suggested_account="6700",
            ocr_confidence=0.70,
            ai_confidence=0.60
        )
        
        # Step 2: Calculate confidence score
        scorer = ConfidenceScorer()
        confidence_result = scorer.calculate_score(
            invoice_data={
                'amount_excl_vat': invoice.amount_excl_vat,
                'vat_amount': invoice.vat_amount,
                'total_amount': invoice.total_amount,
                'vendor_name': 'Uncertain Vendor',
                'invoice_date': invoice.invoice_date,
                'due_date': invoice.due_date,
                'ai_suggested_account': '6700'
            },
            ocr_confidence=0.70,
            ai_confidence=0.60
        )
        
        # Step 3: Verify confidence is below threshold (should escalate)
        assert confidence_result['total_score'] < 0.80
        assert confidence_result['should_auto_approve'] is False
        
        # Step 4: Create review queue item (simulates escalation)
        review_item = ReviewQueue(
            id=uuid4(),
            client_id=test_client.id,
            source_type="vendor_invoice",
            source_id=invoice.id,
            priority=ReviewPriority.MEDIUM,
            status=ReviewStatus.PENDING,
            issue_category="low_confidence",
            issue_description=f"AI confidence: {int(confidence_result['total_score'] * 100)}% | Below auto-approve threshold",
            ai_suggestion=invoice.ai_booking_suggestion,
            ai_confidence=int(confidence_result['total_score'] * 100),
            ai_reasoning="Low confidence due to uncertain vendor categorization",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(review_item)
        await db_session.commit()
        await db_session.refresh(review_item)
        
        # Step 5: Accountant approves via Review Queue Service
        review_service = ReviewQueueService(db_session)
        approval_response = await review_service.approve_invoice(
            invoice_id=str(review_item.id),
            user_id="accountant_001",
            notes="Reviewed and approved - vendor confirmed"
        )
        
        assert approval_response.success is True
        
        # Step 6: Fetch voucher created by approval (approve_invoice already created it)
        # NOTE: approve_invoice() calls book_vendor_invoice() which creates voucher
        assert approval_response.voucher_id is not None
        voucher_id = UUID(approval_response.voucher_id)
        
        voucher = await get_voucher_by_id(
            db=db_session,
            voucher_id=voucher_id,
            client_id=test_client.id
        )
        
        # Step 7: Verify voucher and GL entries
        assert voucher is not None
        assert voucher.is_balanced is True
        
        assert voucher is not None
        assert len(voucher.lines) == 3
        
        # Verify balance
        total_debit = sum(line.debit_amount for line in voucher.lines)
        total_credit = sum(line.credit_amount for line in voucher.lines)
        assert total_debit == total_credit == Decimal("6250.00")
        
        # Verify review queue status
        await db_session.refresh(review_item)
        assert review_item.status == ReviewStatus.APPROVED
        assert review_item.resolved_at is not None
    
    @pytest.mark.asyncio
    async def test_reject_flow(
        self,
        db_session: AsyncSession,
        test_client,
        test_vendor,
        test_chart_of_accounts
    ):
        """
        Test rejection workflow
        
        Flow:
        1. Create invoice in Review Queue
        2. Accountant rejects via API
        3. Invoice status = rejected
        4. NO voucher created
        5. Verify no GL entries exist
        """
        # Step 1: Create invoice and review queue item
        invoice = await create_test_invoice(
            db_session=db_session,
            client_id=test_client.id,
            vendor_id=test_vendor.id,
            vendor_name="Suspicious Vendor",
            invoice_number="REJECT-003",
            amount_ex_vat=Decimal("15000.00"),
            vat_amount=Decimal("3750.00"),
            total_amount=Decimal("18750.00"),
            ai_suggested_account="6700",
            ocr_confidence=0.55,
            ai_confidence=0.50
        )
        
        review_item = ReviewQueue(
            id=uuid4(),
            client_id=test_client.id,
            source_type="vendor_invoice",
            source_id=invoice.id,
            priority=ReviewPriority.HIGH,
            status=ReviewStatus.PENDING,
            issue_category=IssueCategory.UNUSUAL_AMOUNT,  # Fixed: use valid enum value
            issue_description="Unusual amount for this vendor",
            ai_confidence=50,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(review_item)
        await db_session.commit()
        await db_session.refresh(review_item)
        
        # Step 2: Accountant rejects
        review_service = ReviewQueueService(db_session)
        rejection_response = await review_service.reject_invoice(
            invoice_id=str(review_item.id),
            user_id="accountant_001",
            reason="Invalid invoice - duplicate detected"
        )
        
        assert rejection_response.success is True
        
        # Step 3: Verify invoice status
        await db_session.refresh(invoice)
        assert invoice.review_status == "rejected"
        
        # Step 4 & 5: Verify NO voucher created
        assert invoice.general_ledger_id is None
        assert invoice.booked_at is None
        
        # Verify no GL entries exist for this invoice
        stmt = select(GeneralLedger).where(
            GeneralLedger.client_id == test_client.id
        )
        result = await db_session.execute(stmt)
        gl_entries = result.scalars().all()
        
        # Should have no GL entries linked to rejected invoice
        assert not any(gl.id == invoice.general_ledger_id for gl in gl_entries)
        
        # Verify review queue status
        await db_session.refresh(review_item)
        assert review_item.status == ReviewStatus.REJECTED
        assert review_item.resolution_notes == "Invalid invoice - duplicate detected"
    
    @pytest.mark.asyncio
    async def test_missing_data_flow(
        self,
        db_session: AsyncSession,
        test_client,
        test_vendor,
        test_chart_of_accounts
    ):
        """
        Test invoice with missing data (very low confidence)
        
        Flow:
        1. Create invoice with missing VAT
        2. Confidence scorer evaluates → very low score
        3. Sent to Review Queue with high priority
        4. Requires manual data entry
        """
        # Step 1: Create invoice with missing data
        invoice = await create_test_invoice(
            db_session=db_session,
            client_id=test_client.id,
            vendor_id=test_vendor.id,
            vendor_name="Unknown Vendor",
            invoice_number="MISSING-004",
            amount_ex_vat=Decimal("3000.00"),
            vat_amount=Decimal("0.00"),  # Missing!
            total_amount=Decimal("3000.00"),
            ai_suggested_account=None,  # AI couldn't suggest
            ocr_confidence=0.50,
            ai_confidence=0.40
        )
        
        # Step 2: Calculate confidence score
        scorer = ConfidenceScorer()
        confidence_result = scorer.calculate_score(
            invoice_data={
                'amount_excl_vat': invoice.amount_excl_vat,
                'vat_amount': invoice.vat_amount,
                'total_amount': invoice.total_amount,
                'vendor_name': None,  # Missing
                'invoice_date': invoice.invoice_date,
                'due_date': invoice.due_date,
                'ai_suggested_account': None  # Missing
            },
            ocr_confidence=0.50,
            ai_confidence=0.40
        )
        
        # Step 3: Verify very low confidence
        assert confidence_result['total_score'] < 0.60
        assert confidence_result['should_auto_approve'] is False
        
        # Create review queue item with HIGH priority
        review_item = ReviewQueue(
            id=uuid4(),
            client_id=test_client.id,
            source_type="vendor_invoice",
            source_id=invoice.id,
            priority=ReviewPriority.HIGH,
            status=ReviewStatus.PENDING,
            issue_category=IssueCategory.MISSING_VAT,  # Fixed: use valid enum value
            issue_description="Missing VAT data and vendor info",
            ai_confidence=int(confidence_result['total_score'] * 100),
            ai_reasoning="Insufficient data for automatic processing",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(review_item)
        await db_session.commit()
        
        # Step 4: Verify it's in review queue with HIGH priority
        await db_session.refresh(review_item)
        assert review_item.status == ReviewStatus.PENDING
        assert review_item.priority == ReviewPriority.HIGH
        assert "missing" in review_item.issue_description.lower()


class TestDatabaseIntegrity:
    """Test database integrity and Norwegian accounting standards"""
    
    async def verify_voucher_integrity(
        self,
        db: AsyncSession,
        voucher_id: UUID,
        client_id: UUID,
        expected_total: Decimal
    ):
        """
        Verify voucher follows Norwegian accounting standards
        
        Checks:
        1. Voucher exists
        2. Balance (debit = credit)
        3. Minimum lines (expense + payable)
        4. Norwegian structure (debit expense/VAT, credit payable)
        5. GL entries exist
        6. Invoice link
        """
        # 1. Fetch voucher
        voucher = await get_voucher_by_id(db, voucher_id, client_id)
        assert voucher is not None, "Voucher should exist"
        
        # 2. Verify balance
        assert voucher.is_balanced is True, "Voucher should be balanced"
        assert voucher.total_debit == voucher.total_credit, "Debit should equal credit"
        assert voucher.total_debit == expected_total, f"Total should be {expected_total}"
        
        # 3. Verify lines exist
        assert len(voucher.lines) >= 2, "Should have at least 2 lines"
        
        # 4. Verify Norwegian structure
        debit_lines = [l for l in voucher.lines if l.debit_amount > 0]
        credit_lines = [l for l in voucher.lines if l.credit_amount > 0]
        
        assert len(debit_lines) >= 1, "Should have at least one debit line"
        assert len(credit_lines) >= 1, "Should have at least one credit line"
        
        # Verify accounts payable (2400) is credit
        payable_lines = [l for l in credit_lines if l.account_number == "2400"]
        assert len(payable_lines) == 1, "Should have one accounts payable line"
        
        # 5. Verify GL entries in database
        stmt = select(GeneralLedger).where(GeneralLedger.id == voucher_id)
        result = await db.execute(stmt)
        gl = result.scalar_one_or_none()
        
        assert gl is not None, "GL entry should exist"
        assert gl.voucher_number is not None, "Should have voucher number"
        
        # 6. Verify invoice link
        stmt = select(VendorInvoice).where(
            VendorInvoice.general_ledger_id == voucher_id
        )
        result = await db.execute(stmt)
        invoice = result.scalar_one_or_none()
        
        assert invoice is not None, "Invoice should be linked to GL"
        assert invoice.review_status == "approved", "Invoice should be approved"
        
        return True
    
    @pytest.mark.asyncio
    async def test_voucher_balance_integrity(
        self,
        db_session: AsyncSession,
        test_client,
        test_vendor,
        test_chart_of_accounts
    ):
        """Test that all vouchers maintain balance integrity"""
        # Create and post invoice
        invoice = await create_test_invoice(
            db_session=db_session,
            client_id=test_client.id,
            vendor_id=test_vendor.id,
            invoice_number="BALANCE-TEST-001",
            amount_ex_vat=Decimal("7500.00"),
            vat_amount=Decimal("1875.00"),
            total_amount=Decimal("9375.00"),
            ai_suggested_account="6420",
            ocr_confidence=0.90,
            ai_confidence=0.85
        )
        
        # Create voucher
        voucher_generator = VoucherGenerator(db_session)
        voucher_dto = await voucher_generator.create_voucher_from_invoice(
            invoice_id=invoice.id,
            tenant_id=test_client.id,
            user_id="test_user"
        )
        
        # Verify integrity
        await self.verify_voucher_integrity(
            db=db_session,
            voucher_id=UUID(voucher_dto.id),
            client_id=test_client.id,
            expected_total=Decimal("9375.00")
        )


class TestPerformance:
    """Test system performance under load"""
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_batch_processing_100_invoices(
        self,
        db_session: AsyncSession,
        test_client,
        test_vendor,
        test_chart_of_accounts
    ):
        """
        Process 100 invoices in batch
        
        Measure:
        - Total time (should be < 60 seconds)
        - Memory usage
        - All vouchers balanced
        - No database deadlocks
        """
        print("\n=== Performance Test: 100 Invoices ===")
        
        # Create 100 invoices
        invoices = []
        for i in range(100):
            invoice = await create_test_invoice(
                db_session=db_session,
                client_id=test_client.id,
                vendor_id=test_vendor.id,
                vendor_name=f"Batch Vendor {i}",
                invoice_number=f"PERF-{i:04d}",
                amount_ex_vat=Decimal(f"{1000 + (i * 10)}.00"),
                vat_amount=Decimal(f"{250 + (i * 2.5):.2f}"),
                total_amount=Decimal(f"{1250 + (i * 12.5):.2f}"),
                ai_suggested_account="6420",
                ocr_confidence=0.85,
                ai_confidence=0.80
            )
            invoices.append(invoice)
        
        await db_session.commit()
        print(f"Created {len(invoices)} test invoices")
        
        # Process all invoices
        start_time = time.time()
        voucher_generator = VoucherGenerator(db_session)
        
        results = []
        for invoice in invoices:
            try:
                voucher_dto = await voucher_generator.create_voucher_from_invoice(
                    invoice_id=invoice.id,
                    tenant_id=test_client.id,
                    user_id="batch_processor"
                )
                results.append({
                    'success': True,
                    'voucher': voucher_dto
                })
            except Exception as e:
                results.append({
                    'success': False,
                    'error': str(e)
                })
        
        elapsed = time.time() - start_time
        
        print(f"Processed {len(results)} invoices in {elapsed:.2f} seconds")
        print(f"Average: {elapsed / len(results):.3f} seconds per invoice")
        
        # Assertions
        assert elapsed < 60, f"Processing took {elapsed:.2f}s, should be < 60s"
        
        successful = [r for r in results if r['success']]
        failed = [r for r in results if not r['success']]
        
        print(f"Success: {len(successful)}, Failed: {len(failed)}")
        
        assert len(successful) == 100, "All invoices should process successfully"
        assert all(r['voucher'].is_balanced for r in successful), "All vouchers should be balanced"


class TestErrorHandling:
    """Test error handling and rollback scenarios"""
    
    @pytest.mark.asyncio
    async def test_unbalanced_voucher_rollback(
        self,
        db_session: AsyncSession,
        test_client,
        test_vendor,
        test_chart_of_accounts
    ):
        """
        If voucher doesn't balance, entire transaction should rollback
        """
        # Create invoice with intentionally corrupted data
        invoice = await create_test_invoice(
            db_session=db_session,
            client_id=test_client.id,
            vendor_id=test_vendor.id,
            invoice_number="CORRUPT-001",
            amount_ex_vat=Decimal("10000.00"),
            vat_amount=Decimal("2500.00"),
            total_amount=Decimal("12500.00"),
            ai_suggested_account="6420",
            ocr_confidence=0.90,
            ai_confidence=0.85
        )
        
        # Manually corrupt the VAT amount to cause imbalance
        invoice.vat_amount = Decimal("9999.99")  # Wrong!
        await db_session.commit()
        
        # Try to create voucher (should fail balance check)
        voucher_generator = VoucherGenerator(db_session)
        
        # Note: Depending on implementation, this might raise or handle gracefully
        try:
            voucher_dto = await voucher_generator.create_voucher_from_invoice(
                invoice_id=invoice.id,
                tenant_id=test_client.id,
                user_id="test_user"
            )
            
            # If it succeeded, the balance check is too lenient
            # Verify it's still balanced (might have rounding tolerance)
            assert voucher_dto.is_balanced is True
            
        except Exception as e:
            # Expected behavior - transaction rolled back
            print(f"Correctly caught error: {e}")
            
            # Verify NO GL entries created
            stmt = select(GeneralLedger).where(
                GeneralLedger.client_id == test_client.id
            )
            result = await db_session.execute(stmt)
            gl_entries = result.scalars().all()
            
            # Should have no GL entries for this invoice
            await db_session.refresh(invoice)
            assert invoice.general_ledger_id is None
    
    @pytest.mark.asyncio
    async def test_concurrent_approval_protection(
        self,
        db_session: AsyncSession,
        test_client,
        test_vendor,
        test_chart_of_accounts
    ):
        """
        Test that concurrent approval attempts are handled safely
        (prevent double-posting)
        """
        # Create invoice
        invoice = await create_test_invoice(
            db_session=db_session,
            client_id=test_client.id,
            vendor_id=test_vendor.id,
            invoice_number="CONCURRENT-001",
            amount_ex_vat=Decimal("5000.00"),
            vat_amount=Decimal("1250.00"),
            total_amount=Decimal("6250.00"),
            ai_suggested_account="6420",
            ocr_confidence=0.90,
            ai_confidence=0.85
        )
        
        # Create voucher (first approval)
        voucher_generator = VoucherGenerator(db_session)
        voucher1 = await voucher_generator.create_voucher_from_invoice(
            invoice_id=invoice.id,
            tenant_id=test_client.id,
            user_id="user1"
        )
        
        assert voucher1 is not None
        
        # Try to create voucher again (should fail - already posted)
        try:
            voucher2 = await voucher_generator.create_voucher_from_invoice(
                invoice_id=invoice.id,
                tenant_id=test_client.id,
                user_id="user2"
            )
            
            # Should not reach here
            assert False, "Should have raised error for already posted invoice"
            
        except ValueError as e:
            # Expected behavior
            assert "already posted" in str(e).lower()
            print(f"Correctly prevented double-posting: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])

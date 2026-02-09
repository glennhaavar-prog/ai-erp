#!/usr/bin/env python3
"""
Comprehensive test for Fase 3: Periodisering & Period Close

Tests all functionality:
1. Accruals API (create, list, details, auto-post)
2. Period Close API (validation checks, closing workflow)
3. Database integration
4. Auto-posting cron job simulation
"""

import asyncio
import sys
from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db_session
from app.models.client import Client
from app.models.accrual import Accrual
from app.models.accrual_posting import AccrualPosting
from app.services.accrual_service import AccrualService
from app.services.period_close_service import PeriodCloseService
from app.models.general_ledger import GeneralLedger


class Fase3Tester:
    """Comprehensive tester for Fase 3 features"""
    
    def __init__(self):
        self.test_client_id = None
        self.test_accrual_id = None
        self.passed = 0
        self.failed = 0
        self.service = AccrualService()
        self.period_service = PeriodCloseService()
    
    def log(self, message: str, level: str = "INFO"):
        symbols = {
            "INFO": "ℹ️",
            "SUCCESS": "✅",
            "ERROR": "❌",
            "WARNING": "⚠️"
        }
        print(f"{symbols.get(level, 'ℹ️')}  {message}")
    
    async def setup_test_client(self, db: AsyncSession):
        """Create or find test client"""
        self.log("Setting up test client...")
        
        from sqlalchemy import select
        result = await db.execute(select(Client).limit(1))
        client = result.scalar_one_or_none()
        
        if not client:
            self.log("No clients found - creating test client", "WARNING")
            client = Client(
                id=uuid4(),
                name="Test Client for Fase 3",
                org_number="999999999",
                active=True
            )
            db.add(client)
            await db.commit()
        
        self.test_client_id = client.id
        self.log(f"Using client: {client.name} ({client.id})", "SUCCESS")
    
    async def test_create_accrual(self, db: AsyncSession):
        """Test 1: Create accrual with posting schedule"""
        self.log("\n📝 Test 1: Create accrual")
        
        try:
            # Create 12-month insurance accrual
            from_date = date(2026, 1, 1)
            to_date = date(2026, 12, 31)
            
            result = await self.service.create_accrual(
                db=db,
                client_id=self.test_client_id,
                description="Test Forsikring 2026",
                from_date=from_date,
                to_date=to_date,
                total_amount=Decimal("12000.00"),
                balance_account="1580",
                result_account="6820",
                frequency="monthly",
                created_by="test_user"
            )
            
            self.test_accrual_id = result['accrual_id']
            
            assert result['success'], "Failed to create accrual"
            assert len(result['posting_schedule']) == 12, f"Expected 12 postings, got {len(result['posting_schedule'])}"
            
            self.log(f"Created accrual: {self.test_accrual_id}", "SUCCESS")
            self.log(f"  Generated {len(result['posting_schedule'])} monthly postings")
            self.passed += 1
        
        except Exception as e:
            self.log(f"Failed: {e}", "ERROR")
            self.failed += 1
            raise
    
    async def test_list_accruals(self, db: AsyncSession):
        """Test 2: List accruals for client"""
        self.log("\n📋 Test 2: List accruals")
        
        try:
            from sqlalchemy import select
            result = await db.execute(
                select(Accrual).where(Accrual.client_id == self.test_client_id)
            )
            accruals = result.scalars().all()
            
            assert len(accruals) > 0, "No accruals found"
            
            self.log(f"Found {len(accruals)} accruals", "SUCCESS")
            for accrual in accruals:
                self.log(f"  - {accrual.description} ({accrual.status})")
            
            self.passed += 1
        
        except Exception as e:
            self.log(f"Failed: {e}", "ERROR")
            self.failed += 1
    
    async def test_accrual_details(self, db: AsyncSession):
        """Test 3: Get accrual details with postings"""
        self.log("\n🔍 Test 3: Get accrual details")
        
        try:
            from sqlalchemy import select
            
            # Fetch accrual
            result = await db.execute(
                select(Accrual).where(Accrual.id == self.test_accrual_id)
            )
            accrual = result.scalar_one()
            
            # Fetch postings
            result = await db.execute(
                select(AccrualPosting)
                .where(AccrualPosting.accrual_id == self.test_accrual_id)
                .order_by(AccrualPosting.posting_date)
            )
            postings = result.scalars().all()
            
            assert len(postings) == 12, f"Expected 12 postings, got {len(postings)}"
            assert all(p.status == "pending" for p in postings), "All postings should be pending initially"
            
            self.log(f"Accrual details loaded", "SUCCESS")
            self.log(f"  Description: {accrual.description}")
            self.log(f"  Total: kr {accrual.total_amount:,.2f}")
            self.log(f"  Postings: {len(postings)} pending")
            
            self.passed += 1
        
        except Exception as e:
            self.log(f"Failed: {e}", "ERROR")
            self.failed += 1
    
    async def test_post_single_accrual(self, db: AsyncSession):
        """Test 4: Post single accrual manually"""
        self.log("\n💳 Test 4: Post single accrual")
        
        try:
            from sqlalchemy import select
            
            # Find first pending posting
            result = await db.execute(
                select(AccrualPosting)
                .where(
                    AccrualPosting.accrual_id == self.test_accrual_id,
                    AccrualPosting.status == "pending"
                )
                .order_by(AccrualPosting.posting_date)
                .limit(1)
            )
            posting = result.scalar_one()
            
            # Post it
            result = await self.service.post_accrual(
                db=db,
                posting_id=posting.id,
                posted_by="test_user"
            )
            
            assert result['success'], "Failed to post accrual"
            assert result['gl_entry_id'], "No GL entry created"
            
            # Verify GL entry was created
            gl_result = await db.execute(
                select(GeneralLedger).where(GeneralLedger.id == result['gl_entry_id'])
            )
            gl_entry = gl_result.scalar_one()
            
            assert gl_entry.source_type == "accrual", "GL entry should have source_type='accrual'"
            assert len(gl_entry.lines) == 2, "GL entry should have 2 lines (debit + credit)"
            
            # Check balance
            debit_sum = sum(line.debit for line in gl_entry.lines)
            credit_sum = sum(line.credit for line in gl_entry.lines)
            assert debit_sum == credit_sum, "GL entry must balance"
            
            self.log(f"Posted accrual: {result['voucher_number']}", "SUCCESS")
            self.log(f"  GL Entry: {gl_entry.id}")
            self.log(f"  Amount: kr {posting.amount:,.2f}")
            self.log(f"  Balanced: Debit={debit_sum} = Credit={credit_sum}")
            
            self.passed += 1
        
        except Exception as e:
            self.log(f"Failed: {e}", "ERROR")
            self.failed += 1
    
    async def test_auto_post_due_accruals(self, db: AsyncSession):
        """Test 5: Auto-post all due accruals (cron job simulation)"""
        self.log("\n🤖 Test 5: Auto-post due accruals")
        
        try:
            # Set some postings to have past dates
            from sqlalchemy import select, update
            
            # Update first 3 pending postings to be "due" (past dates)
            today = date.today()
            result = await db.execute(
                select(AccrualPosting)
                .where(
                    AccrualPosting.accrual_id == self.test_accrual_id,
                    AccrualPosting.status == "pending"
                )
                .order_by(AccrualPosting.posting_date)
                .limit(3)
            )
            postings = result.scalars().all()
            
            for i, posting in enumerate(postings):
                posting.posting_date = today - timedelta(days=(3 - i))
            
            await db.commit()
            
            # Run auto-post
            result = await self.service.auto_post_due_accruals(
                db=db,
                as_of_date=today
            )
            
            assert result['success'], "Auto-post failed"
            assert result['posted_count'] == 3, f"Expected 3 postings, got {result['posted_count']}"
            
            self.log(f"Auto-posted {result['posted_count']} due accruals", "SUCCESS")
            self.log(f"  Total amount: kr {result['total_amount']:,.2f}")
            if result['errors']:
                self.log(f"  Errors: {len(result['errors'])}", "WARNING")
            
            self.passed += 1
        
        except Exception as e:
            self.log(f"Failed: {e}", "ERROR")
            self.failed += 1
    
    async def test_period_close(self, db: AsyncSession):
        """Test 6: Period close workflow"""
        self.log("\n🔒 Test 6: Period close")
        
        try:
            # Close January 2026
            result = await self.period_service.run_period_close(
                client_id=self.test_client_id,
                period="2026-01",
                db=db
            )
            
            assert result['status'] in ['success', 'failed'], f"Unexpected status: {result['status']}"
            assert len(result['checks']) >= 2, "Should have at least 2 checks (balance + accruals)"
            
            self.log(f"Period close result: {result['status'].upper()}", "SUCCESS" if result['status'] == "success" else "WARNING")
            self.log(f"  Summary: {result['summary']}")
            self.log(f"  Checks performed: {len(result['checks'])}")
            
            for check in result['checks']:
                self.log(f"    - {check['name']}: {check['status']}")
            
            if result['warnings']:
                self.log(f"  Warnings: {len(result['warnings'])}", "WARNING")
            
            if result['errors']:
                self.log(f"  Errors: {len(result['errors'])}", "ERROR")
            
            self.passed += 1
        
        except Exception as e:
            self.log(f"Failed: {e}", "ERROR")
            self.failed += 1
    
    async def run_all_tests(self):
        """Run all tests"""
        self.log("=" * 60)
        self.log("🚀 FASE 3 COMPREHENSIVE TEST SUITE")
        self.log("=" * 60)
        
        async with get_db_session() as db:
            await self.setup_test_client(db)
            
            await self.test_create_accrual(db)
            await self.test_list_accruals(db)
            await self.test_accrual_details(db)
            await self.test_post_single_accrual(db)
            await self.test_auto_post_due_accruals(db)
            await self.test_period_close(db)
        
        self.log("\n" + "=" * 60)
        self.log(f"TEST RESULTS: {self.passed} passed, {self.failed} failed")
        self.log("=" * 60)
        
        if self.failed > 0:
            self.log("❌ Some tests failed", "ERROR")
            sys.exit(1)
        else:
            self.log("✅ All tests passed!", "SUCCESS")
            sys.exit(0)


async def main():
    tester = Fase3Tester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())

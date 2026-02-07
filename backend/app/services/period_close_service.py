"""
Period Close Service - Automated month/quarter closing

Orchestrates automated period close:
1. Validation checks
2. Auto-post accruals
3. Close period
4. Generate summary
"""

from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from uuid import UUID
from datetime import datetime, timedelta
from decimal import Decimal

from app.models.accounting_period import AccountingPeriod
from app.services.accrual_service import AccrualService


class PeriodCloseService:
    """Automated period close orchestrator"""
    
    async def run_period_close(
        self,
        client_id: UUID,
        period: str,  # YYYY-MM format
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Run automated period close.
        
        Args:
            client_id: Client UUID
            period: Period in YYYY-MM format
            db: Database session
        
        Returns:
            Dict with status, checks, warnings, summary
        """
        
        results = {
            "period": period,
            "status": "running",
            "checks": [],
            "warnings": [],
            "errors": [],
            "summary": ""
        }
        
        # Step 1: Check if already closed
        if await self._is_period_closed(client_id, period, db):
            results["errors"].append("Period is already closed")
            results["status"] = "failed"
            results["summary"] = f"Periode {period} er allerede lukket"
            return results
        
        # Step 2: Run validation checks
        print(f"Running balance check for {period}...")
        balance_check = await self._check_balance(client_id, period, db)
        results["checks"].append(balance_check)
        
        if balance_check["status"] == "failed":
            results["errors"].append(f"Balance check failed: {balance_check.get('diff', 0)}")
        
        # Step 3: Auto-post accruals
        print(f"Auto-posting accruals for {period}...")
        accrual_result = await self._post_accruals(client_id, period, db)
        results["checks"].append(accrual_result)
        
        if accrual_result["posted_count"] > 0:
            results["warnings"].append(f"{accrual_result['posted_count']} periodiseringer ble automatisk bokført")
        
        # Step 4: Check for unresolved issues
        if results["errors"]:
            results["status"] = "failed"
            results["summary"] = f"Periode {period} kunne ikke lukkes. {len(results['errors'])} feil funnet."
            return results
        
        # Step 5: Mark period as closed
        print(f"Closing period {period}...")
        await self._close_period(client_id, period, db)
        
        results["status"] = "success"
        results["summary"] = f"✅ Periode {period} lukket. {len(results['checks'])} kontroller utført, {len(results['warnings'])} advarsler."
        
        return results
    
    async def _is_period_closed(
        self,
        client_id: UUID,
        period: str,
        db: AsyncSession
    ) -> bool:
        """Check if period is already closed by checking if any GL entries are locked"""
        
        from app.models.general_ledger import GeneralLedger
        
        result = await db.execute(
            select(GeneralLedger).where(
                GeneralLedger.client_id == client_id,
                GeneralLedger.period == period,
                GeneralLedger.locked == True
            ).limit(1)
        )
        locked_entry = result.scalar_one_or_none()
        
        return locked_entry is not None
    
    async def _check_balance(
        self,
        client_id: UUID,
        period: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Verify all entries balance (Debit = Credit).
        This is the fundamental accounting equation.
        """
        
        query = """
        SELECT 
            SUM(gll.debit_amount) - SUM(gll.credit_amount) as diff,
            COUNT(DISTINCT gl.id) as entry_count
        FROM general_ledger_lines gll
        JOIN general_ledger gl ON gll.general_ledger_id = gl.id
        WHERE gl.client_id = :client_id 
          AND gl.period = :period
          AND gl.status = 'posted'
        """
        
        result = await db.execute(
            text(query),
            {"client_id": str(client_id), "period": period}
        )
        row = result.first()
        
        diff = row[0] if row and row[0] is not None else Decimal("0.00")
        entry_count = row[1] if row else 0
        
        # Allow for small rounding errors (< 1 kr)
        if abs(float(diff)) < 1.00:
            return {
                "name": "Balansekontroll",
                "status": "passed",
                "message": f"{entry_count} bilag kontrollert, alt balanserer",
                "diff": 0
            }
        else:
            return {
                "name": "Balansekontroll",
                "status": "failed",
                "message": f"Ubalanse funnet: {float(diff):.2f} kr",
                "diff": float(diff),
                "entry_count": entry_count
            }
    
    async def _post_accruals(
        self,
        client_id: UUID,
        period: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Auto-post all pending accruals for this period"""
        
        # Parse period to get end date
        year, month = period.split("-")
        period_date = datetime(int(year), int(month), 1)
        
        # Get last day of month
        if int(month) == 12:
            next_month = datetime(int(year) + 1, 1, 1)
        else:
            next_month = datetime(int(year), int(month) + 1, 1)
        
        last_day = next_month - timedelta(days=1)
        
        # Use AccrualService to auto-post
        accrual_service = AccrualService()
        result = await accrual_service.auto_post_due_accruals(db, last_day.date())
        
        return {
            "name": "Periodiseringer",
            "status": "passed",
            "message": f"{result['posted_count']} periodiseringer bokført",
            "posted_count": result["posted_count"],
            "amount": result["total_amount"]
        }
    
    async def _close_period(
        self,
        client_id: UUID,
        period: str,
        db: AsyncSession
    ) -> None:
        """Mark period as closed by locking all GL entries"""
        
        from app.models.general_ledger import GeneralLedger
        
        # Lock all GL entries for this period
        query = text("""
            UPDATE general_ledger
            SET locked = true
            WHERE client_id = :client_id AND period = :period
        """)
        
        await db.execute(query, {"client_id": str(client_id), "period": period})
        await db.commit()

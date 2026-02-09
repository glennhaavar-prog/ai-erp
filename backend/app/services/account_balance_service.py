"""
Account Balance Service - Calculate and manage account balances

Handles:
- Recalculate balances from GL entries
- Drill-down to transactions for specific account
- Balance validation and reconciliation
"""

from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, and_
from uuid import UUID
from datetime import date
from decimal import Decimal

from app.models.general_ledger import GeneralLedger, GeneralLedgerLine
from app.models.chart_of_accounts import Account


class AccountBalanceService:
    """Service for managing account balances"""
    
    async def get_account_transactions(
        self,
        db: AsyncSession,
        client_id: UUID,
        account_number: str,
        from_date: date = None,
        to_date: date = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Get all GL transactions for a specific account (drill-down).
        
        Args:
            client_id: Client UUID
            account_number: Account number to drill down
            from_date: Start date filter (optional)
            to_date: End date filter (optional)
            limit: Maximum number of transactions
        
        Returns:
            Dict with account info and transactions
        """
        
        # Get account info
        account_result = await db.execute(
            select(Account).where(
                and_(
                    Account.client_id == client_id,
                    Account.account_number == account_number
                )
            )
        )
        account = account_result.scalar_one_or_none()
        
        if not account:
            raise ValueError(f"Account {account_number} not found for client {client_id}")
        
        # Build query for transactions
        query = """
        SELECT 
            gl.id as entry_id,
            gl.accounting_date,
            gl.entry_date,
            gl.voucher_number,
            gl.voucher_series,
            gl.description as entry_description,
            gl.period,
            gll.id as line_id,
            gll.line_description,
            gll.debit_amount as debit,
            gll.credit_amount as credit,
            gll.debit_amount - gll.credit_amount as net_amount
        FROM general_ledger_lines gll
        JOIN general_ledger gl ON gll.general_ledger_id = gl.id
        WHERE gl.client_id = :client_id
          AND gll.account_number = :account_number
          AND gl.status = 'posted'
        """
        
        params = {
            "client_id": str(client_id),
            "account_number": account_number
        }
        
        # Add date filters
        if from_date:
            query += " AND gl.accounting_date >= :from_date"
            params["from_date"] = from_date
        
        if to_date:
            query += " AND gl.accounting_date <= :to_date"
            params["to_date"] = to_date
        
        query += " ORDER BY gl.accounting_date DESC, gl.voucher_number DESC"
        query += f" LIMIT {limit}"
        
        # Execute query
        result = await db.execute(text(query), params)
        rows = result.fetchall()
        
        # Calculate running balance
        transactions = []
        running_balance = Decimal("0.00")
        
        # Reverse for running balance calculation (oldest first)
        for row in reversed(rows):
            net_amount = row.net_amount or Decimal("0.00")
            running_balance += net_amount
            
            transactions.append({
                "entry_id": str(row.entry_id),
                "line_id": str(row.line_id),
                "accounting_date": row.accounting_date.isoformat(),
                "entry_date": row.entry_date.isoformat(),
                "voucher_number": row.voucher_number,
                "voucher_series": row.voucher_series,
                "entry_description": row.entry_description,
                "line_description": row.line_description,
                "period": row.period,
                "debit": float(row.debit) if row.debit else 0.0,
                "credit": float(row.credit) if row.credit else 0.0,
                "net_amount": float(net_amount),
                "running_balance": float(running_balance)
            })
        
        # Reverse back for newest-first display
        transactions.reverse()
        
        # Calculate summary
        total_debit = sum(t["debit"] for t in transactions)
        total_credit = sum(t["credit"] for t in transactions)
        net_change = total_debit - total_credit
        
        return {
            "account": {
                "account_number": account_number,
                "account_name": account.account_name,
                "account_type": account.account_type
            },
            "filters": {
                "from_date": from_date.isoformat() if from_date else None,
                "to_date": to_date.isoformat() if to_date else None,
                "limit": limit
            },
            "transactions": transactions,
            "transaction_count": len(transactions),
            "summary": {
                "total_debit": total_debit,
                "total_credit": total_credit,
                "net_change": net_change,
                "current_balance": float(running_balance)
            }
        }
    
    async def recalculate_balances(
        self,
        db: AsyncSession,
        client_id: UUID,
        period: str = None
    ) -> Dict[str, Any]:
        """
        Recalculate account balances from GL entries.
        
        Useful for:
        - Ensuring data consistency
        - Fixing any balance discrepancies
        - End-of-period validation
        
        Args:
            client_id: Client UUID
            period: Optional period to recalculate (YYYY-MM format)
        
        Returns:
            Dict with recalculation summary
        """
        
        # Build query to sum up all GL lines per account
        query = """
        SELECT 
            gll.account_number,
            SUM(gll.debit_amount) as total_debit,
            SUM(gll.credit_amount) as total_credit,
            SUM(gll.debit_amount - gll.credit_amount) as balance
        FROM general_ledger_lines gll
        JOIN general_ledger gl ON gll.general_ledger_id = gl.id
        WHERE gl.client_id = :client_id
          AND gl.status = 'posted'
        """
        
        params = {"client_id": str(client_id)}
        
        if period:
            query += " AND gl.period = :period"
            params["period"] = period
        
        query += " GROUP BY gll.account_number"
        
        result = await db.execute(text(query), params)
        balances = result.fetchall()
        
        recalculated = []
        for row in balances:
            recalculated.append({
                "account_number": row.account_number,
                "total_debit": float(row.total_debit) if row.total_debit else 0.0,
                "total_credit": float(row.total_credit) if row.total_credit else 0.0,
                "balance": float(row.balance) if row.balance else 0.0
            })
        
        return {
            "success": True,
            "client_id": str(client_id),
            "period": period,
            "accounts_recalculated": len(recalculated),
            "balances": recalculated
        }
    
    async def validate_balance(
        self,
        db: AsyncSession,
        client_id: UUID,
        period: str = None
    ) -> Dict[str, Any]:
        """
        Validate that all GL entries balance (Debit = Credit).
        
        This is the fundamental accounting equation.
        
        Returns validation result with any discrepancies.
        """
        
        query = """
        SELECT 
            SUM(gll.debit_amount) as total_debit,
            SUM(gll.credit_amount) as total_credit,
            COUNT(DISTINCT gl.id) as entry_count
        FROM general_ledger_lines gll
        JOIN general_ledger gl ON gll.general_ledger_id = gl.id
        WHERE gl.client_id = :client_id
          AND gl.status = 'posted'
        """
        
        params = {"client_id": str(client_id)}
        
        if period:
            query += " AND gl.period = :period"
            params["period"] = period
        
        result = await db.execute(text(query), params)
        row = result.first()
        
        total_debit = row.total_debit if row and row.total_debit else Decimal("0.00")
        total_credit = row.total_credit if row and row.total_credit else Decimal("0.00")
        entry_count = row.entry_count if row else 0
        
        diff = abs(float(total_debit - total_credit))
        balanced = diff < 0.01  # Allow 1 øre rounding error
        
        return {
            "balanced": balanced,
            "total_debit": float(total_debit),
            "total_credit": float(total_credit),
            "difference": diff,
            "entry_count": entry_count,
            "period": period,
            "status": "OK" if balanced else "UBALANSERT"
        }

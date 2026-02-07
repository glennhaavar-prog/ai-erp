"""
Report Service - Business logic for financial reports
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from datetime import date
from typing import Optional, List, Dict, Any
from uuid import UUID
from decimal import Decimal

from app.models.chart_of_accounts import Account
from app.models.account_balance import AccountBalance
from app.models.general_ledger import GeneralLedgerLine, GeneralLedger


async def calculate_saldobalanse(
    db: AsyncSession,
    client_id: UUID,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    account_class: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Calculate saldobalanse (trial balance) for a client.
    
    For each account:
    - Opening balance (inngående saldo) from account_balances table
    - Transactions sum (debit - credit) from general_ledger_lines
    - Current balance (nåværende saldo) = opening + transactions
    
    Args:
        db: Database session
        client_id: Client UUID
        from_date: Start date for transaction filtering (optional)
        to_date: End date for transaction filtering (optional)
        account_class: Filter by account class (first digit of account number, e.g., "1", "2")
    
    Returns:
        List of account dictionaries with balance information
    """
    
    # Step 1: Get all active accounts for the client
    accounts_query = select(Account).where(
        and_(
            Account.client_id == client_id,
            Account.is_active == True
        )
    ).order_by(Account.account_number)
    
    # Filter by account class if provided
    if account_class:
        accounts_query = accounts_query.where(
            Account.account_number.like(f"{account_class}%")
        )
    
    accounts_result = await db.execute(accounts_query)
    accounts = accounts_result.scalars().all()
    
    # Step 2: Get opening balances
    # Determine fiscal year from to_date or use current year
    fiscal_year = str(to_date.year if to_date else date.today().year)
    
    opening_balances_query = select(AccountBalance).where(
        and_(
            AccountBalance.client_id == client_id,
            AccountBalance.fiscal_year == fiscal_year
        )
    )
    
    opening_balances_result = await db.execute(opening_balances_query)
    opening_balances = {
        ob.account_number: ob.opening_balance 
        for ob in opening_balances_result.scalars().all()
    }
    
    # Step 3: Calculate transaction sums per account
    # Build query for transaction sums
    transactions_query = (
        select(
            GeneralLedgerLine.account_number,
            func.sum(GeneralLedgerLine.debit_amount).label("total_debit"),
            func.sum(GeneralLedgerLine.credit_amount).label("total_credit"),
        )
        .join(GeneralLedger, GeneralLedgerLine.general_ledger_id == GeneralLedger.id)
        .where(
            and_(
                GeneralLedger.client_id == client_id,
                GeneralLedger.status == "posted"  # Only posted entries
            )
        )
        .group_by(GeneralLedgerLine.account_number)
    )
    
    # Apply date filters if provided
    date_filters = []
    if from_date:
        date_filters.append(GeneralLedger.accounting_date >= from_date)
    if to_date:
        date_filters.append(GeneralLedger.accounting_date <= to_date)
    
    if date_filters:
        transactions_query = transactions_query.where(and_(*date_filters))
    
    # Filter by account class if provided
    if account_class:
        transactions_query = transactions_query.where(
            GeneralLedgerLine.account_number.like(f"{account_class}%")
        )
    
    transactions_result = await db.execute(transactions_query)
    transactions = {
        row.account_number: {
            "debit": row.total_debit or Decimal("0.00"),
            "credit": row.total_credit or Decimal("0.00"),
        }
        for row in transactions_result.all()
    }
    
    # Step 4: Compile results
    result = []
    
    for account in accounts:
        account_number = account.account_number
        
        # Get opening balance (default to 0 if not found)
        opening_balance = opening_balances.get(account_number, Decimal("0.00"))
        
        # Get transaction totals
        trans = transactions.get(account_number, {
            "debit": Decimal("0.00"),
            "credit": Decimal("0.00")
        })
        
        total_debit = trans["debit"]
        total_credit = trans["credit"]
        
        # Calculate net change and current balance
        # Net change = debit - credit (positive means increase for asset/expense accounts)
        net_change = total_debit - total_credit
        current_balance = opening_balance + net_change
        
        # Build account data
        account_data = {
            "account_number": account_number,
            "account_name": account.account_name,
            "account_type": account.account_type,
            "opening_balance": float(opening_balance),
            "total_debit": float(total_debit),
            "total_credit": float(total_credit),
            "net_change": float(net_change),
            "current_balance": float(current_balance),
        }
        
        result.append(account_data)
    
    return result


async def get_saldobalanse_summary(
    accounts: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Calculate summary statistics for saldobalanse data.
    
    Args:
        accounts: List of account dictionaries from calculate_saldobalanse
    
    Returns:
        Summary dictionary with totals by account type
    """
    
    summary = {
        "total_accounts": len(accounts),
        "total_opening_balance": 0.0,
        "total_debit": 0.0,
        "total_credit": 0.0,
        "total_current_balance": 0.0,
        "by_type": {},
        "balance_check": {
            "balanced": False,
            "difference": 0.0
        }
    }
    
    type_totals = {}
    
    for account in accounts:
        account_type = account["account_type"]
        
        # Initialize type if not exists
        if account_type not in type_totals:
            type_totals[account_type] = {
                "count": 0,
                "opening_balance": 0.0,
                "current_balance": 0.0,
                "total_debit": 0.0,
                "total_credit": 0.0,
            }
        
        # Accumulate totals
        type_totals[account_type]["count"] += 1
        type_totals[account_type]["opening_balance"] += account["opening_balance"]
        type_totals[account_type]["current_balance"] += account["current_balance"]
        type_totals[account_type]["total_debit"] += account["total_debit"]
        type_totals[account_type]["total_credit"] += account["total_credit"]
        
        # Grand totals
        summary["total_opening_balance"] += account["opening_balance"]
        summary["total_current_balance"] += account["current_balance"]
        summary["total_debit"] += account["total_debit"]
        summary["total_credit"] += account["total_credit"]
    
    summary["by_type"] = type_totals
    
    # Balance check: total debits should equal total credits
    diff = abs(summary["total_debit"] - summary["total_credit"])
    summary["balance_check"]["difference"] = round(diff, 2)
    summary["balance_check"]["balanced"] = diff < 0.01  # Allow for rounding errors
    
    return summary

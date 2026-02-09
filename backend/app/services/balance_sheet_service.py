"""
Balance Sheet Service - Balanserapport
Generates balance sheet / statement of financial position from general ledger
"""
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from decimal import Decimal
from typing import Dict, List

from app.models import GeneralLedger, GeneralLedgerLine


class BalanceSheetService:
    """
    Balanserapport (Balance Sheet / Statement of Financial Position)
    
    NS 4102 Standard account structure:
    - 1xxx: Assets (Eiendeler)
      - 10xx-14xx: Fixed assets (Anleggsmidler)
      - 15xx-19xx: Current assets (Omløpsmidler)
    - 2xxx: Liabilities & Equity (Gjeld og egenkapital)
      - 20xx: Equity (Egenkapital)
      - 21xx-24xx: Long-term liabilities (Langsiktig gjeld)
      - 25xx-29xx: Current liabilities (Kortsiktig gjeld)
    """
    
    @staticmethod
    async def generate_balance_sheet(
        db: AsyncSession,
        client_id: str,
        as_of_date: date
    ) -> Dict:
        """
        Generate balance sheet as of a specific date
        
        Args:
            client_id: Client UUID
            as_of_date: Balance sheet date (end of period)
        
        Returns:
            Dict with assets, liabilities, and equity breakdown
        """
        
        # Get all GL lines up to and including the as_of_date
        result = await db.execute(
            select(
                GeneralLedgerLine.account_number,
                func.sum(GeneralLedgerLine.debit_amount).label('total_debit'),
                func.sum(GeneralLedgerLine.credit_amount).label('total_credit')
            )
            .join(GeneralLedger, GeneralLedgerLine.general_ledger_id == GeneralLedger.id)
            .where(
                and_(
                    GeneralLedger.client_id == client_id,
                    GeneralLedger.accounting_date <= as_of_date
                )
            )
            .group_by(GeneralLedgerLine.account_number)
        )
        
        lines = result.all()
        
        # Categorize accounts
        fixed_assets = []
        current_assets = []
        equity_accounts = []
        long_term_liabilities = []
        current_liabilities = []
        
        for account_number, total_debit, total_credit in lines:
            account_int = int(account_number) if account_number.isdigit() else 0
            
            # Net balance (debit - credit for assets, credit - debit for liabilities/equity)
            if account_int < 2000:  # Assets
                net_balance = (total_debit or Decimal("0")) - (total_credit or Decimal("0"))
            else:  # Liabilities & Equity
                net_balance = (total_credit or Decimal("0")) - (total_debit or Decimal("0"))
            
            account_data = {
                "account_number": account_number,
                "balance": float(net_balance),
                "debit": float(total_debit or Decimal("0")),
                "credit": float(total_credit or Decimal("0"))
            }
            
            # Categorize by account range (NS 4102)
            if 1000 <= account_int < 1500:
                fixed_assets.append(account_data)
            elif 1500 <= account_int < 2000:
                current_assets.append(account_data)
            elif 2000 <= account_int < 2100:
                equity_accounts.append(account_data)
            elif 2100 <= account_int < 2500:
                long_term_liabilities.append(account_data)
            elif 2500 <= account_int < 3000:
                current_liabilities.append(account_data)
        
        # Calculate totals
        total_fixed_assets = sum(a["balance"] for a in fixed_assets)
        total_current_assets = sum(a["balance"] for a in current_assets)
        total_assets = total_fixed_assets + total_current_assets
        
        total_equity = sum(a["balance"] for a in equity_accounts)
        total_long_term_liabilities = sum(a["balance"] for a in long_term_liabilities)
        total_current_liabilities = sum(a["balance"] for a in current_liabilities)
        total_liabilities = total_long_term_liabilities + total_current_liabilities
        total_liabilities_and_equity = total_equity + total_liabilities
        
        # Balance check
        balance_difference = total_assets - total_liabilities_and_equity
        is_balanced = abs(balance_difference) < 0.01  # Allow for rounding errors
        
        return {
            "client_id": client_id,
            "as_of_date": as_of_date.isoformat(),
            "currency": "NOK",
            "assets": {
                "fixed_assets": {
                    "accounts": fixed_assets,
                    "total": total_fixed_assets
                },
                "current_assets": {
                    "accounts": current_assets,
                    "total": total_current_assets
                },
                "total": total_assets
            },
            "liabilities_and_equity": {
                "equity": {
                    "accounts": equity_accounts,
                    "total": total_equity
                },
                "long_term_liabilities": {
                    "accounts": long_term_liabilities,
                    "total": total_long_term_liabilities
                },
                "current_liabilities": {
                    "accounts": current_liabilities,
                    "total": total_current_liabilities
                },
                "total_liabilities": total_liabilities,
                "total": total_liabilities_and_equity
            },
            "balance_check": {
                "is_balanced": is_balanced,
                "difference": float(balance_difference)
            }
        }

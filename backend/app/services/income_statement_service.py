"""
Income Statement Service - Resultatregnskap
Generates profit & loss reports from general ledger
"""
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from decimal import Decimal
from typing import Dict, List, Optional

from app.models import GeneralLedger, GeneralLedgerLine


class IncomeStatementService:
    """
    Resultatregnskap (Income Statement / Profit & Loss)
    
    NS 4102 Standard account structure:
    - 3xxx: Revenue (Driftsinntekter)
    - 4xxx: Cost of goods sold (Varekostnad)
    - 5xxx-7xxx: Operating expenses (Driftskostnader)
    - 8xxx: Financial income/expenses (Finansinntekter/-kostnader)
    - 9xxx: Extraordinary items (Ekstraordinære poster)
    """
    
    @staticmethod
    async def generate_income_statement(
        db: AsyncSession,
        client_id: str,
        start_date: date,
        end_date: date,
        comparison_start_date: Optional[date] = None,
        comparison_end_date: Optional[date] = None
    ) -> Dict:
        """
        Generate income statement for a period
        
        Args:
            client_id: Client UUID
            start_date: Period start
            end_date: Period end
            comparison_start_date: Optional comparison period start
            comparison_end_date: Optional comparison period end
        
        Returns:
            Dict with revenue, expenses, and profit/loss breakdown
        """
        
        # Get current period data
        current_data = await IncomeStatementService._get_period_data(
            db, client_id, start_date, end_date
        )
        
        result = {
            "client_id": client_id,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "currency": "NOK",
            "revenue": current_data["revenue"],
            "cost_of_goods_sold": current_data["cogs"],
            "gross_profit": current_data["revenue"]["total"] - current_data["cogs"]["total"],
            "operating_expenses": current_data["opex"],
            "operating_profit": (
                current_data["revenue"]["total"] 
                - current_data["cogs"]["total"]
                - current_data["opex"]["total"]
            ),
            "financial_items": current_data["financial"],
            "extraordinary_items": current_data["extraordinary"],
            "profit_before_tax": (
                current_data["revenue"]["total"]
                - current_data["cogs"]["total"]
                - current_data["opex"]["total"]
                + current_data["financial"]["total"]
                + current_data["extraordinary"]["total"]
            )
        }
        
        # Add comparison if requested
        if comparison_start_date and comparison_end_date:
            comparison_data = await IncomeStatementService._get_period_data(
                db, client_id, comparison_start_date, comparison_end_date
            )
            result["comparison_period"] = {
                "start_date": comparison_start_date.isoformat(),
                "end_date": comparison_end_date.isoformat()
            }
            result["comparison"] = {
                "revenue": comparison_data["revenue"],
                "cost_of_goods_sold": comparison_data["cogs"],
                "gross_profit": comparison_data["revenue"]["total"] - comparison_data["cogs"]["total"],
                "operating_expenses": comparison_data["opex"],
                "operating_profit": (
                    comparison_data["revenue"]["total"]
                    - comparison_data["cogs"]["total"]
                    - comparison_data["opex"]["total"]
                ),
                "financial_items": comparison_data["financial"],
                "profit_before_tax": (
                    comparison_data["revenue"]["total"]
                    - comparison_data["cogs"]["total"]
                    - comparison_data["opex"]["total"]
                    + comparison_data["financial"]["total"]
                    + comparison_data["extraordinary"]["total"]
                )
            }
        
        return result
    
    @staticmethod
    async def _get_period_data(
        db: AsyncSession,
        client_id: str,
        start_date: date,
        end_date: date
    ) -> Dict:
        """Get aggregated data for a period"""
        
        # Get all GL lines for period
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
                    GeneralLedger.accounting_date >= start_date,
                    GeneralLedger.accounting_date <= end_date
                )
            )
            .group_by(GeneralLedgerLine.account_number)
        )
        
        lines = result.all()
        
        # Categorize accounts
        revenue_accounts = []
        cogs_accounts = []
        opex_accounts = []
        financial_accounts = []
        extraordinary_accounts = []
        
        for account_number, total_debit, total_credit in lines:
            account_int = int(account_number) if account_number.isdigit() else 0
            
            # Net amount (credit - debit for revenue/income, debit - credit for expenses)
            net_amount = (total_credit or Decimal("0")) - (total_debit or Decimal("0"))
            
            account_data = {
                "account_number": account_number,
                "amount": float(net_amount),
                "debit": float(total_debit or Decimal("0")),
                "credit": float(total_credit or Decimal("0"))
            }
            
            # Categorize by account range (NS 4102)
            if 3000 <= account_int < 4000:
                revenue_accounts.append(account_data)
            elif 4000 <= account_int < 5000:
                cogs_accounts.append(account_data)
            elif 5000 <= account_int < 8000:
                opex_accounts.append(account_data)
            elif 8000 <= account_int < 9000:
                financial_accounts.append(account_data)
            elif 9000 <= account_int < 10000:
                extraordinary_accounts.append(account_data)
        
        return {
            "revenue": {
                "accounts": revenue_accounts,
                "total": sum(a["amount"] for a in revenue_accounts)
            },
            "cogs": {
                "accounts": cogs_accounts,
                "total": -sum(a["amount"] for a in cogs_accounts)  # Negative because expenses
            },
            "opex": {
                "accounts": opex_accounts,
                "total": -sum(a["amount"] for a in opex_accounts)  # Negative because expenses
            },
            "financial": {
                "accounts": financial_accounts,
                "total": sum(a["amount"] for a in financial_accounts)
            },
            "extraordinary": {
                "accounts": extraordinary_accounts,
                "total": sum(a["amount"] for a in extraordinary_accounts)
            }
        }

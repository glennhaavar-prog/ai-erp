"""
Demo Reset Service

Handles resetting demo data while preserving clients and accounts.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update
from app.models.tenant import Tenant
from app.models.client import Client
from app.models.vendor_invoice import VendorInvoice
from app.models.customer_invoice import CustomerInvoice
from app.models.bank_transaction import BankTransaction
from app.models.general_ledger import GeneralLedger
from app.models.chart_of_accounts import Account
from app.models.account_balance import AccountBalance
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DemoResetService:
    """Service for resetting demo environment"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_demo_tenant(self) -> Tenant | None:
        """Get the demo tenant"""
        result = await self.db.execute(
            select(Tenant).where(Tenant.is_demo == True)
        )
        return result.scalar_one_or_none()
    
    async def get_demo_stats(self) -> dict:
        """Get current demo environment statistics"""
        
        demo_tenant = await self.get_demo_tenant()
        if not demo_tenant:
            return {
                "demo_environment_exists": False,
                "message": "No demo environment found"
            }
        
        # Count demo clients
        result = await self.db.execute(
            select(Client).where(
                Client.tenant_id == demo_tenant.id,
                Client.is_demo == True
            )
        )
        demo_clients = result.scalars().all()
        client_ids = [str(c.id) for c in demo_clients]
        
        # Count invoices
        result = await self.db.execute(
            select(VendorInvoice).where(VendorInvoice.client_id.in_(client_ids))
        )
        vendor_invoices_count = len(result.scalars().all())
        
        result = await self.db.execute(
            select(CustomerInvoice).where(CustomerInvoice.client_id.in_(client_ids))
        )
        customer_invoices_count = len(result.scalars().all())
        
        # Count bank transactions
        result = await self.db.execute(
            select(BankTransaction).where(BankTransaction.client_id.in_(client_ids))
        )
        bank_transactions_count = len(result.scalars().all())
        
        # Count general ledger entries
        result = await self.db.execute(
            select(GeneralLedger).where(GeneralLedger.client_id.in_(client_ids))
        )
        gl_entries_count = len(result.scalars().all())
        
        # Count accounts
        result = await self.db.execute(
            select(Account).where(Account.client_id.in_(client_ids))
        )
        accounts_count = len(result.scalars().all())
        
        return {
            "demo_environment_exists": True,
            "tenant": {
                "id": str(demo_tenant.id),
                "name": demo_tenant.name,
                "org_number": demo_tenant.org_number,
            },
            "stats": {
                "clients": len(demo_clients),
                "vendor_invoices": vendor_invoices_count,
                "customer_invoices": customer_invoices_count,
                "total_invoices": vendor_invoices_count + customer_invoices_count,
                "bank_transactions": bank_transactions_count,
                "general_ledger_entries": gl_entries_count,
                "chart_of_accounts": accounts_count,
            },
            "last_reset": demo_tenant.demo_reset_at.isoformat() if demo_tenant.demo_reset_at else None,
        }
    
    async def reset_demo_data(self) -> dict:
        """
        Reset demo data:
        - Delete all demo invoices
        - Delete all demo transactions
        - Delete all demo general ledger entries
        - Preserve clients and accounts
        - Reset account balances to zero
        """
        
        logger.info("Starting demo data reset...")
        
        demo_tenant = await self.get_demo_tenant()
        if not demo_tenant:
            raise ValueError("No demo tenant found")
        
        # Get all demo clients
        result = await self.db.execute(
            select(Client).where(
                Client.tenant_id == demo_tenant.id,
                Client.is_demo == True
            )
        )
        demo_clients = result.scalars().all()
        client_ids = [c.id for c in demo_clients]
        
        if not client_ids:
            raise ValueError("No demo clients found")
        
        deleted_counts = {}
        
        # 1. Delete vendor invoices
        result = await self.db.execute(
            delete(VendorInvoice).where(VendorInvoice.client_id.in_(client_ids))
        )
        deleted_counts["vendor_invoices"] = result.rowcount
        logger.info(f"Deleted {deleted_counts['vendor_invoices']} vendor invoices")
        
        # 2. Delete customer invoices
        result = await self.db.execute(
            delete(CustomerInvoice).where(CustomerInvoice.client_id.in_(client_ids))
        )
        deleted_counts["customer_invoices"] = result.rowcount
        logger.info(f"Deleted {deleted_counts['customer_invoices']} customer invoices")
        
        # 3. Delete bank transactions
        result = await self.db.execute(
            delete(BankTransaction).where(BankTransaction.client_id.in_(client_ids))
        )
        deleted_counts["bank_transactions"] = result.rowcount
        logger.info(f"Deleted {deleted_counts['bank_transactions']} bank transactions")
        
        # 4. Delete general ledger entries
        result = await self.db.execute(
            delete(GeneralLedger).where(GeneralLedger.client_id.in_(client_ids))
        )
        deleted_counts["general_ledger_entries"] = result.rowcount
        logger.info(f"Deleted {deleted_counts['general_ledger_entries']} GL entries")
        
        # 5. Reset account balances (if AccountBalance table exists)
        try:
            result = await self.db.execute(
                update(AccountBalance)
                .where(AccountBalance.client_id.in_(client_ids))
                .values(
                    balance=0.0,
                    debit_balance=0.0,
                    credit_balance=0.0,
                )
            )
            deleted_counts["account_balances_reset"] = result.rowcount
            logger.info(f"Reset {deleted_counts['account_balances_reset']} account balances")
        except Exception as e:
            logger.warning(f"Could not reset account balances: {e}")
            deleted_counts["account_balances_reset"] = 0
        
        # 6. Update demo_reset_at timestamp
        demo_tenant.demo_reset_at = datetime.utcnow()
        await self.db.flush()
        
        # Commit all changes
        await self.db.commit()
        
        logger.info("Demo data reset complete!")
        
        return {
            "success": True,
            "message": "Demo environment reset successfully",
            "deleted_counts": deleted_counts,
            "reset_at": demo_tenant.demo_reset_at.isoformat(),
            "clients_preserved": len(demo_clients),
        }

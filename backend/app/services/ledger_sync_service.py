"""
Ledger Sync Service - Auto-sync supplier/customer ledgers

When journal entries are posted to accounts 2400 (supplier debt) or 1500 (customer receivable),
automatically create/update corresponding ledger entries.

This is CRITICAL for accounting workflow - without it, sub-ledgers don't reflect GL.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from decimal import Decimal
from datetime import date
from typing import Optional, List
import uuid

from app.models.general_ledger import GeneralLedger, GeneralLedgerLine
from app.models.supplier_ledger import SupplierLedger, SupplierLedgerTransaction
from app.models.customer_ledger import CustomerLedger, CustomerLedgerTransaction
from app.models.vendor_invoice import VendorInvoice
from app.models.customer_invoice import CustomerInvoice
from app.models.supplier import Supplier
from app.models.customer import Customer


# Account constants
ACCOUNT_SUPPLIER_DEBT = "2400"  # Leverandørgjeld
ACCOUNT_CUSTOMER_RECEIVABLE = "1500"  # Kundefordring


class LedgerSyncService:
    """Service to sync sub-ledgers when GL entries are posted"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def sync_ledgers_for_journal_entry(
        self,
        journal_entry: GeneralLedger,
        lines: List[GeneralLedgerLine]
    ) -> dict:
        """
        Sync supplier/customer ledgers based on journal entry lines
        
        Args:
            journal_entry: The posted journal entry
            lines: All lines in the journal entry
            
        Returns:
            dict with sync results: {
                "supplier_ledger_created": bool,
                "customer_ledger_created": bool,
                "errors": List[str]
            }
        """
        results = {
            "supplier_ledger_created": False,
            "customer_ledger_created": False,
            "errors": []
        }
        
        # Check for supplier debt (account 2400)
        supplier_lines = [
            line for line in lines
            if line.account_number == ACCOUNT_SUPPLIER_DEBT and line.credit_amount > 0
        ]
        
        # Check for customer receivable (account 1500)
        customer_lines = [
            line for line in lines
            if line.account_number == ACCOUNT_CUSTOMER_RECEIVABLE and line.debit_amount > 0
        ]
        
        # Process supplier ledger
        if supplier_lines:
            try:
                await self._create_supplier_ledger_entry(
                    journal_entry,
                    supplier_lines
                )
                results["supplier_ledger_created"] = True
            except Exception as e:
                results["errors"].append(f"Supplier ledger sync failed: {str(e)}")
        
        # Process customer ledger
        if customer_lines:
            try:
                await self._create_customer_ledger_entry(
                    journal_entry,
                    customer_lines
                )
                results["customer_ledger_created"] = True
            except Exception as e:
                results["errors"].append(f"Customer ledger sync failed: {str(e)}")
        
        return results
    
    async def _create_supplier_ledger_entry(
        self,
        journal_entry: GeneralLedger,
        supplier_lines: List[GeneralLedgerLine]
    ):
        """Create supplier ledger entry for account 2400 credit"""
        
        # Calculate total supplier debt from this entry
        total_amount = sum(line.credit_amount for line in supplier_lines)
        
        # Try to find supplier from source
        supplier_id = await self._find_supplier_from_source(journal_entry)
        
        if not supplier_id:
            # If no supplier found, skip ledger creation
            # This can happen for manual entries or corrections
            return
        
        # Get invoice details if available
        invoice_number, invoice_date, due_date = await self._get_supplier_invoice_details(
            journal_entry
        )
        
        # Create supplier ledger entry
        ledger_entry = SupplierLedger(
            id=uuid.uuid4(),
            client_id=journal_entry.client_id,
            supplier_id=supplier_id,
            voucher_id=journal_entry.id,
            invoice_number=invoice_number,
            invoice_date=invoice_date or journal_entry.accounting_date,
            due_date=due_date or journal_entry.accounting_date,
            amount=total_amount,
            remaining_amount=total_amount,  # Initially unpaid
            currency="NOK",
            status="open"
        )
        
        self.db.add(ledger_entry)
        
        # Create initial transaction (the invoice itself)
        transaction = SupplierLedgerTransaction(
            id=uuid.uuid4(),
            ledger_id=ledger_entry.id,
            voucher_id=journal_entry.id,
            transaction_date=journal_entry.accounting_date,
            amount=total_amount,
            type="invoice"
        )
        
        self.db.add(transaction)
        await self.db.flush()
    
    async def _create_customer_ledger_entry(
        self,
        journal_entry: GeneralLedger,
        customer_lines: List[GeneralLedgerLine]
    ):
        """Create customer ledger entry for account 1500 debit"""
        
        # Calculate total customer receivable from this entry
        total_amount = sum(line.debit_amount for line in customer_lines)
        
        # Try to find customer from source
        customer_id, customer_name = await self._find_customer_from_source(journal_entry)
        
        if not customer_name:
            # If no customer info found, skip ledger creation
            return
        
        # Get invoice details if available
        invoice_number, invoice_date, due_date, kid_number = await self._get_customer_invoice_details(
            journal_entry
        )
        
        # Create customer ledger entry
        ledger_entry = CustomerLedger(
            id=uuid.uuid4(),
            client_id=journal_entry.client_id,
            customer_id=customer_id,  # Can be None
            customer_name=customer_name,
            voucher_id=journal_entry.id,
            invoice_number=invoice_number,
            invoice_date=invoice_date or journal_entry.accounting_date,
            due_date=due_date or journal_entry.accounting_date,
            kid_number=kid_number,
            amount=total_amount,
            remaining_amount=total_amount,  # Initially unpaid
            currency="NOK",
            status="open"
        )
        
        self.db.add(ledger_entry)
        
        # Create initial transaction (the invoice itself)
        transaction = CustomerLedgerTransaction(
            id=uuid.uuid4(),
            ledger_id=ledger_entry.id,
            voucher_id=journal_entry.id,
            transaction_date=journal_entry.accounting_date,
            amount=total_amount,
            type="invoice"
        )
        
        self.db.add(transaction)
        await self.db.flush()
    
    async def _find_supplier_from_source(
        self,
        journal_entry: GeneralLedger
    ) -> Optional[uuid.UUID]:
        """Find supplier ID from journal entry source"""
        
        # If source is vendor_invoice, get vendor_id
        if journal_entry.source_type in ["ehf_invoice", "vendor_invoice"]:
            if journal_entry.source_id:
                result = await self.db.execute(
                    select(VendorInvoice.vendor_id)
                    .where(VendorInvoice.id == journal_entry.source_id)
                )
                vendor_id = result.scalar_one_or_none()
                return vendor_id
        
        return None
    
    async def _find_customer_from_source(
        self,
        journal_entry: GeneralLedger
    ) -> tuple[Optional[uuid.UUID], Optional[str]]:
        """Find customer ID and name from journal entry source"""
        
        # If source is customer_invoice, get customer details
        if journal_entry.source_type == "customer_invoice":
            if journal_entry.source_id:
                result = await self.db.execute(
                    select(CustomerInvoice)
                    .where(CustomerInvoice.id == journal_entry.source_id)
                )
                customer_invoice = result.scalar_one_or_none()
                if customer_invoice:
                    # Use customer_name from invoice (CustomerInvoice doesn't have customer_id FK)
                    # Try to find matching customer by name or org_number
                    customer_id = None
                    if customer_invoice.customer_org_number:
                        result = await self.db.execute(
                            select(Customer.id)
                            .where(
                                Customer.client_id == journal_entry.client_id,
                                Customer.org_number == customer_invoice.customer_org_number
                            )
                        )
                        customer_id = result.scalar_one_or_none()
                    
                    return customer_id, customer_invoice.customer_name
        
        # Fallback: use description as customer name
        return None, journal_entry.description[:255]
    
    async def _get_supplier_invoice_details(
        self,
        journal_entry: GeneralLedger
    ) -> tuple[Optional[str], Optional[date], Optional[date]]:
        """Get invoice details from source"""
        
        if journal_entry.source_type in ["ehf_invoice", "vendor_invoice"]:
            if journal_entry.source_id:
                result = await self.db.execute(
                    select(VendorInvoice)
                    .where(VendorInvoice.id == journal_entry.source_id)
                )
                invoice = result.scalar_one_or_none()
                if invoice:
                    return (
                        invoice.invoice_number,
                        invoice.invoice_date,
                        invoice.due_date
                    )
        
        return None, None, None
    
    async def _get_customer_invoice_details(
        self,
        journal_entry: GeneralLedger
    ) -> tuple[Optional[str], Optional[date], Optional[date], Optional[str]]:
        """Get customer invoice details from source"""
        
        if journal_entry.source_type == "customer_invoice":
            if journal_entry.source_id:
                result = await self.db.execute(
                    select(CustomerInvoice)
                    .where(CustomerInvoice.id == journal_entry.source_id)
                )
                invoice = result.scalar_one_or_none()
                if invoice:
                    return (
                        invoice.invoice_number,
                        invoice.invoice_date,
                        invoice.due_date,
                        invoice.kid_number  # This exists in CustomerInvoice model
                    )
        
        return None, None, None, None


async def sync_ledgers_for_journal_entry(
    db: AsyncSession,
    journal_entry: GeneralLedger,
    lines: List[GeneralLedgerLine]
) -> dict:
    """
    Convenience function to sync ledgers for a journal entry
    
    Usage:
        results = await sync_ledgers_for_journal_entry(db, journal_entry, lines)
        if results["errors"]:
            logger.warning(f"Ledger sync errors: {results['errors']}")
    """
    service = LedgerSyncService(db)
    return await service.sync_ledgers_for_journal_entry(journal_entry, lines)

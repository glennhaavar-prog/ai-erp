"""
Trust Dashboard Service - Transparency & Control for Accountants
Provides visibility into what the AI is doing and verification that nothing is missed
"""
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List

from app.models import (
    VendorInvoice, CustomerInvoice, GeneralLedger, 
    GeneralLedgerLine, Client
)


class TrustDashboardService:
    """
    Trust Dashboard = Regnskapsfører's peace of mind
    
    Key principle: Regnskapsfører sees NOTHING of what happens inside
    the "Kontali motor", so they need PROOF that:
    - All invoices are handled
    - Nothing is "floating around"
    - All bank transactions are processed
    - Everything is under control
    
    From MEMORY.md Trust & Safety section
    """
    
    @staticmethod
    async def get_client_status(
        db: AsyncSession,
        client_id: str
    ) -> Dict:
        """
        Get comprehensive status for a client
        Shows green lights / yellow warnings / red alerts
        """
        
        # Vendor invoices status
        vendor_invoice_stats = await TrustDashboardService._get_vendor_invoice_stats(db, client_id)
        
        # Customer invoices status
        customer_invoice_stats = await TrustDashboardService._get_customer_invoice_stats(db, client_id)
        
        # General ledger status
        gl_stats = await TrustDashboardService._get_gl_stats(db, client_id)
        
        # Calculate overall health
        has_warnings = (
            vendor_invoice_stats["unprocessed_count"] > 0 or
            vendor_invoice_stats["needs_review_count"] > 0 or
            customer_invoice_stats["unpaid_overdue_count"] > 0
        )
        
        has_errors = (
            vendor_invoice_stats["stuck_count"] > 0 or
            not gl_stats["is_balanced"]
        )
        
        if has_errors:
            overall_status = "error"
        elif has_warnings:
            overall_status = "warning"
        else:
            overall_status = "ok"
        
        return {
            "client_id": client_id,
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": overall_status,
            "status_indicators": {
                "vendor_invoices": {
                    "status": "ok" if vendor_invoice_stats["stuck_count"] == 0 else "error",
                    "total_received": vendor_invoice_stats["total_count"],
                    "processed": vendor_invoice_stats["processed_count"],
                    "ai_approved": vendor_invoice_stats["ai_approved_count"],
                    "needs_review": vendor_invoice_stats["needs_review_count"],
                    "stuck": vendor_invoice_stats["stuck_count"],
                    "message": TrustDashboardService._format_vendor_message(vendor_invoice_stats)
                },
                "customer_invoices": {
                    "status": "ok" if customer_invoice_stats["unpaid_overdue_count"] == 0 else "warning",
                    "total_invoices": customer_invoice_stats["total_count"],
                    "paid": customer_invoice_stats["paid_count"],
                    "unpaid": customer_invoice_stats["unpaid_count"],
                    "overdue": customer_invoice_stats["unpaid_overdue_count"],
                    "message": TrustDashboardService._format_customer_message(customer_invoice_stats)
                },
                "general_ledger": {
                    "status": "ok" if gl_stats["is_balanced"] else "error",
                    "total_entries": gl_stats["entry_count"],
                    "total_lines": gl_stats["line_count"],
                    "is_balanced": gl_stats["is_balanced"],
                    "message": TrustDashboardService._format_gl_message(gl_stats)
                }
            }
        }
    
    @staticmethod
    async def _get_vendor_invoice_stats(db: AsyncSession, client_id: str) -> Dict:
        """Get vendor invoice statistics"""
        
        # Total count
        total_result = await db.execute(
            select(func.count(VendorInvoice.id))
            .where(VendorInvoice.client_id == client_id)
        )
        total_count = total_result.scalar() or 0
        
        # Processed (has GL entry)
        processed_result = await db.execute(
            select(func.count(VendorInvoice.id))
            .where(
                and_(
                    VendorInvoice.client_id == client_id,
                    VendorInvoice.general_ledger_id.isnot(None)
                )
            )
        )
        processed_count = processed_result.scalar() or 0
        
        # AI approved (high confidence, auto-approved)
        ai_approved_result = await db.execute(
            select(func.count(VendorInvoice.id))
            .where(
                and_(
                    VendorInvoice.client_id == client_id,
                    VendorInvoice.review_status == "auto_approved"
                )
            )
        )
        ai_approved_count = ai_approved_result.scalar() or 0
        
        # Needs review
        needs_review_result = await db.execute(
            select(func.count(VendorInvoice.id))
            .where(
                and_(
                    VendorInvoice.client_id == client_id,
                    VendorInvoice.review_status == "needs_review"
                )
            )
        )
        needs_review_count = needs_review_result.scalar() or 0
        
        # Stuck (pending for >7 days)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        stuck_result = await db.execute(
            select(func.count(VendorInvoice.id))
            .where(
                and_(
                    VendorInvoice.client_id == client_id,
                    VendorInvoice.review_status == "pending",
                    VendorInvoice.created_at < seven_days_ago
                )
            )
        )
        stuck_count = stuck_result.scalar() or 0
        
        unprocessed_count = total_count - processed_count
        
        return {
            "total_count": total_count,
            "processed_count": processed_count,
            "unprocessed_count": unprocessed_count,
            "ai_approved_count": ai_approved_count,
            "needs_review_count": needs_review_count,
            "stuck_count": stuck_count
        }
    
    @staticmethod
    async def _get_customer_invoice_stats(db: AsyncSession, client_id: str) -> Dict:
        """Get customer invoice statistics"""
        
        # Total count
        total_result = await db.execute(
            select(func.count(CustomerInvoice.id))
            .where(CustomerInvoice.client_id == client_id)
        )
        total_count = total_result.scalar() or 0
        
        # Paid
        paid_result = await db.execute(
            select(func.count(CustomerInvoice.id))
            .where(
                and_(
                    CustomerInvoice.client_id == client_id,
                    CustomerInvoice.payment_status == "paid"
                )
            )
        )
        paid_count = paid_result.scalar() or 0
        
        # Unpaid
        unpaid_result = await db.execute(
            select(func.count(CustomerInvoice.id))
            .where(
                and_(
                    CustomerInvoice.client_id == client_id,
                    or_(
                        CustomerInvoice.payment_status == "unpaid",
                        CustomerInvoice.payment_status == "overdue"
                    )
                )
            )
        )
        unpaid_count = unpaid_result.scalar() or 0
        
        # Overdue
        today = datetime.utcnow().date()
        overdue_result = await db.execute(
            select(func.count(CustomerInvoice.id))
            .where(
                and_(
                    CustomerInvoice.client_id == client_id,
                    CustomerInvoice.payment_status != "paid",
                    CustomerInvoice.due_date < today
                )
            )
        )
        unpaid_overdue_count = overdue_result.scalar() or 0
        
        return {
            "total_count": total_count,
            "paid_count": paid_count,
            "unpaid_count": unpaid_count,
            "unpaid_overdue_count": unpaid_overdue_count
        }
    
    @staticmethod
    async def _get_gl_stats(db: AsyncSession, client_id: str) -> Dict:
        """Get general ledger statistics"""
        
        # Entry count
        entry_result = await db.execute(
            select(func.count(GeneralLedger.id))
            .where(GeneralLedger.client_id == client_id)
        )
        entry_count = entry_result.scalar() or 0
        
        # Line count
        line_result = await db.execute(
            select(func.count(GeneralLedgerLine.id))
            .join(GeneralLedger, GeneralLedgerLine.general_ledger_id == GeneralLedger.id)
            .where(GeneralLedger.client_id == client_id)
        )
        line_count = line_result.scalar() or 0
        
        # Balance check (sum of debits should equal sum of credits)
        balance_result = await db.execute(
            select(
                func.sum(GeneralLedgerLine.debit_amount).label('total_debit'),
                func.sum(GeneralLedgerLine.credit_amount).label('total_credit')
            )
            .join(GeneralLedger, GeneralLedgerLine.general_ledger_id == GeneralLedger.id)
            .where(GeneralLedger.client_id == client_id)
        )
        balance_row = balance_result.first()
        
        total_debit = balance_row.total_debit or Decimal("0")
        total_credit = balance_row.total_credit or Decimal("0")
        difference = abs(total_debit - total_credit)
        is_balanced = difference < Decimal("0.01")  # Allow for rounding errors
        
        return {
            "entry_count": entry_count,
            "line_count": line_count,
            "total_debit": float(total_debit),
            "total_credit": float(total_credit),
            "difference": float(difference),
            "is_balanced": is_balanced
        }
    
    @staticmethod
    def _format_vendor_message(stats: Dict) -> str:
        """Generate human-readable message for vendor invoices"""
        if stats["stuck_count"] > 0:
            return f"⚠️ {stats['stuck_count']} fakturaer har ligget i >7 dager uten behandling"
        elif stats["needs_review_count"] > 0:
            return f"⏳ {stats['needs_review_count']} fakturaer venter på gjennomgang"
        elif stats["unprocessed_count"] > 0:
            return f"🔄 {stats['unprocessed_count']} fakturaer under behandling"
        else:
            return f"✅ Alle {stats['total_count']} fakturaer behandlet"
    
    @staticmethod
    def _format_customer_message(stats: Dict) -> str:
        """Generate human-readable message for customer invoices"""
        if stats["unpaid_overdue_count"] > 0:
            return f"⚠️ {stats['unpaid_overdue_count']} fakturaer forfalt"
        elif stats["unpaid_count"] > 0:
            return f"⏳ {stats['unpaid_count']} fakturaer ubetalt"
        else:
            return f"✅ Alle {stats['total_count']} fakturaer betalt"
    
    @staticmethod
    def _format_gl_message(stats: Dict) -> str:
        """Generate human-readable message for general ledger"""
        if not stats["is_balanced"]:
            return f"❌ Ubalanse: {stats['difference']:.2f} NOK forskjell (debet ≠ kredit)"
        else:
            return f"✅ {stats['entry_count']} bilag, {stats['line_count']} linjer - alt balansert"

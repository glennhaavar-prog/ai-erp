"""
Payment-related background tasks

Tasks:
1. detect_overdue_invoices - Run daily to mark overdue invoices
2. payment_reminder_check - Check for invoices approaching due date

These tasks should be scheduled to run automatically:
- detect_overdue_invoices: Daily at 00:00
- payment_reminder_check: Daily at 09:00

Integration options:
- APScheduler (recommended for standalone)
- Celery (for distributed systems)
- Cron job (simple)
"""

import asyncio
from datetime import datetime, date
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from uuid import UUID
import logging

from app.services.payment_status_service import PaymentStatusService
from app.models.client import Client
from app.database import get_db
from app.config import settings

logger = logging.getLogger(__name__)


async def detect_overdue_invoices_task():
    """
    Background task to detect and mark overdue invoices.
    
    Runs daily at 00:00 UTC.
    
    For each client:
    - Find invoices with due_date < today
    - Mark as 'overdue' if payment_status is 'unpaid' or 'partially_paid'
    
    Norwegian accounting compliance: Required for accurate reporting
    """
    
    logger.info("Starting overdue invoice detection task")
    
    try:
        # Create async database session
        engine = create_async_engine(settings.DATABASE_URL)
        async_session = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        
        async with async_session() as db:
            # Get all active clients
            from sqlalchemy import select
            result = await db.execute(select(Client))
            clients = result.scalars().all()
            
            total_overdue = 0
            
            for client in clients:
                try:
                    result = await PaymentStatusService.detect_overdue_invoices(
                        db=db,
                        client_id=client.id
                    )
                    
                    client_overdue = result["total_overdue"]
                    total_overdue += client_overdue
                    
                    if client_overdue > 0:
                        logger.info(
                            f"Client {client.company_name}: "
                            f"Marked {client_overdue} invoices as overdue"
                        )
                
                except Exception as e:
                    logger.error(
                        f"Error detecting overdue invoices for client {client.id}: {e}"
                    )
            
            logger.info(
                f"Overdue detection complete: {total_overdue} invoices marked overdue "
                f"across {len(clients)} clients"
            )
            
            return {
                "success": True,
                "total_overdue": total_overdue,
                "clients_processed": len(clients),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    except Exception as e:
        logger.error(f"Fatal error in overdue detection task: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


async def payment_reminder_check_task(days_before_due: int = 7):
    """
    Background task to check for invoices approaching due date.
    
    Can be used to trigger payment reminders.
    
    Args:
        days_before_due: Number of days before due date to trigger reminder
    
    Norwegian practice: Common to send reminder 7 days before due date
    """
    
    from datetime import timedelta
    from sqlalchemy import select, and_
    from app.models.vendor_invoice import VendorInvoice
    from app.models.customer_invoice import CustomerInvoice
    
    logger.info(f"Starting payment reminder check (threshold: {days_before_due} days)")
    
    try:
        engine = create_async_engine(settings.DATABASE_URL)
        async_session = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        
        async with async_session() as db:
            today = date.today()
            reminder_date = today + timedelta(days=days_before_due)
            
            # Find customer invoices due in X days (unpaid)
            result = await db.execute(
                select(CustomerInvoice).where(
                    and_(
                        CustomerInvoice.due_date == reminder_date,
                        CustomerInvoice.payment_status.in_(['unpaid', 'partially_paid'])
                    )
                )
            )
            invoices_needing_reminder = result.scalars().all()
            
            reminder_list = []
            
            for invoice in invoices_needing_reminder:
                reminder_list.append({
                    "invoice_id": str(invoice.id),
                    "invoice_number": invoice.invoice_number,
                    "customer_name": invoice.customer_name,
                    "customer_email": invoice.customer_email,
                    "total_amount": float(invoice.total_amount),
                    "paid_amount": float(invoice.paid_amount or 0),
                    "due_date": invoice.due_date.isoformat(),
                    "days_until_due": days_before_due
                })
            
            logger.info(
                f"Payment reminder check complete: "
                f"{len(reminder_list)} invoices need reminders"
            )
            
            return {
                "success": True,
                "reminders_needed": len(reminder_list),
                "invoices": reminder_list,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    except Exception as e:
        logger.error(f"Error in payment reminder check: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


# Scheduler integration example (using APScheduler)
def setup_payment_tasks():
    """
    Setup scheduled payment tasks using APScheduler.
    
    Call this from your application startup.
    
    Example:
        from app.tasks.payment_tasks import setup_payment_tasks
        setup_payment_tasks()
    """
    
    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        from apscheduler.triggers.cron import CronTrigger
        
        scheduler = AsyncIOScheduler()
        
        # Run overdue detection daily at 00:00 UTC
        scheduler.add_job(
            detect_overdue_invoices_task,
            CronTrigger(hour=0, minute=0),
            id='detect_overdue_invoices',
            name='Detect overdue invoices',
            replace_existing=True
        )
        
        # Run payment reminder check daily at 09:00 UTC
        scheduler.add_job(
            payment_reminder_check_task,
            CronTrigger(hour=9, minute=0),
            id='payment_reminder_check',
            name='Check for payment reminders',
            replace_existing=True
        )
        
        scheduler.start()
        logger.info("Payment tasks scheduled successfully")
        
        return scheduler
    
    except ImportError:
        logger.warning(
            "APScheduler not installed. Payment tasks will not be scheduled automatically. "
            "Install with: pip install apscheduler"
        )
        return None


# Manual execution functions (for testing or cron integration)
def run_overdue_detection():
    """Run overdue detection task manually (sync wrapper)"""
    asyncio.run(detect_overdue_invoices_task())


def run_payment_reminder_check():
    """Run payment reminder check manually (sync wrapper)"""
    asyncio.run(payment_reminder_check_task())


if __name__ == "__main__":
    # For testing: python -m app.tasks.payment_tasks
    print("Running overdue detection task...")
    result = asyncio.run(detect_overdue_invoices_task())
    print(f"Result: {result}")

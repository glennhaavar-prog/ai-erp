"""
Agent Utilities - Helper functions for testing and debugging
"""
import asyncio
import uuid
from typing import Optional, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_event import AgentEvent
from app.models.vendor_invoice import VendorInvoice
from app.models.client import Client


async def trigger_invoice_received(
    db: AsyncSession,
    tenant_id: str,
    invoice_id: str
):
    """
    Manually trigger invoice_received event
    
    Args:
        db: Database session
        tenant_id: Tenant UUID
        invoice_id: Invoice UUID
    """
    event = AgentEvent(
        tenant_id=tenant_id,
        event_type="invoice_received",
        payload={"invoice_id": invoice_id}
    )
    
    db.add(event)
    await db.commit()
    
    print(f"✅ Triggered invoice_received event for invoice {invoice_id}")
    print(f"   Orchestrator will pick it up within 30 seconds")


async def trigger_correction_received(
    db: AsyncSession,
    tenant_id: str,
    correction_id: str
):
    """
    Manually trigger correction_received event
    
    Args:
        db: Database session
        tenant_id: Tenant UUID
        correction_id: Correction UUID
    """
    event = AgentEvent(
        tenant_id=tenant_id,
        event_type="correction_received",
        payload={"correction_id": correction_id}
    )
    
    db.add(event)
    await db.commit()
    
    print(f"✅ Triggered correction_received event for correction {correction_id}")


async def create_test_invoice(
    db: AsyncSession,
    client_id: str,
    ehf_xml: Optional[str] = None
) -> VendorInvoice:
    """
    Create a test invoice for development/testing
    
    Args:
        db: Database session
        client_id: Client UUID
        ehf_xml: Optional EHF XML content
    
    Returns:
        Created invoice
    """
    # Default EHF XML if not provided
    if not ehf_xml:
        ehf_xml = """<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2">
    <cbc:ID>TEST-001</cbc:ID>
    <cbc:IssueDate>2024-02-04</cbc:IssueDate>
    <cbc:DueDate>2024-02-18</cbc:DueDate>
    <cbc:DocumentCurrencyCode>NOK</cbc:DocumentCurrencyCode>
    
    <cac:AccountingSupplierParty>
        <cac:Party>
            <cbc:EndpointID schemeID="0192">123456789</cbc:EndpointID>
            <cac:PartyName>
                <cbc:Name>Test Supplier AS</cbc:Name>
            </cac:PartyName>
        </cac:Party>
    </cac:AccountingSupplierParty>
    
    <cac:LegalMonetaryTotal>
        <cbc:TaxExclusiveAmount currencyID="NOK">1000.00</cbc:TaxExclusiveAmount>
        <cbc:PayableAmount currencyID="NOK">1250.00</cbc:PayableAmount>
    </cac:LegalMonetaryTotal>
    
    <cac:TaxTotal>
        <cbc:TaxAmount currencyID="NOK">250.00</cbc:TaxAmount>
    </cac:TaxTotal>
</Invoice>
"""
    
    invoice = VendorInvoice(
        client_id=client_id,
        invoice_number="TEST-001",
        invoice_date=date.today(),
        due_date=date.today(),
        amount_excl_vat=Decimal("1000.00"),
        vat_amount=Decimal("250.00"),
        total_amount=Decimal("1250.00"),
        currency="NOK",
        ehf_raw_xml=ehf_xml,
        review_status="received"
    )
    
    db.add(invoice)
    await db.commit()
    await db.refresh(invoice)
    
    print(f"✅ Created test invoice {invoice.id}")
    
    return invoice


async def trigger_test_flow(
    db: AsyncSession,
    client_id: str
):
    """
    Create test invoice and trigger complete flow
    
    Args:
        db: Database session
        client_id: Client UUID
    """
    # Create test invoice
    invoice = await create_test_invoice(db, client_id)
    
    # Trigger invoice_received event
    await trigger_invoice_received(
        db,
        tenant_id=client_id,
        invoice_id=str(invoice.id)
    )
    
    print(f"\n✅ Test flow triggered!")
    print(f"   1. Invoice created: {invoice.id}")
    print(f"   2. invoice_received event published")
    print(f"   3. Orchestrator will:")
    print(f"      → Create parse task")
    print(f"      → Invoice Parser will parse EHF")
    print(f"      → Publish invoice_parsed event")
    print(f"      → Create booking task")
    print(f"      → Bookkeeping Agent will create journal entry")
    print(f"      → Publish booking_completed event")
    print(f"      → Orchestrator will evaluate confidence")
    print(f"      → Auto-approve OR send to review queue")
    print(f"\nWatch the logs to see the flow!")


async def get_agent_stats(db: AsyncSession, tenant_id: str) -> Dict[str, Any]:
    """
    Get agent performance statistics
    
    Args:
        db: Database session
        tenant_id: Tenant UUID
    
    Returns:
        Statistics dictionary
    """
    from sqlalchemy import select, func
    from app.models.agent_task import AgentTask
    from app.models.agent_event import AgentEvent
    from app.models.review_queue import ReviewQueue
    from app.models.agent_learned_pattern import AgentLearnedPattern
    
    # Count events
    result = await db.execute(
        select(func.count(AgentEvent.id))
        .where(AgentEvent.tenant_id == tenant_id)
    )
    total_events = result.scalar()
    
    result = await db.execute(
        select(func.count(AgentEvent.id))
        .where(
            AgentEvent.tenant_id == tenant_id,
            AgentEvent.processed == False
        )
    )
    unprocessed_events = result.scalar()
    
    # Count tasks
    result = await db.execute(
        select(func.count(AgentTask.id))
        .where(AgentTask.tenant_id == tenant_id)
    )
    total_tasks = result.scalar()
    
    result = await db.execute(
        select(func.count(AgentTask.id))
        .where(
            AgentTask.tenant_id == tenant_id,
            AgentTask.status == 'pending'
        )
    )
    pending_tasks = result.scalar()
    
    result = await db.execute(
        select(func.count(AgentTask.id))
        .where(
            AgentTask.tenant_id == tenant_id,
            AgentTask.status == 'completed'
        )
    )
    completed_tasks = result.scalar()
    
    result = await db.execute(
        select(func.count(AgentTask.id))
        .where(
            AgentTask.tenant_id == tenant_id,
            AgentTask.status == 'failed'
        )
    )
    failed_tasks = result.scalar()
    
    # Count review queue
    result = await db.execute(
        select(func.count(ReviewQueue.id))
        .where(
            ReviewQueue.client_id == tenant_id,
            ReviewQueue.status == 'pending'
        )
    )
    pending_reviews = result.scalar()
    
    # Count patterns
    result = await db.execute(
        select(func.count(AgentLearnedPattern.id))
        .where(
            AgentLearnedPattern.is_active == True
        )
    )
    active_patterns = result.scalar()
    
    return {
        "events": {
            "total": total_events,
            "unprocessed": unprocessed_events
        },
        "tasks": {
            "total": total_tasks,
            "pending": pending_tasks,
            "completed": completed_tasks,
            "failed": failed_tasks
        },
        "review_queue": {
            "pending": pending_reviews
        },
        "patterns": {
            "active": active_patterns
        }
    }


def print_stats(stats: Dict[str, Any]):
    """Pretty print agent statistics"""
    print("\n📊 Agent System Statistics")
    print("=" * 50)
    
    print("\n🔔 Events:")
    print(f"   Total: {stats['events']['total']}")
    print(f"   Unprocessed: {stats['events']['unprocessed']}")
    
    print("\n📋 Tasks:")
    print(f"   Total: {stats['tasks']['total']}")
    print(f"   Pending: {stats['tasks']['pending']}")
    print(f"   Completed: {stats['tasks']['completed']}")
    print(f"   Failed: {stats['tasks']['failed']}")
    
    print("\n👀 Review Queue:")
    print(f"   Pending: {stats['review_queue']['pending']}")
    
    print("\n🧠 Learned Patterns:")
    print(f"   Active: {stats['patterns']['active']}")
    
    print("=" * 50)


# CLI interface for manual testing

if __name__ == "__main__":
    import sys
    from app.config import settings
    from app.database import get_db
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy.orm import sessionmaker
    
    async def main():
        if len(sys.argv) < 2:
            print("Usage:")
            print("  python -m app.agents.utils trigger <client_id>")
            print("  python -m app.agents.utils stats <client_id>")
            sys.exit(1)
        
        command = sys.argv[1]
        
        # Create database session
        engine = create_async_engine(settings.DATABASE_URL, echo=False)
        async_session = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        
        async with async_session() as db:
            if command == "trigger":
                if len(sys.argv) < 3:
                    print("Error: client_id required")
                    sys.exit(1)
                
                client_id = sys.argv[2]
                await trigger_test_flow(db, client_id)
            
            elif command == "stats":
                if len(sys.argv) < 3:
                    print("Error: client_id required")
                    sys.exit(1)
                
                client_id = sys.argv[2]
                stats = await get_agent_stats(db, client_id)
                print_stats(stats)
            
            else:
                print(f"Unknown command: {command}")
                sys.exit(1)
    
    asyncio.run(main())

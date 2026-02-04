"""
EHF Webhook Endpoint
Receives EHF invoices from PEPPOL access point (Unimicro)
"""

from fastapi import APIRouter, Request, Header, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
import os
from datetime import datetime

from app.database import get_db
from app.models.vendor_invoice import VendorInvoice
from app.models.vendor import Vendor
from app.services.ehf import receive_ehf_invoice

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/ehf")
async def ehf_webhook(
    request: Request,
    x_unimicro_signature: str = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Receive EHF invoice from Unimicro PEPPOL access point
    
    This endpoint is called by Unimicro when an EHF invoice arrives.
    """
    # Get raw XML
    xml_content = await request.body()
    xml_content = xml_content.decode('utf-8')
    
    # TODO: Implement tenant detection from request
    # For MVP, you can hardcode tenant_id or extract from headers
    # tenant_id = extract_tenant_from_request(request)
    # For now, using placeholder - replace with actual logic
    tenant_id = UUID("00000000-0000-0000-0000-000000000001")  # Replace with actual tenant detection
    
    # Get webhook secret from environment
    webhook_secret = os.getenv("UNIMICRO_WEBHOOK_SECRET")
    
    # Process EHF
    result = await receive_ehf_invoice(
        xml_content=xml_content,
        tenant_id=tenant_id,
        webhook_secret=webhook_secret,
        metadata={
            "message_id": request.headers.get("X-Message-ID"),
            "received_at": request.headers.get("Date")
        }
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=400,
            detail={"errors": result["errors"], "warnings": result["warnings"]}
        )
    
    # Get vendor invoice data
    vendor_data = result["vendor_invoice_data"]
    
    # Find or create vendor
    vendor = await find_or_create_vendor(
        db=db,
        tenant_id=tenant_id,
        org_number=vendor_data["vendor_org_number"],
        name=vendor_data["vendor_name"]
    )
    
    # Create VendorInvoice
    invoice = VendorInvoice(
        client_id=vendor.client_id,  # Inherit from vendor
        vendor_id=vendor.id,
        invoice_number=vendor_data["invoice_number"],
        invoice_date=vendor_data["invoice_date"],
        due_date=vendor_data["due_date"],
        currency=vendor_data.get("currency", "NOK"),
        amount_excl_vat=vendor_data["amount_excl_vat"],
        vat_amount=vendor_data["vat_amount"],
        total_amount=vendor_data["total_amount"],
        
        # EHF fields
        ehf_message_id=vendor_data.get("ehf_message_id"),
        ehf_raw_xml=vendor_data["ehf_raw_xml"],
        ehf_received_at=datetime.fromisoformat(vendor_data["ehf_received_at"]) if vendor_data.get("ehf_received_at") else None,
        
        # Status
        payment_status="unpaid",
        review_status="pending"
    )
    
    db.add(invoice)
    await db.commit()
    await db.refresh(invoice)
    
    # TODO: Trigger async processing by Invoice Agent
    # from app.tasks.invoice_processing import process_invoice
    # process_invoice.delay(str(invoice.id))
    
    return {
        "status": "received",
        "invoice_id": str(invoice.id),
        "ehf_invoice_id": result["ehf_invoice_id"],
        "warnings": result["warnings"]
    }


async def find_or_create_vendor(
    db: AsyncSession,
    tenant_id: UUID,
    org_number: str,
    name: str
) -> Vendor:
    """
    Find existing vendor by org number or create new
    """
    # Try to find existing
    query = select(Vendor).where(
        Vendor.org_number == org_number
    )
    result = await db.execute(query)
    vendor = result.scalar_one_or_none()
    
    if vendor:
        return vendor
    
    # Create new - using minimal required fields for now
    # TODO: Add proper client_id detection
    vendor = Vendor(
        client_id=UUID("00000000-0000-0000-0000-000000000001"),  # Placeholder
        org_number=org_number,
        name=name,
    )
    db.add(vendor)
    await db.commit()
    await db.refresh(vendor)
    
    return vendor

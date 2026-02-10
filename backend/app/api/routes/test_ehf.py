"""
EHF Test Endpoint
Allows testing EHF processing without webhook signature verification
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from datetime import datetime
from typing import Optional
import structlog

from app.database import get_db
from app.models.vendor_invoice import VendorInvoice
from app.models.vendor import Vendor
from app.models.client import Client
from app.services.ehf import receive_ehf_invoice
from app.services.invoice_processing import process_vendor_invoice

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/test/ehf", tags=["test"])


@router.post("/send")
async def test_ehf_send(
    xml_file: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Test EHF Processing Endpoint
    
    Accepts EHF XML as:
    - File upload (multipart/form-data)
    - Raw XML body (application/xml or text/xml)
    
    Processes through full pipeline:
    1. Parse XML → EHFInvoice model
    2. Validate against PEPPOL/EHF standard
    3. Find/create Vendor
    4. Create VendorInvoice
    5. Process through AI agent
    6. Add to Review Queue if needed
    
    Returns detailed status at each step.
    
    This endpoint bypasses webhook signature verification for easy testing.
    """
    try:
        # Get XML content
        if xml_file:
            xml_content = (await xml_file.read()).decode('utf-8')
            logger.info("ehf_test_file_upload", filename=xml_file.filename, size=len(xml_content))
        else:
            # Assume raw body (handled by FastAPI middleware)
            raise HTTPException(
                status_code=400,
                detail="No XML content provided. Send as file upload or raw XML body."
            )
        
        # Get or create test client
        test_client = await get_or_create_test_client(db)
        
        # Process EHF (no signature verification in test mode)
        logger.info("ehf_test_processing_start", client_id=str(test_client.id))
        
        result = await receive_ehf_invoice(
            xml_content=xml_content,
            tenant_id=test_client.id,
            webhook_secret=None,  # Skip signature verification
            metadata={
                "test_mode": True,
                "received_at": datetime.utcnow().isoformat()
            }
        )
        
        response = {
            "test_mode": True,
            "timestamp": datetime.utcnow().isoformat(),
            "steps": []
        }
        
        # Step 1: Parse
        if result["success"]:
            response["steps"].append({
                "step": "parse",
                "status": "✅ success",
                "message": "EHF XML parsed successfully",
                "ehf_invoice_id": result.get("ehf_invoice_id")
            })
        else:
            response["steps"].append({
                "step": "parse",
                "status": "❌ failed",
                "errors": result["errors"]
            })
            response["success"] = False
            return JSONResponse(content=response, status_code=400)
        
        # Step 2: Validate
        if result["warnings"]:
            response["steps"].append({
                "step": "validate",
                "status": "⚠️  warnings",
                "warnings": result["warnings"]
            })
        else:
            response["steps"].append({
                "step": "validate",
                "status": "✅ success",
                "message": "EHF validation passed"
            })
        
        # Step 3: Find/Create Vendor
        vendor_data = result["vendor_invoice_data"]
        
        vendor = await find_or_create_vendor(
            db=db,
            client_id=test_client.id,
            org_number=vendor_data["vendor_org_number"],
            name=vendor_data["vendor_name"]
        )
        
        response["steps"].append({
            "step": "vendor",
            "status": "✅ success",
            "vendor_id": str(vendor.id),
            "vendor_name": vendor.name,
            "vendor_org_number": vendor.org_number,
            "is_new": not vendor.created_at or (datetime.utcnow() - vendor.created_at).total_seconds() < 5
        })
        
        # Step 4: Create VendorInvoice
        invoice = VendorInvoice(
            client_id=vendor.client_id,
            vendor_id=vendor.id,
            invoice_number=vendor_data["invoice_number"],
            invoice_date=vendor_data["invoice_date"],
            due_date=vendor_data["due_date"],
            currency=vendor_data.get("currency", "NOK"),
            amount_excl_vat=vendor_data["amount_excl_vat"],
            vat_amount=vendor_data["vat_amount"],
            total_amount=vendor_data["total_amount"],
            
            # Line items
            line_items=vendor_data.get("line_items", []),
            
            # EHF fields
            ehf_message_id=vendor_data.get("ehf_message_id"),
            ehf_raw_xml=vendor_data["ehf_raw_xml"],
            ehf_received_at=datetime.utcnow(),
            
            # Status
            payment_status="unpaid",
            review_status="pending"
        )
        
        db.add(invoice)
        await db.commit()
        await db.refresh(invoice)
        
        response["steps"].append({
            "step": "invoice_created",
            "status": "✅ success",
            "invoice_id": str(invoice.id),
            "invoice_number": invoice.invoice_number,
            "amount": {
                "excl_vat": float(invoice.amount_excl_vat),
                "vat": float(invoice.vat_amount),
                "total": float(invoice.total_amount),
                "currency": invoice.currency
            },
            "dates": {
                "invoice_date": invoice.invoice_date.isoformat() if invoice.invoice_date else None,
                "due_date": invoice.due_date.isoformat() if invoice.due_date else None
            }
        })
        
        # Step 5: AI Processing
        try:
            processing_result = await process_vendor_invoice(db, invoice.id)
            
            response["steps"].append({
                "step": "ai_processing",
                "status": "✅ success" if processing_result.get("success") else "❌ failed",
                "confidence": processing_result.get("confidence"),
                "action": processing_result.get("action"),
                "suggested_booking": processing_result.get("suggested_booking")
            })
            
            # Step 6: Review Queue
            if processing_result.get("review_queue_id"):
                response["steps"].append({
                    "step": "review_queue",
                    "status": "✅ added",
                    "message": f"Added to review queue (confidence: {processing_result.get('confidence')}%)",
                    "review_queue_id": str(processing_result["review_queue_id"])
                })
            else:
                response["steps"].append({
                    "step": "review_queue",
                    "status": "⏭️  skipped",
                    "message": f"High confidence ({processing_result.get('confidence')}%) - ready for auto-booking"
                })
                
        except Exception as e:
            logger.error("ehf_test_processing_failed", error=str(e), exc_info=True)
            response["steps"].append({
                "step": "ai_processing",
                "status": "❌ failed",
                "error": str(e)
            })
        
        response["success"] = True
        response["summary"] = {
            "invoice_id": str(invoice.id),
            "ehf_invoice_id": result["ehf_invoice_id"],
            "vendor_name": vendor.name,
            "total_amount": float(invoice.total_amount),
            "currency": invoice.currency,
            "processing_complete": True
        }
        
        logger.info(
            "ehf_test_completed",
            invoice_id=str(invoice.id),
            vendor=vendor.name,
            amount=float(invoice.total_amount)
        )
        
        return JSONResponse(content=response, status_code=200)
        
    except Exception as e:
        logger.error("ehf_test_failed", error=str(e), exc_info=True)
        return JSONResponse(
            content={
                "success": False,
                "error": str(e),
                "test_mode": True
            },
            status_code=500
        )


@router.post("/send-raw")
async def test_ehf_send_raw(
    xml_content: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Alternative endpoint that accepts XML as raw string in JSON body
    
    Useful for testing from JavaScript/curl with simple JSON payload:
    
    ```bash
    curl -X POST http://localhost:8000/api/test/ehf/send-raw \
      -H "Content-Type: application/json" \
      -d '{"xml_content": "<Invoice>...</Invoice>"}'
    ```
    """
    # Reuse main endpoint logic by creating a mock file
    class MockFile:
        def __init__(self, content: str):
            self.content = content
            self.filename = "test.xml"
        
        async def read(self):
            return self.content.encode('utf-8')
    
    return await test_ehf_send(xml_file=MockFile(xml_content), db=db)


async def get_or_create_test_client(db: AsyncSession) -> Client:
    """
    Get or create test client for EHF testing
    """
    # Try to find existing test client
    query = select(Client).where(Client.name == "EHF Test Client")
    result = await db.execute(query)
    client = result.scalar_one_or_none()
    
    if client:
        return client
    
    # Create test client
    client = Client(
        name="EHF Test Client",
        org_number="999999999",  # Test org number
        is_active=True
    )
    db.add(client)
    await db.commit()
    await db.refresh(client)
    
    logger.info("ehf_test_client_created", client_id=str(client.id))
    return client


async def find_or_create_vendor(
    db: AsyncSession,
    client_id: UUID,
    org_number: str,
    name: str
) -> Vendor:
    """
    Find existing vendor by org number or create new
    """
    # Try to find existing
    query = select(Vendor).where(
        Vendor.org_number == org_number,
        Vendor.client_id == client_id
    )
    result = await db.execute(query)
    vendor = result.scalar_one_or_none()
    
    if vendor:
        return vendor
    
    # Create new
    vendor = Vendor(
        client_id=client_id,
        org_number=org_number,
        name=name,
    )
    db.add(vendor)
    await db.commit()
    await db.refresh(vendor)
    
    logger.info("ehf_test_vendor_created", vendor_id=str(vendor.id), name=name)
    return vendor

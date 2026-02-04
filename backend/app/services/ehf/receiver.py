"""
EHF Receiver
Receives EHF invoices from PEPPOL network via webhook
"""

from datetime import datetime
from typing import Optional
import structlog
import hashlib
import hmac

from .parser import parse_ehf_xml, ehf_to_vendor_invoice_dict
from .validator import validate_ehf_xml
from .models import EHFInvoice, VendorInvoiceFromEHF

logger = structlog.get_logger(__name__)


class EHFReceiver:
    """
    Receives and processes EHF invoices from PEPPOL access point
    """
    
    def __init__(self, webhook_secret: Optional[str] = None):
        """
        Initialize receiver
        
        Args:
            webhook_secret: Secret key for webhook signature verification
        """
        self.webhook_secret = webhook_secret
    
    def verify_webhook_signature(self, payload: str, signature: str) -> bool:
        """
        Verify webhook signature from access point
        
        Args:
            payload: Raw webhook payload (XML)
            signature: Signature from X-Unimicro-Signature header (or similar)
            
        Returns:
            True if signature is valid
        """
        if not self.webhook_secret:
            logger.warning("webhook_signature_verification_skipped_no_secret")
            return True  # Skip verification if no secret configured
        
        # Compute expected signature (HMAC-SHA256)
        expected = hmac.new(
            self.webhook_secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Constant-time comparison
        is_valid = hmac.compare_digest(expected, signature)
        
        if not is_valid:
            logger.warning(
                "webhook_signature_invalid",
                expected=expected[:8] + "...",
                received=signature[:8] + "..."
            )
        
        return is_valid
    
    async def receive_ehf_invoice(
        self,
        xml_content: str,
        tenant_id: int,
        metadata: Optional[dict] = None
    ) -> dict:
        """
        Receive and process EHF invoice
        
        This is the main entry point called by webhook handler.
        
        Args:
            xml_content: EHF XML content
            tenant_id: Tenant ID (accounting firm)
            metadata: Optional metadata (webhook headers, etc.)
            
        Returns:
            Dict with processing result:
            {
                "success": bool,
                "vendor_invoice_id": int (if success),
                "ehf_invoice_id": str,
                "errors": List[str],
                "warnings": List[str]
            }
        """
        start_time = datetime.utcnow()
        
        logger.info(
            "ehf_receive_started",
            tenant_id=tenant_id,
            xml_size=len(xml_content),
        )
        
        result = {
            "success": False,
            "vendor_invoice_id": None,
            "ehf_invoice_id": None,
            "errors": [],
            "warnings": [],
        }
        
        try:
            # Step 1: Validate XML
            is_valid, validation_messages = validate_ehf_xml(xml_content)
            
            # Separate errors and warnings
            errors = [msg for msg in validation_messages if "[ERROR]" in msg]
            warnings = [msg for msg in validation_messages if "[WARNING]" in msg]
            
            result["errors"].extend(errors)
            result["warnings"].extend(warnings)
            
            if not is_valid:
                logger.warning(
                    "ehf_validation_failed",
                    tenant_id=tenant_id,
                    errors=len(errors)
                )
                return result
            
            # Step 2: Parse XML
            parse_result = parse_ehf_xml(xml_content)
            
            if not parse_result.success:
                result["errors"].extend(parse_result.errors)
                result["warnings"].extend(parse_result.warnings)
                logger.error(
                    "ehf_parse_failed",
                    tenant_id=tenant_id,
                    errors=parse_result.errors
                )
                return result
            
            ehf_invoice = parse_result.invoice
            result["ehf_invoice_id"] = ehf_invoice.invoice_id
            
            logger.info(
                "ehf_parsed",
                invoice_id=ehf_invoice.invoice_id,
                supplier=ehf_invoice.accounting_supplier_party.name,
                amount=float(ehf_invoice.payable_amount),
            )
            
            # Step 3: Convert to VendorInvoice format
            vendor_invoice_data = ehf_to_vendor_invoice_dict(ehf_invoice)
            vendor_invoice_data["ehf_raw_xml"] = xml_content
            
            # Add EHF metadata
            if metadata:
                vendor_invoice_data["ehf_message_id"] = metadata.get("message_id")
            
            # Step 4: Create VendorInvoice
            # NOTE: This is where we hand off to the existing system
            # The actual database save happens in the calling code
            # We return the data needed to create VendorInvoice
            
            result["success"] = True
            result["vendor_invoice_data"] = vendor_invoice_data
            result["warnings"].extend(parse_result.warnings)
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.info(
                "ehf_receive_completed",
                tenant_id=tenant_id,
                invoice_id=ehf_invoice.invoice_id,
                duration_seconds=duration
            )
            
            return result
            
        except Exception as e:
            error_msg = f"Unexpected error processing EHF: {str(e)}"
            logger.error(
                "ehf_receive_failed",
                tenant_id=tenant_id,
                error=error_msg,
                exc_info=True
            )
            result["errors"].append(error_msg)
            return result


# Convenience function for direct use
async def receive_ehf_invoice(
    xml_content: str,
    tenant_id: int,
    webhook_secret: Optional[str] = None,
    metadata: Optional[dict] = None
) -> dict:
    """
    Convenience function to receive EHF invoice
    
    Args:
        xml_content: EHF XML string
        tenant_id: Tenant ID
        webhook_secret: Optional webhook secret for signature verification
        metadata: Optional metadata
        
    Returns:
        Processing result dict
    """
    receiver = EHFReceiver(webhook_secret=webhook_secret)
    return await receiver.receive_ehf_invoice(xml_content, tenant_id, metadata)


# Example usage in FastAPI webhook endpoint:
"""
from fastapi import APIRouter, Request, HTTPException, Header
from app.services.ehf.receiver import receive_ehf_invoice
from app.database import get_db
from app.models.vendor_invoice import VendorInvoice

router = APIRouter()

@router.post("/webhooks/ehf")
async def ehf_webhook(
    request: Request,
    x_unimicro_signature: str = Header(None),
    db = Depends(get_db)
):
    # Get raw XML
    xml_content = await request.body()
    xml_content = xml_content.decode('utf-8')
    
    # Get tenant from request (you'll need to implement this)
    tenant_id = extract_tenant_from_request(request)
    
    # Verify signature
    webhook_secret = get_webhook_secret(tenant_id)
    receiver = EHFReceiver(webhook_secret=webhook_secret)
    
    if x_unimicro_signature:
        if not receiver.verify_webhook_signature(xml_content, x_unimicro_signature):
            raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Process EHF
    result = await receive_ehf_invoice(
        xml_content,
        tenant_id,
        webhook_secret=webhook_secret,
        metadata={"message_id": request.headers.get("X-Message-ID")}
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["errors"])
    
    # Create VendorInvoice in database
    vendor_invoice_data = result["vendor_invoice_data"]
    
    # Find or create vendor
    vendor = await find_or_create_vendor(
        db,
        tenant_id=tenant_id,
        org_number=vendor_invoice_data["vendor_org_number"],
        name=vendor_invoice_data["vendor_name"],
    )
    
    # Create invoice
    invoice = VendorInvoice(
        tenant_id=tenant_id,
        vendor_id=vendor.id,
        invoice_number=vendor_invoice_data["invoice_number"],
        invoice_date=vendor_invoice_data["invoice_date"],
        due_date=vendor_invoice_data["due_date"],
        currency=vendor_invoice_data["currency"],
        amount_excl_vat=vendor_invoice_data["amount_excl_vat"],
        vat_amount=vendor_invoice_data["vat_amount"],
        total_amount=vendor_invoice_data["total_amount"],
        kid_number=vendor_invoice_data["kid_number"],
        payment_terms=vendor_invoice_data["payment_terms"],
        line_items=vendor_invoice_data["line_items"],
        tax_breakdown=vendor_invoice_data["tax_breakdown"],
        ehf_message_id=vendor_invoice_data.get("ehf_message_id"),
        ehf_raw_xml=vendor_invoice_data["ehf_raw_xml"],
        ehf_received_at=vendor_invoice_data["ehf_received_at"],
        review_status="pending",  # Will be processed by Invoice Agent
    )
    
    db.add(invoice)
    await db.commit()
    await db.refresh(invoice)
    
    # Trigger async processing by Invoice Agent
    from app.tasks.invoice_processing import process_invoice
    process_invoice.delay(invoice.id)
    
    return {
        "status": "received",
        "invoice_id": invoice.id,
        "ehf_invoice_id": result["ehf_invoice_id"],
        "warnings": result["warnings"]
    }
"""

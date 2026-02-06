"""
Invoice Parser Agent - Parse EHF og PDF fakturaer
"""
import logging
from typing import Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.agents.base import BaseAgent
from app.models.agent_task import AgentTask
from app.models.vendor_invoice import VendorInvoice
from app.models.vendor import Vendor
from app.services.ehf.parser import parse_ehf_xml
from app.services.ehf.models import EHFParseResult

logger = logging.getLogger(__name__)


class InvoiceParserAgent(BaseAgent):
    """
    Invoice Parser Agent
    
    Ansvar:
    - Parse EHF-XML og trekke ut strukturerte data
    - (Fremtidig) OCR/parse PDF-fakturaer
    - Identifisere leverandør, beløp, MVA, fakturanummer, dato, forfallsdato
    - Matche leverandør mot kjente leverandører i systemet
    - Flagge uvanlige fakturaer (duplikat, uvanlig beløp, ukjent leverandør)
    """
    
    def __init__(self):
        super().__init__(agent_type="invoice_parser")
    
    async def execute_task(
        self,
        db: AsyncSession,
        task: AgentTask
    ) -> Dict[str, Any]:
        """
        Execute parsing task
        
        Args:
            db: Database session
            task: Task to execute
        
        Returns:
            Result dictionary
        """
        task_type = task.task_type
        
        if task_type == "parse_invoice":
            return await self.parse_invoice(db, task)
        else:
            raise ValueError(
                f"Unknown task type for invoice_parser: {task_type}"
            )
    
    async def parse_invoice(
        self,
        db: AsyncSession,
        task: AgentTask
    ) -> Dict[str, Any]:
        """
        Parse invoice from raw data
        
        Args:
            db: Database session
            task: Task with invoice_id in payload
        
        Returns:
            Result with parsed data
        """
        invoice_id = task.payload.get("invoice_id")
        
        if not invoice_id:
            raise ValueError("parse_invoice task missing invoice_id")
        
        # Get invoice
        result = await db.execute(
            select(VendorInvoice).where(VendorInvoice.id == invoice_id)
        )
        invoice = result.scalar_one_or_none()
        
        if not invoice:
            raise ValueError(f"Invoice {invoice_id} not found")
        
        # Parse based on type
        if invoice.ehf_raw_xml:
            parsed_data = await self.parse_ehf(db, invoice)
        else:
            raise ValueError(
                f"Invoice {invoice_id} has no parseable data "
                "(no EHF XML or PDF path)"
            )
        
        # Update invoice with parsed data
        await self.update_invoice(db, invoice, parsed_data)
        
        # Publish invoice_parsed event
        await self.publish_event(
            db,
            tenant_id=task.tenant_id,
            event_type="invoice_parsed",
            payload={"invoice_id": str(invoice.id)}
        )
        
        # Log audit
        await self.log_audit(
            db,
            tenant_id=task.tenant_id,
            action="invoice_parsed",
            entity_type="vendor_invoice",
            entity_id=str(invoice.id),
            details={
                "vendor_name": parsed_data.get("vendor_name"),
                "total_amount": parsed_data.get("total_amount")
            }
        )
        
        return {
            "invoice_id": str(invoice.id),
            "vendor_name": parsed_data.get("vendor_name"),
            "total_amount": parsed_data.get("total_amount")
        }
    
    async def parse_ehf(
        self,
        db: AsyncSession,
        invoice: VendorInvoice
    ) -> Dict[str, Any]:
        """
        Parse EHF XML
        
        Args:
            db: Database session
            invoice: Invoice with ehf_raw_xml
        
        Returns:
            Parsed data dictionary
        """
        logger.info(f"InvoiceParser: Parsing EHF for invoice {invoice.id}")
        
        try:
            # Parse using existing EHF parser
            ehf_result: EHFParseResult = parse_ehf_xml(
                invoice.ehf_raw_xml.encode('utf-8')
            )
            
            if not ehf_result.success:
                raise ValueError(
                    f"EHF parsing failed: "
                    f"{', '.join(ehf_result.errors or [])}"
                )
            
            ehf_invoice = ehf_result.invoice
            
            # Find or create vendor
            vendor = await self.find_or_create_vendor(
                db,
                client_id=invoice.client_id,
                name=ehf_invoice.supplier.name,
                org_number=ehf_invoice.supplier.party_id
            )
            
            # Build parsed data
            parsed_data = {
                "vendor_id": str(vendor.id),
                "vendor_name": ehf_invoice.supplier.name,
                "vendor_org_number": ehf_invoice.supplier.party_id,
                "invoice_number": ehf_invoice.invoice_number,
                "invoice_date": ehf_invoice.issue_date,
                "due_date": ehf_invoice.due_date,
                "amount_excl_vat": float(ehf_invoice.tax_exclusive_amount),
                "vat_amount": float(
                    ehf_invoice.tax_total.tax_amount
                    if ehf_invoice.tax_total
                    else 0
                ),
                "total_amount": float(ehf_invoice.payable_amount),
                "currency": ehf_invoice.document_currency_code or "NOK",
                "parse_confidence": 95.0,  # High confidence for valid EHF
                "parse_warnings": ehf_result.warnings or []
            }
            
            logger.info(
                f"InvoiceParser: Successfully parsed EHF invoice {invoice.id}"
            )
            
            return parsed_data
            
        except Exception as e:
            logger.error(
                f"InvoiceParser: Failed to parse EHF for invoice {invoice.id}: {e}",
                exc_info=True
            )
            raise
    
    async def find_or_create_vendor(
        self,
        db: AsyncSession,
        client_id: str,
        name: str,
        org_number: str
    ) -> Vendor:
        """
        Find existing vendor or create new
        
        Args:
            db: Database session
            client_id: Client UUID
            name: Vendor name
            org_number: Organization number
        
        Returns:
            Vendor
        """
        # Try to find by org number
        if org_number:
            result = await db.execute(
                select(Vendor).where(
                    Vendor.client_id == client_id,
                    Vendor.org_number == org_number
                )
            )
            vendor = result.scalar_one_or_none()
            
            if vendor:
                logger.info(
                    f"InvoiceParser: Found existing vendor {vendor.id} "
                    f"({vendor.name})"
                )
                return vendor
        
        # Create new vendor
        vendor = Vendor(
            client_id=client_id,
            name=name,
            org_number=org_number
        )
        
        db.add(vendor)
        await db.commit()
        await db.refresh(vendor)
        
        logger.info(
            f"InvoiceParser: Created new vendor {vendor.id} ({vendor.name})"
        )
        
        return vendor
    
    async def update_invoice(
        self,
        db: AsyncSession,
        invoice: VendorInvoice,
        parsed_data: Dict[str, Any]
    ):
        """
        Update invoice with parsed data
        
        Args:
            db: Database session
            invoice: Invoice to update
            parsed_data: Parsed data
        """
        await db.execute(
            update(VendorInvoice)
            .where(VendorInvoice.id == invoice.id)
            .values(
                vendor_id=parsed_data.get("vendor_id"),
                invoice_number=parsed_data.get("invoice_number"),
                invoice_date=parsed_data.get("invoice_date"),
                due_date=parsed_data.get("due_date"),
                amount_excl_vat=parsed_data.get("amount_excl_vat"),
                vat_amount=parsed_data.get("vat_amount"),
                total_amount=parsed_data.get("total_amount"),
                currency=parsed_data.get("currency"),
                ai_processed=True,
                review_status="parsed"
            )
        )
        
        await db.commit()
        
        logger.info(
            f"InvoiceParser: Updated invoice {invoice.id} with parsed data"
        )

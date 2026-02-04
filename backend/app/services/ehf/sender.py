"""
EHF Sender
Sends EHF invoices via PEPPOL network (Unimicro API)
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
import structlog
import httpx
from lxml import etree

from .models import (
    EHFInvoice,
    EHFParty,
    EHFInvoiceLine,
    EHFTaxTotal,
    EHFTaxSubtotal,
    EHFPaymentMeans,
)

logger = structlog.get_logger(__name__)


class EHFSender:
    """
    Sends EHF invoices via PEPPOL network using Unimicro API
    """
    
    def __init__(
        self,
        api_key: str,
        api_url: str = "https://api.unimicro.no/peppol/v1",
        test_mode: bool = False
    ):
        """
        Initialize sender
        
        Args:
            api_key: Unimicro API key
            api_url: API endpoint URL
            test_mode: If True, use test environment
        """
        self.api_key = api_key
        self.api_url = api_url
        self.test_mode = test_mode
        
        if test_mode:
            self.api_url = "https://api-test.unimicro.no/peppol/v1"
    
    def generate_ehf_xml(self, invoice: EHFInvoice) -> str:
        """
        Generate EHF 3.0 XML from EHFInvoice model
        
        Args:
            invoice: EHFInvoice model
            
        Returns:
            XML string
        """
        # Define namespaces
        nsmap = {
            None: "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2",
            "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
            "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
        }
        
        # Create root element
        root = etree.Element("Invoice", nsmap=nsmap)
        
        # Add namespace declarations
        root.attrib["{http://www.w3.org/2001/XMLSchema-instance}schemaLocation"] = (
            "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2 "
            "http://docs.oasis-open.org/ubl/os-UBL-2.1/xsd/maindoc/UBL-Invoice-2.1.xsd"
        )
        
        # Helper function to add element with text
        def add_elem(parent, tag, text, attrib=None):
            if text is not None:
                elem = etree.SubElement(parent, tag)
                if isinstance(text, (date, datetime)):
                    elem.text = text.strftime("%Y-%m-%d")
                elif isinstance(text, Decimal):
                    elem.text = str(text)
                else:
                    elem.text = str(text)
                if attrib:
                    for k, v in attrib.items():
                        elem.attrib[k] = v
                return elem
            return None
        
        # Header
        add_elem(root, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}CustomizationID", invoice.customization_id)
        add_elem(root, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}ProfileID", invoice.profile_id)
        add_elem(root, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}ID", invoice.invoice_id)
        add_elem(root, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}IssueDate", invoice.issue_date)
        if invoice.due_date:
            add_elem(root, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}DueDate", invoice.due_date)
        add_elem(root, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}InvoiceTypeCode", invoice.invoice_type_code)
        if invoice.note:
            add_elem(root, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}Note", invoice.note)
        add_elem(root, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}DocumentCurrencyCode", invoice.document_currency_code)
        
        # Order reference
        if invoice.order_reference:
            order_ref = etree.SubElement(root, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}OrderReference")
            add_elem(order_ref, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}ID", invoice.order_reference)
        
        # Supplier party
        supplier_party = etree.SubElement(root, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}AccountingSupplierParty")
        self._add_party(supplier_party, invoice.accounting_supplier_party)
        
        # Customer party
        customer_party = etree.SubElement(root, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}AccountingCustomerParty")
        self._add_party(customer_party, invoice.accounting_customer_party)
        
        # Payment means
        if invoice.payment_means:
            self._add_payment_means(root, invoice.payment_means)
        
        # Payment terms
        if invoice.payment_terms_note:
            payment_terms = etree.SubElement(root, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}PaymentTerms")
            add_elem(payment_terms, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}Note", invoice.payment_terms_note)
        
        # Tax total
        self._add_tax_total(root, invoice.tax_total)
        
        # Legal monetary total
        monetary = etree.SubElement(root, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}LegalMonetaryTotal")
        add_elem(monetary, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}LineExtensionAmount", invoice.line_extension_amount, {"currencyID": invoice.document_currency_code})
        add_elem(monetary, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}TaxExclusiveAmount", invoice.tax_exclusive_amount, {"currencyID": invoice.document_currency_code})
        add_elem(monetary, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}TaxInclusiveAmount", invoice.tax_inclusive_amount, {"currencyID": invoice.document_currency_code})
        add_elem(monetary, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}PayableAmount", invoice.payable_amount, {"currencyID": invoice.document_currency_code})
        
        # Invoice lines
        for line in invoice.invoice_lines:
            self._add_invoice_line(root, line, invoice.document_currency_code)
        
        # Convert to string
        xml_bytes = etree.tostring(root, pretty_print=True, xml_declaration=True, encoding='UTF-8')
        return xml_bytes.decode('utf-8')
    
    def _add_party(self, parent, party: EHFParty):
        """Add party (supplier/customer) to XML"""
        party_elem = etree.SubElement(parent, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}Party")
        
        # Endpoint
        endpoint = etree.SubElement(party_elem, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}EndpointID")
        endpoint.text = party.endpoint_id
        endpoint.attrib["schemeID"] = party.endpoint_scheme
        
        # Name
        party_name = etree.SubElement(party_elem, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}PartyName")
        name = etree.SubElement(party_name, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}Name")
        name.text = party.name
        
        # Address
        if party.street_name or party.city_name:
            address = etree.SubElement(party_elem, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}PostalAddress")
            if party.street_name:
                street = etree.SubElement(address, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}StreetName")
                street.text = party.street_name
            if party.city_name:
                city = etree.SubElement(address, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}CityName")
                city.text = party.city_name
            if party.postal_zone:
                postal = etree.SubElement(address, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}PostalZone")
                postal.text = party.postal_zone
            country = etree.SubElement(address, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}Country")
            country_id = etree.SubElement(country, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}IdentificationCode")
            country_id.text = party.country_code
        
        # Legal entity
        if party.company_id:
            legal = etree.SubElement(party_elem, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}PartyLegalEntity")
            company_id = etree.SubElement(legal, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}CompanyID")
            company_id.text = party.company_id
    
    def _add_payment_means(self, parent, payment: EHFPaymentMeans):
        """Add payment means to XML"""
        payment_elem = etree.SubElement(parent, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}PaymentMeans")
        code = etree.SubElement(payment_elem, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}PaymentMeansCode")
        code.text = payment.payment_means_code
        
        if payment.payment_id:
            payment_id = etree.SubElement(payment_elem, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}PaymentID")
            payment_id.text = payment.payment_id
        
        if payment.payee_financial_account_id:
            account = etree.SubElement(payment_elem, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}PayeeFinancialAccount")
            account_id = etree.SubElement(account, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}ID")
            account_id.text = payment.payee_financial_account_id
    
    def _add_tax_total(self, parent, tax: EHFTaxTotal):
        """Add tax total to XML"""
        tax_elem = etree.SubElement(parent, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}TaxTotal")
        amount = etree.SubElement(tax_elem, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}TaxAmount")
        amount.text = str(tax.tax_amount)
        amount.attrib["currencyID"] = "NOK"  # Should be from invoice
        
        for subtotal in tax.tax_subtotals:
            sub_elem = etree.SubElement(tax_elem, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}TaxSubtotal")
            taxable = etree.SubElement(sub_elem, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}TaxableAmount")
            taxable.text = str(subtotal.taxable_amount)
            taxable.attrib["currencyID"] = "NOK"
            
            tax_amt = etree.SubElement(sub_elem, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}TaxAmount")
            tax_amt.text = str(subtotal.tax_amount)
            tax_amt.attrib["currencyID"] = "NOK"
            
            category = etree.SubElement(sub_elem, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}TaxCategory")
            cat_id = etree.SubElement(category, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}ID")
            cat_id.text = subtotal.tax_category_id
            
            percent = etree.SubElement(category, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}Percent")
            percent.text = str(subtotal.tax_category_percent)
    
    def _add_invoice_line(self, parent, line: EHFInvoiceLine, currency: str):
        """Add invoice line to XML"""
        line_elem = etree.SubElement(parent, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}InvoiceLine")
        
        id_elem = etree.SubElement(line_elem, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}ID")
        id_elem.text = line.id
        
        qty = etree.SubElement(line_elem, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}InvoicedQuantity")
        qty.text = str(line.invoiced_quantity)
        qty.attrib["unitCode"] = line.invoiced_quantity_unit_code
        
        amount = etree.SubElement(line_elem, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}LineExtensionAmount")
        amount.text = str(line.line_extension_amount)
        amount.attrib["currencyID"] = currency
        
        # Item
        item = etree.SubElement(line_elem, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}Item")
        name = etree.SubElement(item, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}Name")
        name.text = line.item_name
        
        # Tax category
        tax_cat = etree.SubElement(item, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}ClassifiedTaxCategory")
        cat_id = etree.SubElement(tax_cat, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}ID")
        cat_id.text = line.tax_category_id
        percent = etree.SubElement(tax_cat, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}Percent")
        percent.text = str(line.tax_category_percent)
        
        # Price
        price = etree.SubElement(line_elem, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}Price")
        price_amt = etree.SubElement(price, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}PriceAmount")
        price_amt.text = str(line.price_amount)
        price_amt.attrib["currencyID"] = currency
    
    async def send_invoice_ehf(
        self,
        invoice: EHFInvoice,
        recipient_org_number: str,
    ) -> dict:
        """
        Send EHF invoice via Unimicro API
        
        Args:
            invoice: EHFInvoice model
            recipient_org_number: Recipient's organization number
            
        Returns:
            {
                "status": "sent",
                "ehf_id": "...",
                "sent_at": "...",
                "transmission_id": "..."
            }
        """
        logger.info(
            "ehf_send_started",
            invoice_id=invoice.invoice_id,
            recipient=recipient_org_number
        )
        
        try:
            # Generate XML
            xml_content = self.generate_ehf_xml(invoice)
            
            # Send via API
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/send",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/xml",
                        "X-Recipient-ID": recipient_org_number,
                        "X-Recipient-Scheme": "0192",  # Norwegian org.nr
                    },
                    content=xml_content,
                    timeout=30.0
                )
                
                response.raise_for_status()
                
                result = response.json()
                
                logger.info(
                    "ehf_sent_successfully",
                    invoice_id=invoice.invoice_id,
                    transmission_id=result.get("transmission_id")
                )
                
                return {
                    "status": "sent",
                    "ehf_id": invoice.invoice_id,
                    "sent_at": datetime.utcnow().isoformat(),
                    "transmission_id": result.get("transmission_id"),
                    "recipient": recipient_org_number,
                }
                
        except httpx.HTTPStatusError as e:
            error_msg = f"API error: {e.response.status_code} - {e.response.text}"
            logger.error(
                "ehf_send_failed",
                invoice_id=invoice.invoice_id,
                error=error_msg
            )
            return {
                "status": "failed",
                "error": error_msg
            }
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(
                "ehf_send_failed",
                invoice_id=invoice.invoice_id,
                error=error_msg,
                exc_info=True
            )
            return {
                "status": "failed",
                "error": error_msg
            }


# Convenience function
async def send_invoice_ehf(
    invoice_id: int,
    recipient_org_number: str,
    tenant_id: int,
    api_key: str,
    test_mode: bool = False
) -> dict:
    """
    Convenience function to send invoice via EHF
    
    Args:
        invoice_id: ID of invoice to send
        recipient_org_number: Recipient's org.nr
        tenant_id: Tenant ID
        api_key: Unimicro API key
        test_mode: Use test environment
        
    Returns:
        Send result dict
    """
    # NOTE: This would need to fetch the invoice from database
    # and convert it to EHFInvoice model first
    # Implementation depends on your database models
    
    sender = EHFSender(api_key=api_key, test_mode=test_mode)
    
    # TODO: Fetch invoice from database
    # invoice = await fetch_invoice(invoice_id, tenant_id)
    # ehf_invoice = convert_to_ehf_invoice(invoice)
    
    # return await sender.send_invoice_ehf(ehf_invoice, recipient_org_number)
    
    raise NotImplementedError("Need to fetch invoice from database first")

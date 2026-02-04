"""
EHF XML Parser
Parses EHF 3.0 XML (UBL 2.1) to Pydantic models
"""

from lxml import etree
from decimal import Decimal
from datetime import datetime, date
from typing import Optional, List
import structlog

from .models import (
    EHFInvoice,
    EHFCreditNote,
    EHFParty,
    EHFInvoiceLine,
    EHFTaxTotal,
    EHFTaxSubtotal,
    EHFPaymentMeans,
    EHFParseResult,
)

logger = structlog.get_logger(__name__)

# UBL 2.1 namespaces
NAMESPACES = {
    'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
    'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2',
    'ubl': 'urn:oasis:names:specification:ubl:schema:xsd:Invoice-2',
    'ccts': 'urn:un:unece:uncefact:documentation:2',
}


def get_text(element, xpath: str, namespaces: dict = NAMESPACES) -> Optional[str]:
    """
    Get text content from XML element using XPath
    
    Args:
        element: lxml element
        xpath: XPath expression
        namespaces: XML namespaces
        
    Returns:
        Text content or None
    """
    result = element.xpath(xpath, namespaces=namespaces)
    if result and len(result) > 0:
        # If result is a string (e.g., from attribute selection), return it directly
        if isinstance(result[0], str):
            return result[0].strip() if result[0] else None
        # Otherwise, get the text from the element
        text = result[0].text
        return text.strip() if text else None
    return None


def get_decimal(element, xpath: str, namespaces: dict = NAMESPACES) -> Optional[Decimal]:
    """Get decimal value from XML element"""
    text = get_text(element, xpath, namespaces)
    if text:
        try:
            return Decimal(text)
        except Exception as e:
            logger.warning("failed_to_parse_decimal", xpath=xpath, text=text, error=str(e))
    return None


def get_date(element, xpath: str, namespaces: dict = NAMESPACES) -> Optional[date]:
    """Get date from XML element"""
    text = get_text(element, xpath, namespaces)
    if text:
        try:
            return datetime.strptime(text, "%Y-%m-%d").date()
        except Exception as e:
            logger.warning("failed_to_parse_date", xpath=xpath, text=text, error=str(e))
    return None


def parse_party(party_element, namespaces: dict = NAMESPACES) -> EHFParty:
    """
    Parse Party information (supplier or customer)
    
    Args:
        party_element: cac:Party XML element
        
    Returns:
        EHFParty model
    """
    endpoint_id = get_text(party_element, ".//cbc:EndpointID", namespaces)
    endpoint_scheme = get_text(party_element, ".//cbc:EndpointID/@schemeID", namespaces) or "0192"
    
    name = get_text(party_element, ".//cac:PartyName/cbc:Name", namespaces) or \
           get_text(party_element, ".//cac:PartyLegalEntity/cbc:RegistrationName", namespaces)
    
    # Address
    address = party_element.xpath(".//cac:PostalAddress", namespaces=namespaces)
    street = city = postal = country = None
    if address:
        street = get_text(address[0], ".//cbc:StreetName", namespaces)
        city = get_text(address[0], ".//cbc:CityName", namespaces)
        postal = get_text(address[0], ".//cbc:PostalZone", namespaces)
        country_elem = get_text(address[0], ".//cac:Country/cbc:IdentificationCode", namespaces)
        country = country_elem or "NO"
    
    # Contact
    contact = party_element.xpath(".//cac:Contact", namespaces=namespaces)
    contact_name = telephone = email = None
    if contact:
        contact_name = get_text(contact[0], ".//cbc:Name", namespaces)
        telephone = get_text(contact[0], ".//cbc:Telephone", namespaces)
        email = get_text(contact[0], ".//cbc:ElectronicMail", namespaces)
    
    # Tax/Company IDs
    company_id = get_text(party_element, ".//cac:PartyLegalEntity/cbc:CompanyID", namespaces)
    vat_id = get_text(party_element, ".//cac:PartyTaxScheme/cbc:CompanyID", namespaces)
    
    return EHFParty(
        endpoint_id=endpoint_id or company_id or "",
        endpoint_scheme=endpoint_scheme,
        name=name or "Unknown",
        street_name=street,
        city_name=city,
        postal_zone=postal,
        country_code=country or "NO",
        contact_name=contact_name,
        telephone=telephone,
        email=email,
        company_id=company_id,
        vat_id=vat_id,
    )


def parse_invoice_line(line_element, namespaces: dict = NAMESPACES) -> EHFInvoiceLine:
    """Parse invoice line"""
    line_id = get_text(line_element, ".//cbc:ID", namespaces) or "1"
    
    # Quantity
    quantity = get_decimal(line_element, ".//cbc:InvoicedQuantity", namespaces) or Decimal("1.0")
    quantity_unit = get_text(line_element, ".//cbc:InvoicedQuantity/@unitCode", namespaces) or "EA"
    
    # Amount
    line_amount = get_decimal(line_element, ".//cbc:LineExtensionAmount", namespaces) or Decimal("0.0")
    
    # Item
    item_name = get_text(line_element, ".//cac:Item/cbc:Name", namespaces) or "Unknown item"
    item_desc = get_text(line_element, ".//cac:Item/cbc:Description", namespaces)
    
    # Price
    price = get_decimal(line_element, ".//cac:Price/cbc:PriceAmount", namespaces) or Decimal("0.0")
    base_qty = get_decimal(line_element, ".//cac:Price/cbc:BaseQuantity", namespaces) or Decimal("1.0")
    
    # Tax
    tax_category = get_text(line_element, ".//cac:Item/cac:ClassifiedTaxCategory/cbc:ID", namespaces) or "S"
    tax_percent = get_decimal(line_element, ".//cac:Item/cac:ClassifiedTaxCategory/cbc:Percent", namespaces) or Decimal("0.0")
    
    # Optional
    accounting_cost = get_text(line_element, ".//cbc:AccountingCost", namespaces)
    
    return EHFInvoiceLine(
        id=line_id,
        invoiced_quantity=quantity,
        invoiced_quantity_unit_code=quantity_unit,
        line_extension_amount=line_amount,
        item_name=item_name,
        item_description=item_desc,
        price_amount=price,
        base_quantity=base_qty,
        tax_category_id=tax_category,
        tax_category_percent=tax_percent,
        accounting_cost=accounting_cost,
    )


def parse_tax_total(tax_element, namespaces: dict = NAMESPACES) -> EHFTaxTotal:
    """Parse tax total and subtotals"""
    tax_amount = get_decimal(tax_element, ".//cbc:TaxAmount", namespaces) or Decimal("0.0")
    
    subtotals = []
    for subtotal_elem in tax_element.xpath(".//cac:TaxSubtotal", namespaces=namespaces):
        taxable = get_decimal(subtotal_elem, ".//cbc:TaxableAmount", namespaces) or Decimal("0.0")
        tax = get_decimal(subtotal_elem, ".//cbc:TaxAmount", namespaces) or Decimal("0.0")
        category = get_text(subtotal_elem, ".//cac:TaxCategory/cbc:ID", namespaces) or "S"
        percent = get_decimal(subtotal_elem, ".//cac:TaxCategory/cbc:Percent", namespaces) or Decimal("0.0")
        
        subtotals.append(EHFTaxSubtotal(
            taxable_amount=taxable,
            tax_amount=tax,
            tax_category_id=category,
            tax_category_percent=percent,
        ))
    
    return EHFTaxTotal(
        tax_amount=tax_amount,
        tax_subtotals=subtotals,
    )


def parse_payment_means(payment_element, namespaces: dict = NAMESPACES) -> Optional[EHFPaymentMeans]:
    """Parse payment means"""
    if payment_element is None:
        return None
    
    code = get_text(payment_element, ".//cbc:PaymentMeansCode", namespaces) or "30"
    payment_id = get_text(payment_element, ".//cbc:PaymentID", namespaces)  # KID
    
    account_id = get_text(payment_element, ".//cac:PayeeFinancialAccount/cbc:ID", namespaces)
    account_name = get_text(payment_element, ".//cac:PayeeFinancialAccount/cbc:Name", namespaces)
    branch_id = get_text(payment_element, ".//cac:PayeeFinancialAccount/cac:FinancialInstitutionBranch/cbc:ID", namespaces)
    
    return EHFPaymentMeans(
        payment_means_code=code,
        payment_id=payment_id,
        payee_financial_account_id=account_id,
        payee_financial_account_name=account_name,
        financial_institution_branch_id=branch_id,
    )


def parse_ehf_xml(xml_content: str) -> EHFParseResult:
    """
    Parse EHF XML to EHFInvoice model
    
    Args:
        xml_content: EHF XML string
        
    Returns:
        EHFParseResult with parsed invoice or errors
    """
    errors = []
    warnings = []
    
    try:
        # Parse XML
        root = etree.fromstring(xml_content.encode('utf-8'))
        
        # Determine if Invoice or CreditNote
        is_credit_note = root.tag.endswith('CreditNote')
        
        # Basic fields
        customization = get_text(root, "//cbc:CustomizationID", NAMESPACES)
        profile = get_text(root, "//cbc:ProfileID", NAMESPACES)
        invoice_id = get_text(root, "//cbc:ID", NAMESPACES)
        issue_date = get_date(root, "//cbc:IssueDate", NAMESPACES)
        due_date = get_date(root, "//cbc:DueDate", NAMESPACES)
        invoice_type = get_text(root, "//cbc:InvoiceTypeCode", NAMESPACES) or ("381" if is_credit_note else "380")
        
        # Currency
        currency = get_text(root, "//cbc:DocumentCurrencyCode", NAMESPACES) or "NOK"
        tax_currency = get_text(root, "//cbc:TaxCurrencyCode", NAMESPACES)
        
        # Parties
        supplier_elem = root.xpath("//cac:AccountingSupplierParty/cac:Party", namespaces=NAMESPACES)
        customer_elem = root.xpath("//cac:AccountingCustomerParty/cac:Party", namespaces=NAMESPACES)
        
        if not supplier_elem:
            errors.append("Missing AccountingSupplierParty")
            return EHFParseResult(success=False, errors=errors, raw_xml=xml_content)
        
        if not customer_elem:
            errors.append("Missing AccountingCustomerParty")
            return EHFParseResult(success=False, errors=errors, raw_xml=xml_content)
        
        supplier = parse_party(supplier_elem[0], NAMESPACES)
        customer = parse_party(customer_elem[0], NAMESPACES)
        
        # Payment
        payment_elem = root.xpath("//cac:PaymentMeans", namespaces=NAMESPACES)
        payment = parse_payment_means(payment_elem[0], NAMESPACES) if payment_elem else None
        payment_terms = get_text(root, "//cac:PaymentTerms/cbc:Note", NAMESPACES)
        
        # Lines
        line_elements = root.xpath("//cac:InvoiceLine", namespaces=NAMESPACES)
        if not line_elements:
            line_elements = root.xpath("//cac:CreditNoteLine", namespaces=NAMESPACES)
        
        if not line_elements:
            errors.append("No invoice lines found")
            return EHFParseResult(success=False, errors=errors, raw_xml=xml_content)
        
        lines = [parse_invoice_line(line, NAMESPACES) for line in line_elements]
        
        # Totals
        monetary = root.xpath("//cac:LegalMonetaryTotal", namespaces=NAMESPACES)
        if not monetary:
            errors.append("Missing LegalMonetaryTotal")
            return EHFParseResult(success=False, errors=errors, raw_xml=xml_content)
        
        line_extension = get_decimal(monetary[0], ".//cbc:LineExtensionAmount", NAMESPACES) or Decimal("0.0")
        tax_exclusive = get_decimal(monetary[0], ".//cbc:TaxExclusiveAmount", NAMESPACES) or Decimal("0.0")
        tax_inclusive = get_decimal(monetary[0], ".//cbc:TaxInclusiveAmount", NAMESPACES) or Decimal("0.0")
        payable = get_decimal(monetary[0], ".//cbc:PayableAmount", NAMESPACES) or Decimal("0.0")
        
        # Tax
        tax_elem = root.xpath("//cac:TaxTotal", namespaces=NAMESPACES)
        if not tax_elem:
            errors.append("Missing TaxTotal")
            return EHFParseResult(success=False, errors=errors, raw_xml=xml_content)
        
        tax_total = parse_tax_total(tax_elem[0], NAMESPACES)
        
        # Optional fields
        order_ref = get_text(root, "//cac:OrderReference/cbc:ID", NAMESPACES)
        contract_ref = get_text(root, "//cac:ContractDocumentReference/cbc:ID", NAMESPACES)
        note = get_text(root, "//cbc:Note", NAMESPACES)
        
        # Validation warnings
        if not invoice_id:
            warnings.append("Missing invoice ID")
        if not issue_date:
            warnings.append("Missing issue date")
        
        # Build invoice
        invoice_data = {
            "customization_id": customization or "urn:cen.eu:en16931:2017#compliant#urn:fdc:peppol.eu:2017:poacc:billing:3.0",
            "profile_id": profile or "urn:fdc:peppol.eu:2017:poacc:billing:01:1.0",
            "invoice_id": invoice_id or "UNKNOWN",
            "issue_date": issue_date or date.today(),
            "due_date": due_date,
            "invoice_type_code": invoice_type,
            "document_currency_code": currency,
            "tax_currency_code": tax_currency,
            "accounting_supplier_party": supplier,
            "accounting_customer_party": customer,
            "payment_means": payment,
            "payment_terms_note": payment_terms,
            "invoice_lines": lines,
            "line_extension_amount": line_extension,
            "tax_exclusive_amount": tax_exclusive,
            "tax_inclusive_amount": tax_inclusive,
            "payable_amount": payable,
            "tax_total": tax_total,
            "order_reference": order_ref,
            "contract_document_reference": contract_ref,
            "note": note,
        }
        
        # Create appropriate model
        if is_credit_note:
            invoice = EHFCreditNote(**invoice_data)
        else:
            invoice = EHFInvoice(**invoice_data)
        
        logger.info(
            "ehf_parsed_successfully",
            invoice_id=invoice_id,
            supplier=supplier.name,
            amount=float(payable),
            lines=len(lines),
        )
        
        return EHFParseResult(
            success=True,
            invoice=invoice,
            errors=errors,
            warnings=warnings,
            raw_xml=xml_content,
        )
        
    except etree.XMLSyntaxError as e:
        error_msg = f"Invalid XML: {str(e)}"
        logger.error("ehf_parse_failed_xml_syntax", error=error_msg)
        errors.append(error_msg)
        return EHFParseResult(success=False, errors=errors, raw_xml=xml_content)
        
    except Exception as e:
        error_msg = f"Parse error: {str(e)}"
        logger.error("ehf_parse_failed", error=error_msg, exc_info=True)
        errors.append(error_msg)
        return EHFParseResult(success=False, errors=errors, raw_xml=xml_content)


def ehf_to_vendor_invoice_dict(ehf_invoice: EHFInvoice) -> dict:
    """
    Convert EHFInvoice to dict suitable for VendorInvoice model
    
    Args:
        ehf_invoice: Parsed EHF invoice
        
    Returns:
        Dict with fields for VendorInvoice
    """
    supplier = ehf_invoice.accounting_supplier_party
    
    # Build address string
    address_parts = [
        supplier.street_name,
        supplier.postal_zone,
        supplier.city_name,
    ]
    address = ", ".join([p for p in address_parts if p])
    
    # Extract line items as dicts
    line_items = [
        {
            "line_number": line.id,
            "description": line.item_name,
            "quantity": float(line.invoiced_quantity),
            "unit": line.invoiced_quantity_unit_code,
            "unit_price": float(line.price_amount),
            "amount": float(line.line_extension_amount),
            "vat_rate": float(line.tax_category_percent),
            "vat_category": line.tax_category_id,
            "accounting_cost": line.accounting_cost,
        }
        for line in ehf_invoice.invoice_lines
    ]
    
    # Extract tax breakdown
    tax_breakdown = [
        {
            "category": sub.tax_category_id,
            "rate": float(sub.tax_category_percent),
            "taxable_amount": float(sub.taxable_amount),
            "tax_amount": float(sub.tax_amount),
        }
        for sub in ehf_invoice.tax_total.tax_subtotals
    ]
    
    # KID number from payment means
    kid = None
    bank_account = None
    if ehf_invoice.payment_means:
        kid = ehf_invoice.payment_means.payment_id
        bank_account = ehf_invoice.payment_means.payee_financial_account_id
    
    return {
        "invoice_number": ehf_invoice.invoice_id,
        "invoice_date": ehf_invoice.issue_date,
        "due_date": ehf_invoice.due_date,
        "vendor_org_number": supplier.company_id or supplier.endpoint_id,
        "vendor_name": supplier.name,
        "vendor_address": address if address else None,
        "vendor_city": supplier.city_name,
        "vendor_postal_code": supplier.postal_zone,
        "vendor_bank_account": bank_account,
        "currency": ehf_invoice.document_currency_code,
        "amount_excl_vat": ehf_invoice.tax_exclusive_amount,
        "vat_amount": ehf_invoice.tax_total.tax_amount,
        "total_amount": ehf_invoice.payable_amount,
        "kid_number": kid,
        "payment_terms": ehf_invoice.payment_terms_note,
        "line_items": line_items,
        "tax_breakdown": tax_breakdown,
        "ehf_received_at": datetime.utcnow(),
    }

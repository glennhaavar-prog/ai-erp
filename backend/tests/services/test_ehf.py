"""
Unit Tests for EHF Module
Run with: pytest tests/services/test_ehf.py -v
"""

import pytest
from datetime import date
from decimal import Decimal
from lxml import etree

from app.services.ehf.models import (
    EHFInvoice,
    EHFParty,
    EHFInvoiceLine,
    EHFTaxTotal,
    EHFTaxSubtotal,
    map_ehf_tax_to_norwegian_code,
)
from app.services.ehf.parser import parse_ehf_xml, ehf_to_vendor_invoice_dict
from app.services.ehf.validator import validate_ehf_xml, EHFValidator
from app.services.ehf.sender import EHFSender


# Sample EHF XML (minimal valid invoice)
SAMPLE_EHF_XML = """<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
         xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
         xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
    <cbc:CustomizationID>urn:cen.eu:en16931:2017#compliant#urn:fdc:peppol.eu:2017:poacc:billing:3.0</cbc:CustomizationID>
    <cbc:ProfileID>urn:fdc:peppol.eu:2017:poacc:billing:01:1.0</cbc:ProfileID>
    <cbc:ID>INV-2024-001</cbc:ID>
    <cbc:IssueDate>2024-02-01</cbc:IssueDate>
    <cbc:DueDate>2024-03-01</cbc:DueDate>
    <cbc:InvoiceTypeCode>380</cbc:InvoiceTypeCode>
    <cbc:DocumentCurrencyCode>NOK</cbc:DocumentCurrencyCode>
    
    <cac:AccountingSupplierParty>
        <cac:Party>
            <cbc:EndpointID schemeID="0192">987654321</cbc:EndpointID>
            <cac:PartyName>
                <cbc:Name>Test Supplier AS</cbc:Name>
            </cac:PartyName>
            <cac:PostalAddress>
                <cbc:StreetName>Testveien 1</cbc:StreetName>
                <cbc:CityName>Oslo</cbc:CityName>
                <cbc:PostalZone>0123</cbc:PostalZone>
                <cac:Country>
                    <cbc:IdentificationCode>NO</cbc:IdentificationCode>
                </cac:Country>
            </cac:PostalAddress>
            <cac:PartyLegalEntity>
                <cbc:CompanyID>987654321</cbc:CompanyID>
            </cac:PartyLegalEntity>
        </cac:Party>
    </cac:AccountingSupplierParty>
    
    <cac:AccountingCustomerParty>
        <cac:Party>
            <cbc:EndpointID schemeID="0192">123456789</cbc:EndpointID>
            <cac:PartyName>
                <cbc:Name>Test Customer AS</cbc:Name>
            </cac:PartyName>
            <cac:PostalAddress>
                <cbc:StreetName>Kundeveien 2</cbc:StreetName>
                <cbc:CityName>Bergen</cbc:CityName>
                <cbc:PostalZone>5003</cbc:PostalZone>
                <cac:Country>
                    <cbc:IdentificationCode>NO</cbc:IdentificationCode>
                </cac:Country>
            </cac:PostalAddress>
            <cac:PartyLegalEntity>
                <cbc:CompanyID>123456789</cbc:CompanyID>
            </cac:PartyLegalEntity>
        </cac:Party>
    </cac:AccountingCustomerParty>
    
    <cac:PaymentMeans>
        <cbc:PaymentMeansCode>30</cbc:PaymentMeansCode>
        <cbc:PaymentID>12345678901</cbc:PaymentID>
        <cac:PayeeFinancialAccount>
            <cbc:ID>12341234567</cbc:ID>
        </cac:PayeeFinancialAccount>
    </cac:PaymentMeans>
    
    <cac:TaxTotal>
        <cbc:TaxAmount currencyID="NOK">2500.00</cbc:TaxAmount>
        <cac:TaxSubtotal>
            <cbc:TaxableAmount currencyID="NOK">10000.00</cbc:TaxableAmount>
            <cbc:TaxAmount currencyID="NOK">2500.00</cbc:TaxAmount>
            <cac:TaxCategory>
                <cbc:ID>S</cbc:ID>
                <cbc:Percent>25.0</cbc:Percent>
            </cac:TaxCategory>
        </cac:TaxSubtotal>
    </cac:TaxTotal>
    
    <cac:LegalMonetaryTotal>
        <cbc:LineExtensionAmount currencyID="NOK">10000.00</cbc:LineExtensionAmount>
        <cbc:TaxExclusiveAmount currencyID="NOK">10000.00</cbc:TaxExclusiveAmount>
        <cbc:TaxInclusiveAmount currencyID="NOK">12500.00</cbc:TaxInclusiveAmount>
        <cbc:PayableAmount currencyID="NOK">12500.00</cbc:PayableAmount>
    </cac:LegalMonetaryTotal>
    
    <cac:InvoiceLine>
        <cbc:ID>1</cbc:ID>
        <cbc:InvoicedQuantity unitCode="EA">10</cbc:InvoicedQuantity>
        <cbc:LineExtensionAmount currencyID="NOK">10000.00</cbc:LineExtensionAmount>
        <cac:Item>
            <cbc:Name>Test Product</cbc:Name>
            <cac:ClassifiedTaxCategory>
                <cbc:ID>S</cbc:ID>
                <cbc:Percent>25.0</cbc:Percent>
            </cac:ClassifiedTaxCategory>
        </cac:Item>
        <cac:Price>
            <cbc:PriceAmount currencyID="NOK">1000.00</cbc:PriceAmount>
        </cac:Price>
    </cac:InvoiceLine>
</Invoice>
"""


class TestEHFParser:
    """Test EHF XML parsing"""
    
    def test_parse_valid_ehf(self):
        """Test parsing valid EHF XML"""
        result = parse_ehf_xml(SAMPLE_EHF_XML)
        
        assert result.success is True
        assert result.invoice is not None
        assert result.invoice.invoice_id == "INV-2024-001"
        assert result.invoice.issue_date == date(2024, 2, 1)
        assert result.invoice.due_date == date(2024, 3, 1)
        assert result.invoice.document_currency_code == "NOK"
        assert result.invoice.payable_amount == Decimal("12500.00")
    
    def test_parse_supplier_info(self):
        """Test parsing supplier information"""
        result = parse_ehf_xml(SAMPLE_EHF_XML)
        
        supplier = result.invoice.accounting_supplier_party
        assert supplier.name == "Test Supplier AS"
        assert supplier.company_id == "987654321"
        assert supplier.city_name == "Oslo"
        assert supplier.postal_zone == "0123"
    
    def test_parse_customer_info(self):
        """Test parsing customer information"""
        result = parse_ehf_xml(SAMPLE_EHF_XML)
        
        customer = result.invoice.accounting_customer_party
        assert customer.name == "Test Customer AS"
        assert customer.company_id == "123456789"
        assert customer.city_name == "Bergen"
    
    def test_parse_invoice_lines(self):
        """Test parsing invoice lines"""
        result = parse_ehf_xml(SAMPLE_EHF_XML)
        
        assert len(result.invoice.invoice_lines) == 1
        line = result.invoice.invoice_lines[0]
        assert line.id == "1"
        assert line.item_name == "Test Product"
        assert line.invoiced_quantity == Decimal("10")
        assert line.line_extension_amount == Decimal("10000.00")
        assert line.tax_category_percent == Decimal("25.0")
    
    def test_parse_tax_total(self):
        """Test parsing tax information"""
        result = parse_ehf_xml(SAMPLE_EHF_XML)
        
        tax = result.invoice.tax_total
        assert tax.tax_amount == Decimal("2500.00")
        assert len(tax.tax_subtotals) == 1
        assert tax.tax_subtotals[0].taxable_amount == Decimal("10000.00")
        assert tax.tax_subtotals[0].tax_category_id == "S"
        assert tax.tax_subtotals[0].tax_category_percent == Decimal("25.0")
    
    def test_parse_payment_means(self):
        """Test parsing payment information"""
        result = parse_ehf_xml(SAMPLE_EHF_XML)
        
        payment = result.invoice.payment_means
        assert payment is not None
        assert payment.payment_id == "12345678901"  # KID
        assert payment.payee_financial_account_id == "12341234567"
    
    def test_parse_invalid_xml(self):
        """Test parsing invalid XML"""
        invalid_xml = "<Invoice>broken xml"
        result = parse_ehf_xml(invalid_xml)
        
        assert result.success is False
        assert len(result.errors) > 0
    
    def test_ehf_to_vendor_invoice_dict(self):
        """Test conversion to VendorInvoice format"""
        result = parse_ehf_xml(SAMPLE_EHF_XML)
        vendor_dict = ehf_to_vendor_invoice_dict(result.invoice)
        
        assert vendor_dict["invoice_number"] == "INV-2024-001"
        assert vendor_dict["vendor_name"] == "Test Supplier AS"
        assert vendor_dict["vendor_org_number"] == "987654321"
        assert vendor_dict["currency"] == "NOK"
        assert vendor_dict["total_amount"] == Decimal("12500.00")
        assert vendor_dict["kid_number"] == "12345678901"
        assert len(vendor_dict["line_items"]) == 1


class TestEHFValidator:
    """Test EHF validation"""
    
    def test_validate_valid_ehf(self):
        """Test validating valid EHF"""
        is_valid, messages = validate_ehf_xml(SAMPLE_EHF_XML)
        
        assert is_valid is True
        # May have warnings but no errors
        errors = [msg for msg in messages if "[ERROR]" in msg]
        assert len(errors) == 0
    
    def test_validate_missing_invoice_id(self):
        """Test validation with missing invoice ID"""
        xml_without_id = SAMPLE_EHF_XML.replace("<cbc:ID>INV-2024-001</cbc:ID>", "")
        is_valid, messages = validate_ehf_xml(xml_without_id)
        
        assert is_valid is False
        assert any("BR-01" in msg for msg in messages)
    
    def test_validate_missing_supplier(self):
        """Test validation with missing supplier"""
        xml_without_supplier = SAMPLE_EHF_XML.replace(
            "<cac:AccountingSupplierParty>", "<!-- "
        ).replace("</cac:AccountingSupplierParty>", " -->")
        is_valid, messages = validate_ehf_xml(xml_without_supplier)
        
        assert is_valid is False
    
    def test_validate_norwegian_org_number(self):
        """Test Norwegian organization number validation"""
        validator = EHFValidator()
        
        # Valid org.nr: 987654321
        assert validator._is_valid_norwegian_org_nr("987654321") is True
        
        # Invalid: wrong length
        assert validator._is_valid_norwegian_org_nr("12345") is False
        
        # Invalid: wrong checksum
        assert validator._is_valid_norwegian_org_nr("987654320") is False


class TestNorwegianVATMapping:
    """Test VAT code mapping"""
    
    def test_map_standard_25_percent(self):
        """Test mapping 25% VAT"""
        code = map_ehf_tax_to_norwegian_code("S", Decimal("25.0"))
        assert code == "5"  # Input VAT 25%
    
    def test_map_standard_15_percent(self):
        """Test mapping 15% VAT"""
        code = map_ehf_tax_to_norwegian_code("S", Decimal("15.0"))
        assert code == "51"  # Input VAT 15%
    
    def test_map_zero_rate(self):
        """Test mapping 0% VAT"""
        code = map_ehf_tax_to_norwegian_code("Z", Decimal("0.0"))
        assert code == "6"  # No VAT
    
    def test_map_exempt(self):
        """Test mapping exempt"""
        code = map_ehf_tax_to_norwegian_code("E", Decimal("0.0"))
        assert code == "6"


class TestEHFSender:
    """Test EHF XML generation"""
    
    def test_generate_ehf_xml(self):
        """Test generating EHF XML from model"""
        # Create minimal invoice
        supplier = EHFParty(
            endpoint_id="987654321",
            endpoint_scheme="0192",
            name="Test Supplier AS",
            company_id="987654321",
        )
        
        customer = EHFParty(
            endpoint_id="123456789",
            endpoint_scheme="0192",
            name="Test Customer AS",
            company_id="123456789",
        )
        
        line = EHFInvoiceLine(
            id="1",
            invoiced_quantity=Decimal("10"),
            line_extension_amount=Decimal("10000"),
            item_name="Test Product",
            price_amount=Decimal("1000"),
            tax_category_id="S",
            tax_category_percent=Decimal("25.0"),
        )
        
        tax_subtotal = EHFTaxSubtotal(
            taxable_amount=Decimal("10000"),
            tax_amount=Decimal("2500"),
            tax_category_id="S",
            tax_category_percent=Decimal("25.0"),
        )
        
        tax_total = EHFTaxTotal(
            tax_amount=Decimal("2500"),
            tax_subtotals=[tax_subtotal],
        )
        
        invoice = EHFInvoice(
            invoice_id="TEST-001",
            issue_date=date(2024, 2, 1),
            accounting_supplier_party=supplier,
            accounting_customer_party=customer,
            invoice_lines=[line],
            line_extension_amount=Decimal("10000"),
            tax_exclusive_amount=Decimal("10000"),
            tax_inclusive_amount=Decimal("12500"),
            payable_amount=Decimal("12500"),
            tax_total=tax_total,
        )
        
        # Generate XML
        sender = EHFSender(api_key="test", test_mode=True)
        xml = sender.generate_ehf_xml(invoice)
        
        # Verify it's valid XML
        root = etree.fromstring(xml.encode('utf-8'))
        assert root.tag.endswith("Invoice")
        
        # Verify key elements
        namespaces = {
            'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2',
        }
        invoice_id = root.xpath("//cbc:ID", namespaces=namespaces)
        assert invoice_id[0].text == "TEST-001"


# Integration test (requires test environment)
@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_workflow():
    """Test complete EHF workflow (parse → validate → convert)"""
    # Parse
    parse_result = parse_ehf_xml(SAMPLE_EHF_XML)
    assert parse_result.success is True
    
    # Validate
    is_valid, messages = validate_ehf_xml(SAMPLE_EHF_XML)
    assert is_valid is True
    
    # Convert to VendorInvoice format
    vendor_dict = ehf_to_vendor_invoice_dict(parse_result.invoice)
    assert vendor_dict["invoice_number"] == "INV-2024-001"
    assert vendor_dict["total_amount"] == Decimal("12500.00")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

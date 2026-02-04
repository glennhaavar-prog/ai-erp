"""
Quick test of EHF module integration
"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.ehf.parser import parse_ehf_xml

# Minimal valid EHF XML for testing
SAMPLE_EHF = """<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
         xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
         xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
    <cbc:CustomizationID>urn:cen.eu:en16931:2017#compliant#urn:fdc:peppol.eu:2017:poacc:billing:3.0</cbc:CustomizationID>
    <cbc:ProfileID>urn:fdc:peppol.eu:2017:poacc:billing:01:1.0</cbc:ProfileID>
    <cbc:ID>2024-001</cbc:ID>
    <cbc:IssueDate>2024-01-15</cbc:IssueDate>
    <cbc:DueDate>2024-02-15</cbc:DueDate>
    <cbc:InvoiceTypeCode>380</cbc:InvoiceTypeCode>
    <cbc:DocumentCurrencyCode>NOK</cbc:DocumentCurrencyCode>
    
    <cac:AccountingSupplierParty>
        <cac:Party>
            <cac:PartyName>
                <cbc:Name>Test Leverandør AS</cbc:Name>
            </cac:PartyName>
            <cac:PartyIdentification>
                <cbc:ID schemeID="0192">987654321</cbc:ID>
            </cac:PartyIdentification>
        </cac:Party>
    </cac:AccountingSupplierParty>
    
    <cac:AccountingCustomerParty>
        <cac:Party>
            <cac:PartyName>
                <cbc:Name>Test Kunde AS</cbc:Name>
            </cac:PartyName>
        </cac:Party>
    </cac:AccountingCustomerParty>
    
    <cac:LegalMonetaryTotal>
        <cbc:LineExtensionAmount currencyID="NOK">10000.00</cbc:LineExtensionAmount>
        <cbc:TaxExclusiveAmount currencyID="NOK">10000.00</cbc:TaxExclusiveAmount>
        <cbc:TaxInclusiveAmount currencyID="NOK">12500.00</cbc:TaxInclusiveAmount>
        <cbc:PayableAmount currencyID="NOK">12500.00</cbc:PayableAmount>
    </cac:LegalMonetaryTotal>
    
    <cac:InvoiceLine>
        <cbc:ID>1</cbc:ID>
        <cbc:InvoicedQuantity unitCode="EA">1</cbc:InvoicedQuantity>
        <cbc:LineExtensionAmount currencyID="NOK">10000.00</cbc:LineExtensionAmount>
        <cac:Item>
            <cbc:Name>Test Vare</cbc:Name>
        </cac:Item>
        <cac:Price>
            <cbc:PriceAmount currencyID="NOK">10000.00</cbc:PriceAmount>
        </cac:Price>
    </cac:InvoiceLine>
</Invoice>"""

def test_parse():
    """Test basic EHF parsing"""
    print("🧪 Testing EHF module integration...")
    print()
    
    try:
        result = parse_ehf_xml(SAMPLE_EHF)
        
        if result.success:
            print("✅ Parse successful!")
            print(f"   Invoice ID: {result.invoice.invoice_id}")
            print(f"   Supplier: {result.invoice.accounting_supplier_party.name}")
            print(f"   Amount: {result.invoice.payable_amount} {result.invoice.document_currency_code}")
            print(f"   Lines: {len(result.invoice.invoice_lines)}")
            print()
            print("✅ EHF module integration working!")
            return True
        else:
            print("❌ Parse failed!")
            print(f"   Errors: {result.errors}")
            return False
            
    except Exception as e:
        print(f"❌ Exception occurred: {type(e).__name__}")
        print(f"   Message: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_parse()
    sys.exit(0 if success else 1)

"""
EHF 3.0 Pydantic Models
Based on PEPPOL BIS Billing 3.0 (UBL 2.1)

These models represent the structure of Norwegian EHF invoices.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, validator


class EHFParty(BaseModel):
    """Party information (supplier or customer)"""
    endpoint_id: str = Field(..., description="PEPPOL endpoint ID (org number)")
    endpoint_scheme: str = Field(default="0192", description="Norway org.nr = 0192")
    name: str = Field(..., description="Company name")
    
    # Address
    street_name: Optional[str] = None
    city_name: Optional[str] = None
    postal_zone: Optional[str] = None
    country_code: str = Field(default="NO", description="ISO country code")
    
    # Contact
    contact_name: Optional[str] = None
    telephone: Optional[str] = None
    email: Optional[str] = None
    
    # Tax
    company_id: Optional[str] = Field(None, description="Organization number")
    vat_id: Optional[str] = Field(None, description="MVA number")


class EHFTaxSubtotal(BaseModel):
    """Tax breakdown per rate"""
    taxable_amount: Decimal = Field(..., description="Amount before tax")
    tax_amount: Decimal = Field(..., description="Tax amount")
    tax_category_id: str = Field(..., description="Tax category (S=Standard, Z=Zero, E=Exempt)")
    tax_category_percent: Decimal = Field(..., description="Tax rate percentage")


class EHFTaxTotal(BaseModel):
    """Total tax information"""
    tax_amount: Decimal = Field(..., description="Total tax amount")
    tax_subtotals: List[EHFTaxSubtotal] = Field(default_factory=list)


class EHFInvoiceLine(BaseModel):
    """Individual invoice line"""
    id: str = Field(..., description="Line number")
    
    # Quantity
    invoiced_quantity: Decimal = Field(..., description="Quantity")
    invoiced_quantity_unit_code: str = Field(default="EA", description="Unit code (EA=each, HUR=hour)")
    
    # Amounts
    line_extension_amount: Decimal = Field(..., description="Line total (excl. VAT)")
    
    # Item
    item_name: str = Field(..., description="Product/service description")
    item_description: Optional[str] = None
    
    # Price
    price_amount: Decimal = Field(..., description="Unit price")
    base_quantity: Decimal = Field(default=Decimal("1.0"))
    
    # Tax
    tax_category_id: str = Field(..., description="S/Z/E")
    tax_category_percent: Decimal = Field(..., description="VAT percentage")
    
    # Optional
    accounting_cost: Optional[str] = Field(None, description="Cost center or project")


class EHFPaymentMeans(BaseModel):
    """Payment information"""
    payment_means_code: str = Field(..., description="30=bank transfer, 31=debit transfer")
    payment_id: Optional[str] = Field(None, description="KID number")
    
    # Bank account
    payee_financial_account_id: Optional[str] = Field(None, description="Bank account number")
    payee_financial_account_name: Optional[str] = None
    financial_institution_branch_id: Optional[str] = Field(None, description="BIC/SWIFT")


class EHFInvoice(BaseModel):
    """
    Complete EHF 3.0 Invoice
    Based on PEPPOL BIS Billing 3.0
    """
    
    # Header
    customization_id: str = Field(
        default="urn:cen.eu:en16931:2017#compliant#urn:fdc:peppol.eu:2017:poacc:billing:3.0",
        description="PEPPOL specification"
    )
    profile_id: str = Field(
        default="urn:fdc:peppol.eu:2017:poacc:billing:01:1.0",
        description="PEPPOL profile"
    )
    
    # Invoice identification
    invoice_id: str = Field(..., description="Invoice number")
    issue_date: date = Field(..., description="Invoice date")
    due_date: Optional[date] = Field(None, description="Payment due date")
    invoice_type_code: str = Field(default="380", description="380=Invoice, 381=Credit note")
    
    # Currency
    document_currency_code: str = Field(default="NOK", description="ISO currency code")
    tax_currency_code: Optional[str] = Field(None, description="Tax currency if different")
    
    # Parties
    accounting_supplier_party: EHFParty = Field(..., description="Supplier/vendor")
    accounting_customer_party: EHFParty = Field(..., description="Customer")
    
    # Payment
    payment_means: Optional[EHFPaymentMeans] = None
    payment_terms_note: Optional[str] = Field(None, description="Payment terms text")
    
    # Lines
    invoice_lines: List[EHFInvoiceLine] = Field(..., min_items=1)
    
    # Totals
    line_extension_amount: Decimal = Field(..., description="Sum of all lines (excl. VAT)")
    tax_exclusive_amount: Decimal = Field(..., description="Total excl. VAT")
    tax_inclusive_amount: Decimal = Field(..., description="Total incl. VAT")
    payable_amount: Decimal = Field(..., description="Amount to pay")
    
    # Tax
    tax_total: EHFTaxTotal = Field(..., description="Tax breakdown")
    
    # Optional
    order_reference: Optional[str] = Field(None, description="PO number")
    contract_document_reference: Optional[str] = Field(None, description="Contract reference")
    note: Optional[str] = Field(None, description="General note")
    
    @validator('tax_inclusive_amount')
    def validate_total(cls, v, values):
        """Verify that tax_inclusive = tax_exclusive + tax"""
        if 'tax_exclusive_amount' in values and 'tax_total' in values:
            expected = values['tax_exclusive_amount'] + values['tax_total'].tax_amount
            if abs(v - expected) > Decimal("0.01"):  # Allow 1 øre rounding difference
                raise ValueError(f"Tax inclusive amount {v} doesn't match calculated {expected}")
        return v
    
    @validator('payable_amount')
    def validate_payable(cls, v, values):
        """Verify payable amount"""
        if 'tax_inclusive_amount' in values:
            if abs(v - values['tax_inclusive_amount']) > Decimal("0.01"):
                raise ValueError(f"Payable amount {v} doesn't match tax inclusive {values['tax_inclusive_amount']}")
        return v


class EHFCreditNote(EHFInvoice):
    """
    Credit Note (negative invoice)
    Inherits from EHFInvoice with invoice_type_code = 381
    """
    invoice_type_code: str = Field(default="381", description="381=Credit note")


# For parsing results
class EHFParseResult(BaseModel):
    """Result from parsing EHF XML"""
    success: bool
    invoice: Optional[EHFInvoice] = None
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    raw_xml: Optional[str] = None


# For vendor invoice mapping
class VendorInvoiceFromEHF(BaseModel):
    """
    Mapping from EHF to our VendorInvoice model
    This is what we'll save to database
    """
    # From EHF
    invoice_number: str
    invoice_date: date
    due_date: Optional[date]
    
    # Vendor info (for matching/creating vendor)
    vendor_org_number: str
    vendor_name: str
    vendor_address: Optional[str]
    vendor_city: Optional[str]
    vendor_postal_code: Optional[str]
    vendor_bank_account: Optional[str]
    
    # Amounts
    currency: str
    amount_excl_vat: Decimal
    vat_amount: Decimal
    total_amount: Decimal
    
    # Payment
    kid_number: Optional[str]
    payment_terms: Optional[str]
    
    # Lines (as JSON)
    line_items: List[dict]  # Will be stored as JSONB
    
    # Tax breakdown (as JSON)
    tax_breakdown: List[dict]
    
    # Metadata
    ehf_message_id: Optional[str]
    ehf_received_at: datetime
    ehf_raw_xml: str


# Norwegian VAT codes mapping
NORWEGIAN_VAT_CODES = {
    "S": {  # Standard rate
        "25.0": "5",   # 25% = code 5 (inngående høy sats)
        "15.0": "51",  # 15% = code 51 (inngående middels sats)
        "12.0": "52",  # 12% = code 52 (inngående lav sats)
    },
    "Z": {  # Zero rate
        "0.0": "6",    # 0% = code 6 (ingen MVA-plikt)
    },
    "E": {  # Exempt
        "0.0": "6",    # Exempt = code 6
    }
}


def map_ehf_tax_to_norwegian_code(tax_category: str, tax_percent: Decimal) -> str:
    """
    Map EHF tax category and percentage to Norwegian MVA code
    
    Args:
        tax_category: S (Standard), Z (Zero), E (Exempt)
        tax_percent: Tax percentage (e.g. 25.0)
        
    Returns:
        Norwegian VAT code (e.g. "5" for 25% input VAT)
    """
    category_map = NORWEGIAN_VAT_CODES.get(tax_category, {})
    return category_map.get(str(float(tax_percent)), "6")  # Default to code 6 if unknown

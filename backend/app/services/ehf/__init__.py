"""
EHF Service Module
EHF 3.0 (PEPPOL BIS Billing 3.0) integration for Norwegian invoices
"""

from .models import (
    EHFInvoice,
    EHFCreditNote,
    EHFParty,
    EHFInvoiceLine,
    EHFTaxTotal,
    EHFTaxSubtotal,
    EHFPaymentMeans,
    EHFParseResult,
    VendorInvoiceFromEHF,
    map_ehf_tax_to_norwegian_code,
)

from .parser import (
    parse_ehf_xml,
    ehf_to_vendor_invoice_dict,
)

from .validator import (
    EHFValidator,
    validate_ehf_xml,
)

from .receiver import (
    EHFReceiver,
    receive_ehf_invoice,
)

from .sender import (
    EHFSender,
    send_invoice_ehf,
)

__version__ = "1.0.0"

__all__ = [
    # Models
    "EHFInvoice",
    "EHFCreditNote",
    "EHFParty",
    "EHFInvoiceLine",
    "EHFTaxTotal",
    "EHFTaxSubtotal",
    "EHFPaymentMeans",
    "EHFParseResult",
    "VendorInvoiceFromEHF",
    "map_ehf_tax_to_norwegian_code",
    
    # Parser
    "parse_ehf_xml",
    "ehf_to_vendor_invoice_dict",
    
    # Validator
    "EHFValidator",
    "validate_ehf_xml",
    
    # Receiver
    "EHFReceiver",
    "receive_ehf_invoice",
    
    # Sender
    "EHFSender",
    "send_invoice_ehf",
]

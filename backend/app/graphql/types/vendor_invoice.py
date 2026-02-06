"""
GraphQL VendorInvoice Type
"""
import strawberry
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal


@strawberry.type
class VendorInvoice:
    """VendorInvoice GraphQL Type (Leverandørfaktura)"""
    id: strawberry.ID
    client_id: strawberry.ID
    vendor_id: Optional[strawberry.ID]
    
    # Invoice details
    invoice_number: str
    invoice_date: date
    due_date: date
    
    # Amounts
    amount_excl_vat: Decimal
    vat_amount: Decimal
    total_amount: Decimal
    currency: str
    
    # EHF data
    ehf_message_id: Optional[str]
    ehf_received_at: Optional[datetime]
    
    # Document
    document_id: Optional[strawberry.ID]
    
    # Booking
    general_ledger_id: Optional[strawberry.ID]
    booked_at: Optional[datetime]
    
    # Payment
    payment_status: str
    paid_amount: Decimal
    payment_date: Optional[date]
    
    # AI processing
    ai_processed: bool
    ai_confidence_score: Optional[int]
    ai_detected_category: Optional[str]
    ai_reasoning: Optional[str]
    
    # Review
    review_status: str
    reviewed_by_user_id: Optional[strawberry.ID]
    reviewed_at: Optional[datetime]
    
    # Timestamps
    created_at: datetime
    updated_at: datetime

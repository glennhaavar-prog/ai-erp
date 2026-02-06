"""
GraphQL Vendor Type
"""
import strawberry
from typing import Optional
from datetime import datetime
from decimal import Decimal


@strawberry.type
class Vendor:
    """Vendor GraphQL Type (Leverandør)"""
    id: strawberry.ID
    client_id: strawberry.ID
    vendor_number: str
    name: str
    org_number: Optional[str]
    contact_person: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    account_number: str
    payment_terms: str
    default_vat_code: Optional[str]
    bank_account: Optional[str]
    iban: Optional[str]
    swift_bic: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    # AI learned fields (optional to expose)
    # ai_average_amount: Optional[Decimal]

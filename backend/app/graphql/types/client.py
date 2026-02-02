"""
GraphQL Client Type
"""
import strawberry
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


@strawberry.enum
class AutomationLevel:
    """AI automation level"""
    FULL = "full"
    ASSISTED = "assisted"
    MANUAL = "manual"


@strawberry.type
class Client:
    """Client GraphQL Type"""
    id: strawberry.ID
    tenant_id: strawberry.ID
    client_number: str
    name: str
    org_number: str
    
    # Fiscal setup
    fiscal_year_start: int
    accounting_method: str
    vat_term: str
    base_currency: str
    
    # AI settings
    ai_automation_level: AutomationLevel
    ai_confidence_threshold: int
    
    # Status
    status: str
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    
    # Computed fields
    @strawberry.field
    def total_invoices(self) -> int:
        """Total number of invoices for this client"""
        # TODO: Implement database query
        return 0
    
    @strawberry.field
    def auto_booked_percentage(self) -> float:
        """Percentage of invoices auto-booked by AI"""
        # TODO: Implement database query
        return 0.0
    
    @strawberry.field
    def pending_review_count(self) -> int:
        """Number of items pending review"""
        # TODO: Implement database query
        return 0


@strawberry.input
class ClientInput:
    """Input type for creating/updating clients"""
    name: str
    org_number: str
    base_currency: str = "NOK"
    ai_automation_level: AutomationLevel = AutomationLevel.ASSISTED
    ai_confidence_threshold: int = 85
    fiscal_year_start: int = 1
    accounting_method: str = "accrual"
    vat_term: str = "bimonthly"

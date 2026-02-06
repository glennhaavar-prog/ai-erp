"""
GraphQL Tenant Type
"""
import strawberry
from typing import Optional, List
from datetime import datetime
from enum import Enum


@strawberry.enum
class SubscriptionTier(str, Enum):
    """Subscription tiers for tenants"""
    BASIC = "basic"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


@strawberry.type
class Tenant:
    """Tenant GraphQL Type (Regnskapsbyrå)"""
    id: strawberry.ID
    name: str
    org_number: str
    subscription_tier: SubscriptionTier
    max_clients: Optional[int]
    billing_email: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    # Relationships (lazy-loaded)
    # clients: List["Client"] - Can be added later if needed
    # users: List["User"] - Can be added later if needed

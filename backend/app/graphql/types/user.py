"""
GraphQL User Type
"""
import strawberry
from typing import Optional, List
from datetime import datetime


@strawberry.type
class User:
    """User GraphQL Type (Regnskapsfører)"""
    id: strawberry.ID
    tenant_id: strawberry.ID
    email: str
    name: str
    role: str
    is_active: bool
    bankid_verified: bool
    created_at: datetime
    last_login: Optional[datetime]
    
    # Note: hashed_password is NOT exposed via GraphQL for security
    # Note: assigned_clients can be added later if needed

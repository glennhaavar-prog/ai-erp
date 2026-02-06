"""
GraphQL ReviewQueue Type
"""
import strawberry
from typing import Optional
from datetime import datetime
from enum import Enum


@strawberry.enum
class ReviewPriority(str, Enum):
    """Priority levels for review items"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


@strawberry.enum
class ReviewStatus(str, Enum):
    """Status of review item"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    APPROVED = "approved"
    CORRECTED = "corrected"
    REJECTED = "rejected"


@strawberry.enum
class IssueCategory(str, Enum):
    """Category of issue that needs review"""
    LOW_CONFIDENCE = "low_confidence"
    UNKNOWN_VENDOR = "unknown_vendor"
    UNUSUAL_AMOUNT = "unusual_amount"
    MISSING_VAT = "missing_vat"
    UNCLEAR_DESCRIPTION = "unclear_description"
    DUPLICATE_INVOICE = "duplicate_invoice"
    PROCESSING_ERROR = "processing_error"
    MANUAL_REVIEW_REQUIRED = "manual_review_required"


@strawberry.type
class ReviewQueue:
    """ReviewQueue GraphQL Type"""
    id: strawberry.ID
    client_id: strawberry.ID
    
    # Source
    source_type: str
    source_id: strawberry.ID
    
    # Priority & Status
    priority: ReviewPriority
    status: ReviewStatus
    
    # Issue
    issue_category: IssueCategory
    issue_description: str
    
    # AI
    ai_confidence: Optional[int]
    ai_reasoning: Optional[str]
    
    # Assignment
    assigned_to_user_id: Optional[strawberry.ID]
    assigned_at: Optional[datetime]
    
    # Resolution
    resolved_by_user_id: Optional[strawberry.ID]
    resolved_at: Optional[datetime]
    resolution_notes: Optional[str]
    
    # Learning
    apply_to_similar: bool
    similar_items_affected: int
    
    # Timestamps
    created_at: datetime
    updated_at: datetime

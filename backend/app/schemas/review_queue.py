"""
Pydantic schemas for Review Queue API
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID


class InvoiceReviewDTO(BaseModel):
    """Review Queue Item DTO for list view"""
    id: str
    vendor_name: str
    invoice_number: str
    amount: Decimal
    invoice_date: date
    ai_suggested_account: Optional[str] = None
    confidence_score: float = Field(ge=0.0, le=1.0)
    review_status: str
    priority: str
    created_at: datetime
    client_id: Optional[str] = None
    client_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class InvoiceReviewDetailDTO(BaseModel):
    """Detailed Review Queue Item for single view"""
    id: str
    vendor_name: str
    vendor_org_number: Optional[str] = None
    invoice_number: str
    invoice_date: date
    due_date: Optional[date] = None
    amount: Decimal
    amount_excl_vat: Decimal
    vat_amount: Decimal
    currency: str = "NOK"
    ai_suggested_account: Optional[str] = None
    ai_suggestion: Optional[Dict[str, Any]] = None
    confidence_score: float = Field(ge=0.0, le=1.0)
    ai_reasoning: Optional[str] = None
    review_status: str
    priority: str
    issue_category: Optional[str] = None
    issue_description: Optional[str] = None
    created_at: datetime
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None
    resolution_notes: Optional[str] = None
    client_id: Optional[str] = None
    client_name: Optional[str] = None
    document_url: Optional[str] = None
    
    class Config:
        from_attributes = True


class ApprovalRequest(BaseModel):
    """Request to approve an invoice"""
    approved_by: str
    notes: Optional[str] = None


class ApprovalResponse(BaseModel):
    """Response after approving an invoice"""
    success: bool
    voucher_id: Optional[str] = None
    general_ledger_id: Optional[str] = None
    voucher_number: Optional[str] = None
    message: str


class RejectionRequest(BaseModel):
    """Request to reject an invoice"""
    rejected_by: str
    reason: str


class RejectionResponse(BaseModel):
    """Response after rejecting an invoice"""
    success: bool
    message: str


class StatusUpdateRequest(BaseModel):
    """Request to update review status"""
    status: str
    updated_by: str
    notes: Optional[str] = None
    
    @validator('status')
    def validate_status(cls, v):
        valid_statuses = ['pending', 'in_progress', 'approved', 'rejected', 'needs_review']
        if v not in valid_statuses:
            raise ValueError(f'Status must be one of {valid_statuses}')
        return v


class StatusUpdateResponse(BaseModel):
    """Response after updating status"""
    success: bool
    message: str
    new_status: str


class ReviewQueueListRequest(BaseModel):
    """Request parameters for listing review queue items"""
    status: Optional[str] = None
    client_id: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=100)


class ReviewQueueListResponse(BaseModel):
    """Response for review queue list"""
    items: List[InvoiceReviewDTO]
    total: int
    page: int
    page_size: int
    total_pages: int


class ConfidenceBreakdown(BaseModel):
    """Confidence score breakdown"""
    vendor_familiarity: float
    vat_validation: float
    amount_reasonableness: float
    historical_similarity: float
    account_consistency: float


class ConfidenceScoreResponse(BaseModel):
    """Response with confidence score details"""
    invoice_id: str
    confidence_score: float
    breakdown: ConfidenceBreakdown
    reasoning: str
    should_auto_approve: bool

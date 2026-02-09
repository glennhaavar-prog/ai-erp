"""
Review Queue Service - Business logic for review queue operations
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, date
from uuid import UUID
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, update
from sqlalchemy.orm import selectinload
from fastapi import HTTPException

from app.models.review_queue import ReviewQueue, ReviewStatus, ReviewPriority, IssueCategory
from app.models.vendor_invoice import VendorInvoice
from app.models.vendor import Vendor
from app.models.client import Client
from app.schemas.review_queue import (
    InvoiceReviewDTO, InvoiceReviewDetailDTO, ApprovalResponse,
    RejectionResponse, ConfidenceScoreResponse
)

logger = logging.getLogger(__name__)


class ReviewQueueService:
    """Service for managing review queue operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    @staticmethod
    def _parse_user_uuid(user_id: str) -> Optional[UUID]:
        """
        Safely parse user_id to UUID. Returns None if not valid UUID.
        Allows descriptive user identifiers like "accountant_001", "system", etc.
        """
        try:
            return UUID(user_id)
        except (ValueError, AttributeError):
            return None
    
    async def get_pending_reviews(
        self,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[InvoiceReviewDTO]:
        """
        Get all pending review items with optional filters
        
        Args:
            filters: Optional dict with keys:
                - status: review status filter
                - client_id: client UUID filter
                - date_from: start date filter
                - date_to: end date filter
                - page: page number (default 1)
                - page_size: items per page (default 50)
        
        Returns:
            List of InvoiceReviewDTO objects
        """
        filters = filters or {}
        
        # Build query
        query = select(ReviewQueue, VendorInvoice, Vendor, Client).join(
            VendorInvoice,
            ReviewQueue.source_id == VendorInvoice.id
        ).outerjoin(
            Vendor,
            VendorInvoice.vendor_id == Vendor.id
        ).outerjoin(
            Client,
            ReviewQueue.client_id == Client.id
        ).where(
            ReviewQueue.source_type == 'vendor_invoice'
        )
        
        # Apply filters
        if filters.get('status'):
            try:
                status_enum = ReviewStatus(filters['status'].upper())
                query = query.where(ReviewQueue.status == status_enum)
            except ValueError:
                logger.warning(f"Invalid status filter: {filters['status']}")
        
        if filters.get('client_id'):
            try:
                client_uuid = UUID(filters['client_id'])
                query = query.where(ReviewQueue.client_id == client_uuid)
            except ValueError:
                logger.warning(f"Invalid client_id: {filters['client_id']}")
        
        if filters.get('date_from'):
            query = query.where(VendorInvoice.invoice_date >= filters['date_from'])
        
        if filters.get('date_to'):
            query = query.where(VendorInvoice.invoice_date <= filters['date_to'])
        
        # Order by priority and creation date
        query = query.order_by(
            ReviewQueue.priority.desc(),
            ReviewQueue.created_at.desc()
        )
        
        # Pagination
        page = filters.get('page', 1)
        page_size = filters.get('page_size', 50)
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        # Execute query
        result = await self.db.execute(query)
        rows = result.all()
        
        # Convert to DTOs
        items = []
        for review, invoice, vendor, client in rows:
            items.append(InvoiceReviewDTO(
                id=str(review.id),
                vendor_name=vendor.name if vendor else "Unknown Vendor",
                invoice_number=invoice.invoice_number,
                amount=invoice.total_amount,
                invoice_date=invoice.invoice_date,
                ai_suggested_account=self._extract_suggested_account(review.ai_suggestion),
                confidence_score=float(review.ai_confidence or 0) / 100.0,
                review_status=review.status.value,
                priority=review.priority.value,
                created_at=review.created_at,
                client_id=str(review.client_id) if review.client_id else None,
                client_name=client.name if client else None
            ))
        
        return items
    
    async def get_review_detail(self, invoice_id: str) -> InvoiceReviewDetailDTO:
        """
        Get detailed information about a review queue item
        
        Args:
            invoice_id: UUID of the review queue item
        
        Returns:
            InvoiceReviewDetailDTO with all details
        
        Raises:
            HTTPException: If review item not found
        """
        try:
            review_uuid = UUID(invoice_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid UUID format")
        
        query = select(ReviewQueue, VendorInvoice, Vendor, Client).join(
            VendorInvoice,
            ReviewQueue.source_id == VendorInvoice.id
        ).outerjoin(
            Vendor,
            VendorInvoice.vendor_id == Vendor.id
        ).outerjoin(
            Client,
            ReviewQueue.client_id == Client.id
        ).where(
            and_(
                ReviewQueue.id == review_uuid,
                ReviewQueue.source_type == 'vendor_invoice'
            )
        )
        
        result = await self.db.execute(query)
        row = result.first()
        
        if not row:
            raise HTTPException(status_code=404, detail="Review item not found")
        
        review, invoice, vendor, client = row
        
        return InvoiceReviewDetailDTO(
            id=str(review.id),
            vendor_name=vendor.name if vendor else "Unknown Vendor",
            vendor_org_number=vendor.org_number if vendor else None,
            invoice_number=invoice.invoice_number,
            invoice_date=invoice.invoice_date,
            due_date=invoice.due_date,
            amount=invoice.total_amount,
            amount_excl_vat=invoice.amount_excl_vat,
            vat_amount=invoice.vat_amount,
            currency=invoice.currency,
            ai_suggested_account=self._extract_suggested_account(review.ai_suggestion),
            ai_suggestion=review.ai_suggestion,
            confidence_score=float(review.ai_confidence or 0) / 100.0,
            ai_reasoning=review.ai_reasoning,
            review_status=review.status.value,
            priority=review.priority.value,
            issue_category=review.issue_category.value if review.issue_category else None,
            issue_description=review.issue_description,
            created_at=review.created_at,
            reviewed_at=review.resolved_at,
            reviewed_by=str(review.resolved_by_user_id) if review.resolved_by_user_id else None,
            resolution_notes=review.resolution_notes,
            client_id=str(review.client_id) if review.client_id else None,
            client_name=client.name if client else None,
            document_url=f"/api/v1/documents/{invoice.document_id}" if invoice.document_id else None
        )
    
    async def approve_invoice(
        self,
        invoice_id: str,
        user_id: str,
        notes: Optional[str] = None
    ) -> ApprovalResponse:
        """
        Approve a review queue item and trigger voucher creation
        
        Args:
            invoice_id: UUID of the review queue item
            user_id: UUID or descriptive string of the user approving
            notes: Optional approval notes
        
        Returns:
            ApprovalResponse with success status and voucher info
        
        Raises:
            HTTPException: If validation fails or booking fails
        """
        try:
            review_uuid = UUID(invoice_id)
            user_uuid = self._parse_user_uuid(user_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid UUID format")
        
        # Get review item
        query = select(ReviewQueue, VendorInvoice).join(
            VendorInvoice,
            ReviewQueue.source_id == VendorInvoice.id
        ).where(
            and_(
                ReviewQueue.id == review_uuid,
                ReviewQueue.source_type == 'vendor_invoice'
            )
        )
        
        result = await self.db.execute(query)
        row = result.first()
        
        if not row:
            raise HTTPException(status_code=404, detail="Review item not found")
        
        review, invoice = row
        
        # Check if already processed
        if review.status != ReviewStatus.PENDING:
            raise HTTPException(
                status_code=400,
                detail=f"Invoice already {review.status.value}"
            )
        
        # Create voucher using VoucherGenerator (Sprint 1 new flow)
        voucher_id = None
        voucher_number = None
        general_ledger_id = None
        
        try:
            from app.services.voucher_service import VoucherGenerator
            
            voucher_generator = VoucherGenerator(self.db)
            voucher_dto = await voucher_generator.create_voucher_from_invoice(
                invoice_id=review.source_id,
                tenant_id=invoice.client_id,
                user_id=user_id if user_uuid is None else str(user_uuid),
                accounting_date=None,
                override_account=None
            )
            
            voucher_id = voucher_dto.id
            voucher_number = voucher_dto.voucher_number
            # Note: general_ledger_id not set yet (vouchers don't link to GL in Sprint 1 MVP)
            
        except Exception as e:
            logger.error(f"Error creating voucher: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Voucher creation failed: {str(e)}"
            )
        
        # Update review status
        review.status = ReviewStatus.APPROVED
        review.resolved_at = datetime.utcnow()
        review.resolved_by_user_id = user_uuid
        review.resolution_notes = notes
        
        # Update invoice status
        invoice.review_status = 'approved'
        invoice.reviewed_at = datetime.utcnow()
        invoice.reviewed_by_user_id = user_uuid
        
        # Commit transaction (atomic)
        try:
            await self.db.commit()
            await self.db.refresh(review)
            await self.db.refresh(invoice)
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error committing approval: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save approval: {str(e)}"
            )
        
        logger.info(f"Invoice {invoice_id} approved by user {user_id}")
        
        return ApprovalResponse(
            success=True,
            voucher_id=voucher_id,
            general_ledger_id=general_ledger_id,
            voucher_number=voucher_number,
            message="Invoice approved and voucher created successfully"
        )
    
    async def reject_invoice(
        self,
        invoice_id: str,
        user_id: str,
        reason: str
    ) -> RejectionResponse:
        """
        Reject a review queue item
        
        Args:
            invoice_id: UUID of the review queue item
            user_id: UUID or descriptive string of the user rejecting
            reason: Rejection reason (required)
        
        Returns:
            RejectionResponse with success status
        
        Raises:
            HTTPException: If validation fails
        """
        try:
            review_uuid = UUID(invoice_id)
            user_uuid = self._parse_user_uuid(user_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid UUID format")
        
        # Get review item
        query = select(ReviewQueue, VendorInvoice).join(
            VendorInvoice,
            ReviewQueue.source_id == VendorInvoice.id
        ).where(
            and_(
                ReviewQueue.id == review_uuid,
                ReviewQueue.source_type == 'vendor_invoice'
            )
        )
        
        result = await self.db.execute(query)
        row = result.first()
        
        if not row:
            raise HTTPException(status_code=404, detail="Review item not found")
        
        review, invoice = row
        
        # Check if already processed
        if review.status != ReviewStatus.PENDING:
            raise HTTPException(
                status_code=400,
                detail=f"Invoice already {review.status.value}"
            )
        
        # Update review status
        review.status = ReviewStatus.REJECTED
        review.resolved_at = datetime.utcnow()
        review.resolved_by_user_id = user_uuid
        review.resolution_notes = reason
        
        # Update invoice status
        invoice.review_status = 'rejected'
        invoice.reviewed_at = datetime.utcnow()
        invoice.reviewed_by_user_id = user_uuid
        
        # Commit transaction
        try:
            await self.db.commit()
            await self.db.refresh(review)
            await self.db.refresh(invoice)
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error committing rejection: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save rejection: {str(e)}"
            )
        
        logger.info(f"Invoice {invoice_id} rejected by user {user_id}: {reason}")
        
        return RejectionResponse(
            success=True,
            message="Invoice rejected successfully"
        )
    
    async def update_confidence_score(
        self,
        invoice_id: str,
        score: float
    ) -> ConfidenceScoreResponse:
        """
        Update confidence score for a review queue item
        
        Args:
            invoice_id: UUID of the review queue item
            score: New confidence score (0-100)
        
        Returns:
            ConfidenceScoreResponse with updated score details
        
        Raises:
            HTTPException: If validation fails
        """
        try:
            review_uuid = UUID(invoice_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid UUID format")
        
        if not 0 <= score <= 100:
            raise HTTPException(
                status_code=400,
                detail="Confidence score must be between 0 and 100"
            )
        
        # Get review item
        query = select(ReviewQueue).where(ReviewQueue.id == review_uuid)
        result = await self.db.execute(query)
        review = result.scalar_one_or_none()
        
        if not review:
            raise HTTPException(status_code=404, detail="Review item not found")
        
        # Update confidence
        review.ai_confidence = int(score)
        
        # Adjust priority based on new confidence
        if score >= 85:
            review.priority = ReviewPriority.LOW
        elif score >= 60:
            review.priority = ReviewPriority.MEDIUM
        else:
            review.priority = ReviewPriority.HIGH
        
        await self.db.commit()
        await self.db.refresh(review)
        
        logger.info(f"Updated confidence score for {invoice_id} to {score}%")
        
        # Return response (breakdown not recalculated in this simple update)
        from app.schemas.review_queue import ConfidenceBreakdown
        
        return ConfidenceScoreResponse(
            invoice_id=str(review.id),
            confidence_score=float(score) / 100.0,
            breakdown=ConfidenceBreakdown(
                vendor_familiarity=0.0,
                vat_validation=0.0,
                amount_reasonableness=0.0,
                historical_similarity=0.0,
                account_consistency=0.0
            ),
            reasoning=review.ai_reasoning or "Manual confidence update",
            should_auto_approve=score >= 85
        )
    
    async def update_status(
        self,
        invoice_id: str,
        new_status: str,
        user_id: str,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update review status (for re-open, escalate, etc.)
        
        Args:
            invoice_id: UUID of the review queue item
            new_status: New status string
            user_id: UUID or descriptive string of the user updating
            notes: Optional notes
        
        Returns:
            Dict with success status and message
        
        Raises:
            HTTPException: If validation fails
        """
        try:
            review_uuid = UUID(invoice_id)
            user_uuid = self._parse_user_uuid(user_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid UUID format")
        
        # Validate status
        try:
            status_enum = ReviewStatus(new_status.upper())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status: {new_status}"
            )
        
        # Get review item
        query = select(ReviewQueue).where(ReviewQueue.id == review_uuid)
        result = await self.db.execute(query)
        review = result.scalar_one_or_none()
        
        if not review:
            raise HTTPException(status_code=404, detail="Review item not found")
        
        # Update status
        old_status = review.status
        review.status = status_enum
        
        # Update resolution info if moving to resolved state
        if status_enum in [ReviewStatus.APPROVED, ReviewStatus.REJECTED]:
            review.resolved_at = datetime.utcnow()
            review.resolved_by_user_id = user_uuid
            if notes:
                review.resolution_notes = notes
        
        await self.db.commit()
        await self.db.refresh(review)
        
        logger.info(f"Updated status for {invoice_id} from {old_status.value} to {new_status}")
        
        return {
            'success': True,
            'message': f"Status updated from {old_status.value} to {new_status}",
            'new_status': new_status
        }
    
    def _extract_suggested_account(self, ai_suggestion: Optional[Dict[str, Any]]) -> Optional[str]:
        """Extract main account from AI suggestion"""
        if not ai_suggestion:
            return None
        
        lines = ai_suggestion.get('lines', [])
        if not lines:
            return None
        
        # Find debit line (usually the expense account)
        for line in lines:
            if line.get('debit', 0) > 0:
                return str(line.get('account_number', ''))
        
        return str(lines[0].get('account_number', '')) if lines else None


async def get_review_queue_stats(
    db: AsyncSession,
    client_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get statistics about the review queue
    
    Args:
        db: Database session
        client_id: Optional client filter
    
    Returns:
        Dict with queue statistics
    """
    filters = []
    if client_id:
        try:
            client_uuid = UUID(client_id)
            filters.append(ReviewQueue.client_id == client_uuid)
        except ValueError:
            pass
    
    # Count by status
    pending_query = select(func.count(ReviewQueue.id)).where(
        and_(ReviewQueue.status == ReviewStatus.PENDING, *filters) if filters
        else ReviewQueue.status == ReviewStatus.PENDING
    )
    pending_result = await db.execute(pending_query)
    pending_count = pending_result.scalar() or 0
    
    approved_query = select(func.count(ReviewQueue.id)).where(
        and_(ReviewQueue.status == ReviewStatus.APPROVED, *filters) if filters
        else ReviewQueue.status == ReviewStatus.APPROVED
    )
    approved_result = await db.execute(approved_query)
    approved_count = approved_result.scalar() or 0
    
    rejected_query = select(func.count(ReviewQueue.id)).where(
        and_(ReviewQueue.status == ReviewStatus.REJECTED, *filters) if filters
        else ReviewQueue.status == ReviewStatus.REJECTED
    )
    rejected_result = await db.execute(rejected_query)
    rejected_count = rejected_result.scalar() or 0
    
    # Average confidence
    avg_confidence_query = select(func.avg(ReviewQueue.ai_confidence)).where(
        ReviewQueue.ai_confidence.isnot(None)
    )
    if filters:
        avg_confidence_query = avg_confidence_query.where(and_(*filters))
    
    avg_confidence_result = await db.execute(avg_confidence_query)
    avg_confidence = avg_confidence_result.scalar() or 0
    
    total_resolved = approved_count + rejected_count
    
    return {
        'pending': pending_count,
        'approved': approved_count,
        'rejected': rejected_count,
        'total_resolved': total_resolved,
        'average_confidence': round(float(avg_confidence), 2),
        'approval_rate': round(approved_count / total_resolved * 100, 2) if total_resolved > 0 else 0,
        'rejection_rate': round(rejected_count / total_resolved * 100, 2) if total_resolved > 0 else 0
    }

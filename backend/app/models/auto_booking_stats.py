"""
Auto Booking Statistics Model
Tracks performance metrics for auto-booking agent (critical for Skattefunn reporting)
"""
from sqlalchemy import (
    Column, String, Integer, DateTime, ForeignKey, Numeric, Date
)
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from decimal import Decimal
import uuid

from app.database import Base


class AutoBookingStats(Base):
    """
    Auto Booking Statistics - Track performance metrics
    
    Critical for Skattefunn AP1+AP2:
    - Success rate must be 95%+ 
    - Track false positive rate
    - Track escalation rate to review queue
    """
    __tablename__ = "auto_booking_stats"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Multi-tenant
    client_id = Column(
        UUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=True,  # NULL = global stats across all clients
        index=True
    )
    
    # Time Period
    period_date = Column(Date, nullable=False, index=True)  # Daily stats
    period_type = Column(String(20), default="daily", nullable=False)  # daily/weekly/monthly
    
    # Processing Metrics
    invoices_processed = Column(Integer, default=0, nullable=False)
    invoices_auto_booked = Column(Integer, default=0, nullable=False)
    invoices_to_review = Column(Integer, default=0, nullable=False)
    invoices_failed = Column(Integer, default=0, nullable=False)
    
    # Success Metrics (calculated)
    success_rate = Column(Numeric(5, 2), default=Decimal("0.00"), nullable=False)  # Percentage
    escalation_rate = Column(Numeric(5, 2), default=Decimal("0.00"), nullable=False)  # Percentage to review
    failure_rate = Column(Numeric(5, 2), default=Decimal("0.00"), nullable=False)  # Percentage failed
    
    # Confidence Metrics
    avg_confidence_auto_booked = Column(Numeric(5, 2), nullable=True)  # Average confidence of auto-booked
    avg_confidence_escalated = Column(Numeric(5, 2), nullable=True)  # Average confidence of escalated
    
    # False Positive Tracking (after human review)
    # False positive = auto-booked but human later corrects
    false_positives = Column(Integer, default=0, nullable=False)
    false_positive_rate = Column(Numeric(5, 2), default=Decimal("0.00"), nullable=False)
    
    # Pattern Learning Metrics
    patterns_applied = Column(Integer, default=0, nullable=False)
    patterns_created = Column(Integer, default=0, nullable=False)
    
    # Performance Metrics
    total_amount_processed = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    total_amount_auto_booked = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    avg_processing_time_seconds = Column(Numeric(8, 2), nullable=True)
    
    # Breakdown by issue category (JSON)
    escalation_reasons = Column(JSON, nullable=True)  # {'low_confidence': 5, 'unknown_vendor': 3, ...}
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    # Relationships
    client = relationship("Client")
    
    def __repr__(self):
        return (
            f"<AutoBookingStats(period={self.period_date}, "
            f"success_rate={self.success_rate}%, processed={self.invoices_processed})>"
        )
    
    def calculate_rates(self):
        """Calculate success, escalation, and failure rates"""
        if self.invoices_processed > 0:
            self.success_rate = Decimal(
                (self.invoices_auto_booked / self.invoices_processed) * 100
            ).quantize(Decimal("0.01"))
            
            self.escalation_rate = Decimal(
                (self.invoices_to_review / self.invoices_processed) * 100
            ).quantize(Decimal("0.01"))
            
            self.failure_rate = Decimal(
                (self.invoices_failed / self.invoices_processed) * 100
            ).quantize(Decimal("0.01"))
            
            if self.invoices_auto_booked > 0:
                self.false_positive_rate = Decimal(
                    (self.false_positives / self.invoices_auto_booked) * 100
                ).quantize(Decimal("0.01"))
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "client_id": str(self.client_id) if self.client_id else None,
            "period_date": self.period_date.isoformat(),
            "period_type": self.period_type,
            "invoices_processed": self.invoices_processed,
            "invoices_auto_booked": self.invoices_auto_booked,
            "invoices_to_review": self.invoices_to_review,
            "invoices_failed": self.invoices_failed,
            "success_rate": float(self.success_rate),
            "escalation_rate": float(self.escalation_rate),
            "failure_rate": float(self.failure_rate),
            "false_positives": self.false_positives,
            "false_positive_rate": float(self.false_positive_rate),
            "avg_confidence_auto_booked": float(self.avg_confidence_auto_booked) if self.avg_confidence_auto_booked else None,
            "avg_confidence_escalated": float(self.avg_confidence_escalated) if self.avg_confidence_escalated else None,
            "patterns_applied": self.patterns_applied,
            "patterns_created": self.patterns_created,
            "total_amount_processed": float(self.total_amount_processed),
            "total_amount_auto_booked": float(self.total_amount_auto_booked),
            "escalation_reasons": self.escalation_reasons,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

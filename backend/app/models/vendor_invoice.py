"""
Vendor Invoice model - Leverandørfakturaer
"""
from sqlalchemy import (
    Column, String, DateTime, ForeignKey, Numeric, Boolean,
    Text, JSON, Date, Integer
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from datetime import datetime, date
from decimal import Decimal
import uuid

from app.database import Base


class VendorInvoice(Base):
    """
    Vendor Invoice = Leverandørfaktura (incoming invoices)
    
    Supports both EHF (electronic) and PDF invoices.
    Stores AI analysis and booking suggestions.
    """
    __tablename__ = "vendor_invoices"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Multi-tenant
    client_id = Column(
        UUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    
    # Vendor
    vendor_id = Column(
        UUID(as_uuid=True),
        ForeignKey("vendors.id", ondelete="RESTRICT"),
        nullable=True,  # Can be NULL if vendor not yet created
        index=True
    )
    
    # Invoice Details
    invoice_number = Column(String(100), nullable=False, index=True)
    invoice_date = Column(Date, nullable=False, index=True)
    due_date = Column(Date, nullable=False, index=True)
    
    # Amounts
    amount_excl_vat = Column(Numeric(15, 2), nullable=False)
    vat_amount = Column(Numeric(15, 2), nullable=False)
    total_amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default="NOK")
    
    # EHF Data (if electronic invoice)
    ehf_message_id = Column(String(255), nullable=True, index=True)
    ehf_raw_xml = Column(Text, nullable=True)  # Store complete EHF XML
    ehf_received_at = Column(DateTime, nullable=True)
    
    # Document Storage
    document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("documents.id"),
        nullable=True
    )
    
    # Booking (link to general ledger)
    general_ledger_id = Column(
        UUID(as_uuid=True),
        ForeignKey("general_ledger.id"),
        nullable=True
    )
    booked_at = Column(DateTime, nullable=True)
    
    # Payment Tracking
    payment_status = Column(
        String(20),
        default="unpaid",
        nullable=False
    )  # unpaid/partial/paid/overdue
    paid_amount = Column(Numeric(15, 2), default=Decimal("0.00"))
    payment_date = Column(Date, nullable=True)
    
    # AI Processing
    ai_processed = Column(Boolean, default=False)
    ai_confidence_score = Column(Integer, nullable=True)  # 0-100
    ai_booking_suggestion = Column(JSON, nullable=True)  # Suggested GL lines
    ai_detected_category = Column(String(100), nullable=True)
    ai_detected_issues = Column(ARRAY(String), default=list)
    ai_reasoning = Column(Text, nullable=True)
    
    # Review Status
    review_status = Column(
        String(20),
        default="pending",
        nullable=False
    )  # pending/auto_approved/needs_review/reviewed/rejected
    reviewed_by_user_id = Column(UUID(as_uuid=True), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    # Relationships
    client = relationship("Client", back_populates="vendor_invoices")
    vendor = relationship("Vendor", back_populates="invoices")
    document = relationship("Document")
    general_ledger_entry = relationship("GeneralLedger")
    ai_matched_transactions = relationship("BankTransaction", foreign_keys="[BankTransaction.ai_matched_invoice_id]", back_populates="ai_matched_invoice")
    accruals = relationship("Accrual", back_populates="source_invoice")
    
    def __repr__(self):
        return (
            f"<VendorInvoice(id={self.id}, invoice_number='{self.invoice_number}', "
            f"total={self.total_amount})>"
        )
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "client_id": str(self.client_id),
            "vendor_id": str(self.vendor_id) if self.vendor_id else None,
            "invoice_number": self.invoice_number,
            "invoice_date": self.invoice_date.isoformat(),
            "due_date": self.due_date.isoformat(),
            "amount_excl_vat": float(self.amount_excl_vat),
            "vat_amount": float(self.vat_amount),
            "total_amount": float(self.total_amount),
            "currency": self.currency,
            "payment_status": self.payment_status,
            "review_status": self.review_status,
            "ai_confidence_score": self.ai_confidence_score,
            "created_at": self.created_at.isoformat(),
        }

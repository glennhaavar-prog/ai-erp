"""
Bank Connection model - OAuth2 tokens and account links for DNB Open Banking
"""
from sqlalchemy import (
    Column, String, DateTime, Boolean, Integer, ForeignKey, Text, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class BankConnection(Base):
    """
    Bank Connection = OAuth2 connection to DNB Open Banking API
    
    Stores encrypted OAuth tokens and account mappings for automatic
    transaction import via PSD2/Open Banking.
    """
    __tablename__ = "bank_connections"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Client relationship
    client_id = Column(
        UUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Bank Details
    bank_name = Column(String(100), default="DNB", nullable=False)
    bank_account_number = Column(String(20), nullable=False, index=True)  # Norwegian account
    bank_account_id = Column(String(100), nullable=False)  # DNB API account ID
    account_name = Column(String(255), nullable=True)
    
    # OAuth2 Tokens (encrypted)
    access_token = Column(Text, nullable=False)  # Encrypted access token
    refresh_token = Column(Text, nullable=True)  # Encrypted refresh token
    token_expires_at = Column(DateTime, nullable=False)
    
    # OAuth2 Metadata
    scope = Column(String(500), nullable=True)
    token_type = Column(String(50), default="Bearer", nullable=False)
    
    # Consent Management
    consent_id = Column(String(100), nullable=True)  # PSD2 consent ID
    consent_expires_at = Column(DateTime, nullable=True)
    consent_status = Column(String(50), nullable=True)  # authorized, expired, revoked
    
    # Sync Configuration
    auto_sync_enabled = Column(Boolean, default=True, nullable=False)
    sync_frequency_hours = Column(Integer, default=24, nullable=False)  # How often to sync
    last_sync_at = Column(DateTime, nullable=True)
    last_sync_status = Column(String(50), nullable=True)  # success, error
    last_sync_error = Column(Text, nullable=True)
    
    # Transaction History
    oldest_transaction_date = Column(DateTime, nullable=True)  # First transaction fetched
    newest_transaction_date = Column(DateTime, nullable=True)  # Last transaction fetched
    total_transactions_imported = Column(Integer, default=0, nullable=False)
    
    # API Rate Limiting
    last_api_call = Column(DateTime, nullable=True)
    api_calls_today = Column(Integer, default=0, nullable=False)
    rate_limit_reset = Column(DateTime, nullable=True)
    
    # Additional data
    extra_data = Column(JSON, nullable=True)  # Store additional bank-specific data
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    connection_status = Column(String(50), default="active", nullable=False)  # active, expired, error
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    # Relationships
    client = relationship("Client", back_populates="bank_connections")
    
    def __repr__(self):
        return f"<BankConnection(id={self.id}, client_id={self.client_id}, bank={self.bank_name}, account={self.bank_account_number})>"
    
    def to_dict(self):
        """Convert to dictionary (without sensitive tokens)"""
        return {
            "id": str(self.id),
            "client_id": str(self.client_id),
            "bank_name": self.bank_name,
            "bank_account_number": self.bank_account_number,
            "account_name": self.account_name,
            "auto_sync_enabled": self.auto_sync_enabled,
            "sync_frequency_hours": self.sync_frequency_hours,
            "last_sync_at": self.last_sync_at.isoformat() if self.last_sync_at else None,
            "last_sync_status": self.last_sync_status,
            "total_transactions_imported": self.total_transactions_imported,
            "connection_status": self.connection_status,
            "consent_expires_at": self.consent_expires_at.isoformat() if self.consent_expires_at else None,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
        }

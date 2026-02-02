"""
Document model - PDF/XML lagring i S3
"""
from sqlalchemy import (
    Column, String, Integer, DateTime, ForeignKey, Boolean, BigInteger
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class Document(Base):
    """
    Document = PDF/XML/file storage metadata
    
    Actual files are stored in AWS S3, this table tracks metadata
    """
    __tablename__ = "documents"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Multi-tenant
    client_id = Column(
        UUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # S3 Storage
    s3_bucket = Column(String(255), nullable=False)
    s3_key = Column(String(1024), nullable=False, index=True)  # Full S3 path
    s3_version_id = Column(String(255), nullable=True)  # For versioned buckets
    
    # File Information
    filename = Column(String(255), nullable=False)
    mime_type = Column(String(100), nullable=False)  # application/pdf etc
    file_size = Column(BigInteger, nullable=False)  # Bytes
    file_hash = Column(String(64), nullable=True, index=True)  # SHA-256 hash for deduplication
    
    # Document Type
    document_type = Column(String(50), nullable=False)  # invoice_pdf/ehf_xml/receipt etc
    
    # OCR Data (if applicable)
    ocr_text = Column(String, nullable=True)  # Extracted text from OCR
    ocr_processed = Column(Boolean, default=False)
    ocr_processed_at = Column(DateTime, nullable=True)
    
    # Access Control
    is_public = Column(Boolean, default=False)
    download_url = Column(String(1024), nullable=True)  # Pre-signed URL (temporary)
    download_url_expires_at = Column(DateTime, nullable=True)
    
    # Timestamps
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    uploaded_by_user_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Relationships
    client = relationship("Client")
    
    def __repr__(self):
        return f"<Document(id={self.id}, filename='{self.filename}', type={self.document_type})>"
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "client_id": str(self.client_id),
            "filename": self.filename,
            "mime_type": self.mime_type,
            "file_size": self.file_size,
            "document_type": self.document_type,
            "download_url": self.download_url,
            "uploaded_at": self.uploaded_at.isoformat(),
        }

"""
Documents API - PDF/file retrieval
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import select
from uuid import UUID
import boto3
from botocore.exceptions import ClientError
from datetime import datetime, timedelta

from app.database import get_db
from app.models.document import Document
from app.models.vendor_invoice import VendorInvoice
from app.config import settings


router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.get("/{document_id}/url")
async def get_document_url(
    document_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get pre-signed URL for document download
    Returns a temporary URL valid for 1 hour
    """
    # Get document from database
    stmt = select(Document).where(Document.id == document_id)
    result = db.execute(stmt)
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # For demo: if no S3 data, return placeholder
    if not document.s3_bucket or not document.s3_key:
        return JSONResponse({
            "document_id": str(document.id),
            "filename": document.filename,
            "download_url": None,
            "expires_at": None,
            "demo_mode": True,
            "message": "PDF preview not available - document not in S3 storage"
        })
    
    try:
        # Generate pre-signed URL (valid for 1 hour)
        s3_client = boto3.client('s3', region_name='eu-west-1')
        presigned_url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': document.s3_bucket,
                'Key': document.s3_key
            },
            ExpiresIn=3600  # 1 hour
        )
        
        expires_at = datetime.utcnow() + timedelta(hours=1)
        
        # Update document record with URL and expiry
        document.download_url = presigned_url
        document.download_url_expires_at = expires_at
        db.commit()
        
        return JSONResponse({
            "document_id": str(document.id),
            "filename": document.filename,
            "mime_type": document.mime_type,
            "file_size": document.file_size,
            "download_url": presigned_url,
            "expires_at": expires_at.isoformat(),
            "demo_mode": False
        })
        
    except ClientError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating download URL: {str(e)}"
        )


@router.get("/invoice/{invoice_id}/pdf")
async def get_invoice_pdf_url(
    invoice_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get PDF URL for a specific invoice
    Shortcut endpoint that resolves invoice → document → URL
    """
    # Get invoice
    stmt = select(VendorInvoice).where(VendorInvoice.id == invoice_id)
    result = db.execute(stmt)
    invoice = result.scalar_one_or_none()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    if not invoice.document_id:
        return JSONResponse({
            "invoice_id": str(invoice.id),
            "invoice_number": invoice.invoice_number,
            "has_pdf": False,
            "message": "No PDF document attached to this invoice"
        })
    
    # Get document
    stmt = select(Document).where(Document.id == invoice.document_id)
    result = db.execute(stmt)
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Use the main document URL endpoint logic
    return await get_document_url(document.id, db)


@router.get("/{document_id}/info")
async def get_document_info(
    document_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get document metadata (without generating download URL)
    """
    stmt = select(Document).where(Document.id == document_id)
    result = db.execute(stmt)
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return JSONResponse({
        "id": str(document.id),
        "filename": document.filename,
        "mime_type": document.mime_type,
        "file_size": document.file_size,
        "document_type": document.document_type,
        "uploaded_at": document.uploaded_at.isoformat() if document.uploaded_at else None,
        "has_s3_storage": bool(document.s3_bucket and document.s3_key),
        "ocr_processed": document.ocr_processed
    })

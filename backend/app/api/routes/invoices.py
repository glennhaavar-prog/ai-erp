"""
Invoice Upload API - Manual vendor invoice upload
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID, uuid4
from datetime import datetime
import boto3
from botocore.exceptions import ClientError
import hashlib
import logging

from app.database import get_db
from app.config import settings
from app.models.document import Document
from app.models.vendor_invoice import VendorInvoice
from app.models.review_queue import ReviewQueue, ReviewStatus, ReviewPriority, IssueCategory
from app.services.ocr_service import OCRService
from app.agents.invoice_agent import InvoiceAgent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/invoices", tags=["invoices"])


@router.post("/upload/")
async def upload_invoice(
    file: UploadFile = File(...),
    client_id: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload vendor invoice PDF and process automatically
    
    Flow:
    1. Validate PDF file
    2. Upload to S3 (kontali-erp-documents-eu-west-1)
    3. Trigger OCR (AWS Textract)
    4. Trigger AI analysis (Claude)
    5. Insert into review_queue
    6. Return response
    
    Args:
        file: PDF file (multipart/form-data)
        client_id: UUID of client
    
    Returns:
        {
            'success': True,
            'invoice_id': 'uuid',
            'document_id': 'uuid',
            's3_url': 's3://bucket/key',
            'status': 'pending_review',
            'confidence_score': 85,
            'ai_suggestion': {...}
        }
    """
    try:
        # 1. Validate file
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail="Only PDF files are supported"
            )
        
        # Validate client_id
        try:
            client_uuid = UUID(client_id)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid client_id format"
            )
        
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)
        
        if file_size > 10 * 1024 * 1024:  # 10 MB limit
            raise HTTPException(
                status_code=400,
                detail="File size exceeds 10 MB limit"
            )
        
        # Calculate file hash for deduplication
        file_hash = hashlib.sha256(file_content).hexdigest()
        
        logger.info(
            f"Uploading invoice PDF: {file.filename} ({file_size} bytes) "
            f"for client {client_id}"
        )
        
        # 2. Upload to S3
        s3_client = boto3.client(
            's3',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY,
            aws_secret_access_key=settings.AWS_SECRET_KEY
        )
        
        bucket_name = settings.S3_BUCKET_DOCUMENTS
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        s3_key = f"invoices/{client_id}/{timestamp}_{file.filename}"
        
        try:
            s3_client.put_object(
                Bucket=bucket_name,
                Key=s3_key,
                Body=file_content,
                ContentType='application/pdf',
                Metadata={
                    'client_id': client_id,
                    'original_filename': file.filename,
                    'uploaded_at': datetime.utcnow().isoformat()
                }
            )
            logger.info(f"Uploaded to S3: s3://{bucket_name}/{s3_key}")
        except ClientError as e:
            logger.error(f"S3 upload failed: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to upload file to S3: {str(e)}"
            )
        
        # 3. Create Document record
        document = Document(
            id=uuid4(),
            client_id=client_uuid,
            s3_bucket=bucket_name,
            s3_key=s3_key,
            filename=file.filename,
            mime_type='application/pdf',
            file_size=file_size,
            file_hash=file_hash,
            document_type='invoice_pdf',
            ocr_processed=False,
            uploaded_at=datetime.utcnow()
        )
        
        db.add(document)
        await db.flush()  # Get document.id without committing yet
        
        logger.info(f"Created Document record: {document.id}")
        
        # 4. Trigger OCR (AWS Textract)
        ocr_service = OCRService()
        ocr_result = await ocr_service.extract_text_from_s3(
            bucket=bucket_name,
            key=s3_key
        )
        
        if not ocr_result['success']:
            logger.error(f"OCR failed: {ocr_result.get('error')}")
            # Continue anyway - we can process without OCR
            ocr_text = ""
        else:
            ocr_text = ocr_result['text']
            logger.info(f"OCR extracted {len(ocr_text)} characters")
            
            # Update document with OCR text
            document.ocr_text = ocr_text
            document.ocr_processed = True
            document.ocr_processed_at = datetime.utcnow()
        
        # 5. Trigger AI analysis (Claude)
        invoice_agent = InvoiceAgent()
        
        try:
            ai_analysis = await invoice_agent.analyze_invoice(
                ocr_text=ocr_text,
                client_id=client_id,
                vendor_history=None,  # TODO: Look up vendor history
                learned_patterns=None  # TODO: Fetch learned patterns
            )
            
            confidence_score = ai_analysis.get('confidence_score', 0)
            logger.info(f"AI analysis completed. Confidence: {confidence_score}%")
            
        except Exception as e:
            logger.error(f"AI analysis failed: {str(e)}", exc_info=True)
            ai_analysis = {
                'error': f"AI analysis failed: {str(e)}",
                'confidence_score': 0,
                'reasoning': 'Could not analyze invoice due to error'
            }
            confidence_score = 0
        
        # 6. Create VendorInvoice record
        vendor_data = ai_analysis.get('vendor', {})
        
        # Extract invoice details from AI analysis
        invoice = VendorInvoice(
            id=uuid4(),
            client_id=client_uuid,
            vendor_id=None,  # TODO: Match or create vendor
            invoice_number=ai_analysis.get('invoice_number', 'UNKNOWN'),
            invoice_date=datetime.fromisoformat(ai_analysis['invoice_date']).date() 
                if ai_analysis.get('invoice_date') else datetime.utcnow().date(),
            due_date=datetime.fromisoformat(ai_analysis['due_date']).date()
                if ai_analysis.get('due_date') else datetime.utcnow().date(),
            amount_excl_vat=ai_analysis.get('amount_excl_vat', 0),
            vat_amount=ai_analysis.get('vat_amount', 0),
            total_amount=ai_analysis.get('total_amount', 0),
            currency=ai_analysis.get('currency', 'NOK'),
            document_id=document.id,
            ai_processed=True,
            ai_confidence_score=confidence_score,
            ai_booking_suggestion=ai_analysis.get('suggested_booking'),
            ai_reasoning=ai_analysis.get('reasoning'),
            review_status='pending',
            created_at=datetime.utcnow()
        )
        
        db.add(invoice)
        await db.flush()  # Get invoice.id
        
        logger.info(f"Created VendorInvoice record: {invoice.id}")
        
        # 7. Insert into review_queue
        # Determine priority based on confidence
        if confidence_score < 50:
            priority = ReviewPriority.HIGH
        elif confidence_score < 70:
            priority = ReviewPriority.MEDIUM
        else:
            priority = ReviewPriority.LOW
        
        issue_description = f"""
Manual opplastet faktura fra {vendor_data.get('name', 'Ukjent leverandør')}.

AI er {confidence_score}% sikker på bokføringsforslaget.

Årsak: {ai_analysis.get('reasoning', 'Vennligst gjennomgå og godkjenn.')}
"""
        
        review_item = ReviewQueue(
            id=uuid4(),
            client_id=client_uuid,
            source_type='vendor_invoice',
            source_id=invoice.id,
            priority=priority,
            status=ReviewStatus.PENDING,
            issue_category=IssueCategory.LOW_CONFIDENCE if confidence_score < 70 
                else IssueCategory.MANUAL_REVIEW_REQUIRED,
            issue_description=issue_description.strip(),
            ai_suggestion=ai_analysis,
            ai_confidence=confidence_score,
            ai_reasoning=ai_analysis.get('reasoning'),
            created_at=datetime.utcnow()
        )
        
        db.add(review_item)
        
        # Commit all changes
        await db.commit()
        await db.refresh(invoice)
        await db.refresh(document)
        await db.refresh(review_item)
        
        logger.info(
            f"✅ Invoice upload complete! "
            f"Invoice: {invoice.id}, Review Queue: {review_item.id}"
        )
        
        # 8. Return response
        return JSONResponse({
            'success': True,
            'invoice_id': str(invoice.id),
            'document_id': str(document.id),
            'review_queue_id': str(review_item.id),
            's3_url': f"s3://{bucket_name}/{s3_key}",
            's3_bucket': bucket_name,
            's3_key': s3_key,
            'status': 'pending_review',
            'confidence_score': confidence_score,
            'ai_suggestion': ai_analysis.get('suggested_booking'),
            'vendor': vendor_data,
            'invoice_details': {
                'invoice_number': invoice.invoice_number,
                'invoice_date': invoice.invoice_date.isoformat(),
                'due_date': invoice.due_date.isoformat(),
                'total_amount': float(invoice.total_amount),
                'currency': invoice.currency
            },
            'message': 'Invoice uploaded and added to review queue successfully'
        })
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process invoice upload: {str(e)}"
        )


@router.get("/")
async def list_invoices(
    client_id: str = None,
    status: str = None,
    db: AsyncSession = Depends(get_db)
):
    """
    List vendor invoices
    
    Query params:
    - client_id: Filter by client
    - status: Filter by review status (pending/approved/rejected)
    """
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    
    query = select(VendorInvoice).options(
        selectinload(VendorInvoice.vendor)
    )
    
    if client_id:
        query = query.where(VendorInvoice.client_id == UUID(client_id))
    
    if status:
        query = query.where(VendorInvoice.review_status == status)
    
    query = query.order_by(VendorInvoice.created_at.desc())
    
    result = await db.execute(query)
    invoices = result.scalars().all()
    
    return [
        {
            'id': str(inv.id),
            'invoice_number': inv.invoice_number,
            'invoice_date': inv.invoice_date.isoformat() if inv.invoice_date else None,
            'total_amount': float(inv.total_amount),
            'currency': inv.currency,
            'vendor_name': inv.vendor.name if inv.vendor else 'Unknown',
            'review_status': inv.review_status,
            'ai_confidence_score': inv.ai_confidence_score,
            'created_at': inv.created_at.isoformat()
        }
        for inv in invoices
    ]


@router.get("/{invoice_id}")
async def get_invoice(
    invoice_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get single invoice with full details"""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    
    query = select(VendorInvoice).where(
        VendorInvoice.id == UUID(invoice_id)
    ).options(
        selectinload(VendorInvoice.vendor),
        selectinload(VendorInvoice.document)
    )
    
    result = await db.execute(query)
    invoice = result.scalar_one_or_none()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    return {
        'id': str(invoice.id),
        'client_id': str(invoice.client_id),
        'invoice_number': invoice.invoice_number,
        'invoice_date': invoice.invoice_date.isoformat() if invoice.invoice_date else None,
        'due_date': invoice.due_date.isoformat() if invoice.due_date else None,
        'amount_excl_vat': float(invoice.amount_excl_vat),
        'vat_amount': float(invoice.vat_amount),
        'total_amount': float(invoice.total_amount),
        'currency': invoice.currency,
        'vendor': {
            'id': str(invoice.vendor.id) if invoice.vendor else None,
            'name': invoice.vendor.name if invoice.vendor else 'Unknown',
            'org_number': invoice.vendor.org_number if invoice.vendor else None
        } if invoice.vendor else None,
        'document': {
            'id': str(invoice.document.id) if invoice.document else None,
            'filename': invoice.document.filename if invoice.document else None,
            's3_bucket': invoice.document.s3_bucket if invoice.document else None,
            's3_key': invoice.document.s3_key if invoice.document else None
        } if invoice.document else None,
        'review_status': invoice.review_status,
        'ai_confidence_score': invoice.ai_confidence_score,
        'ai_booking_suggestion': invoice.ai_booking_suggestion,
        'ai_reasoning': invoice.ai_reasoning,
        'created_at': invoice.created_at.isoformat()
    }

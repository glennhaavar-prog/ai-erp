"""
AI Features API Endpoints

Endpoints for:
1. Smart Expense Categorization
2. Anomaly Detection
3. Smart Reconciliation
4. Payment Terms Extraction
5. Contextual Help
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime
from pydantic import BaseModel

from app.database import get_db
from app.services.ai_categorization_service import (
    AICategorizationService,
    suggest_account_for_invoice
)
from app.services.anomaly_detection_service import (
    AnomalyDetectionService,
    detect_invoice_anomalies,
    get_risk_score
)
from app.services.smart_reconciliation_service import (
    SmartReconciliationService,
    find_transaction_matches,
    auto_reconcile_transactions
)
from app.services.payment_terms_extractor import (
    PaymentTermsExtractor,
    extract_invoice_payment_terms
)
from app.services.contextual_help_service import (
    ContextualHelpService,
    get_field_help,
    get_all_page_help
)

router = APIRouter(prefix="/api/ai", tags=["AI Features"])


# ============================================
# 1. SMART EXPENSE CATEGORIZATION
# ============================================

@router.get("/categorization/suggest/{invoice_id}")
async def get_account_suggestions(
    invoice_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get account categorization suggestions for an invoice
    
    Returns list of suggested accounts with confidence scores
    """
    try:
        suggestions = await suggest_account_for_invoice(db, invoice_id)
        return {
            "invoice_id": str(invoice_id),
            "suggestions": suggestions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/categorization/learn/{invoice_id}")
async def learn_from_booking(
    invoice_id: uuid.UUID,
    booked_account: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Learn from a confirmed booking
    
    Stores pattern for future suggestions
    """
    try:
        from app.models import VendorInvoice
        from sqlalchemy import select
        
        result = await db.execute(
            select(VendorInvoice).where(VendorInvoice.id == invoice_id)
        )
        invoice = result.scalar_one_or_none()
        
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        service = AICategorizationService(db)
        await service.learn_from_booking(invoice, booked_account)
        
        return {
            "success": True,
            "message": "Pattern learned successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/categorization/update/{invoice_id}")
async def update_invoice_categorization(
    invoice_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Update invoice with AI categorization
    
    Analyzes and stores suggestions in invoice
    """
    try:
        service = AICategorizationService(db)
        result = await service.update_invoice_suggestion(invoice_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="Invoice not found or no suggestions")
        
        return {
            "invoice_id": str(invoice_id),
            "suggestion": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# 2. ANOMALY DETECTION
# ============================================

@router.get("/anomalies/detect/{invoice_id}")
async def detect_anomalies(
    invoice_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Detect anomalies for an invoice
    
    Returns list of detected anomalies with severity
    """
    try:
        flags = await detect_invoice_anomalies(db, invoice_id)
        return {
            "invoice_id": str(invoice_id),
            "anomalies": flags,
            "count": len(flags)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/anomalies/risk-score/{invoice_id}")
async def get_invoice_risk_score(
    invoice_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get risk assessment for an invoice
    
    Returns risk score (0-100) and recommendation
    """
    try:
        risk_assessment = await get_risk_score(db, invoice_id)
        return risk_assessment
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/anomalies/high-risk")
async def get_high_risk_invoices(
    client_id: uuid.UUID,
    min_risk_score: int = Query(60, ge=0, le=100),
    limit: int = Query(50, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of high-risk invoices for a client
    
    Returns invoices with anomalies above threshold
    """
    try:
        from app.models import VendorInvoice
        from sqlalchemy import select, and_
        
        # Get recent unreviewed invoices
        result = await db.execute(
            select(VendorInvoice).where(
                and_(
                    VendorInvoice.client_id == client_id,
                    VendorInvoice.review_status.in_(['pending', 'needs_review']),
                    VendorInvoice.ai_detected_issues != []
                )
            ).limit(limit)
        )
        invoices = result.scalars().all()
        
        # Calculate risk score for each
        high_risk = []
        service = AnomalyDetectionService(db)
        
        for invoice in invoices:
            risk = await service.get_invoice_risk_score(invoice.id)
            if risk['risk_score'] >= min_risk_score:
                high_risk.append({
                    "invoice_id": str(invoice.id),
                    "invoice_number": invoice.invoice_number,
                    "vendor_id": str(invoice.vendor_id) if invoice.vendor_id else None,
                    "total_amount": float(invoice.total_amount),
                    "risk_score": risk['risk_score'],
                    "risk_level": risk['risk_level'],
                    "flags": risk['flags']
                })
        
        # Sort by risk score (highest first)
        high_risk.sort(key=lambda x: x['risk_score'], reverse=True)
        
        return {
            "client_id": str(client_id),
            "high_risk_invoices": high_risk,
            "count": len(high_risk)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# 3. SMART RECONCILIATION
# ============================================

@router.get("/reconciliation/matches/{transaction_id}")
async def get_transaction_matches(
    transaction_id: uuid.UUID,
    limit: int = Query(5, le=20),
    db: AsyncSession = Depends(get_db)
):
    """
    Find potential matches for a bank transaction
    
    Returns sorted list of matches with confidence scores
    """
    try:
        matches = await find_transaction_matches(db, transaction_id, limit)
        return {
            "transaction_id": str(transaction_id),
            "matches": matches,
            "count": len(matches)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reconciliation/apply-match")
async def apply_reconciliation_match(
    transaction_id: uuid.UUID,
    matched_entity_type: str,
    matched_entity_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Apply a reconciliation match
    
    Updates transaction and invoice status
    """
    try:
        from app.services.smart_reconciliation_service import ReconciliationMatch
        
        # Create match object
        match = ReconciliationMatch(
            bank_transaction_id=transaction_id,
            matched_entity_type=matched_entity_type,
            matched_entity_id=matched_entity_id,
            confidence=100,  # Manual match
            match_reason="Manually confirmed"
        )
        
        service = SmartReconciliationService(db)
        success = await service.apply_match(match)
        
        if not success:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        return {
            "success": True,
            "message": "Match applied successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reconciliation/auto-reconcile/{client_id}")
async def auto_reconcile(
    client_id: uuid.UUID,
    confidence_threshold: int = Query(90, ge=70, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Auto-reconcile all unmatched transactions above confidence threshold
    
    Returns summary of matches made
    """
    try:
        result = await auto_reconcile_transactions(db, client_id, confidence_threshold)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# 4. PAYMENT TERMS EXTRACTION
# ============================================

@router.post("/payment-terms/extract/{invoice_id}")
async def extract_payment_terms(
    invoice_id: uuid.UUID,
    ocr_text: Optional[str] = None,
    use_ai_fallback: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """
    Extract payment terms from invoice
    
    Uses regex + AI to parse terms like "30 dager netto"
    """
    try:
        result = await extract_invoice_payment_terms(db, invoice_id, ocr_text)
        return {
            "invoice_id": str(invoice_id),
            "payment_terms": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/payment-terms/bulk-update/{client_id}")
async def bulk_update_payment_terms(
    client_id: uuid.UUID,
    limit: int = Query(100, le=500),
    db: AsyncSession = Depends(get_db)
):
    """
    Bulk update payment terms for invoices without them
    
    Returns summary of updates
    """
    try:
        service = PaymentTermsExtractor(db)
        result = await service.bulk_update_payment_terms(client_id, limit)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# 5. CONTEXTUAL HELP
# ============================================

@router.get("/help/{page}/{field}")
async def get_help_text(
    page: str,
    field: str,
    user_role: str = Query("client", regex="^(accountant|client|all)$"),
    language: str = Query("nb", regex="^(nb|en)$"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get contextual help text for a field
    
    Returns help text with examples
    """
    try:
        help_text = await get_field_help(db, page, field, user_role)
        
        if not help_text:
            # Generate if not found
            service = ContextualHelpService(db)
            help_text = await service.generate_help_text(
                page, field, user_role, language
            )
        
        if not help_text:
            raise HTTPException(status_code=404, detail="Help text not found")
        
        return help_text
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/help/{page}")
async def get_page_help_texts(
    page: str,
    user_role: str = Query("client", regex="^(accountant|client|all)$"),
    language: str = Query("nb", regex="^(nb|en)$"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all help texts for a page
    
    Returns dict of field → help text
    """
    try:
        help_texts = await get_all_page_help(db, page, user_role)
        return {
            "page": page,
            "user_role": user_role,
            "language": language,
            "help_texts": help_texts
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/help/generate")
async def generate_help_text(
    page: str,
    field: str,
    field_label: Optional[str] = None,
    user_role: str = "client",
    language: str = "nb",
    db: AsyncSession = Depends(get_db)
):
    """
    Generate new help text using AI
    
    Stores result in database
    """
    try:
        service = ContextualHelpService(db)
        result = await service.generate_help_text(
            page, field, user_role, language, field_label
        )
        
        if not result:
            raise HTTPException(status_code=500, detail="Failed to generate help text")
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# COMBINED ENDPOINT FOR INVOICE PROCESSING
# ============================================

@router.post("/process-invoice/{invoice_id}")
async def process_invoice_with_ai(
    invoice_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Process invoice with ALL AI features
    
    1. Categorization
    2. Anomaly detection
    3. Payment terms extraction
    
    Returns combined results
    """
    try:
        results = {}
        
        # 1. Categorization
        categorization_service = AICategorizationService(db)
        categorization = await categorization_service.update_invoice_suggestion(invoice_id)
        results['categorization'] = categorization
        
        # 2. Anomaly detection
        anomalies = await detect_invoice_anomalies(db, invoice_id)
        risk = await get_risk_score(db, invoice_id)
        results['anomalies'] = {
            "flags": anomalies,
            "risk_assessment": risk
        }
        
        # 3. Payment terms (if OCR text available)
        # This would normally be called when OCR completes
        # results['payment_terms'] = await extract_invoice_payment_terms(db, invoice_id)
        
        return {
            "invoice_id": str(invoice_id),
            "ai_processing_results": results,
            "processed_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Health check endpoint
@router.get("/health")
async def ai_features_health():
    """
    Health check for AI features
    """
    return {
        "status": "healthy",
        "features": [
            "smart_categorization",
            "anomaly_detection",
            "smart_reconciliation",
            "payment_terms_extraction",
            "contextual_help"
        ]
    }

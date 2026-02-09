"""
Trust Dashboard API - Transparency & Control for Accountants

Provides visibility into system status and proof that nothing is missed.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.trust_dashboard_service import TrustDashboardService

router = APIRouter(prefix="/api/trust", tags=["trust"])


@router.get("/dashboard/{client_id}")
async def get_trust_dashboard(
    client_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get complete trust dashboard for a client
    
    Shows:
    - Overall health status (green/yellow/red traffic lights)
    - Vendor invoice processing status
    - Customer invoice payment status
    - General ledger balance verification
    - Human-readable status messages
    
    This gives regnskapsfører peace of mind that everything is under control.
    """
    try:
        result = await TrustDashboardService.get_client_status(
            db=db,
            client_id=client_id
        )
        
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate trust dashboard: {str(e)}"
        )


@router.get("/status/{client_id}/vendor-invoices")
async def get_vendor_invoice_status(
    client_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed vendor invoice status
    
    Shows proof that all invoices are being handled:
    - Total received
    - Processed vs unprocessed
    - AI-approved vs needs review
    - Any stuck/forgotten invoices
    """
    try:
        stats = await TrustDashboardService._get_vendor_invoice_stats(db, client_id)
        message = TrustDashboardService._format_vendor_message(stats)
        
        return {
            "success": True,
            "data": {
                **stats,
                "message": message,
                "status": "ok" if stats["stuck_count"] == 0 else "error"
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get vendor invoice status: {str(e)}"
        )


@router.get("/status/{client_id}/customer-invoices")
async def get_customer_invoice_status(
    client_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed customer invoice status
    
    Shows payment tracking:
    - Total invoices
    - Paid vs unpaid
    - Overdue invoices
    """
    try:
        stats = await TrustDashboardService._get_customer_invoice_stats(db, client_id)
        message = TrustDashboardService._format_customer_message(stats)
        
        return {
            "success": True,
            "data": {
                **stats,
                "message": message,
                "status": "ok" if stats["unpaid_overdue_count"] == 0 else "warning"
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get customer invoice status: {str(e)}"
        )


@router.get("/status/{client_id}/general-ledger")
async def get_general_ledger_status(
    client_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get general ledger health check
    
    Verifies accounting integrity:
    - Total entries and lines
    - Debit = Credit balance check
    - Any imbalances
    """
    try:
        stats = await TrustDashboardService._get_gl_stats(db, client_id)
        message = TrustDashboardService._format_gl_message(stats)
        
        return {
            "success": True,
            "data": {
                **stats,
                "message": message,
                "status": "ok" if stats["is_balanced"] else "error"
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get GL status: {str(e)}"
        )

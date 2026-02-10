"""
DNB Open Banking API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID
from pydantic import BaseModel
from datetime import datetime, date
import secrets
import logging

from app.database import get_db
from app.services.dnb.service import DNBService
from app.services.dnb.oauth_client import DNBOAuth2Client
from app.models.bank_connection import BankConnection
from app.config import settings
from sqlalchemy import select


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/dnb", tags=["DNB Open Banking"])


# Initialize DNB service (load from environment)
# In production, these should be in .env
DNB_CLIENT_ID = settings.DNB_CLIENT_ID if hasattr(settings, 'DNB_CLIENT_ID') else ""
DNB_CLIENT_SECRET = settings.DNB_CLIENT_SECRET if hasattr(settings, 'DNB_CLIENT_SECRET') else ""
DNB_API_KEY = settings.DNB_API_KEY if hasattr(settings, 'DNB_API_KEY') else ""
DNB_REDIRECT_URI = settings.DNB_REDIRECT_URI if hasattr(settings, 'DNB_REDIRECT_URI') else "http://localhost:8000/api/dnb/oauth/callback"
DNB_USE_SANDBOX = settings.DNB_USE_SANDBOX if hasattr(settings, 'DNB_USE_SANDBOX') else True

dnb_service = DNBService(
    client_id=DNB_CLIENT_ID,
    client_secret=DNB_CLIENT_SECRET,
    api_key=DNB_API_KEY,
    redirect_uri=DNB_REDIRECT_URI,
    use_sandbox=DNB_USE_SANDBOX
)


# Request/Response models
class InitiateOAuthRequest(BaseModel):
    client_id: str  # Client UUID


class OAuthCallbackParams(BaseModel):
    code: str
    state: str


class ConnectAccountRequest(BaseModel):
    client_id: str
    code: str
    state: str
    account_id: str
    account_number: str
    account_name: Optional[str] = None


class SyncTransactionsRequest(BaseModel):
    connection_id: str
    from_date: Optional[str] = None  # YYYY-MM-DD
    to_date: Optional[str] = None    # YYYY-MM-DD


# OAuth state storage (in production, use Redis)
oauth_states = {}


@router.post("/oauth/initiate")
async def initiate_oauth(
    request: InitiateOAuthRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Initiate OAuth2 flow with DNB
    
    Returns authorization URL for user to visit.
    """
    try:
        # Generate CSRF state token
        state = secrets.token_urlsafe(32)
        
        # Store state for verification (with client_id)
        oauth_states[state] = {
            "client_id": request.client_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Get authorization URL
        oauth_client = dnb_service.get_oauth_client()
        auth_url = oauth_client.get_authorization_url(state=state)
        await oauth_client.close()
        
        return {
            "success": True,
            "authorization_url": auth_url,
            "state": state,
            "message": "Visit the authorization URL to grant access to your DNB account"
        }
        
    except Exception as e:
        logger.error(f"Failed to initiate OAuth: {e}")
        raise HTTPException(status_code=500, detail=f"OAuth initiation failed: {str(e)}")


@router.get("/oauth/callback")
async def oauth_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """
    OAuth2 callback endpoint
    
    DNB redirects here after user authorization.
    """
    try:
        # Verify state (CSRF protection)
        if state not in oauth_states:
            raise HTTPException(status_code=400, detail="Invalid state parameter")
        
        state_data = oauth_states.pop(state)
        client_id = UUID(state_data["client_id"])
        
        # Exchange code for token
        oauth_client = dnb_service.get_oauth_client()
        token_data = await oauth_client.exchange_code_for_token(code)
        await oauth_client.close()
        
        # Get user's accounts
        api_client = dnb_service.get_api_client(token_data["access_token"])
        accounts = await api_client.get_accounts()
        await api_client.close()
        
        # Return success page with account selection
        return {
            "success": True,
            "message": "Authorization successful! Please select an account to connect.",
            "client_id": str(client_id),
            "code": code,
            "state": state,
            "accounts": accounts,
            "next_step": "Call POST /api/dnb/connect with selected account"
        }
        
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        raise HTTPException(status_code=500, detail=f"OAuth callback failed: {str(e)}")


@router.post("/connect")
async def connect_account(
    request: ConnectAccountRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Connect DNB account after OAuth authorization
    
    Creates bank_connection record and starts initial sync.
    """
    try:
        client_id = UUID(request.client_id)
        
        # Exchange code for fresh token
        oauth_client = dnb_service.get_oauth_client()
        token_data = await oauth_client.exchange_code_for_token(request.code)
        await oauth_client.close()
        
        # Create bank connection
        connection = await dnb_service.create_bank_connection(
            db=db,
            client_id=client_id,
            token_data=token_data,
            account_id=request.account_id,
            account_number=request.account_number,
            account_name=request.account_name
        )
        
        # Initial sync (last 90 days)
        sync_result = await dnb_service.fetch_and_store_transactions(
            db=db,
            connection=connection
        )
        
        # Trigger auto-matching
        await dnb_service.trigger_auto_matching(db, client_id)
        
        return {
            "success": True,
            "connection_id": str(connection.id),
            "account_number": connection.bank_account_number,
            "initial_sync": sync_result,
            "message": "Bank account connected successfully!"
        }
        
    except Exception as e:
        logger.error(f"Failed to connect account: {e}")
        raise HTTPException(status_code=500, detail=f"Account connection failed: {str(e)}")


@router.post("/sync")
async def sync_transactions(
    request: SyncTransactionsRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Manually trigger transaction sync for a connection
    """
    try:
        connection_id = UUID(request.connection_id)
        
        # Get connection
        result = await db.execute(
            select(BankConnection).where(BankConnection.id == connection_id)
        )
        connection = result.scalars().first()
        
        if not connection:
            raise HTTPException(status_code=404, detail="Bank connection not found")
        
        # Parse dates
        from_date = date.fromisoformat(request.from_date) if request.from_date else None
        to_date = date.fromisoformat(request.to_date) if request.to_date else None
        
        # Sync transactions
        sync_result = await dnb_service.fetch_and_store_transactions(
            db=db,
            connection=connection,
            from_date=from_date,
            to_date=to_date
        )
        
        # Trigger auto-matching
        await dnb_service.trigger_auto_matching(db, connection.client_id)
        
        return {
            "success": True,
            "connection_id": str(connection.id),
            "sync_result": sync_result,
            "message": "Transactions synced successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to sync transactions: {e}")
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


@router.get("/connections")
async def list_connections(
    client_id: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """
    List bank connections for a client
    """
    try:
        result = await db.execute(
            select(BankConnection).where(
                BankConnection.client_id == UUID(client_id)
            )
        )
        connections = result.scalars().all()
        
        return {
            "success": True,
            "connections": [conn.to_dict() for conn in connections]
        }
        
    except Exception as e:
        logger.error(f"Failed to list connections: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list connections: {str(e)}")


@router.delete("/connections/{connection_id}")
async def disconnect_account(
    connection_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Disconnect (revoke) bank connection
    """
    try:
        # Get connection
        result = await db.execute(
            select(BankConnection).where(BankConnection.id == UUID(connection_id))
        )
        connection = result.scalars().first()
        
        if not connection:
            raise HTTPException(status_code=404, detail="Connection not found")
        
        # Revoke OAuth token
        from app.services.dnb.encryption import token_encryption
        access_token = token_encryption.decrypt(connection.access_token)
        
        oauth_client = dnb_service.get_oauth_client()
        await oauth_client.revoke_token(access_token)
        await oauth_client.close()
        
        # Mark as inactive
        connection.is_active = False
        connection.connection_status = "revoked"
        await db.commit()
        
        return {
            "success": True,
            "message": "Bank connection disconnected successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to disconnect account: {e}")
        raise HTTPException(status_code=500, detail=f"Disconnect failed: {str(e)}")


@router.post("/sync/all")
async def sync_all_connections(db: AsyncSession = Depends(get_db)):
    """
    Sync all active connections (for cron job)
    
    This endpoint should be called by a scheduled job (cron).
    """
    try:
        await dnb_service.sync_all_active_connections(db)
        
        return {
            "success": True,
            "message": "All connections synced successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to sync all connections: {e}")
        raise HTTPException(status_code=500, detail=f"Sync all failed: {str(e)}")

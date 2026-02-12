"""
Tink Bank Integration API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel
from datetime import datetime
import secrets
import logging
import os

from app.database import get_db
from app.services.tink.service import TinkService
from app.models.bank_connection import BankConnection
from app.models.bank_transaction import BankTransaction, TransactionStatus
from sqlalchemy import select, and_

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/tink", tags=["Tink Bank Integration"])


# Auto-matching helper function
async def run_auto_matching(client_id: UUID):
    """
    Run auto-matching for unmatched transactions
    
    Background task that matches bank transactions to invoices/vouchers.
    Note: This triggers the existing bank matching service.
    """
    try:
        # Import here to avoid circular dependencies
        from app.services.bank_matching_service import BankMatchingService
        from app.models.vendor_invoice import VendorInvoice
        from app.database import get_db
        
        async for db in get_db():
            try:
                matching_service = BankMatchingService()
                
                # Get unmatched transactions
                result = await db.execute(
                    select(BankTransaction).where(
                        and_(
                            BankTransaction.client_id == client_id,
                            BankTransaction.status == TransactionStatus.UNMATCHED
                        )
                    )
                )
                unmatched_transactions = result.scalars().all()
                
                logger.info(f"Auto-matching {len(unmatched_transactions)} transactions for client {client_id}")
                
                matched_count = 0
                for txn in unmatched_transactions:
                    # Get potential vouchers/invoices to match against
                    voucher_result = await db.execute(
                        select(VendorInvoice).where(
                            VendorInvoice.client_id == client_id
                        )
                    )
                    potential_vouchers = voucher_result.scalars().all()
                    
                    # Run auto-matching
                    try:
                        match_result = await matching_service.auto_match(
                            bank_transaction=txn,
                            potential_vouchers=potential_vouchers,
                            db=db
                        )
                        
                        # Update transaction if high confidence match
                        if match_result.confidence >= 80 and match_result.matched_voucher_id:
                            txn.ai_matched_invoice_id = UUID(match_result.matched_voucher_id)
                            txn.ai_match_confidence = match_result.confidence
                            txn.ai_match_reason = match_result.reason
                            txn.status = TransactionStatus.MATCHED
                            matched_count += 1
                    except Exception as match_error:
                        logger.warning(f"Could not match transaction {txn.id}: {match_error}")
                        continue
                
                await db.commit()
                logger.info(f"Auto-matched {matched_count}/{len(unmatched_transactions)} transactions")
                
            except Exception as e:
                logger.error(f"Auto-matching failed: {e}")
            finally:
                break  # Exit the async generator
                
    except ImportError as e:
        # If matching service not available, just log
        logger.warning(f"Auto-matching service not available: {e}")
        logger.info(f"Transactions imported for client {client_id}, but auto-matching skipped")


# Load Tink credentials
def load_tink_credentials():
    """Load Tink credentials from .tink_credentials file"""
    creds_file = os.path.join(os.path.expanduser("~"), ".openclaw/workspace/.tink_credentials")
    
    creds = {}
    if os.path.exists(creds_file):
        with open(creds_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    creds[key.strip()] = value.strip()
    
    return creds


# Initialize Tink service
tink_creds = load_tink_credentials()
TINK_CLIENT_ID = tink_creds.get("CLIENT_ID", "")
TINK_CLIENT_SECRET = tink_creds.get("CLIENT_SECRET", "")
TINK_BASE_URL = tink_creds.get("BASE_URL", "https://api.tink.com")
TINK_REDIRECT_URI = tink_creds.get("REDIRECT_URI", "http://localhost:3000/callback")
TINK_USE_SANDBOX = True  # Default to sandbox for testing

tink_service = TinkService(
    client_id=TINK_CLIENT_ID,
    client_secret=TINK_CLIENT_SECRET,
    redirect_uri=TINK_REDIRECT_URI,
    base_url=TINK_BASE_URL,
    use_sandbox=TINK_USE_SANDBOX
)


# Request/Response models
class InitiateOAuthRequest(BaseModel):
    """Request to initiate OAuth flow"""
    client_id: str  # Client UUID
    market: Optional[str] = "NO"
    locale: Optional[str] = "no_NO"


class OAuthCallbackRequest(BaseModel):
    """OAuth callback parameters"""
    code: str
    state: str


class ConnectAccountRequest(BaseModel):
    """Request to connect a bank account"""
    client_id: str
    code: str
    state: str
    account_id: str
    account_number: str
    account_name: Optional[str] = None


class SyncTransactionsRequest(BaseModel):
    """Request to sync transactions"""
    connection_id: str
    from_date: Optional[str] = None  # YYYY-MM-DD
    to_date: Optional[str] = None    # YYYY-MM-DD
    trigger_auto_match: Optional[bool] = True


class AccountResponse(BaseModel):
    """Account information response"""
    id: str
    name: str
    account_number: str
    type: str
    balance: Optional[float] = None
    currency: str


class ConnectionResponse(BaseModel):
    """Bank connection response"""
    id: str
    client_id: str
    bank_name: str
    account_number: str
    account_name: Optional[str]
    connection_status: str
    last_sync_at: Optional[str]
    total_transactions_imported: int
    is_active: bool


# OAuth state storage (in production, use Redis)
oauth_states = {}


@router.post("/oauth/authorize")
async def initiate_oauth(
    request: InitiateOAuthRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Step 1: Initiate OAuth2 flow with Tink
    
    Returns authorization URL for user to visit.
    Frontend should redirect user to this URL.
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
        oauth_client = tink_service.get_oauth_client()
        auth_url = oauth_client.get_authorization_url(
            state=state,
            market=request.market,
            locale=request.locale
        )
        await oauth_client.close()
        
        logger.info(f"Initiated OAuth for client {request.client_id}")
        
        return {
            "success": True,
            "authorization_url": auth_url,
            "state": state,
            "message": "Visit the authorization URL to grant access to your bank account",
            "next_step": "User completes OAuth flow, then call POST /api/tink/callback"
        }
        
    except Exception as e:
        logger.error(f"Failed to initiate OAuth: {e}")
        raise HTTPException(status_code=500, detail=f"OAuth initiation failed: {str(e)}")


@router.get("/oauth/callback")
@router.post("/oauth/callback")
async def oauth_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Step 2: OAuth2 callback endpoint
    
    Tink redirects here after user authorization.
    Exchanges code for access token and fetches available accounts.
    """
    try:
        # Verify state (CSRF protection)
        if state not in oauth_states:
            raise HTTPException(status_code=400, detail="Invalid state parameter (CSRF check failed)")
        
        state_data = oauth_states.get(state)
        client_id = state_data["client_id"]
        
        # Exchange code for token
        oauth_client = tink_service.get_oauth_client()
        token_data = await oauth_client.exchange_code_for_token(code)
        await oauth_client.close()
        
        # Get user's accounts
        api_client = tink_service.get_api_client(token_data["access_token"])
        accounts = await api_client.get_accounts()
        await api_client.close()
        
        # Format accounts for response
        formatted_accounts = []
        for acc in accounts:
            formatted_accounts.append({
                "id": acc.get("id"),
                "name": acc.get("name", "Unknown Account"),
                "account_number": acc.get("accountNumber", ""),
                "type": acc.get("type", ""),
                "balance": acc.get("balance", {}).get("amount", {}).get("value", 0),
                "currency": acc.get("balance", {}).get("amount", {}).get("currencyCode", "NOK"),
                "bank": acc.get("financialInstitution", {}).get("name", "Unknown")
            })
        
        logger.info(f"OAuth callback successful for client {client_id}, found {len(accounts)} accounts")
        
        # Keep state and tokens for account connection
        oauth_states[state] = {
            **state_data,
            "code": code,
            "token_data": token_data,
            "accounts": formatted_accounts
        }
        
        return {
            "success": True,
            "message": "Authorization successful! Please select an account to connect.",
            "client_id": client_id,
            "state": state,
            "accounts": formatted_accounts,
            "next_step": "Call POST /api/tink/connect with selected account_id"
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
    Step 3: Connect a specific bank account
    
    Creates a bank_connection record and stores encrypted tokens.
    """
    try:
        # Verify state
        if request.state not in oauth_states:
            raise HTTPException(status_code=400, detail="Invalid state - please restart OAuth flow")
        
        state_data = oauth_states[request.state]
        token_data = state_data.get("token_data")
        
        if not token_data:
            raise HTTPException(status_code=400, detail="Token data not found - please restart OAuth flow")
        
        # Create connection
        connection = await tink_service.create_connection(
            db=db,
            client_id=UUID(request.client_id),
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token"),
            expires_in=token_data.get("expires_in", 3600),
            account_id=request.account_id,
            account_number=request.account_number,
            account_name=request.account_name,
            scope=token_data.get("scope")
        )
        
        # Clean up state
        oauth_states.pop(request.state, None)
        
        logger.info(f"Connected account {request.account_number} for client {request.client_id}")
        
        return {
            "success": True,
            "message": f"Successfully connected bank account {request.account_number}",
            "connection": connection.to_dict(),
            "next_step": "Call POST /api/tink/transactions to import transactions"
        }
        
    except Exception as e:
        logger.error(f"Failed to connect account: {e}")
        raise HTTPException(status_code=500, detail=f"Account connection failed: {str(e)}")


@router.get("/accounts")
async def list_accounts(
    client_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    List all connected bank accounts (connections)
    
    Optional filter by client_id.
    """
    try:
        query = select(BankConnection).where(
            BankConnection.bank_name == "Tink",
            BankConnection.is_active == True
        )
        
        if client_id:
            query = query.where(BankConnection.client_id == UUID(client_id))
        
        result = await db.execute(query)
        connections = result.scalars().all()
        
        return {
            "success": True,
            "accounts": [conn.to_dict() for conn in connections],
            "count": len(connections)
        }
        
    except Exception as e:
        logger.error(f"Failed to list accounts: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list accounts: {str(e)}")


@router.post("/transactions")
async def sync_transactions(
    request: SyncTransactionsRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Fetch and store transactions from Tink
    
    Fetches transactions for the specified connection and stores them
    in the bank_transactions table. Optionally triggers auto-matching.
    """
    try:
        # Get connection
        result = await db.execute(
            select(BankConnection).where(
                BankConnection.id == UUID(request.connection_id)
            )
        )
        connection = result.scalar_one_or_none()
        
        if not connection:
            raise HTTPException(status_code=404, detail="Connection not found")
        
        # Parse dates
        from_date = None
        to_date = None
        
        if request.from_date:
            from_date = datetime.fromisoformat(request.from_date)
        if request.to_date:
            to_date = datetime.fromisoformat(request.to_date)
        
        # Sync transactions
        new_count = await tink_service.sync_transactions(
            db=db,
            connection=connection,
            from_date=from_date,
            to_date=to_date
        )
        
        # Trigger auto-matching if requested
        if request.trigger_auto_match and new_count > 0:
            # Schedule auto-matching as background task
            background_tasks.add_task(
                run_auto_matching,
                client_id=connection.client_id
            )
            logger.info(f"Scheduled auto-matching for {new_count} new transactions")
        
        return {
            "success": True,
            "message": f"Imported {new_count} new transactions",
            "new_transactions": new_count,
            "auto_match_scheduled": request.trigger_auto_match and new_count > 0,
            "connection_id": str(connection.id),
            "last_sync": connection.last_sync_at.isoformat() if connection.last_sync_at else None
        }
        
    except Exception as e:
        logger.error(f"Failed to sync transactions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to sync transactions: {str(e)}")


@router.get("/transactions")
async def get_transactions(
    client_id: str = Query(...),
    connection_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(100),
    db: AsyncSession = Depends(get_db)
):
    """
    Get bank transactions from database
    
    Returns transactions that were imported from Tink.
    """
    try:
        query = select(BankTransaction).where(
            BankTransaction.client_id == UUID(client_id)
        )
        
        if connection_id:
            # Filter by bank account from connection
            conn_result = await db.execute(
                select(BankConnection).where(
                    BankConnection.id == UUID(connection_id)
                )
            )
            connection = conn_result.scalar_one_or_none()
            if connection:
                query = query.where(
                    BankTransaction.bank_account == connection.bank_account_number
                )
        
        if status:
            from app.models.bank_transaction import TransactionStatus
            query = query.where(BankTransaction.status == status)
        
        query = query.order_by(BankTransaction.transaction_date.desc())
        query = query.limit(limit)
        
        result = await db.execute(query)
        transactions = result.scalars().all()
        
        return {
            "success": True,
            "transactions": [txn.to_dict() for txn in transactions],
            "count": len(transactions)
        }
        
    except Exception as e:
        logger.error(f"Failed to get transactions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get transactions: {str(e)}")


@router.post("/disconnect/{connection_id}")
async def disconnect_account(
    connection_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Disconnect a bank account
    
    Marks the connection as inactive (does not delete data).
    """
    try:
        result = await db.execute(
            select(BankConnection).where(
                BankConnection.id == UUID(connection_id)
            )
        )
        connection = result.scalar_one_or_none()
        
        if not connection:
            raise HTTPException(status_code=404, detail="Connection not found")
        
        connection.is_active = False
        connection.connection_status = "disconnected"
        await db.commit()
        
        logger.info(f"Disconnected Tink connection {connection_id}")
        
        return {
            "success": True,
            "message": "Bank account disconnected",
            "connection_id": connection_id
        }
        
    except Exception as e:
        logger.error(f"Failed to disconnect account: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to disconnect: {str(e)}")


@router.get("/status")
async def get_status():
    """
    Get Tink integration status
    
    Returns configuration and health status.
    """
    return {
        "success": True,
        "service": "Tink Bank Integration",
        "status": "operational",
        "configuration": {
            "client_id": TINK_CLIENT_ID[:8] + "..." if TINK_CLIENT_ID else "NOT_SET",
            "base_url": TINK_BASE_URL,
            "redirect_uri": TINK_REDIRECT_URI,
            "sandbox_mode": TINK_USE_SANDBOX
        },
        "endpoints": {
            "authorize": "POST /api/tink/oauth/authorize",
            "callback": "GET /api/tink/oauth/callback",
            "connect": "POST /api/tink/connect",
            "accounts": "GET /api/tink/accounts",
            "sync": "POST /api/tink/transactions",
            "get_transactions": "GET /api/tink/transactions"
        }
    }

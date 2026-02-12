"""
Tink Service - Main integration service
Coordinates OAuth, API calls, and transaction storage
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from cryptography.fernet import Fernet
import base64

from .oauth_client import TinkOAuth2Client
from .api_client import TinkAPIClient
from app.models.bank_connection import BankConnection
from app.models.bank_transaction import BankTransaction, TransactionType, TransactionStatus

logger = logging.getLogger(__name__)


class TinkService:
    """Main Tink integration service"""
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        base_url: str = "https://api.tink.com",
        use_sandbox: bool = False,
        encryption_key: Optional[str] = None
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.base_url = base_url
        self.use_sandbox = use_sandbox
        
        # Initialize encryption (for storing tokens)
        if encryption_key:
            self.cipher = Fernet(encryption_key.encode())
        else:
            # Generate a key if none provided (in production, load from environment)
            key = Fernet.generate_key()
            self.cipher = Fernet(key)
            logger.warning("Using generated encryption key - tokens will not persist across restarts!")
    
    def get_oauth_client(self) -> TinkOAuth2Client:
        """Get OAuth2 client instance"""
        return TinkOAuth2Client(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
            base_url=self.base_url,
            use_sandbox=self.use_sandbox
        )
    
    def get_api_client(self, access_token: str) -> TinkAPIClient:
        """Get API client instance"""
        return TinkAPIClient(
            access_token=access_token,
            base_url=self.base_url,
            use_sandbox=self.use_sandbox
        )
    
    def encrypt_token(self, token: str) -> str:
        """Encrypt token for storage"""
        encrypted = self.cipher.encrypt(token.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt_token(self, encrypted_token: str) -> str:
        """Decrypt token from storage"""
        encrypted = base64.urlsafe_b64decode(encrypted_token.encode())
        decrypted = self.cipher.decrypt(encrypted)
        return decrypted.decode()
    
    async def create_connection(
        self,
        db: AsyncSession,
        client_id: UUID,
        access_token: str,
        refresh_token: Optional[str],
        expires_in: int,
        account_id: str,
        account_number: str,
        account_name: Optional[str] = None,
        scope: Optional[str] = None
    ) -> BankConnection:
        """
        Create a new bank connection record
        
        Args:
            db: Database session
            client_id: Client UUID
            access_token: OAuth access token
            refresh_token: OAuth refresh token
            expires_in: Token expiry time in seconds
            account_id: Tink account ID
            account_number: Bank account number
            account_name: Account name (optional)
            scope: OAuth scopes
        
        Returns:
            BankConnection object
        """
        # Encrypt tokens
        encrypted_access = self.encrypt_token(access_token)
        encrypted_refresh = self.encrypt_token(refresh_token) if refresh_token else None
        
        # Calculate expiry time
        token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        
        # Create connection
        connection = BankConnection(
            client_id=client_id,
            bank_name="Tink",
            bank_account_number=account_number,
            bank_account_id=account_id,
            account_name=account_name,
            access_token=encrypted_access,
            refresh_token=encrypted_refresh,
            token_expires_at=token_expires_at,
            scope=scope,
            auto_sync_enabled=True,
            sync_frequency_hours=24,
            connection_status="active",
            is_active=True
        )
        
        db.add(connection)
        await db.commit()
        await db.refresh(connection)
        
        logger.info(f"Created Tink connection for client {client_id}, account {account_number}")
        return connection
    
    async def sync_transactions(
        self,
        db: AsyncSession,
        connection: BankConnection,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> int:
        """
        Sync transactions from Tink to database
        
        Args:
            db: Database session
            connection: Bank connection object
            from_date: Start date (optional, defaults to 90 days ago)
            to_date: End date (optional, defaults to today)
        
        Returns:
            Number of new transactions imported
        """
        try:
            # Decrypt access token
            access_token = self.decrypt_token(connection.access_token)
            
            # Get API client
            api_client = self.get_api_client(access_token)
            
            # Fetch transactions
            transactions = await api_client.get_transactions(
                account_id=connection.bank_account_id,
                from_date=from_date,
                to_date=to_date
            )
            
            await api_client.close()
            
            # Store transactions
            new_count = 0
            for txn_data in transactions:
                # Check if transaction already exists (by Tink ID)
                tink_txn_id = txn_data.get("id")
                
                # Check existing
                result = await db.execute(
                    select(BankTransaction).where(
                        BankTransaction.reference_number == tink_txn_id,
                        BankTransaction.client_id == connection.client_id
                    )
                )
                existing = result.scalar_one_or_none()
                
                if existing:
                    continue  # Skip duplicates
                
                # Parse transaction data
                amount = float(txn_data.get("amount", {}).get("value", {}).get("unscaledValue", 0)) / 100
                currency_code = txn_data.get("amount", {}).get("currencyCode", "NOK")
                
                # Determine transaction type (debit/credit)
                transaction_type = TransactionType.CREDIT if amount > 0 else TransactionType.DEBIT
                amount_abs = abs(amount)
                
                # Parse dates
                txn_date_str = txn_data.get("dates", {}).get("booked")
                if not txn_date_str:
                    txn_date_str = txn_data.get("dates", {}).get("value")
                
                txn_date = datetime.fromisoformat(txn_date_str.replace("Z", "+00:00")) if txn_date_str else datetime.utcnow()
                
                # Extract description and counterparty
                description = txn_data.get("descriptions", {}).get("display", "")
                if not description:
                    description = txn_data.get("descriptions", {}).get("original", "Unknown")
                
                counterparty_name = txn_data.get("counterparty", {}).get("name")
                counterparty_account = txn_data.get("counterparty", {}).get("accountNumber")
                
                # Create transaction record
                bank_txn = BankTransaction(
                    client_id=connection.client_id,
                    transaction_date=txn_date,
                    booking_date=txn_date,
                    amount=amount_abs,
                    transaction_type=transaction_type,
                    description=description,
                    reference_number=tink_txn_id,
                    counterparty_name=counterparty_name,
                    counterparty_account=counterparty_account,
                    bank_account=connection.bank_account_number,
                    status=TransactionStatus.UNMATCHED,
                    upload_batch_id=None,
                    original_filename="Tink API Import"
                )
                
                db.add(bank_txn)
                new_count += 1
            
            # Update connection sync status
            connection.last_sync_at = datetime.utcnow()
            connection.last_sync_status = "success"
            connection.total_transactions_imported += new_count
            
            if transactions:
                # Update date range
                dates = [
                    datetime.fromisoformat(
                        txn.get("dates", {}).get("booked", "").replace("Z", "+00:00")
                    ) 
                    for txn in transactions 
                    if txn.get("dates", {}).get("booked")
                ]
                
                if dates:
                    if not connection.oldest_transaction_date or min(dates) < connection.oldest_transaction_date:
                        connection.oldest_transaction_date = min(dates)
                    if not connection.newest_transaction_date or max(dates) > connection.newest_transaction_date:
                        connection.newest_transaction_date = max(dates)
            
            await db.commit()
            
            logger.info(
                f"Synced {new_count} new transactions for connection {connection.id} "
                f"(total: {len(transactions)})"
            )
            
            return new_count
            
        except Exception as e:
            # Update connection with error
            connection.last_sync_at = datetime.utcnow()
            connection.last_sync_status = "error"
            connection.last_sync_error = str(e)
            await db.commit()
            
            logger.error(f"Error syncing transactions for connection {connection.id}: {e}")
            raise

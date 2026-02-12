"""
DNB Integration Service - Main orchestration service
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta, timezone
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.bank_connection import BankConnection
from app.models.bank_transaction import BankTransaction, TransactionType, TransactionStatus
from app.services.dnb.oauth_client import DNBOAuth2Client
from app.services.dnb.api_client import DNBAPIClient
from app.services.dnb.encryption import token_encryption
from app.config import settings


logger = logging.getLogger(__name__)


class DNBService:
    """
    DNB Integration Service
    
    Main service for:
    - OAuth2 authentication flow
    - Fetching transactions from DNB
    - Storing transactions in database
    - Triggering auto-matching
    - Scheduled sync management
    """
    
    def __init__(
        self,
        client_id: str = "",
        client_secret: str = "",
        api_key: str = "",
        redirect_uri: str = "http://localhost:8000/api/dnb/oauth/callback",
        use_sandbox: bool = True
    ):
        """
        Initialize DNB service
        
        Args:
            client_id: DNB OAuth2 client ID
            client_secret: DNB OAuth2 client secret
            api_key: DNB API key
            redirect_uri: OAuth2 redirect URI
            use_sandbox: Use sandbox environment
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.api_key = api_key
        self.redirect_uri = redirect_uri
        self.use_sandbox = use_sandbox
    
    def get_oauth_client(self) -> DNBOAuth2Client:
        """Get OAuth2 client instance"""
        return DNBOAuth2Client(
            client_id=self.client_id,
            client_secret=self.client_secret,
            api_key=self.api_key,
            redirect_uri=self.redirect_uri,
            use_sandbox=self.use_sandbox
        )
    
    def get_api_client(self, access_token: str) -> DNBAPIClient:
        """Get API client instance"""
        return DNBAPIClient(
            api_key=self.api_key,
            access_token=access_token,
            use_sandbox=self.use_sandbox
        )
    
    async def create_bank_connection(
        self,
        db: AsyncSession,
        client_id: UUID,
        token_data: Dict[str, Any],
        account_id: str,
        account_number: str,
        account_name: Optional[str] = None
    ) -> BankConnection:
        """
        Create bank connection after successful OAuth
        
        Args:
            db: Database session
            client_id: Client UUID
            token_data: OAuth token response
            account_id: DNB account ID
            account_number: Norwegian account number
            account_name: Optional account name
        
        Returns:
            Created BankConnection
        """
        # Encrypt tokens
        encrypted_access_token = token_encryption.encrypt(token_data["access_token"])
        encrypted_refresh_token = token_encryption.encrypt(token_data.get("refresh_token", ""))
        
        # Calculate expiration
        expires_in = token_data.get("expires_in", 3600)
        token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
        
        # Create connection
        connection = BankConnection(
            client_id=client_id,
            bank_name="DNB",
            bank_account_number=account_number,
            bank_account_id=account_id,
            account_name=account_name,
            access_token=encrypted_access_token,
            refresh_token=encrypted_refresh_token,
            token_expires_at=token_expires_at,
            scope=token_data.get("scope", ""),
            token_type=token_data.get("token_type", "Bearer"),
            auto_sync_enabled=True,
            sync_frequency_hours=24,
            connection_status="active",
            is_active=True
        )
        
        db.add(connection)
        await db.commit()
        await db.refresh(connection)
        
        logger.info(f"Created bank connection for client {client_id}, account {account_number}")
        return connection
    
    async def refresh_token_if_needed(
        self,
        db: AsyncSession,
        connection: BankConnection
    ) -> str:
        """
        Refresh access token if expired or about to expire
        
        Args:
            db: Database session
            connection: Bank connection
        
        Returns:
            Valid access token (decrypted)
        """
        # Check if token expires in next 5 minutes
        if connection.token_expires_at > datetime.now(timezone.utc) + timedelta(minutes=5):
            # Token still valid
            return token_encryption.decrypt(connection.access_token)
        
        # Refresh token
        logger.info(f"Refreshing token for connection {connection.id}")
        
        oauth_client = self.get_oauth_client()
        try:
            refresh_token = token_encryption.decrypt(connection.refresh_token)
            token_data = await oauth_client.refresh_access_token(refresh_token)
            
            # Update connection
            connection.access_token = token_encryption.encrypt(token_data["access_token"])
            if "refresh_token" in token_data:
                connection.refresh_token = token_encryption.encrypt(token_data["refresh_token"])
            
            expires_in = token_data.get("expires_in", 3600)
            connection.token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
            connection.updated_at = datetime.now(timezone.utc)
            
            await db.commit()
            await db.refresh(connection)
            
            logger.info(f"Token refreshed successfully for connection {connection.id}")
            return token_data["access_token"]
            
        except Exception as e:
            logger.error(f"Failed to refresh token: {e}")
            connection.connection_status = "error"
            connection.last_sync_error = f"Token refresh failed: {str(e)}"
            await db.commit()
            raise
        finally:
            await oauth_client.close()
    
    async def fetch_and_store_transactions(
        self,
        db: AsyncSession,
        connection: BankConnection,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Fetch transactions from DNB and store in database
        
        Args:
            db: Database session
            connection: Bank connection
            from_date: Start date (default: 90 days ago)
            to_date: End date (default: today)
        
        Returns:
            Summary of imported transactions
        """
        # Get valid access token
        access_token = await self.refresh_token_if_needed(db, connection)
        
        # Default date range
        if from_date is None:
            from_date = date.today() - timedelta(days=90)
        if to_date is None:
            to_date = date.today()
        
        # Fetch transactions
        api_client = self.get_api_client(access_token)
        try:
            logger.info(f"Fetching transactions for account {connection.bank_account_number} ({from_date} to {to_date})")
            
            transactions = await api_client.get_transactions_paginated(
                account_id=connection.bank_account_id,
                from_date=from_date,
                to_date=to_date
            )
            
            if not transactions:
                logger.info("No transactions found")
                return {
                    "fetched": 0,
                    "new": 0,
                    "duplicates": 0,
                    "errors": 0
                }
            
            # Store transactions (deduplicate)
            new_count = 0
            duplicate_count = 0
            error_count = 0
            
            for txn_data in transactions:
                try:
                    # Check for duplicate (by date, amount, reference)
                    txn_date_str = txn_data.get("valueDate") or txn_data.get("bookingDate")
                    if not txn_date_str:
                        continue
                    
                    txn_date = datetime.fromisoformat(txn_date_str.replace("Z", "+00:00"))
                    amount = float(txn_data.get("transactionAmount", {}).get("amount", 0))
                    reference = txn_data.get("remittanceInformationUnstructured", "")
                    
                    # Check if exists
                    result = await db.execute(
                        select(BankTransaction).where(
                            and_(
                                BankTransaction.client_id == connection.client_id,
                                BankTransaction.transaction_date == txn_date,
                                BankTransaction.amount == abs(amount),
                                BankTransaction.description == reference
                            )
                        )
                    )
                    existing = result.scalars().first()
                    
                    if existing:
                        duplicate_count += 1
                        continue
                    
                    # Create new transaction
                    transaction = self._create_transaction_from_dnb(
                        connection=connection,
                        txn_data=txn_data
                    )
                    
                    db.add(transaction)
                    new_count += 1
                    
                except Exception as e:
                    logger.error(f"Error processing transaction: {e}")
                    error_count += 1
                    continue
            
            # Commit all transactions
            await db.commit()
            
            # Update connection metadata
            connection.last_sync_at = datetime.now(timezone.utc)
            connection.last_sync_status = "success"
            connection.total_transactions_imported += new_count
            
            if transactions:
                # Update date range
                dates = [
                    datetime.fromisoformat((t.get("valueDate") or t.get("bookingDate")).replace("Z", "+00:00"))
                    for t in transactions
                    if t.get("valueDate") or t.get("bookingDate")
                ]
                if dates:
                    connection.oldest_transaction_date = min(dates)
                    connection.newest_transaction_date = max(dates)
            
            await db.commit()
            
            logger.info(f"Import complete: {new_count} new, {duplicate_count} duplicates, {error_count} errors")
            
            return {
                "fetched": len(transactions),
                "new": new_count,
                "duplicates": duplicate_count,
                "errors": error_count
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch/store transactions: {e}")
            connection.last_sync_at = datetime.now(timezone.utc)
            connection.last_sync_status = "error"
            connection.last_sync_error = str(e)
            await db.commit()
            raise
        finally:
            await api_client.close()
    
    def _create_transaction_from_dnb(
        self,
        connection: BankConnection,
        txn_data: Dict[str, Any]
    ) -> BankTransaction:
        """
        Convert DNB transaction to BankTransaction model
        
        Args:
            connection: Bank connection
            txn_data: DNB transaction data
        
        Returns:
            BankTransaction instance
        """
        # Parse dates
        txn_date_str = txn_data.get("valueDate") or txn_data.get("bookingDate")
        booking_date_str = txn_data.get("bookingDate")
        
        transaction_date = datetime.fromisoformat(txn_date_str.replace("Z", "+00:00")) if txn_date_str else datetime.now(timezone.utc)
        booking_date = datetime.fromisoformat(booking_date_str.replace("Z", "+00:00")) if booking_date_str else None
        
        # Parse amount
        amount_data = txn_data.get("transactionAmount", {})
        amount = abs(float(amount_data.get("amount", 0)))
        
        # Determine type (debit/credit)
        # DNB uses positive/negative amounts
        transaction_type = TransactionType.CREDIT if float(amount_data.get("amount", 0)) > 0 else TransactionType.DEBIT
        
        # Description
        description = txn_data.get("remittanceInformationUnstructured", "") or txn_data.get("additionalInformation", "")
        
        # Reference number
        reference = txn_data.get("proprietaryBankTransactionCode", "") or txn_data.get("endToEndId", "")
        
        # Counterparty
        debtor_info = txn_data.get("debtorAccount", {}) or txn_data.get("debtorName", "")
        creditor_info = txn_data.get("creditorAccount", {}) or txn_data.get("creditorName", "")
        
        counterparty_name = debtor_info if transaction_type == TransactionType.DEBIT else creditor_info
        if isinstance(counterparty_name, dict):
            counterparty_name = counterparty_name.get("name", "")
        
        # Create transaction
        return BankTransaction(
            client_id=connection.client_id,
            transaction_date=transaction_date,
            booking_date=booking_date,
            amount=amount,
            transaction_type=transaction_type,
            description=description,
            reference_number=reference,
            counterparty_name=str(counterparty_name) if counterparty_name else None,
            bank_account=connection.bank_account_number,
            status=TransactionStatus.UNMATCHED,
            upload_batch_id=None,  # This is from API, not upload
            original_filename=None
        )
    
    async def trigger_auto_matching(
        self,
        db: AsyncSession,
        client_id: UUID
    ):
        """
        Trigger auto-matching for newly imported transactions
        
        Args:
            db: Database session
            client_id: Client UUID
        """
        # TODO: Integrate with existing auto-matching service
        # This would call the bank reconciliation matching logic
        logger.info(f"TODO: Trigger auto-matching for client {client_id}")
        pass
    
    async def sync_all_active_connections(self, db: AsyncSession):
        """
        Sync all active bank connections (for cron job)
        
        Args:
            db: Database session
        """
        # Get all active connections that need sync
        result = await db.execute(
            select(BankConnection).where(
                and_(
                    BankConnection.is_active == True,
                    BankConnection.auto_sync_enabled == True
                )
            )
        )
        connections = result.scalars().all()
        
        logger.info(f"Starting sync for {len(connections)} bank connections")
        
        for connection in connections:
            try:
                # Check if sync needed (based on sync_frequency_hours)
                if connection.last_sync_at:
                    next_sync = connection.last_sync_at + timedelta(hours=connection.sync_frequency_hours)
                    if datetime.now(timezone.utc) < next_sync:
                        logger.debug(f"Skipping connection {connection.id} - not due for sync")
                        continue
                
                # Fetch last 7 days of transactions
                await self.fetch_and_store_transactions(
                    db=db,
                    connection=connection,
                    from_date=date.today() - timedelta(days=7),
                    to_date=date.today()
                )
                
                # Trigger auto-matching
                await self.trigger_auto_matching(db, connection.client_id)
                
            except Exception as e:
                logger.error(f"Error syncing connection {connection.id}: {e}")
                continue
        
        logger.info("Sync complete for all connections")

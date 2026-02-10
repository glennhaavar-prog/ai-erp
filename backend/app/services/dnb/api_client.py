"""
DNB API Client - Account Information Services (AIS)
"""
import httpx
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta

from app.config import settings


logger = logging.getLogger(__name__)


class DNBAPIClient:
    """
    DNB Open Banking API Client
    
    Provides access to Account Information Services (AIS):
    - Get accounts
    - Get account details
    - Get transactions
    - Get account balance
    """
    
    # API endpoints
    SANDBOX_BASE_URL = "https://api.sandbox.dnb.no"
    PRODUCTION_BASE_URL = "https://api.dnb.no"
    
    ACCOUNTS_PATH = "/psd2/accounts"
    TRANSACTIONS_PATH = "/psd2/accounts/{account_id}/transactions"
    BALANCE_PATH = "/psd2/accounts/{account_id}/balances"
    ACCOUNT_DETAILS_PATH = "/psd2/accounts/{account_id}"
    
    def __init__(
        self,
        api_key: str,
        access_token: str,
        use_sandbox: bool = True
    ):
        """
        Initialize DNB API client
        
        Args:
            api_key: DNB API key
            access_token: OAuth2 access token
            use_sandbox: Use sandbox (True) or production (False)
        """
        self.api_key = api_key
        self.access_token = access_token
        self.base_url = self.SANDBOX_BASE_URL if use_sandbox else self.PRODUCTION_BASE_URL
        
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "x-api-key": self.api_key,
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            },
            timeout=60.0
        )
    
    async def get_accounts(self) -> List[Dict[str, Any]]:
        """
        Get list of accounts
        
        Returns:
            List of account objects
        """
        try:
            response = await self.client.get(self.ACCOUNTS_PATH)
            response.raise_for_status()
            
            data = response.json()
            accounts = data.get("accounts", [])
            
            logger.info(f"Retrieved {len(accounts)} accounts from DNB")
            return accounts
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to fetch accounts: {e.response.status_code} - {e.response.text}")
            raise ValueError(f"Failed to fetch accounts: {e.response.text}")
        except Exception as e:
            logger.error(f"Error fetching accounts: {e}")
            raise
    
    async def get_account_details(self, account_id: str) -> Dict[str, Any]:
        """
        Get account details
        
        Args:
            account_id: DNB account ID
        
        Returns:
            Account details
        """
        try:
            path = self.ACCOUNT_DETAILS_PATH.format(account_id=account_id)
            response = await self.client.get(path)
            response.raise_for_status()
            
            account = response.json()
            logger.info(f"Retrieved details for account {account_id}")
            return account
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to fetch account details: {e.response.status_code} - {e.response.text}")
            raise ValueError(f"Failed to fetch account details: {e.response.text}")
        except Exception as e:
            logger.error(f"Error fetching account details: {e}")
            raise
    
    async def get_transactions(
        self,
        account_id: str,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        booking_status: str = "booked"
    ) -> List[Dict[str, Any]]:
        """
        Get account transactions
        
        Args:
            account_id: DNB account ID
            from_date: Start date for transactions (default: 90 days ago)
            to_date: End date for transactions (default: today)
            booking_status: Transaction status (booked, pending, both)
        
        Returns:
            List of transaction objects
        """
        # Default date range: last 90 days
        if from_date is None:
            from_date = date.today() - timedelta(days=90)
        if to_date is None:
            to_date = date.today()
        
        try:
            path = self.TRANSACTIONS_PATH.format(account_id=account_id)
            params = {
                "dateFrom": from_date.isoformat(),
                "dateTo": to_date.isoformat(),
                "bookingStatus": booking_status
            }
            
            response = await self.client.get(path, params=params)
            response.raise_for_status()
            
            data = response.json()
            transactions = data.get("transactions", {}).get(booking_status, [])
            
            logger.info(f"Retrieved {len(transactions)} transactions for account {account_id} ({from_date} to {to_date})")
            return transactions
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to fetch transactions: {e.response.status_code} - {e.response.text}")
            raise ValueError(f"Failed to fetch transactions: {e.response.text}")
        except Exception as e:
            logger.error(f"Error fetching transactions: {e}")
            raise
    
    async def get_transactions_paginated(
        self,
        account_id: str,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        booking_status: str = "booked",
        max_pages: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get transactions with pagination support
        
        Args:
            account_id: DNB account ID
            from_date: Start date for transactions
            to_date: End date for transactions
            booking_status: Transaction status
            max_pages: Maximum number of pages to fetch
        
        Returns:
            All transactions across pages
        """
        all_transactions = []
        page = 1
        
        while page <= max_pages:
            try:
                transactions = await self.get_transactions(
                    account_id=account_id,
                    from_date=from_date,
                    to_date=to_date,
                    booking_status=booking_status
                )
                
                if not transactions:
                    break
                
                all_transactions.extend(transactions)
                
                # Check if there are more pages (DNB-specific pagination logic)
                # This is a simplified version - actual implementation may differ
                if len(transactions) < 100:  # Assuming page size of 100
                    break
                
                page += 1
                
            except Exception as e:
                logger.error(f"Error fetching page {page}: {e}")
                break
        
        logger.info(f"Retrieved total of {len(all_transactions)} transactions across {page} pages")
        return all_transactions
    
    async def get_balance(self, account_id: str) -> Dict[str, Any]:
        """
        Get account balance
        
        Args:
            account_id: DNB account ID
        
        Returns:
            Balance information
        """
        try:
            path = self.BALANCE_PATH.format(account_id=account_id)
            response = await self.client.get(path)
            response.raise_for_status()
            
            data = response.json()
            balances = data.get("balances", [])
            
            logger.info(f"Retrieved balance for account {account_id}")
            return balances[0] if balances else {}
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to fetch balance: {e.response.status_code} - {e.response.text}")
            raise ValueError(f"Failed to fetch balance: {e.response.text}")
        except Exception as e:
            logger.error(f"Error fetching balance: {e}")
            raise
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

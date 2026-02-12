"""
Tink API Client
Handles API calls to Tink for accounts, transactions, and balances
"""
import aiohttp
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class TinkAPIClient:
    """Client for Tink REST API"""
    
    def __init__(
        self,
        access_token: str,
        base_url: str = "https://api.tink.com",
        use_sandbox: bool = False
    ):
        self.access_token = access_token
        self.base_url = base_url
        self.use_sandbox = use_sandbox
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            }
            self.session = aiohttp.ClientSession(headers=headers)
        return self.session
    
    async def close(self):
        """Close aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def get_accounts(self) -> List[Dict]:
        """
        Fetch all bank accounts
        
        Returns:
            List of account objects
        """
        session = await self._get_session()
        
        url = f"{self.base_url}/api/v1/accounts"
        
        try:
            async with session.get(url) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Failed to fetch accounts: {error_text}")
                    raise Exception(f"Failed to fetch accounts: {error_text}")
                
                data = await response.json()
                accounts = data.get("accounts", [])
                
                logger.info(f"Fetched {len(accounts)} accounts from Tink")
                return accounts
                
        except Exception as e:
            logger.error(f"Error fetching accounts: {e}")
            raise
    
    async def get_account_details(self, account_id: str) -> Dict:
        """
        Fetch details for a specific account
        
        Args:
            account_id: Tink account ID
        
        Returns:
            Account object with details
        """
        session = await self._get_session()
        
        url = f"{self.base_url}/api/v1/accounts/{account_id}"
        
        try:
            async with session.get(url) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Failed to fetch account {account_id}: {error_text}")
                    raise Exception(f"Failed to fetch account: {error_text}")
                
                account = await response.json()
                logger.info(f"Fetched account details for {account_id}")
                return account
                
        except Exception as e:
            logger.error(f"Error fetching account details: {e}")
            raise
    
    async def get_transactions(
        self,
        account_id: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[Dict]:
        """
        Fetch transactions
        
        Args:
            account_id: Filter by account (optional)
            from_date: Start date (optional, defaults to 90 days ago)
            to_date: End date (optional, defaults to today)
            limit: Maximum number of transactions
        
        Returns:
            List of transaction objects
        """
        session = await self._get_session()
        
        # Default date range: last 90 days
        if from_date is None:
            from_date = datetime.now() - timedelta(days=90)
        if to_date is None:
            to_date = datetime.now()
        
        url = f"{self.base_url}/api/v1/transactions"
        
        params = {
            "limit": limit,
        }
        
        if account_id:
            params["accountId"] = account_id
        
        # Tink expects dates in YYYY-MM-DD format
        if from_date:
            params["startDate"] = from_date.strftime("%Y-%m-%d")
        if to_date:
            params["endDate"] = to_date.strftime("%Y-%m-%d")
        
        try:
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Failed to fetch transactions: {error_text}")
                    raise Exception(f"Failed to fetch transactions: {error_text}")
                
                data = await response.json()
                transactions = data.get("transactions", [])
                
                logger.info(
                    f"Fetched {len(transactions)} transactions from Tink "
                    f"({from_date.date()} to {to_date.date()})"
                )
                return transactions
                
        except Exception as e:
            logger.error(f"Error fetching transactions: {e}")
            raise
    
    async def get_balances(self, account_id: Optional[str] = None) -> List[Dict]:
        """
        Fetch account balances
        
        Args:
            account_id: Filter by account (optional)
        
        Returns:
            List of balance objects
        """
        session = await self._get_session()
        
        url = f"{self.base_url}/api/v1/accounts/balances"
        
        params = {}
        if account_id:
            params["accountId"] = account_id
        
        try:
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Failed to fetch balances: {error_text}")
                    raise Exception(f"Failed to fetch balances: {error_text}")
                
                data = await response.json()
                balances = data.get("balances", [])
                
                logger.info(f"Fetched {len(balances)} balances from Tink")
                return balances
                
        except Exception as e:
            logger.error(f"Error fetching balances: {e}")
            raise
    
    async def get_user_info(self) -> Dict:
        """
        Fetch authenticated user information
        
        Returns:
            User object
        """
        session = await self._get_session()
        
        url = f"{self.base_url}/api/v1/user"
        
        try:
            async with session.get(url) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Failed to fetch user info: {error_text}")
                    raise Exception(f"Failed to fetch user info: {error_text}")
                
                user = await response.json()
                logger.info("Fetched user info from Tink")
                return user
                
        except Exception as e:
            logger.error(f"Error fetching user info: {e}")
            raise

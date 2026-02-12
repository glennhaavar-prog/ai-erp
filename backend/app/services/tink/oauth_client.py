"""
Tink OAuth2 Client
Handles authentication flow with Tink API
"""
import aiohttp
import logging
from typing import Dict, Optional
from urllib.parse import urlencode

logger = logging.getLogger(__name__)


class TinkOAuth2Client:
    """OAuth2 client for Tink API"""
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        base_url: str = "https://api.tink.com",
        use_sandbox: bool = False
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.base_url = base_url
        self.use_sandbox = use_sandbox
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close(self):
        """Close aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    def get_authorization_url(
        self,
        state: str,
        market: str = "NO",
        locale: str = "no_NO",
        scopes: Optional[str] = None
    ) -> str:
        """
        Generate authorization URL for user to visit
        
        Args:
            state: CSRF token
            market: Market code (NO for Norway)
            locale: Locale code
            scopes: OAuth scopes (comma-separated)
        
        Returns:
            Authorization URL
        """
        if scopes is None:
            # Default scopes for full access
            scopes = (
                "accounts:read,transactions:read,balances:read,"
                "user:read,statistics:read,investments:read"
            )
        
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": scopes,
            "state": state,
            "market": market,
            "locale": locale,
            "response_type": "code",
        }
        
        if self.use_sandbox:
            params["test"] = "true"
        
        auth_endpoint = f"{self.base_url}/api/v1/oauth/authorize"
        url = f"{auth_endpoint}?{urlencode(params)}"
        
        logger.info(f"Generated Tink authorization URL for market {market}")
        return url
    
    async def exchange_code_for_token(self, code: str) -> Dict:
        """
        Exchange authorization code for access token
        
        Args:
            code: Authorization code from callback
        
        Returns:
            Token data including access_token, refresh_token, expires_in
        """
        session = await self._get_session()
        
        token_url = f"{self.base_url}/api/v1/oauth/token"
        
        data = {
            "code": code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "authorization_code",
            "redirect_uri": self.redirect_uri,
        }
        
        try:
            async with session.post(token_url, data=data) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Token exchange failed: {error_text}")
                    raise Exception(f"Token exchange failed: {error_text}")
                
                token_data = await response.json()
                logger.info("Successfully exchanged code for Tink access token")
                return token_data
                
        except Exception as e:
            logger.error(f"Error exchanging code for token: {e}")
            raise
    
    async def refresh_access_token(self, refresh_token: str) -> Dict:
        """
        Refresh access token using refresh token
        
        Args:
            refresh_token: Refresh token
        
        Returns:
            New token data
        """
        session = await self._get_session()
        
        token_url = f"{self.base_url}/api/v1/oauth/token"
        
        data = {
            "refresh_token": refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token",
        }
        
        try:
            async with session.post(token_url, data=data) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Token refresh failed: {error_text}")
                    raise Exception(f"Token refresh failed: {error_text}")
                
                token_data = await response.json()
                logger.info("Successfully refreshed Tink access token")
                return token_data
                
        except Exception as e:
            logger.error(f"Error refreshing token: {e}")
            raise

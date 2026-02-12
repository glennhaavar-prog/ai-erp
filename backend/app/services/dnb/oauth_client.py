"""
DNB OAuth2 Client - Handles authentication flow
"""
import httpx
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

from app.config import settings


logger = logging.getLogger(__name__)


class DNBOAuth2Client:
    """
    DNB OAuth2 Client
    
    Implements OAuth2 Authorization Code Flow for DNB Open Banking API.
    Handles token acquisition, refresh, and management.
    """
    
    # DNB OAuth2 endpoints (sandbox for testing, production for live)
    SANDBOX_BASE_URL = "https://api.sandbox.dnb.no"
    PRODUCTION_BASE_URL = "https://api.dnb.no"
    
    OAUTH_AUTHORIZE_PATH = "/oauth2/authorize"
    OAUTH_TOKEN_PATH = "/oauth2/token"
    OAUTH_REVOKE_PATH = "/oauth2/revoke"
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        api_key: str,
        redirect_uri: str,
        use_sandbox: bool = True
    ):
        """
        Initialize DNB OAuth2 client
        
        Args:
            client_id: OAuth2 client ID from developer.dnb.no
            client_secret: OAuth2 client secret
            api_key: DNB API key
            redirect_uri: OAuth2 redirect URI (must match registered)
            use_sandbox: Use sandbox environment (True) or production (False)
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.api_key = api_key
        self.redirect_uri = redirect_uri
        self.base_url = self.SANDBOX_BASE_URL if use_sandbox else self.PRODUCTION_BASE_URL
        
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "x-api-key": self.api_key,
                "Content-Type": "application/x-www-form-urlencoded",
            },
            timeout=30.0
        )
    
    def get_authorization_url(self, state: str, scope: str = "psd2:accounts:read psd2:transactions:read") -> str:
        """
        Generate OAuth2 authorization URL
        
        Args:
            state: CSRF protection state parameter (random string)
            scope: OAuth2 scopes (PSD2 Account Information Services)
        
        Returns:
            Authorization URL for user to visit
        """
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": scope,
            "state": state,
        }
        
        url = f"{self.base_url}{self.OAUTH_AUTHORIZE_PATH}?{urlencode(params)}"
        logger.info(f"Generated DNB authorization URL (state={state})")
        return url
    
    async def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access token
        
        Args:
            code: Authorization code from OAuth callback
        
        Returns:
            Token response with access_token, refresh_token, expires_in
        """
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        
        try:
            response = await self.client.post(
                self.OAUTH_TOKEN_PATH,
                data=data
            )
            response.raise_for_status()
            
            token_data = response.json()
            logger.info("Successfully exchanged authorization code for access token")
            
            # Calculate expiration time
            expires_in = token_data.get("expires_in", 3600)
            token_data["expires_at"] = (datetime.now(timezone.utc) + timedelta(seconds=expires_in)).isoformat()
            
            return token_data
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to exchange code for token: {e.response.status_code} - {e.response.text}")
            raise ValueError(f"OAuth token exchange failed: {e.response.text}")
        except Exception as e:
            logger.error(f"Error exchanging authorization code: {e}")
            raise
    
    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh access token using refresh token
        
        Args:
            refresh_token: Valid refresh token
        
        Returns:
            New token response
        """
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        
        try:
            response = await self.client.post(
                self.OAUTH_TOKEN_PATH,
                data=data
            )
            response.raise_for_status()
            
            token_data = response.json()
            logger.info("Successfully refreshed access token")
            
            # Calculate expiration time
            expires_in = token_data.get("expires_in", 3600)
            token_data["expires_at"] = (datetime.now(timezone.utc) + timedelta(seconds=expires_in)).isoformat()
            
            return token_data
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to refresh token: {e.response.status_code} - {e.response.text}")
            raise ValueError(f"Token refresh failed: {e.response.text}")
        except Exception as e:
            logger.error(f"Error refreshing access token: {e}")
            raise
    
    async def revoke_token(self, token: str, token_type_hint: str = "access_token") -> bool:
        """
        Revoke access or refresh token
        
        Args:
            token: Token to revoke
            token_type_hint: Type of token (access_token or refresh_token)
        
        Returns:
            True if revoked successfully
        """
        data = {
            "token": token,
            "token_type_hint": token_type_hint,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        
        try:
            response = await self.client.post(
                self.OAUTH_REVOKE_PATH,
                data=data
            )
            response.raise_for_status()
            
            logger.info(f"Successfully revoked {token_type_hint}")
            return True
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to revoke token: {e.response.status_code} - {e.response.text}")
            return False
        except Exception as e:
            logger.error(f"Error revoking token: {e}")
            return False
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

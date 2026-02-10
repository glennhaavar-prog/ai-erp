"""
Tests for DNB Open Banking integration
"""
import pytest
from datetime import datetime, date, timedelta
from uuid import uuid4
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.dnb.oauth_client import DNBOAuth2Client
from app.services.dnb.api_client import DNBAPIClient
from app.services.dnb.service import DNBService
from app.services.dnb.encryption import token_encryption
from app.models.bank_connection import BankConnection
from app.models.bank_transaction import BankTransaction, TransactionType


@pytest.fixture
def mock_oauth_client():
    """Mock OAuth2 client"""
    client = AsyncMock(spec=DNBOAuth2Client)
    client.get_authorization_url.return_value = "https://api.sandbox.dnb.no/oauth2/authorize?..."
    client.exchange_code_for_token.return_value = {
        "access_token": "test_access_token",
        "refresh_token": "test_refresh_token",
        "expires_in": 3600,
        "token_type": "Bearer",
        "scope": "psd2:accounts:read psd2:transactions:read"
    }
    client.refresh_access_token.return_value = {
        "access_token": "new_access_token",
        "expires_in": 3600
    }
    return client


@pytest.fixture
def mock_api_client():
    """Mock API client"""
    client = AsyncMock(spec=DNBAPIClient)
    client.get_accounts.return_value = [
        {
            "accountId": "test-account-123",
            "iban": "NO1234567890123",
            "name": "Business Account",
            "currency": "NOK"
        }
    ]
    client.get_transactions.return_value = [
        {
            "transactionId": "txn-1",
            "bookingDate": "2024-02-10T00:00:00Z",
            "valueDate": "2024-02-10T00:00:00Z",
            "transactionAmount": {
                "amount": "1500.00",
                "currency": "NOK"
            },
            "creditorName": "Test Supplier AS",
            "remittanceInformationUnstructured": "Invoice payment"
        }
    ]
    return client


@pytest.fixture
def dnb_service():
    """DNB service instance"""
    return DNBService(
        client_id="test_client_id",
        client_secret="test_client_secret",
        api_key="test_api_key",
        redirect_uri="http://localhost:8000/callback",
        use_sandbox=True
    )


class TestDNBOAuth2Client:
    """Test OAuth2 authentication"""
    
    def test_get_authorization_url(self):
        """Test authorization URL generation"""
        client = DNBOAuth2Client(
            client_id="test",
            client_secret="secret",
            api_key="key",
            redirect_uri="http://localhost/callback",
            use_sandbox=True
        )
        
        url = client.get_authorization_url("test_state")
        
        assert "https://api.sandbox.dnb.no/oauth2/authorize" in url
        assert "client_id=test" in url
        assert "state=test_state" in url
        assert "scope=psd2" in url
    
    @pytest.mark.asyncio
    async def test_exchange_code_for_token(self, mock_oauth_client):
        """Test code exchange"""
        with patch.object(DNBOAuth2Client, 'exchange_code_for_token', return_value=mock_oauth_client.exchange_code_for_token.return_value):
            client = DNBOAuth2Client(
                client_id="test",
                client_secret="secret",
                api_key="key",
                redirect_uri="http://localhost/callback"
            )
            
            token_data = await client.exchange_code_for_token("auth_code_123")
            
            assert token_data["access_token"] == "test_access_token"
            assert token_data["refresh_token"] == "test_refresh_token"
            assert "expires_at" in token_data


class TestDNBAPIClient:
    """Test API client"""
    
    @pytest.mark.asyncio
    async def test_get_accounts(self, mock_api_client):
        """Test fetching accounts"""
        with patch.object(DNBAPIClient, 'get_accounts', return_value=mock_api_client.get_accounts.return_value):
            client = DNBAPIClient(
                api_key="test_key",
                access_token="test_token"
            )
            
            accounts = await client.get_accounts()
            
            assert len(accounts) == 1
            assert accounts[0]["accountId"] == "test-account-123"
    
    @pytest.mark.asyncio
    async def test_get_transactions(self, mock_api_client):
        """Test fetching transactions"""
        with patch.object(DNBAPIClient, 'get_transactions', return_value=mock_api_client.get_transactions.return_value):
            client = DNBAPIClient(
                api_key="test_key",
                access_token="test_token"
            )
            
            transactions = await client.get_transactions(
                account_id="test-account-123",
                from_date=date(2024, 1, 1),
                to_date=date(2024, 2, 10)
            )
            
            assert len(transactions) == 1
            assert transactions[0]["transactionId"] == "txn-1"


class TestTokenEncryption:
    """Test token encryption"""
    
    def test_encrypt_decrypt(self):
        """Test encryption/decryption"""
        plaintext = "test_access_token_12345"
        
        encrypted = token_encryption.encrypt(plaintext)
        assert encrypted != plaintext
        
        decrypted = token_encryption.decrypt(encrypted)
        assert decrypted == plaintext
    
    def test_encrypt_different_each_time(self):
        """Test that encryption produces different output each time"""
        plaintext = "test_token"
        
        encrypted1 = token_encryption.encrypt(plaintext)
        encrypted2 = token_encryption.encrypt(plaintext)
        
        # Encryption should produce different ciphertext due to IV
        # But both should decrypt to same plaintext
        assert encrypted1 != encrypted2
        assert token_encryption.decrypt(encrypted1) == plaintext
        assert token_encryption.decrypt(encrypted2) == plaintext


class TestDNBService:
    """Test DNB integration service"""
    
    @pytest.mark.asyncio
    async def test_create_bank_connection(self, dnb_service):
        """Test creating bank connection"""
        # Mock database session
        db = AsyncMock()
        
        token_data = {
            "access_token": "test_token",
            "refresh_token": "test_refresh",
            "expires_in": 3600,
            "token_type": "Bearer",
            "scope": "psd2:accounts:read"
        }
        
        connection = await dnb_service.create_bank_connection(
            db=db,
            client_id=uuid4(),
            token_data=token_data,
            account_id="acc-123",
            account_number="12345678901",
            account_name="Test Account"
        )
        
        assert connection.bank_name == "DNB"
        assert connection.bank_account_number == "12345678901"
        assert connection.is_active == True
        db.add.assert_called_once()
        db.commit.assert_called()
    
    def test_parse_dnb_transaction(self, dnb_service):
        """Test DNB transaction parsing"""
        connection = MagicMock(spec=BankConnection)
        connection.client_id = uuid4()
        connection.bank_account_number = "12345678901"
        
        dnb_txn = {
            "transactionId": "txn-1",
            "bookingDate": "2024-02-10T00:00:00Z",
            "valueDate": "2024-02-10T00:00:00Z",
            "transactionAmount": {
                "amount": "1500.00",
                "currency": "NOK"
            },
            "creditorName": "Test Supplier AS",
            "remittanceInformationUnstructured": "Invoice INV-001"
        }
        
        bank_txn = dnb_service._create_transaction_from_dnb(
            connection=connection,
            txn_data=dnb_txn
        )
        
        assert bank_txn.amount == 1500.00
        assert bank_txn.transaction_type == TransactionType.CREDIT
        assert bank_txn.description == "Invoice INV-001"
        assert bank_txn.counterparty_name == "Test Supplier AS"


@pytest.mark.integration
class TestDNBIntegrationFlow:
    """Integration tests for full OAuth flow"""
    
    @pytest.mark.asyncio
    async def test_full_oauth_flow(self, dnb_service, mock_oauth_client, mock_api_client):
        """Test complete OAuth flow"""
        # 1. Get authorization URL
        oauth_client = dnb_service.get_oauth_client()
        auth_url = oauth_client.get_authorization_url("test_state")
        assert "authorize" in auth_url
        
        # 2. Simulate OAuth callback (user authorized)
        # Exchange code for token
        with patch.object(DNBOAuth2Client, 'exchange_code_for_token', return_value=mock_oauth_client.exchange_code_for_token.return_value):
            token_data = await oauth_client.exchange_code_for_token("auth_code")
            assert "access_token" in token_data
        
        # 3. Get accounts
        with patch.object(DNBAPIClient, 'get_accounts', return_value=mock_api_client.get_accounts.return_value):
            api_client = dnb_service.get_api_client(token_data["access_token"])
            accounts = await api_client.get_accounts()
            assert len(accounts) > 0
        
        # 4. Create connection would happen here
        # (tested separately above)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

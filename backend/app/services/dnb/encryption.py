"""
Token encryption utility for secure storage
"""
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64
import logging

from app.config import settings


logger = logging.getLogger(__name__)


class TokenEncryption:
    """
    Encrypt and decrypt OAuth tokens for secure database storage
    
    Uses Fernet (symmetric encryption) with key derived from SECRET_KEY
    """
    
    def __init__(self):
        """Initialize encryption with key derived from app SECRET_KEY"""
        # Derive encryption key from SECRET_KEY using PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'dnb_token_salt',  # In production, use random salt per connection
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(settings.SECRET_KEY.encode()))
        self.fernet = Fernet(key)
    
    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt plaintext token
        
        Args:
            plaintext: Token string to encrypt
        
        Returns:
            Base64-encoded encrypted token
        """
        try:
            encrypted = self.fernet.encrypt(plaintext.encode())
            return encrypted.decode()
        except Exception as e:
            logger.error(f"Encryption error: {e}")
            raise ValueError("Failed to encrypt token")
    
    def decrypt(self, encrypted: str) -> str:
        """
        Decrypt encrypted token
        
        Args:
            encrypted: Base64-encoded encrypted token
        
        Returns:
            Decrypted plaintext token
        """
        try:
            decrypted = self.fernet.decrypt(encrypted.encode())
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Decryption error: {e}")
            raise ValueError("Failed to decrypt token")


# Global encryption instance
token_encryption = TokenEncryption()

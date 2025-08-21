"""
Encryption utilities for credential management
"""

import json
import base64
import logging
from typing import Dict, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.core.config import settings

logger = logging.getLogger(__name__)


class CredentialEncryption:
    """Handles encryption and decryption of credential data"""
    
    def __init__(self):
        self.key = self._derive_key()
        self.cipher = Fernet(self.key)
    
    def _derive_key(self) -> bytes:
        """Derive encryption key from settings"""
        # Use the encryption key from settings
        key_material = settings.ENCRYPTION_KEY.encode()
        
        # Derive a proper Fernet key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'opsconductor_salt',  # In production, use a random salt per credential
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(key_material))
        return key
    
    def encrypt(self, data: Dict[str, Any]) -> str:
        """Encrypt credential data"""
        try:
            # Convert to JSON string
            json_data = json.dumps(data)
            
            # Encrypt
            encrypted_data = self.cipher.encrypt(json_data.encode())
            
            # Return base64 encoded string
            return base64.urlsafe_b64encode(encrypted_data).decode()
            
        except Exception as e:
            logger.error(f"Failed to encrypt credential data: {e}")
            raise
    
    def decrypt(self, encrypted_data: str) -> Dict[str, Any]:
        """Decrypt credential data"""
        try:
            # Decode from base64
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            
            # Decrypt
            decrypted_data = self.cipher.decrypt(encrypted_bytes)
            
            # Parse JSON
            return json.loads(decrypted_data.decode())
            
        except Exception as e:
            logger.error(f"Failed to decrypt credential data: {e}")
            raise


# Global encryption instance
_encryption = CredentialEncryption()


def encrypt_credential(data: Dict[str, Any]) -> str:
    """Encrypt credential data"""
    return _encryption.encrypt(data)


def decrypt_credential(encrypted_data: str) -> Dict[str, Any]:
    """Decrypt credential data"""
    return _encryption.decrypt(encrypted_data)
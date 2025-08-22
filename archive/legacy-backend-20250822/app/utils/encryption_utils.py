"""
Encryption utilities for secure credential storage.
"""
import json
import base64
from typing import Dict, Any
from cryptography.fernet import Fernet
from app.core.config import settings


class CredentialEncryption:
    """Handle encryption and decryption of credentials."""
    
    def __init__(self):
        """Initialize encryption with key from settings."""
        # Use the secret key from settings, pad/truncate to 32 bytes for Fernet
        key_bytes = settings.SECRET_KEY.encode('utf-8')[:32]
        key_bytes = key_bytes.ljust(32, b'0')  # Pad with zeros if needed
        
        # Fernet requires base64-encoded 32-byte key
        self.key = base64.urlsafe_b64encode(key_bytes)
        self.fernet = Fernet(self.key)
    
    def encrypt_credentials(self, credentials: Dict[str, Any]) -> str:
        """
        Encrypt credential data.
        
        Args:
            credentials: Dictionary containing credential data
            
        Returns:
            str: Encrypted credentials as base64 string
        """
        try:
            # Convert to JSON string
            json_str = json.dumps(credentials)
            
            # Encrypt the JSON string
            encrypted_bytes = self.fernet.encrypt(json_str.encode('utf-8'))
            
            # Return as base64 string for database storage
            return base64.urlsafe_b64encode(encrypted_bytes).decode('utf-8')
        except Exception as e:
            raise ValueError(f"Failed to encrypt credentials: {str(e)}")
    
    def decrypt_credentials(self, encrypted_credentials: str) -> Dict[str, Any]:
        """
        Decrypt credential data.
        
        Args:
            encrypted_credentials: Base64 encoded encrypted credentials
            
        Returns:
            dict: Decrypted credential data
        """
        try:
            # Decode from base64
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_credentials.encode('utf-8'))
            
            # Decrypt the bytes
            decrypted_bytes = self.fernet.decrypt(encrypted_bytes)
            
            # Parse JSON
            json_str = decrypted_bytes.decode('utf-8')
            return json.loads(json_str)
        except Exception as e:
            raise ValueError(f"Failed to decrypt credentials: {str(e)}")


# Global encryption instance
credential_encryption = CredentialEncryption()


def encrypt_password_credentials(username: str, password: str) -> str:
    """
    Encrypt password-based credentials.
    
    Args:
        username: Username for authentication
        password: Password for authentication
        
    Returns:
        str: Encrypted credentials
    """
    credentials = {
        'type': 'password',
        'username': username,
        'password': password
    }
    return credential_encryption.encrypt_credentials(credentials)


def encrypt_ssh_key_credentials(username: str, private_key: str, passphrase: str = None) -> str:
    """
    Encrypt SSH key-based credentials.
    
    Args:
        username: Username for authentication
        private_key: Private SSH key content
        passphrase: Optional passphrase for the private key
        
    Returns:
        str: Encrypted credentials
    """
    credentials = {
        'type': 'ssh_key',
        'username': username,
        'private_key': private_key
    }
    if passphrase:
        credentials['passphrase'] = passphrase
    
    return credential_encryption.encrypt_credentials(credentials)


def decrypt_credentials(encrypted_credentials: str) -> Dict[str, Any]:
    """
    Decrypt any type of credentials.
    
    Args:
        encrypted_credentials: Encrypted credentials string
        
    Returns:
        dict: Decrypted credential data
    """
    return credential_encryption.decrypt_credentials(encrypted_credentials)
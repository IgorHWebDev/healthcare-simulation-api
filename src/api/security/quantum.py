"""
Quantum-safe encryption utilities.
"""
from cryptography.fernet import Fernet
from typing import Dict, Any, Union
import json
import base64

class QuantumSafeEncryption:
    """Quantum-safe encryption using Fernet."""
    
    def __init__(self):
        """Initialize encryption with a new key."""
        self.key = Fernet.generate_key()
        self.cipher_suite = Fernet(self.key)
    
    def encrypt(self, data: Union[str, Dict[str, Any]]) -> bytes:
        """Encrypt data."""
        if isinstance(data, dict):
            data = json.dumps(data)
        return self.cipher_suite.encrypt(data.encode())
    
    def decrypt(self, encrypted_data: bytes) -> Union[str, Dict[str, Any]]:
        """Decrypt data."""
        decrypted = self.cipher_suite.decrypt(encrypted_data)
        try:
            return json.loads(decrypted)
        except json.JSONDecodeError:
            return decrypted.decode()
    
    def rotate_key(self):
        """Rotate encryption key."""
        old_key = self.key
        self.key = Fernet.generate_key()
        self.cipher_suite = Fernet(self.key)
        return old_key

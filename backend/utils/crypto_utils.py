# backend/utils/crypto_utils.py
import base64
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad
import os
from backend.config import TOKEN_AES_SECRET
import logging

logger = logging.getLogger(__name__)

def pad(s):
    """Pad string to AES block size"""
    return s + (16 - len(s) % 16) * chr(16 - len(s) % 16)

def unpad(s):
    """Remove padding from string"""
    return s[:-ord(s[-1])]

def encrypt_token(plain_text: str) -> str:
    """Encrypt OAuth token using AES"""
    try:
        # Ensure key is 32 bytes
        key = TOKEN_AES_SECRET.encode()[:32].ljust(32, b'0')
        cipher = AES.new(key, AES.MODE_ECB)
        padded = pad(plain_text)
        encrypted = cipher.encrypt(padded.encode())
        return base64.b64encode(encrypted).decode()
    except Exception as e:
        logger.error(f"Error encrypting token: {e}")
        raise

def decrypt_token(encrypted_text: str) -> str:
    """Decrypt OAuth token using AES"""
    try:
        # Ensure key is 32 bytes
        key = TOKEN_AES_SECRET.encode()[:32].ljust(32, b'0')
        cipher = AES.new(key, AES.MODE_ECB)
        decoded = base64.b64decode(encrypted_text)
        decrypted = cipher.decrypt(decoded).decode()
        return unpad(decrypted)
    except Exception as e:
        logger.error(f"Error decrypting token: {e}")
        raise

def generate_secure_key(length: int = 32) -> str:
    """Generate a secure random key"""
    return base64.b64encode(get_random_bytes(length)).decode()

def hash_password(password: str) -> str:
    """Hash password for storage"""
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return hash_password(password) == hashed

# JWT utilities
def create_jwt_token(data: dict, expires_delta: int = 30) -> str:
    """Create JWT token"""
    from datetime import datetime, timedelta
    from jose import jwt
    from backend.config import JWT_SECRET_KEY, ALGORITHM
    
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=expires_delta)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_jwt_token(token: str) -> dict:
    """Verify and decode JWT token"""
    from jose import jwt, JWTError
    from backend.config import JWT_SECRET_KEY, ALGORITHM
    
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        logger.error(f"JWT verification failed: {e}")
        raise 
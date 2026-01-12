"""
Authentication Module
====================
JWT autentifikacija i hash lozinki.
"""

import jwt
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AuthManager:
    """
    Klasa za upravljanje autentifikacijom.
    """
    
    def __init__(self, secret_key: Optional[str] = None):
        """
        Inicijalizuje auth manager.
        
        Args:
            secret_key: Secret key za JWT (default: iz env ili generisan)
        """
        self.secret_key = secret_key or os.getenv('JWT_SECRET_KEY') or 'quizmaster-secret-key-change-in-production'
        self.algorithm = 'HS256'
        self.token_expiration_hours = 24
    
    def hash_password(self, password: str) -> str:
        """
        Hash-uje lozinku koristeći bcrypt.
        
        Args:
            password: Plain text lozinka
            
        Returns:
            Hash lozinke
        """
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """
        Proverava da li se lozinka poklapa sa hash-om.
        
        Args:
            password: Plain text lozinka
            password_hash: Hash lozinke
            
        Returns:
            True ako se poklapaju
        """
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'),
                password_hash.encode('utf-8')
            )
        except Exception as e:
            logger.error(f"Greška pri verifikaciji lozinke: {e}")
            return False
    
    def generate_token(self, user_id: int, username: str) -> str:
        """
        Generiše JWT token.
        
        Args:
            user_id: ID korisnika
            username: Korisničko ime
            
        Returns:
            JWT token string
        """
        payload = {
            'user_id': user_id,
            'username': username,
            'exp': datetime.utcnow() + timedelta(hours=self.token_expiration_hours),
            'iat': datetime.utcnow()
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """
        Verifikuje JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            Payload ako je validan, None inače
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token je istekao")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Nevalidan token: {e}")
            return None
    
    def decode_token(self, token: str) -> Optional[Dict]:
        """Dekoduje token bez verifikacije (za debug)."""
        try:
            return jwt.decode(token, options={"verify_signature": False})
        except Exception as e:
            logger.error(f"Greška pri dekodovanju tokena: {e}")
            return None


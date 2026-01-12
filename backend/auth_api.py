"""
Auth API Module
===============
API endpoints za autentifikaciju integrisane u Gradio.
"""

from typing import Optional, Tuple, Dict
import logging
from database import Database
from auth import AuthManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AuthAPI:
    """
    API za autentifikaciju integrisan u Gradio aplikaciju.
    """
    
    def __init__(self):
        """Inicijalizuje Auth API."""
        self.db = Database()
        self.auth = AuthManager()
    
    def register(
        self,
        username: str,
        email: str,
        password: str,
        confirm_password: str
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Registruje novog korisnika.
        
        Args:
            username: Korisničko ime
            email: Email adresa
            password: Lozinka
            confirm_password: Potvrda lozinke
            
        Returns:
            Tuple (success, message, token)
        """
        # Validacija
        if not username or len(username) < 3:
            return False, "Korisničko ime mora imati najmanje 3 karaktera", None
        
        if not email or '@' not in email:
            return False, "Unesite validnu email adresu", None
        
        if not password or len(password) < 6:
            return False, "Lozinka mora imati najmanje 6 karaktera", None
        
        if password != confirm_password:
            return False, "Lozinke se ne poklapaju", None
        
        # Proveri da li korisnik već postoji
        if self.db.get_user_by_username(username):
            return False, "Korisničko ime već postoji", None
        
        if self.db.get_user_by_email(email):
            return False, "Email adresa već postoji", None
        
        # Kreiraj korisnika
        password_hash = self.auth.hash_password(password)
        user_id = self.db.create_user(username, email, password_hash)
        
        if user_id:
            token = self.auth.generate_token(user_id, username)
            logger.info(f"Korisnik registrovan: {username}")
            return True, f"Uspešno ste se registrovali, {username}!", token
        else:
            return False, "Greška pri kreiranju naloga", None
    
    def login(self, username: str, password: str) -> Tuple[bool, str, Optional[str], Optional[Dict]]:
        """
        Prijavljuje korisnika.
        
        Args:
            username: Korisničko ime ili email
            password: Lozinka
            
        Returns:
            Tuple (success, message, token, user_data)
        """
        if not username or not password:
            return False, "Unesite korisničko ime i lozinku", None, None
        
        # Pronađi korisnika po username ili email
        user = self.db.get_user_by_username(username)
        if not user:
            user = self.db.get_user_by_email(username)
        
        if not user:
            return False, "Neispravno korisničko ime ili lozinka", None, None
        
        # Proveri lozinku
        if not self.auth.verify_password(password, user['password_hash']):
            return False, "Neispravno korisničko ime ili lozinka", None, None
        
        # Generiši token
        token = self.auth.generate_token(user['id'], user['username'])
        user_data = {
            'id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'total_quizzes': user['total_quizzes'],
            'total_score': user['total_score'],
            'average_accuracy': user['average_accuracy']
        }
        
        logger.info(f"Korisnik prijavljen: {username}")
        return True, f"Dobrodošli, {user['username']}!", token, user_data
    
    def verify_user(self, token: str) -> Optional[Dict]:
        """
        Verifikuje token i vraća podatke korisnika.
        
        Args:
            token: JWT token
            
        Returns:
            User data ili None
        """
        payload = self.auth.verify_token(token)
        if not payload:
            return None
        
        user_id = payload.get('user_id')
        if not user_id:
            return None
        
        user = self.db.get_user_by_id(user_id)
        if not user:
            return None
        
        return {
            'id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'total_quizzes': user['total_quizzes'],
            'total_score': user['total_score'],
            'average_accuracy': user['average_accuracy']
        }


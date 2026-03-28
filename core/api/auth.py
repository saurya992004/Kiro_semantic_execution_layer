"""
Authentication & Authorization
Bearer token validation and role-based access control
"""

import base64
import hashlib
import hmac
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple

from core.api.models import TokenData, User


logger = logging.getLogger(__name__)


class AuthManager:
    """Manages authentication and authorization"""
    
    def __init__(self, secret_key: str = "jarvis-secret-key-development"):
        """
        Initialize auth manager
        
        Args:
            secret_key: Secret for signing tokens
        """
        self.secret_key = secret_key
        self.token_cache = {}  # Simple cache for parsed tokens
    
    def generate_token(self, user_id: str, role: str = "user", hours: int = 24) -> str:
        """
        Generate a bearer token
        
        Args:
            user_id: User ID
            role: User role (user or admin)
            hours: Token expiration in hours
            
        Returns:
            Bearer token
        """
        exp = int((datetime.now() + timedelta(hours=hours)).timestamp())
        
        payload = {
            "user_id": user_id,
            "role": role,
            "exp": exp,
        }
        
        # Simple JWT-like format (not cryptographically secure, for demo)
        payload_json = json.dumps(payload).encode()
        payload_b64 = base64.b64encode(payload_json).decode()
        
        # Sign payload
        signature = hmac.new(
            self.secret_key.encode(),
            payload_b64.encode(),
            hashlib.sha256
        ).hexdigest()[:32]
        
        token = f"{payload_b64}.{signature}"
        return token
    
    def verify_token(self, token: str) -> Tuple[bool, Optional[TokenData]]:
        """
        Verify and parse bearer token
        
        Args:
            token: Bearer token (without "Bearer " prefix)
            
        Returns:
            (is_valid, token_data)
        """
        try:
            # Check cache
            if token in self.token_cache:
                cached_data, expiration = self.token_cache[token]
                if expiration > datetime.now():
                    return True, cached_data
                else:
                    del self.token_cache[token]
            
            # Parse token
            parts = token.split(".")
            if len(parts) != 2:
                logger.warning("Invalid token format")
                return False, None
            
            payload_b64, signature = parts
            
            # Verify signature
            expected_sig = hmac.new(
                self.secret_key.encode(),
                payload_b64.encode(),
                hashlib.sha256
            ).hexdigest()[:32]
            
            if not hmac.compare_digest(signature, expected_sig):
                logger.warning("Invalid token signature")
                return False, None
            
            # Parse payload
            payload_json = base64.b64decode(payload_b64).decode()
            payload = json.loads(payload_json)
            
            # Check expiration
            if payload.get("exp", 0) < int(datetime.now().timestamp()):
                logger.warning("Token expired")
                return False, None
            
            # Cache token
            token_data = TokenData(**payload)
            self.token_cache[token] = (
                token_data,
                datetime.now() + timedelta(hours=1)
            )
            
            return True, token_data
        
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            return False, None
    
    def get_user_from_token(self, token: str) -> Optional[User]:
        """
        Get user object from token
        
        Args:
            token: Bearer token
            
        Returns:
            User object or None if invalid
        """
        is_valid, token_data = self.verify_token(token)
        
        if not is_valid or token_data is None:
            return None
        
        user = User(
            user_id=token_data.user_id,
            role=token_data.role,
        )
        
        return user
    
    def require_role(self, user: Optional[User], required_role: str = "user") -> bool:
        """
        Check if user has required role
        
        Args:
            user: User object
            required_role: Required role (user or admin)
            
        Returns:
            True if authorized
        """
        if user is None:
            return False
        
        if required_role == "admin":
            return user.is_admin
        
        return user.role in ["user", "admin"]
    
    def invalidate_token(self, token: str):
        """
        Invalidate a token (revoke)
        
        Args:
            token: Token to revoke
        """
        if token in self.token_cache:
            del self.token_cache[token]
        
        logger.info(f"Token revoked for user")


# Global auth manager instance
_auth_manager: Optional[AuthManager] = None


def get_auth_manager() -> AuthManager:
    """Get global auth manager instance"""
    global _auth_manager
    
    if _auth_manager is None:
        _auth_manager = AuthManager()
    
    return _auth_manager


def setup_auth(secret_key: str = "jarvis-secret-key-development"):
    """
    Setup authentication
    
    Args:
        secret_key: Secret for token signing
    """
    global _auth_manager
    _auth_manager = AuthManager(secret_key=secret_key)

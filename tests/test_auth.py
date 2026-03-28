"""
Unit Tests - Authentication
Tests for AuthManager
"""

import pytest
from datetime import datetime, timedelta

from core.api.auth import AuthManager
from core.api.models import User


class TestAuthManager:
    """Test AuthManager"""
    
    def test_generate_token(self):
        """Test generating a token"""
        auth = AuthManager()
        
        token = auth.generate_token("user_1", role="user", hours=24)
        
        assert token is not None
        assert isinstance(token, str)
        assert "." in token
    
    def test_verify_valid_token(self):
        """Test verifying a valid token"""
        auth = AuthManager()
        
        token = auth.generate_token("user_1", role="user", hours=24)
        is_valid, data = auth.verify_token(token)
        
        assert is_valid
        assert data is not None
        assert data.user_id == "user_1"
        assert data.role == "user"
    
    def test_verify_invalid_token(self):
        """Test verifying an invalid token"""
        auth = AuthManager()
        
        is_valid, data = auth.verify_token("invalid.token")
        
        assert not is_valid
        assert data is None
    
    def test_verify_corrupted_token(self):
        """Test verifying a corrupted token"""
        auth = AuthManager()
        
        token = auth.generate_token("user_1", role="user", hours=24)
        # Corrupt the token
        corrupted = token[:-5] + "xxxxx"
        
        is_valid, data = auth.verify_token(corrupted)
        
        assert not is_valid
    
    def test_token_expiration(self):
        """Test token expiration"""
        auth = AuthManager()
        
        # Generate token that expires in past
        token = auth.generate_token("user_1", role="user", hours=-1)
        
        is_valid, data = auth.verify_token(token)
        
        assert not is_valid
    
    def test_get_user_from_token(self):
        """Test extracting user from token"""
        auth = AuthManager()
        
        token = auth.generate_token("user_1", role="user", hours=24)
        user = auth.get_user_from_token(token)
        
        assert user is not None
        assert user.user_id == "user_1"
        assert user.role == "user"
        assert user.is_admin is False
    
    def test_admin_user_from_token(self):
        """Test extracting admin user from token"""
        auth = AuthManager()
        
        token = auth.generate_token("admin_user", role="admin", hours=24)
        user = auth.get_user_from_token(token)
        
        assert user is not None
        assert user.is_admin is True
    
    def test_require_role_user(self):
        """Test require_role for user"""
        auth = AuthManager()
        
        user = User(user_id="user_1", role="user")
        
        assert auth.require_role(user, "user")
        assert auth.require_role(user, "admin") is False
    
    def test_require_role_admin(self):
        """Test require_role for admin"""
        auth = AuthManager()
        
        admin = User(user_id="admin", role="admin")
        
        assert auth.require_role(admin, "user")
        assert auth.require_role(admin, "admin")
    
    def test_require_role_none(self):
        """Test require_role with None user"""
        auth = AuthManager()
        
        assert auth.require_role(None, "user") is False
    
    def test_token_cache(self):
        """Test token caching"""
        auth = AuthManager()
        
        token = auth.generate_token("user_1", role="user", hours=24)
        
        # First verification (cache miss)
        is_valid1, _ = auth.verify_token(token)
        
        # Second verification (cache hit)
        is_valid2, _ = auth.verify_token(token)
        
        assert is_valid1
        assert is_valid2
    
    def test_invalidate_token(self):
        """Test token invalidation"""
        auth = AuthManager()
        
        token = auth.generate_token("user_1", role="user", hours=24)
        
        # Verify token works
        is_valid1, _ = auth.verify_token(token)
        assert is_valid1
        
        # Invalidate token
        auth.invalidate_token(token)
        
        # Token should still be technically valid (not expired),
        # but cache was cleared
        is_valid2, _ = auth.verify_token(token)
        assert is_valid2  # Will re-verify from scratch


class TestAuthManagerIntegration:
    """Integration tests for authentication"""
    
    def test_auth_workflow(self):
        """Test complete authentication workflow"""
        auth = AuthManager(secret_key="test-secret")
        
        # Step 1: Generate token
        token = auth.generate_token("user_1", role="user", hours=24)
        assert token is not None
        
        # Step 2: Verify token
        is_valid, data = auth.verify_token(token)
        assert is_valid
        
        # Step 3: Extract user
        user = auth.get_user_from_token(token)
        assert user is not None
        
        # Step 4: Check permissions
        can_access_user_endpoint = auth.require_role(user, "user")
        can_access_admin_endpoint = auth.require_role(user, "admin")
        
        assert can_access_user_endpoint
        assert not can_access_admin_endpoint


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

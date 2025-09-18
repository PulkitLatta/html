import pytest
from app.utils.auth import get_password_hash, verify_password, create_access_token
from app.utils.auth import get_current_user
from fastapi.security import HTTPAuthorizationCredentials
import uuid

class TestAuthentication:
    
    def test_password_hashing(self):
        """Test password hashing and verification"""
        password = "test_password_123"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert verify_password(password, hashed) is True
        assert verify_password("wrong_password", hashed) is False
    
    def test_create_access_token(self):
        """Test JWT token creation"""
        user_id = uuid.uuid4()
        token_data = {"sub": str(user_id), "type": "athlete"}
        
        token = create_access_token(data=token_data)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 50  # JWT tokens are typically long
    
    @pytest.mark.asyncio
    async def test_invalid_token(self, db_session):
        """Test handling of invalid tokens"""
        from fastapi import HTTPException
        
        # Test with invalid token
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="invalid_token_here"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials, db_session)
        
        assert exc_info.value.status_code == 401
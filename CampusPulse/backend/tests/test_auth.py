import pytest
from app.utils.auth import (
    verify_password, get_password_hash, create_access_token,
    verify_token, validate_password_strength
)

def test_password_hashing():
    """Test password hashing and verification."""
    password = "TestPassword123!"
    hashed = get_password_hash(password)
    
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword", hashed) is False

def test_create_access_token():
    """Test JWT access token creation."""
    test_data = {"sub": "test-user", "username": "testuser"}
    token = create_access_token(test_data)
    
    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 0

def test_verify_token():
    """Test JWT token verification."""
    test_data = {"sub": "test-user", "username": "testuser"}
    token = create_access_token(test_data)
    
    # Valid token
    payload = verify_token(token, "access")
    assert payload is not None
    assert payload["sub"] == "test-user"
    assert payload["username"] == "testuser"
    
    # Invalid token
    invalid_payload = verify_token("invalid-token", "access")
    assert invalid_payload is None

def test_password_strength_validation():
    """Test password strength validation."""
    # Strong password
    strong_result = validate_password_strength("StrongPass123!")
    assert strong_result["is_valid"] is True
    assert strong_result["strength"] in ["Good", "Strong"]
    assert len(strong_result["issues"]) == 0
    
    # Weak password
    weak_result = validate_password_strength("weak")
    assert weak_result["is_valid"] is False
    assert len(weak_result["issues"]) > 0
    assert "Password must be at least 8 characters long" in weak_result["issues"]
    
    # Common password
    common_result = validate_password_strength("password")
    assert common_result["is_valid"] is False
    assert "Password is too common" in common_result["issues"]

def test_token_with_wrong_type():
    """Test token verification with wrong token type."""
    test_data = {"sub": "test-user"}
    access_token = create_access_token(test_data)
    
    # Try to verify access token as refresh token
    payload = verify_token(access_token, "refresh")
    assert payload is None
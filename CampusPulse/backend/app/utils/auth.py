import os
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from passlib.context import CryptContext
from fastapi import HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

security = HTTPBearer()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash password."""
    return pwd_context.hash(password)

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt

def create_refresh_token(data: Dict[str, Any]) -> str:
    """Create JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt

def verify_token(token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
    """Verify JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Check token type
        if payload.get("type") != token_type:
            return None
        
        # Check expiration
        exp = payload.get("exp")
        if exp and datetime.utcnow() > datetime.fromtimestamp(exp):
            return None
        
        return payload
    except jwt.PyJWTError:
        return None

def get_token_from_request(request: Request) -> Optional[str]:
    """Extract token from request headers."""
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return None
    
    try:
        scheme, token = auth_header.split()
        if scheme.lower() != "bearer":
            return None
        return token
    except ValueError:
        return None

async def get_current_user(request: Request) -> Optional[Dict[str, Any]]:
    """Get current user from JWT token."""
    token = get_token_from_request(request)
    if not token:
        return None
    
    payload = verify_token(token, "access")
    if not payload:
        return None
    
    return {
        "user_id": payload.get("sub"),
        "username": payload.get("username"),
        "email": payload.get("email"),
        "role": payload.get("role", "athlete"),
        "is_verified": payload.get("is_verified", False)
    }

async def require_auth(request: Request) -> Dict[str, Any]:
    """Require authentication - raises exception if not authenticated."""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

async def require_verified_user(request: Request) -> Dict[str, Any]:
    """Require authenticated and verified user."""
    user = await require_auth(request)
    if not user.get("is_verified"):
        raise HTTPException(
            status_code=403,
            detail="Email verification required"
        )
    return user

async def require_admin(request: Request) -> Dict[str, Any]:
    """Require admin role."""
    user = await require_auth(request)
    if user.get("role") != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    return user

async def require_coach_or_admin(request: Request) -> Dict[str, Any]:
    """Require coach or admin role."""
    user = await require_auth(request)
    if user.get("role") not in ["coach", "admin"]:
        raise HTTPException(
            status_code=403,
            detail="Coach or admin access required"
        )
    return user

def create_tokens_for_user(user_data: Dict[str, Any]) -> Dict[str, str]:
    """Create both access and refresh tokens for user."""
    token_data = {
        "sub": str(user_data["user_id"]),
        "username": user_data["username"],
        "email": user_data["email"],
        "role": user_data.get("role", "athlete"),
        "is_verified": user_data.get("is_verified", False)
    }
    
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

def refresh_access_token(refresh_token: str) -> Optional[Dict[str, str]]:
    """Create new access token from refresh token."""
    payload = verify_token(refresh_token, "refresh")
    if not payload:
        return None
    
    # Create new access token with same user data
    new_token_data = {
        "sub": payload.get("sub"),
        "username": payload.get("username"),
        "email": payload.get("email"),
        "role": payload.get("role", "athlete"),
        "is_verified": payload.get("is_verified", False)
    }
    
    access_token = create_access_token(new_token_data)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,  # Keep same refresh token
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

# Security middleware for rate limiting by user
def get_user_identifier(request: Request) -> str:
    """Get user identifier for rate limiting."""
    # Try to get user ID from token first
    user = None
    try:
        # This is a synchronous version for rate limiting
        token = get_token_from_request(request)
        if token:
            payload = verify_token(token, "access")
            if payload:
                return f"user:{payload.get('sub')}"
    except Exception:
        pass
    
    # Fall back to IP address
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return f"ip:{forwarded_for.split(',')[0].strip()}"
    
    host = request.client.host if request.client else "unknown"
    return f"ip:{host}"

# Password strength validation
def validate_password_strength(password: str) -> Dict[str, Any]:
    """Validate password strength and return feedback."""
    issues = []
    score = 0
    
    if len(password) < 8:
        issues.append("Password must be at least 8 characters long")
    else:
        score += 1
    
    if not any(c.isupper() for c in password):
        issues.append("Password must contain at least one uppercase letter")
    else:
        score += 1
    
    if not any(c.islower() for c in password):
        issues.append("Password must contain at least one lowercase letter")
    else:
        score += 1
    
    if not any(c.isdigit() for c in password):
        issues.append("Password must contain at least one digit")
    else:
        score += 1
    
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        issues.append("Password should contain at least one special character")
    else:
        score += 1
    
    # Check for common patterns
    if password.lower() in ["password", "123456", "qwerty", "admin"]:
        issues.append("Password is too common")
        score = 0
    
    strength_levels = ["Very Weak", "Weak", "Fair", "Good", "Strong"]
    strength = strength_levels[min(score, 4)]
    
    return {
        "is_valid": len(issues) == 0,
        "issues": issues,
        "strength": strength,
        "score": score
    }

# Token blacklist (in production, use Redis)
_token_blacklist = set()

def blacklist_token(token: str) -> None:
    """Add token to blacklist."""
    _token_blacklist.add(token)

def is_token_blacklisted(token: str) -> bool:
    """Check if token is blacklisted."""
    return token in _token_blacklist

async def get_current_user_with_blacklist_check(request: Request) -> Optional[Dict[str, Any]]:
    """Get current user with blacklist check."""
    token = get_token_from_request(request)
    if not token or is_token_blacklisted(token):
        return None
    
    return await get_current_user(request)
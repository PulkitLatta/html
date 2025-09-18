from datetime import datetime, timedelta
from typing import Union, Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.main import get_db
from app import crud
import uuid

# Security configuration
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get current authenticated user (athlete or admin)"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        user_type: str = payload.get("type")
        
        if user_id is None or user_type is None:
            raise credentials_exception
        
        user_uuid = uuid.UUID(user_id)
        
    except (JWTError, ValueError):
        raise credentials_exception
    
    # Get user based on type
    if user_type == "athlete":
        user = crud.get_athlete(db, athlete_id=user_uuid)
        if user is None:
            raise credentials_exception
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Inactive account"
            )
    elif user_type == "admin":
        user = db.query(crud.Admin).filter(crud.Admin.id == user_uuid).first()
        if user is None:
            raise credentials_exception
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Inactive admin account"
            )
    else:
        raise credentials_exception
    
    return user

async def get_current_athlete(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get current authenticated athlete (athletes only)"""
    user = await get_current_user(credentials, db)
    
    # Check if user is an athlete (has no 'role' attribute or role is not admin-related)
    if hasattr(user, 'role') and user.role in ['admin', 'super_admin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Athlete access required"
        )
    
    return user

async def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get current authenticated admin (admins only)"""
    user = await get_current_user(credentials, db)
    
    # Check if user is an admin
    if not (hasattr(user, 'role') and user.role in ['admin', 'super_admin']):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return user

def require_role(required_roles: list):
    """Decorator factory for role-based access control"""
    def role_checker(current_user = Depends(get_current_user)):
        if not hasattr(current_user, 'role'):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        if current_user.role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required role: {', '.join(required_roles)}"
            )
        
        return current_user
    
    return role_checker

# Role-based dependency shortcuts
require_admin = require_role(['admin', 'super_admin'])
require_super_admin = require_role(['super_admin'])

def create_api_key(user_id: uuid.UUID, user_type: str, expires_days: int = 30) -> str:
    """Create a long-lived API key for external integrations"""
    expires_delta = timedelta(days=expires_days)
    return create_access_token(
        data={"sub": str(user_id), "type": user_type, "api_key": True},
        expires_delta=expires_delta
    )

async def verify_api_key(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Verify API key for external service access"""
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        user_type: str = payload.get("type")
        is_api_key: bool = payload.get("api_key", False)
        
        if user_id is None or user_type is None or not is_api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )
        
        user_uuid = uuid.UUID(user_id)
        
        # Verify user still exists and is active
        if user_type == "athlete":
            user = crud.get_athlete(db, athlete_id=user_uuid)
        else:
            user = db.query(crud.Admin).filter(crud.Admin.id == user_uuid).first()
        
        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )
        
        return user
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
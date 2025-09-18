import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app, get_db
from app.models import Base
from app.utils.auth import create_access_token

# Use in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database dependency override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()

@pytest.fixture
def test_user_data():
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "username": "testuser",
        "password": "TestPass123!",
        "full_name": "Test User",
        "university": "Test University",
        "sport": "Basketball"
    }

@pytest.fixture
def test_user_token(test_user_data):
    """Create a test user access token."""
    token_data = {
        "sub": "test-user-id",
        "username": test_user_data["username"],
        "email": test_user_data["email"],
        "role": "athlete",
        "is_verified": True
    }
    return create_access_token(token_data)

@pytest.fixture
def admin_token():
    """Create an admin access token."""
    token_data = {
        "sub": "admin-user-id",
        "username": "admin",
        "email": "admin@example.com",
        "role": "admin",
        "is_verified": True
    }
    return create_access_token(token_data)

@pytest.fixture
def sample_analysis_data():
    """Sample analysis data for testing submissions."""
    return {
        "overallScore": 85.5,
        "formConsistency": 82.0,
        "movementEfficiency": 88.0,
        "techniqueScore": 87.5,
        "balance": 84.0,
        "duration": 15.5,
        "totalFrames": 465,
        "avgConfidence": 0.85,
        "timestamp": 1642291200000,
        "analysisVersion": "1.0.0"
    }

@pytest.fixture
def auth_headers(test_user_token):
    """Authorization headers for authenticated requests."""
    return {"Authorization": f"Bearer {test_user_token}"}

@pytest.fixture
def admin_headers(admin_token):
    """Authorization headers for admin requests."""
    return {"Authorization": f"Bearer {admin_token}"}
import pytest
from uuid import uuid4
from app import crud, schemas

def test_create_user(db_session):
    """Test user creation."""
    user_data = schemas.UserCreate(
        email="test@example.com",
        username="testuser",
        password="TestPass123!",
        full_name="Test User",
        university="Test University",
        sport="Basketball"
    )
    
    user = crud.create_user(db_session, user_data)
    
    assert user.email == user_data.email
    assert user.username == user_data.username
    assert user.full_name == user_data.full_name
    assert user.university == user_data.university
    assert user.sport == user_data.sport
    assert user.is_active is True
    assert user.is_verified is False
    assert user.hashed_password != user_data.password  # Should be hashed

def test_get_user_by_email(db_session, test_user_data):
    """Test getting user by email."""
    # Create user first
    user_create = schemas.UserCreate(**test_user_data)
    created_user = crud.create_user(db_session, user_create)
    
    # Retrieve by email
    retrieved_user = crud.get_user_by_email(db_session, test_user_data["email"])
    
    assert retrieved_user is not None
    assert retrieved_user.id == created_user.id
    assert retrieved_user.email == test_user_data["email"]

def test_get_user_by_username(db_session, test_user_data):
    """Test getting user by username."""
    # Create user first
    user_create = schemas.UserCreate(**test_user_data)
    created_user = crud.create_user(db_session, user_create)
    
    # Retrieve by username
    retrieved_user = crud.get_user_by_username(db_session, test_user_data["username"])
    
    assert retrieved_user is not None
    assert retrieved_user.id == created_user.id
    assert retrieved_user.username == test_user_data["username"]

def test_authenticate_user(db_session, test_user_data):
    """Test user authentication."""
    # Create user first
    user_create = schemas.UserCreate(**test_user_data)
    crud.create_user(db_session, user_create)
    
    # Authenticate with username
    user = crud.authenticate_user(db_session, test_user_data["username"], test_user_data["password"])
    assert user is not None
    assert user.username == test_user_data["username"]
    
    # Authenticate with email
    user = crud.authenticate_user(db_session, test_user_data["email"], test_user_data["password"])
    assert user is not None
    assert user.email == test_user_data["email"]
    
    # Wrong password
    user = crud.authenticate_user(db_session, test_user_data["username"], "WrongPassword")
    assert user is None

def test_update_user(db_session, test_user_data):
    """Test user update."""
    # Create user first
    user_create = schemas.UserCreate(**test_user_data)
    created_user = crud.create_user(db_session, user_create)
    
    # Update user
    update_data = schemas.UserUpdate(
        full_name="Updated Name",
        sport="Football",
        profile_data={"updated": True}
    )
    
    updated_user = crud.update_user(db_session, created_user.id, update_data)
    
    assert updated_user is not None
    assert updated_user.full_name == "Updated Name"
    assert updated_user.sport == "Football"
    assert updated_user.profile_data == {"updated": True}

def test_delete_user(db_session, test_user_data):
    """Test user deletion (soft delete)."""
    # Create user first
    user_create = schemas.UserCreate(**test_user_data)
    created_user = crud.create_user(db_session, user_create)
    
    # Delete user
    success = crud.delete_user(db_session, created_user.id)
    assert success is True
    
    # User should still exist but be inactive
    user = crud.get_user(db_session, created_user.id)
    assert user is not None
    assert user.is_active is False

def test_create_athlete_stats(db_session, test_user_data):
    """Test athlete stats creation."""
    # Create user first
    user_create = schemas.UserCreate(**test_user_data)
    created_user = crud.create_user(db_session, user_create)
    
    # Stats should be automatically created
    stats = crud.get_athlete_stats(db_session, created_user.id)
    assert stats is not None
    assert stats.user_id == created_user.id
    assert stats.total_sessions == 0
    assert stats.weekly_goal == 5

def test_user_not_found(db_session):
    """Test operations with non-existent user."""
    fake_id = uuid4()
    
    user = crud.get_user(db_session, fake_id)
    assert user is None
    
    success = crud.delete_user(db_session, fake_id)
    assert success is False
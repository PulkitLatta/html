import pytest
from app import crud, schemas
from app.models import Athlete
import uuid

class TestAthletesCRUD:
    
    def test_create_athlete(self, db_session, cleanup_db):
        """Test athlete creation"""
        athlete_data = schemas.AthleteCreate(
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            sport="Basketball",
            year="Junior",
            password="testpassword123"
        )
        
        athlete = crud.create_athlete(db_session, athlete_data)
        
        assert athlete.id is not None
        assert athlete.username == "testuser"
        assert athlete.email == "test@example.com"
        assert athlete.full_name == "Test User"
        assert athlete.sport == "Basketball"
        assert athlete.year == "Junior"
        assert athlete.is_active is True
        assert athlete.is_verified is False
    
    def test_get_athlete_by_username(self, db_session, cleanup_db):
        """Test retrieving athlete by username"""
        # Create test athlete
        athlete_data = schemas.AthleteCreate(
            username="findme",
            email="findme@example.com",
            full_name="Find Me",
            password="password123"
        )
        created_athlete = crud.create_athlete(db_session, athlete_data)
        
        # Find the athlete
        found_athlete = crud.get_athlete_by_username(db_session, "findme")
        
        assert found_athlete is not None
        assert found_athlete.id == created_athlete.id
        assert found_athlete.username == "findme"
    
    def test_get_athlete_by_email(self, db_session, cleanup_db):
        """Test retrieving athlete by email"""
        athlete_data = schemas.AthleteCreate(
            username="emailtest",
            email="email@test.com",
            full_name="Email Test",
            password="password123"
        )
        created_athlete = crud.create_athlete(db_session, athlete_data)
        
        found_athlete = crud.get_athlete_by_email(db_session, "email@test.com")
        
        assert found_athlete is not None
        assert found_athlete.id == created_athlete.id
        assert found_athlete.email == "email@test.com"
    
    def test_authenticate_athlete(self, db_session, cleanup_db):
        """Test athlete authentication"""
        password = "mysecretpassword"
        athlete_data = schemas.AthleteCreate(
            username="authtest",
            email="auth@test.com",
            full_name="Auth Test",
            password=password
        )
        
        crud.create_athlete(db_session, athlete_data)
        
        # Test successful authentication
        authenticated = crud.authenticate_athlete(db_session, "authtest", password)
        assert authenticated is not None
        assert authenticated.username == "authtest"
        
        # Test failed authentication
        failed_auth = crud.authenticate_athlete(db_session, "authtest", "wrongpassword")
        assert failed_auth is None
    
    def test_update_athlete(self, db_session, cleanup_db):
        """Test athlete profile update"""
        # Create athlete
        athlete_data = schemas.AthleteCreate(
            username="updatetest",
            email="update@test.com",
            full_name="Update Test",
            sport="Tennis",
            password="password123"
        )
        created_athlete = crud.create_athlete(db_session, athlete_data)
        
        # Update athlete
        update_data = schemas.AthleteUpdate(
            full_name="Updated Name",
            sport="Soccer",
            year="Senior"
        )
        
        updated_athlete = crud.update_athlete(db_session, created_athlete.id, update_data)
        
        assert updated_athlete is not None
        assert updated_athlete.full_name == "Updated Name"
        assert updated_athlete.sport == "Soccer"
        assert updated_athlete.year == "Senior"
        assert updated_athlete.email == "update@test.com"  # Should remain unchanged
    
    def test_get_athletes_list(self, db_session, cleanup_db):
        """Test retrieving list of athletes"""
        # Create multiple athletes
        athletes_data = [
            schemas.AthleteCreate(username=f"user{i}", email=f"user{i}@test.com", 
                                 full_name=f"User {i}", password="pass123")
            for i in range(5)
        ]
        
        for athlete_data in athletes_data:
            crud.create_athlete(db_session, athlete_data)
        
        # Get athletes list
        athletes = crud.get_athletes(db_session, skip=0, limit=10)
        
        assert len(athletes) == 5
        assert all(isinstance(athlete, Athlete) for athlete in athletes)
    
    def test_athlete_stats_update(self, db_session, cleanup_db):
        """Test athlete stats update after submission"""
        # Create athlete
        athlete_data = schemas.AthleteCreate(
            username="statstest",
            email="stats@test.com",
            full_name="Stats Test",
            password="password123"
        )
        athlete = crud.create_athlete(db_session, athlete_data)
        
        # Update stats
        crud.update_athlete_stats(db_session, athlete.id, 85.5)
        
        # Refresh athlete from DB
        db_session.refresh(athlete)
        
        assert athlete.total_sessions == 1
        assert athlete.best_score == 85.5
        assert athlete.average_score == 85.5
        
        # Add another score
        crud.update_athlete_stats(db_session, athlete.id, 92.0)
        db_session.refresh(athlete)
        
        assert athlete.total_sessions == 2
        assert athlete.best_score == 92.0
        assert athlete.average_score == pytest.approx(88.75, rel=1e-2)
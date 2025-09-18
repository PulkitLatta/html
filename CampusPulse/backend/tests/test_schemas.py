import pytest
from app import schemas
from pydantic import ValidationError

def test_user_create_schema_valid():
    """Test UserCreate schema with valid data."""
    user_data = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "StrongPass123!",
        "full_name": "Test User",
        "university": "Test University",
        "sport": "Basketball"
    }
    
    user = schemas.UserCreate(**user_data)
    
    assert user.email == "test@example.com"
    assert user.username == "testuser"
    assert user.password == "StrongPass123!"
    assert user.full_name == "Test User"

def test_user_create_schema_invalid_email():
    """Test UserCreate schema with invalid email."""
    user_data = {
        "email": "invalid-email",
        "username": "testuser",
        "password": "StrongPass123!"
    }
    
    with pytest.raises(ValidationError) as exc_info:
        schemas.UserCreate(**user_data)
    
    assert "value is not a valid email address" in str(exc_info.value)

def test_user_create_schema_weak_password():
    """Test UserCreate schema with weak password."""
    user_data = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "weak"
    }
    
    with pytest.raises(ValidationError) as exc_info:
        schemas.UserCreate(**user_data)
    
    errors = str(exc_info.value)
    assert "Password must contain at least one uppercase letter" in errors

def test_submission_create_schema_valid(sample_analysis_data):
    """Test SubmissionCreate schema with valid data."""
    submission_data = {
        "analysis_data": sample_analysis_data,
        "submission_type": "analysis",
        "video_url": "https://example.com/video.mp4"
    }
    
    submission = schemas.SubmissionCreate(**submission_data)
    
    assert submission.analysis_data == sample_analysis_data
    assert submission.submission_type == "analysis"
    assert submission.video_url == "https://example.com/video.mp4"

def test_submission_create_schema_missing_required_fields():
    """Test SubmissionCreate schema with missing required analysis fields."""
    incomplete_analysis_data = {
        "overallScore": 85.0,
        # Missing required fields: duration, totalFrames
    }
    
    submission_data = {
        "analysis_data": incomplete_analysis_data,
        "submission_type": "analysis"
    }
    
    with pytest.raises(ValidationError) as exc_info:
        schemas.SubmissionCreate(**submission_data)
    
    assert "Missing required field" in str(exc_info.value)

def test_leaderboard_query_schema_valid():
    """Test LeaderboardQuery schema with valid data."""
    query_data = {
        "period": "weekly",
        "category": "sport_specific",
        "sport": "Basketball",
        "limit": 25
    }
    
    query = schemas.LeaderboardQuery(**query_data)
    
    assert query.period == "weekly"
    assert query.category == "sport_specific"
    assert query.sport == "Basketball"
    assert query.limit == 25

def test_leaderboard_query_schema_invalid_period():
    """Test LeaderboardQuery schema with invalid period."""
    query_data = {
        "period": "daily",  # Not in allowed values
        "category": "overall"
    }
    
    with pytest.raises(ValidationError) as exc_info:
        schemas.LeaderboardQuery(**query_data)
    
    assert "string does not match expected pattern" in str(exc_info.value)

def test_athlete_stats_update_schema():
    """Test AthleteStatsUpdate schema validation."""
    update_data = {
        "weekly_goal": 7,
        "training_patterns": {"preferred_time": "morning"}
    }
    
    update = schemas.AthleteStatsUpdate(**update_data)
    
    assert update.weekly_goal == 7
    assert update.training_patterns == {"preferred_time": "morning"}

def test_athlete_stats_update_schema_invalid_goal():
    """Test AthleteStatsUpdate schema with invalid weekly goal."""
    update_data = {
        "weekly_goal": 25  # Too high, max is 20
    }
    
    with pytest.raises(ValidationError) as exc_info:
        schemas.AthleteStatsUpdate(**update_data)
    
    assert "ensure this value is less than or equal to 20" in str(exc_info.value)

def test_forensics_result_schema():
    """Test ForensicsResult schema validation."""
    forensics_data = {
        "analysis_type": "video_hash",
        "verdict": "authentic",
        "confidence": 0.85,
        "analysis_results": {"hash": "abc123", "flags": []},
        "processing_time": 12.5
    }
    
    forensics = schemas.ForensicsResult(**forensics_data)
    
    assert forensics.analysis_type == "video_hash"
    assert forensics.verdict == "authentic"
    assert forensics.confidence == 0.85

def test_forensics_result_schema_invalid_verdict():
    """Test ForensicsResult schema with invalid verdict."""
    forensics_data = {
        "analysis_type": "video_hash",
        "verdict": "invalid",  # Not in allowed values
        "confidence": 0.85,
        "analysis_results": {},
        "processing_time": 12.5
    }
    
    with pytest.raises(ValidationError) as exc_info:
        schemas.ForensicsResult(**forensics_data)
    
    assert "string does not match expected pattern" in str(exc_info.value)

def test_forensics_result_schema_invalid_confidence():
    """Test ForensicsResult schema with invalid confidence value."""
    forensics_data = {
        "analysis_type": "video_hash",
        "verdict": "authentic",
        "confidence": 1.5,  # Too high, max is 1.0
        "analysis_results": {},
        "processing_time": 12.5
    }
    
    with pytest.raises(ValidationError) as exc_info:
        schemas.ForensicsResult(**forensics_data)
    
    assert "ensure this value is less than or equal to 1" in str(exc_info.value)

def test_analysis_data_validator(sample_analysis_data):
    """Test AnalysisDataValidator schema."""
    validator = schemas.AnalysisDataValidator(**sample_analysis_data)
    
    assert validator.overall_score == 85.5
    assert validator.form_consistency == 82.0
    assert validator.movement_efficiency == 88.0
    assert validator.technique_score == 87.5
    assert validator.balance == 84.0

def test_analysis_data_validator_invalid_score():
    """Test AnalysisDataValidator with invalid score values."""
    invalid_data = {
        "overallScore": 105.0,  # Too high, max is 100
        "formConsistency": 82.0,
        "movementEfficiency": 88.0,
        "techniqueScore": 87.5,
        "balance": 84.0,
        "duration": 15.5,
        "totalFrames": 465,
        "avgConfidence": 0.85,
        "timestamp": 1642291200000
    }
    
    with pytest.raises(ValidationError) as exc_info:
        schemas.AnalysisDataValidator(**invalid_data)
    
    assert "ensure this value is less than or equal to 100" in str(exc_info.value)
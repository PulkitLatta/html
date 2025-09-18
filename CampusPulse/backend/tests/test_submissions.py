import pytest
from uuid import uuid4
from app import crud, schemas

def test_create_submission(db_session, test_user_data, sample_analysis_data):
    """Test submission creation."""
    # Create user first
    user_create = schemas.UserCreate(**test_user_data)
    created_user = crud.create_user(db_session, user_create)
    
    # Create submission
    submission_data = schemas.SubmissionCreate(
        analysis_data=sample_analysis_data,
        submission_type="analysis",
        video_url="https://example.com/video.mp4"
    )
    
    submission = crud.create_submission(db_session, submission_data, created_user.id)
    
    assert submission.user_id == created_user.id
    assert submission.analysis_data == sample_analysis_data
    assert submission.submission_type == "analysis"
    assert submission.video_url == "https://example.com/video.mp4"
    assert submission.status == "pending"
    assert submission.overall_score == 85.5
    assert submission.priority_score > 0

def test_get_user_submissions(db_session, test_user_data, sample_analysis_data):
    """Test getting user submissions."""
    # Create user and submissions
    user_create = schemas.UserCreate(**test_user_data)
    created_user = crud.create_user(db_session, user_create)
    
    submission_data = schemas.SubmissionCreate(
        analysis_data=sample_analysis_data,
        submission_type="analysis"
    )
    
    # Create multiple submissions
    crud.create_submission(db_session, submission_data, created_user.id)
    crud.create_submission(db_session, submission_data, created_user.id)
    
    # Get submissions
    submissions = crud.get_user_submissions(db_session, created_user.id)
    assert len(submissions) == 2
    
    # Test with status filter
    submissions_pending = crud.get_user_submissions(
        db_session, created_user.id, status="pending"
    )
    assert len(submissions_pending) == 2

def test_update_submission(db_session, test_user_data, sample_analysis_data):
    """Test submission update."""
    # Create user and submission
    user_create = schemas.UserCreate(**test_user_data)
    created_user = crud.create_user(db_session, user_create)
    
    submission_data = schemas.SubmissionCreate(
        analysis_data=sample_analysis_data,
        submission_type="analysis"
    )
    
    submission = crud.create_submission(db_session, submission_data, created_user.id)
    
    # Update submission
    update_data = schemas.SubmissionUpdate(
        status="completed",
        verification_status="verified",
        forensics_data={"verdict": "authentic"}
    )
    
    updated_submission = crud.update_submission(db_session, submission.id, update_data)
    
    assert updated_submission.status == "completed"
    assert updated_submission.verification_status == "verified"
    assert updated_submission.forensics_data == {"verdict": "authentic"}
    assert updated_submission.processed_at is not None

def test_calculate_priority_score(sample_analysis_data):
    """Test priority score calculation."""
    priority = crud.calculate_priority_score(sample_analysis_data)
    
    # Should be based on overall score (85.5 * 0.6 = 51.3) + confidence bonus
    assert priority > 50
    assert priority <= 100

def test_update_athlete_stats_after_submission(db_session, test_user_data, sample_analysis_data):
    """Test athlete stats update after submission."""
    # Create user
    user_create = schemas.UserCreate(**test_user_data)
    created_user = crud.create_user(db_session, user_create)
    
    # Get initial stats
    initial_stats = crud.get_athlete_stats(db_session, created_user.id)
    assert initial_stats.total_sessions == 0
    
    # Create submission
    submission_data = schemas.SubmissionCreate(
        analysis_data=sample_analysis_data,
        submission_type="analysis"
    )
    
    submission = crud.create_submission(db_session, submission_data, created_user.id)
    
    # Check updated stats
    updated_stats = crud.get_athlete_stats(db_session, created_user.id)
    assert updated_stats.total_sessions == 1
    assert updated_stats.best_score == 85.5
    assert updated_stats.average_score == 85.5
    assert updated_stats.recent_score == 85.5
    assert updated_stats.total_duration == 15.5
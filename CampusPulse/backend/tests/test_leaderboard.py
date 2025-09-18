import pytest
from app import crud, schemas

def test_get_leaderboard_weekly(db_session, test_user_data, sample_analysis_data):
    """Test getting weekly leaderboard."""
    # Create users and submissions
    user1_data = test_user_data.copy()
    user1_data["email"] = "user1@example.com"
    user1_data["username"] = "user1"
    user1 = crud.create_user(db_session, schemas.UserCreate(**user1_data))
    
    user2_data = test_user_data.copy()
    user2_data["email"] = "user2@example.com"
    user2_data["username"] = "user2"
    user2 = crud.create_user(db_session, schemas.UserCreate(**user2_data))
    
    # Create submissions with different scores
    submission1_data = sample_analysis_data.copy()
    submission1_data["overallScore"] = 95.0
    submission1 = crud.create_submission(
        db_session,
        schemas.SubmissionCreate(
            analysis_data=submission1_data,
            submission_type="analysis"
        ),
        user1.id
    )
    
    submission2_data = sample_analysis_data.copy()
    submission2_data["overallScore"] = 85.0
    submission2 = crud.create_submission(
        db_session,
        schemas.SubmissionCreate(
            analysis_data=submission2_data,
            submission_type="analysis"
        ),
        user2.id
    )
    
    # Mark submissions as completed
    crud.update_submission(db_session, submission1.id, schemas.SubmissionUpdate(status="completed"))
    crud.update_submission(db_session, submission2.id, schemas.SubmissionUpdate(status="completed"))
    
    # Get leaderboard
    leaderboard = crud.get_leaderboard(db_session, period="weekly", limit=10)
    
    assert len(leaderboard) == 2
    assert leaderboard[0]["rank"] == 1
    assert leaderboard[0]["score"] == 95.0
    assert leaderboard[0]["username"] == "user1"
    assert leaderboard[1]["rank"] == 2
    assert leaderboard[1]["score"] == 85.0
    assert leaderboard[1]["username"] == "user2"

def test_get_leaderboard_sport_filter(db_session, test_user_data, sample_analysis_data):
    """Test getting leaderboard with sport filter."""
    # Create basketball user
    basketball_data = test_user_data.copy()
    basketball_data["email"] = "basketball@example.com"
    basketball_data["username"] = "basketball_user"
    basketball_data["sport"] = "Basketball"
    basketball_user = crud.create_user(db_session, schemas.UserCreate(**basketball_data))
    
    # Create football user
    football_data = test_user_data.copy()
    football_data["email"] = "football@example.com"
    football_data["username"] = "football_user"
    football_data["sport"] = "Football"
    football_user = crud.create_user(db_session, schemas.UserCreate(**football_data))
    
    # Create submissions for both
    for user in [basketball_user, football_user]:
        submission = crud.create_submission(
            db_session,
            schemas.SubmissionCreate(
                analysis_data=sample_analysis_data,
                submission_type="analysis"
            ),
            user.id
        )
        crud.update_submission(db_session, submission.id, schemas.SubmissionUpdate(status="completed"))
    
    # Get basketball leaderboard
    basketball_leaderboard = crud.get_leaderboard(
        db_session,
        period="weekly",
        category="sport_specific",
        sport="Basketball",
        limit=10
    )
    
    assert len(basketball_leaderboard) == 1
    assert basketball_leaderboard[0]["sport"] == "Basketball"
    assert basketball_leaderboard[0]["username"] == "basketball_user"

def test_get_leaderboard_university_filter(db_session, test_user_data, sample_analysis_data):
    """Test getting leaderboard with university filter."""
    # Create users from different universities
    user1_data = test_user_data.copy()
    user1_data["email"] = "user1@example.com"
    user1_data["username"] = "user1"
    user1_data["university"] = "University A"
    user1 = crud.create_user(db_session, schemas.UserCreate(**user1_data))
    
    user2_data = test_user_data.copy()
    user2_data["email"] = "user2@example.com"
    user2_data["username"] = "user2"
    user2_data["university"] = "University B"
    user2 = crud.create_user(db_session, schemas.UserCreate(**user2_data))
    
    # Create submissions for both
    for user in [user1, user2]:
        submission = crud.create_submission(
            db_session,
            schemas.SubmissionCreate(
                analysis_data=sample_analysis_data,
                submission_type="analysis"
            ),
            user.id
        )
        crud.update_submission(db_session, submission.id, schemas.SubmissionUpdate(status="completed"))
    
    # Get University A leaderboard
    university_leaderboard = crud.get_leaderboard(
        db_session,
        period="weekly",
        category="university",
        university="University A",
        limit=10
    )
    
    assert len(university_leaderboard) == 1
    assert university_leaderboard[0]["university"] == "University A"
    assert university_leaderboard[0]["username"] == "user1"

def test_get_leaderboard_empty(db_session):
    """Test getting leaderboard with no data."""
    leaderboard = crud.get_leaderboard(db_session, period="weekly", limit=10)
    assert len(leaderboard) == 0

def test_get_leaderboard_monthly_vs_weekly(db_session, test_user_data, sample_analysis_data):
    """Test different time periods return different results."""
    # This test would be more meaningful with time-manipulated data
    # For now, we'll just verify the function accepts different periods
    
    weekly_leaderboard = crud.get_leaderboard(db_session, period="weekly")
    monthly_leaderboard = crud.get_leaderboard(db_session, period="monthly")
    all_time_leaderboard = crud.get_leaderboard(db_session, period="all_time")
    
    # All should return empty lists with no data
    assert isinstance(weekly_leaderboard, list)
    assert isinstance(monthly_leaderboard, list)
    assert isinstance(all_time_leaderboard, list)
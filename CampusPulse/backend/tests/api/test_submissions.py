import pytest
from unittest.mock import Mock, patch
import json
import io
from app import crud, schemas
from app.utils.auth import create_access_token
import uuid

class TestSubmissionsAPI:
    
    @pytest.fixture
    def test_athlete(self, db_session):
        """Create a test athlete for submissions"""
        athlete_data = schemas.AthleteCreate(
            username="submissiontester",
            email="submissions@test.com",
            full_name="Submission Tester",
            password="testpass123"
        )
        return crud.create_athlete(db_session, athlete_data)
    
    @pytest.fixture
    def auth_headers(self, test_athlete):
        """Create authentication headers"""
        token = create_access_token(data={"sub": str(test_athlete.id), "type": "athlete"})
        return {"Authorization": f"Bearer {token}"}
    
    @patch('app.utils.storage.save_video_file')
    @patch('app.forensics.queue_forensics_analysis')
    def test_create_submission(self, mock_queue, mock_save_video, client, auth_headers, cleanup_db):
        """Test submission creation"""
        # Mock video file saving
        mock_save_video.return_value = ("http://example.com/video.mp4", "abc123hash")
        mock_queue.return_value = "job_id_123"
        
        # Create mock video file
        video_content = b"fake video content"
        video_file = ("video.mp4", io.BytesIO(video_content), "video/mp4")
        
        # Analysis data
        analysis_data = {
            "formConsistency": 85.5,
            "stability": 90.2,
            "rangeOfMotion": 120.0,
            "timing": 2.5
        }
        
        response = client.post(
            "/api/submissions/",
            files={"video": video_file},
            data={
                "analysis_data": json.dumps(analysis_data),
                "submission_time": "2024-01-15T10:30:00",
                "client_version": "1.0.0"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        submission = response.json()
        
        assert submission["video_url"] == "http://example.com/video.mp4"
        assert submission["overall_score"] > 0
        assert submission["form_consistency"] == 85.5
        assert submission["stability"] == 90.2
        assert submission["forensics_status"] == "pending"
        assert submission["is_verified"] is False
    
    def test_create_submission_invalid_file(self, client, auth_headers):
        """Test submission with invalid file type"""
        # Create mock text file instead of video
        text_file = ("document.txt", io.BytesIO(b"not a video"), "text/plain")
        
        response = client.post(
            "/api/submissions/",
            files={"video": text_file},
            data={"analysis_data": '{"formConsistency": 80}'},
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "File must be a video" in response.json()["detail"]
    
    def test_create_submission_invalid_analysis(self, client, auth_headers):
        """Test submission with invalid analysis data"""
        video_file = ("video.mp4", io.BytesIO(b"fake video"), "video/mp4")
        
        # Missing required fields
        invalid_analysis = {"someField": 123}
        
        response = client.post(
            "/api/submissions/",
            files={"video": video_file},
            data={"analysis_data": json.dumps(invalid_analysis)},
            headers=auth_headers
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_get_my_submissions(self, client, db_session, test_athlete, auth_headers, cleanup_db):
        """Test retrieving athlete's own submissions"""
        # Create a test submission directly in DB
        submission_data = schemas.SubmissionCreate(
            analysis_data={
                "formConsistency": 88.0,
                "stability": 85.5,
                "rangeOfMotion": 110.0,
                "timing": 2.2
            },
            video_hash="test_hash_123",
            submission_time="2024-01-15T10:00:00"
        )
        
        crud.create_submission(
            db=db_session,
            submission=submission_data,
            athlete_id=test_athlete.id,
            video_url="http://example.com/test_video.mp4"
        )
        
        response = client.get("/api/submissions/my", headers=auth_headers)
        
        assert response.status_code == 200
        submissions = response.json()
        
        assert len(submissions) == 1
        assert submissions[0]["athlete_id"] == str(test_athlete.id)
        assert submissions[0]["form_consistency"] == 88.0
    
    def test_get_submissions_unauthorized(self, client):
        """Test getting submissions without authentication"""
        response = client.get("/api/submissions/my")
        
        assert response.status_code == 401
    
    def test_get_leaderboard(self, client, db_session, cleanup_db):
        """Test leaderboard endpoint"""
        # Create some test athletes and submissions
        athletes = []
        for i in range(3):
            athlete_data = schemas.AthleteCreate(
                username=f"leader{i}",
                email=f"leader{i}@test.com",
                full_name=f"Leader {i}",
                password="pass123"
            )
            athlete = crud.create_athlete(db_session, athlete_data)
            athletes.append(athlete)
            
            # Create submissions with different scores
            submission_data = schemas.SubmissionCreate(
                analysis_data={
                    "formConsistency": 80.0 + (i * 5),
                    "stability": 85.0 + (i * 3),
                    "rangeOfMotion": 100.0 + (i * 10),
                    "timing": 2.0
                },
                video_hash=f"hash_{i}",
                submission_time="2024-01-15T10:00:00"
            )
            
            crud.create_submission(
                db=db_session,
                submission=submission_data,
                athlete_id=athlete.id,
                video_url=f"http://example.com/video_{i}.mp4"
            )
        
        response = client.get("/api/submissions/leaderboard/overall")
        
        assert response.status_code == 200
        leaderboard = response.json()
        
        assert len(leaderboard) == 3
        
        # Check that leaderboard is sorted by best score (descending)
        scores = [entry["best_score"] for entry in leaderboard]
        assert scores == sorted(scores, reverse=True)
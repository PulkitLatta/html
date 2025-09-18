from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from typing import List, Optional
import json
import uuid
from datetime import datetime

from app.main import get_db
from app import crud, schemas
from app.utils.auth import get_current_user, get_current_athlete
from app.utils.storage import save_video_file
from app.forensics import queue_forensics_analysis

router = APIRouter()
security = HTTPBearer()

@router.post("/", response_model=schemas.SubmissionResponse)
async def create_submission(
    background_tasks: BackgroundTasks,
    video: UploadFile = File(...),
    analysis_data: str = Form(...),
    athlete_id: Optional[str] = Form(None),
    submission_time: Optional[str] = Form(None),
    client_id: Optional[str] = Form(None),
    client_version: Optional[str] = Form(None),
    device_info: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_athlete)
):
    """Upload a new exercise video with analysis data"""
    
    try:
        # Parse analysis data
        analysis_dict = json.loads(analysis_data)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid analysis data JSON")
    
    # Validate video file
    if not video.content_type.startswith('video/'):
        raise HTTPException(status_code=400, detail="File must be a video")
    
    if video.size > 100 * 1024 * 1024:  # 100MB limit
        raise HTTPException(status_code=400, detail="Video file too large (max 100MB)")
    
    # Save video file and get URL
    try:
        video_url, video_hash = await save_video_file(video)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save video: {str(e)}")
    
    # Parse optional fields
    parsed_submission_time = datetime.fromisoformat(submission_time) if submission_time else datetime.utcnow()
    parsed_device_info = json.loads(device_info) if device_info else None
    
    # Create submission object
    submission_data = schemas.SubmissionCreate(
        analysis_data=analysis_dict,
        video_hash=video_hash,
        submission_time=parsed_submission_time,
        client_version=client_version,
        device_info=parsed_device_info
    )
    
    # Save to database
    db_submission = crud.create_submission(
        db=db,
        submission=submission_data,
        athlete_id=current_user.id,
        video_url=video_url
    )
    
    # Queue forensics analysis
    background_tasks.add_task(
        queue_forensics_analysis,
        submission_id=db_submission.id,
        video_path=video_url
    )
    
    return db_submission

@router.get("/", response_model=List[schemas.SubmissionResponse])
def get_submissions(
    skip: int = 0,
    limit: int = 20,
    exercise_type: Optional[str] = None,
    min_score: Optional[float] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get submissions (admin can see all, athletes see only their own)"""
    
    if current_user.role in ['admin', 'super_admin']:
        # Admin can see all submissions
        submissions = crud.get_submissions(
            db=db,
            skip=skip,
            limit=limit,
            exercise_type=exercise_type,
            min_score=min_score
        )
    else:
        # Athletes can only see their own
        submissions = crud.get_submissions_by_athlete(
            db=db,
            athlete_id=current_user.id,
            skip=skip,
            limit=limit
        )
        
        # Apply filters if provided
        if exercise_type:
            submissions = [s for s in submissions if s.exercise_type == exercise_type]
        if min_score:
            submissions = [s for s in submissions if s.overall_score >= min_score]
    
    return submissions

@router.get("/my", response_model=List[schemas.SubmissionResponse])
def get_my_submissions(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_athlete)
):
    """Get current athlete's submissions"""
    return crud.get_submissions_by_athlete(
        db=db,
        athlete_id=current_user.id,
        skip=skip,
        limit=limit
    )

@router.get("/{submission_id}", response_model=schemas.SubmissionResponse)
def get_submission(
    submission_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get specific submission by ID"""
    submission = crud.get_submission(db, submission_id=submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    # Check permissions
    if (hasattr(current_user, 'role') and current_user.role in ['admin', 'super_admin']) or \
       (hasattr(current_user, 'id') and submission.athlete_id == current_user.id):
        return submission
    else:
        raise HTTPException(status_code=403, detail="Not authorized to view this submission")

@router.get("/leaderboard/overall", response_model=List[schemas.LeaderboardEntry])
def get_overall_leaderboard(
    limit: int = 50,
    sport: Optional[str] = None,
    period: str = "all_time",
    db: Session = Depends(get_db)
):
    """Get overall leaderboard"""
    if period not in ["all_time", "monthly", "weekly"]:
        raise HTTPException(status_code=400, detail="Invalid period. Use 'all_time', 'monthly', or 'weekly'")
    
    leaderboard = crud.get_leaderboard(
        db=db,
        sport=sport,
        period=period,
        limit=limit
    )
    
    # Convert to LeaderboardEntry format
    entries = []
    for entry in leaderboard:
        entries.append(schemas.LeaderboardEntry(
            athlete_id=entry['athlete_id'],
            username=entry['username'],
            full_name=entry['full_name'],
            sport=entry['sport'],
            best_score=entry['best_score'],
            average_score=entry['average_score'],
            total_submissions=entry['total_submissions'],
            overall_rank=entry['rank']
        ))
    
    return entries

@router.get("/analytics/summary")
def get_submission_analytics(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get submission analytics (admin only)"""
    if not (hasattr(current_user, 'role') and current_user.role in ['admin', 'super_admin']):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    return crud.get_analytics_summary(db)

@router.put("/{submission_id}/verify")
def verify_submission(
    submission_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Manually verify a submission (admin only)"""
    if not (hasattr(current_user, 'role') and current_user.role in ['admin', 'super_admin']):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    submission = crud.get_submission(db, submission_id=submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    submission.is_verified = True
    submission.forensics_status = "completed"
    submission.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(submission)
    
    return {"message": "Submission verified successfully", "submission_id": submission_id}

@router.delete("/{submission_id}")
def delete_submission(
    submission_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Delete a submission"""
    submission = crud.get_submission(db, submission_id=submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    # Check permissions (athlete can delete own, admin can delete any)
    if not ((hasattr(current_user, 'role') and current_user.role in ['admin', 'super_admin']) or \
            (hasattr(current_user, 'id') and submission.athlete_id == current_user.id)):
        raise HTTPException(status_code=403, detail="Not authorized to delete this submission")
    
    db.delete(submission)
    db.commit()
    
    return {"message": "Submission deleted successfully"}
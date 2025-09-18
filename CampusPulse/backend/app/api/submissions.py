from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.main import get_db, limiter
from app.utils.auth import get_current_user
from app import crud, schemas

router = APIRouter()

@router.post("/submissions", response_model=schemas.Submission)
@limiter.limit("20/minute")
async def create_submission(
    request: Request,
    submission: schemas.SubmissionCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new submission with analysis data."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    user_id = UUID(current_user["user_id"])
    
    # Validate user exists and is active
    db_user = crud.get_user(db, user_id)
    if not db_user or not db_user.is_active:
        raise HTTPException(status_code=403, detail="User not found or inactive")
    
    # Check daily submission limit
    daily_submissions = len(crud.get_user_submissions(
        db, user_id, limit=50  # Check recent submissions
    ))
    if daily_submissions >= 100:  # Daily limit
        raise HTTPException(
            status_code=429, 
            detail="Daily submission limit exceeded"
        )
    
    # Create submission
    try:
        db_submission = crud.create_submission(db, submission, user_id)
        
        # Queue for forensics analysis in background
        background_tasks.add_task(
            queue_forensics_analysis, 
            db_submission.id, 
            submission.video_url
        )
        
        return db_submission
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create submission: {str(e)}")

@router.get("/submissions/me", response_model=List[schemas.Submission])
@limiter.limit("60/minute")
async def get_my_submissions(
    request: Request,
    skip: int = 0,
    limit: int = 20,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get current user's submissions."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    user_id = UUID(current_user["user_id"])
    
    # Validate limit
    if limit > 100:
        limit = 100
    
    submissions = crud.get_user_submissions(
        db, user_id, skip=skip, limit=limit, status=status
    )
    
    return submissions

@router.get("/submissions/{submission_id}", response_model=schemas.Submission)
@limiter.limit("100/minute")
async def get_submission(
    request: Request,
    submission_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific submission."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    db_submission = crud.get_submission(db, submission_id)
    if not db_submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    # Check if user owns the submission or is admin
    user_id = UUID(current_user["user_id"])
    user_role = current_user.get("role", "athlete")
    
    if db_submission.user_id != user_id and user_role not in ["admin", "coach"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return db_submission

@router.put("/submissions/{submission_id}", response_model=schemas.Submission)
@limiter.limit("30/minute")
async def update_submission(
    request: Request,
    submission_id: UUID,
    submission_update: schemas.SubmissionUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update a submission (admin/system only)."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    user_role = current_user.get("role", "athlete")
    if user_role not in ["admin"]:
        # Regular users can only update their own submissions with limited fields
        user_id = UUID(current_user["user_id"])
        db_submission = crud.get_submission(db, submission_id)
        if not db_submission or db_submission.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Limit what regular users can update
        allowed_updates = {"status"} 
        update_dict = submission_update.dict(exclude_unset=True)
        if set(update_dict.keys()) - allowed_updates:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    updated_submission = crud.update_submission(db, submission_id, submission_update)
    if not updated_submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    return updated_submission

@router.delete("/submissions/{submission_id}")
@limiter.limit("10/minute")
async def delete_submission(
    request: Request,
    submission_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a submission (soft delete)."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    db_submission = crud.get_submission(db, submission_id)
    if not db_submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    # Check permissions
    user_id = UUID(current_user["user_id"])
    user_role = current_user.get("role", "athlete")
    
    if db_submission.user_id != user_id and user_role not in ["admin"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Soft delete by updating status
    deletion_update = schemas.SubmissionUpdate(status="deleted")
    crud.update_submission(db, submission_id, deletion_update)
    
    return {"message": "Submission deleted successfully"}

@router.get("/submissions/{submission_id}/analysis", response_model=dict)
@limiter.limit("50/minute")
async def get_submission_analysis(
    request: Request,
    submission_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get detailed analysis data for a submission."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    db_submission = crud.get_submission(db, submission_id)
    if not db_submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    # Check permissions
    user_id = UUID(current_user["user_id"])
    user_role = current_user.get("role", "athlete")
    
    if db_submission.user_id != user_id and user_role not in ["admin", "coach"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Return the full analysis data with additional metadata
    analysis_data = db_submission.analysis_data.copy()
    analysis_data.update({
        "submission_id": str(submission_id),
        "created_at": db_submission.created_at.isoformat(),
        "verification_status": db_submission.verification_status,
        "priority_score": db_submission.priority_score,
    })
    
    return analysis_data

@router.get("/submissions/{submission_id}/forensics")
@limiter.limit("20/minute") 
async def get_submission_forensics(
    request: Request,
    submission_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get forensics analysis for a submission (admin only)."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    user_role = current_user.get("role", "athlete")
    if user_role not in ["admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    db_submission = crud.get_submission(db, submission_id)
    if not db_submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    return {
        "submission_id": str(submission_id),
        "verification_status": db_submission.verification_status,
        "forensics_data": db_submission.forensics_data or {},
        "created_at": db_submission.created_at.isoformat()
    }

# Background task functions
async def queue_forensics_analysis(submission_id: UUID, video_url: Optional[str]):
    """Queue submission for forensics analysis."""
    # This would integrate with the forensics worker (RQ)
    # For now, just log that it would be queued
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Queuing forensics analysis for submission {submission_id}")
    
    # In production, this would:
    # 1. Add job to Redis queue
    # 2. Worker would process video forensics  
    # 3. Update submission with results
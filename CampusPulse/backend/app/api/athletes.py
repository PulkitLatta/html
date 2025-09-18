from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List
import uuid

from app.main import get_db
from app import crud, schemas
from app.utils.auth import get_current_user, get_current_athlete, create_access_token

router = APIRouter()
security = HTTPBearer()

@router.post("/register", response_model=schemas.AthleteResponse)
def register_athlete(
    athlete: schemas.AthleteCreate,
    db: Session = Depends(get_db)
):
    """Register a new athlete"""
    
    # Check if username already exists
    db_athlete = crud.get_athlete_by_username(db, username=athlete.username)
    if db_athlete:
        raise HTTPException(
            status_code=400,
            detail="Username already registered"
        )
    
    # Check if email already exists
    db_athlete = crud.get_athlete_by_email(db, email=athlete.email)
    if db_athlete:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    # Create new athlete
    return crud.create_athlete(db=db, athlete=athlete)

@router.post("/login", response_model=schemas.Token)
def login_athlete(
    login_request: schemas.LoginRequest,
    db: Session = Depends(get_db)
):
    """Authenticate athlete and return access token"""
    
    athlete = crud.authenticate_athlete(
        db, 
        username=login_request.username, 
        password=login_request.password
    )
    
    if not athlete:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not athlete.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive account",
        )
    
    access_token = create_access_token(
        data={"sub": str(athlete.id), "type": "athlete"}
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 3600  # 1 hour
    }

@router.get("/", response_model=List[schemas.AthleteResponse])
def get_athletes(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get all athletes (admin only)"""
    
    if not (hasattr(current_user, 'role') and current_user.role in ['admin', 'super_admin']):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    athletes = crud.get_athletes(db, skip=skip, limit=limit)
    return athletes

@router.get("/me", response_model=schemas.AthleteResponse)
def get_current_athlete_info(
    current_user: schemas.AthleteResponse = Depends(get_current_athlete)
):
    """Get current athlete's profile"""
    return current_user

@router.get("/{athlete_id}", response_model=schemas.AthleteResponse)
def get_athlete(
    athlete_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get athlete by ID"""
    
    # Athletes can view their own profile, admins can view any
    if not ((hasattr(current_user, 'role') and current_user.role in ['admin', 'super_admin']) or \
            (hasattr(current_user, 'id') and current_user.id == athlete_id)):
        raise HTTPException(status_code=403, detail="Not authorized to view this profile")
    
    db_athlete = crud.get_athlete(db, athlete_id=athlete_id)
    if db_athlete is None:
        raise HTTPException(status_code=404, detail="Athlete not found")
    
    return db_athlete

@router.put("/me", response_model=schemas.AthleteResponse)
def update_current_athlete(
    athlete_update: schemas.AthleteUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_athlete)
):
    """Update current athlete's profile"""
    
    updated_athlete = crud.update_athlete(
        db=db,
        athlete_id=current_user.id,
        athlete_update=athlete_update
    )
    
    if not updated_athlete:
        raise HTTPException(status_code=404, detail="Athlete not found")
    
    return updated_athlete

@router.put("/{athlete_id}", response_model=schemas.AthleteResponse)
def update_athlete(
    athlete_id: uuid.UUID,
    athlete_update: schemas.AthleteUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update athlete profile (admin only)"""
    
    if not (hasattr(current_user, 'role') and current_user.role in ['admin', 'super_admin']):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    updated_athlete = crud.update_athlete(
        db=db,
        athlete_id=athlete_id,
        athlete_update=athlete_update
    )
    
    if not updated_athlete:
        raise HTTPException(status_code=404, detail="Athlete not found")
    
    return updated_athlete

@router.get("/{athlete_id}/submissions", response_model=List[schemas.SubmissionResponse])
def get_athlete_submissions(
    athlete_id: uuid.UUID,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get athlete's submissions"""
    
    # Athletes can view their own submissions, admins can view any
    if not ((hasattr(current_user, 'role') and current_user.role in ['admin', 'super_admin']) or \
            (hasattr(current_user, 'id') and current_user.id == athlete_id)):
        raise HTTPException(status_code=403, detail="Not authorized to view these submissions")
    
    # Verify athlete exists
    athlete = crud.get_athlete(db, athlete_id=athlete_id)
    if not athlete:
        raise HTTPException(status_code=404, detail="Athlete not found")
    
    submissions = crud.get_submissions_by_athlete(
        db=db,
        athlete_id=athlete_id,
        skip=skip,
        limit=limit
    )
    
    return submissions

@router.get("/{athlete_id}/stats")
def get_athlete_stats(
    athlete_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get athlete's detailed statistics"""
    
    # Athletes can view their own stats, admins can view any
    if not ((hasattr(current_user, 'role') and current_user.role in ['admin', 'super_admin']) or \
            (hasattr(current_user, 'id') and current_user.id == athlete_id)):
        raise HTTPException(status_code=403, detail="Not authorized to view these statistics")
    
    athlete = crud.get_athlete(db, athlete_id=athlete_id)
    if not athlete:
        raise HTTPException(status_code=404, detail="Athlete not found")
    
    # Get recent submissions for trend analysis
    recent_submissions = crud.get_submissions_by_athlete(db, athlete_id, limit=10)
    
    # Calculate additional stats
    scores = [s.overall_score for s in recent_submissions]
    
    stats = {
        "basic_stats": {
            "total_sessions": athlete.total_sessions,
            "best_score": athlete.best_score,
            "average_score": athlete.average_score,
        },
        "recent_performance": {
            "recent_scores": scores,
            "trend": "improving" if len(scores) >= 2 and scores[0] > scores[-1] else "stable",
            "recent_sessions": len(recent_submissions),
        },
        "achievements": {
            "verified_submissions": len([s for s in recent_submissions if s.is_verified]),
            "high_scores": len([s for s in recent_submissions if s.overall_score >= 90]),
        }
    }
    
    return stats

@router.delete("/{athlete_id}")
def delete_athlete(
    athlete_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Delete athlete account (admin only)"""
    
    if not (hasattr(current_user, 'role') and current_user.role == 'super_admin'):
        raise HTTPException(status_code=403, detail="Super admin access required")
    
    athlete = crud.get_athlete(db, athlete_id=athlete_id)
    if not athlete:
        raise HTTPException(status_code=404, detail="Athlete not found")
    
    # Soft delete - just deactivate the account
    athlete.is_active = False
    athlete.updated_at = datetime.utcnow()
    
    db.commit()
    
    return {"message": "Athlete account deactivated successfully"}

@router.post("/{athlete_id}/verify")
def verify_athlete(
    athlete_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Verify athlete account (admin only)"""
    
    if not (hasattr(current_user, 'role') and current_user.role in ['admin', 'super_admin']):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    athlete = crud.get_athlete(db, athlete_id=athlete_id)
    if not athlete:
        raise HTTPException(status_code=404, detail="Athlete not found")
    
    athlete.is_verified = True
    athlete.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(athlete)
    
    return {"message": "Athlete verified successfully", "athlete_id": athlete_id}
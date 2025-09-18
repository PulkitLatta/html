from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import uuid
from datetime import datetime

from app.main import get_db
from app import crud, schemas
from app.utils.auth import get_current_user, create_access_token

router = APIRouter()

@router.post("/login", response_model=schemas.Token)
def login_admin(
    login_request: schemas.LoginRequest,
    db: Session = Depends(get_db)
):
    """Admin login endpoint"""
    
    admin = crud.authenticate_admin(
        db, 
        username=login_request.username, 
        password=login_request.password
    )
    
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive admin account",
        )
    
    # Update last login
    admin.last_login = datetime.utcnow()
    db.commit()
    
    access_token = create_access_token(
        data={"sub": str(admin.id), "type": "admin"}
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 3600
    }

@router.post("/create", response_model=schemas.AdminResponse)
def create_admin_account(
    admin: schemas.AdminCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create new admin account (super admin only)"""
    
    if not (hasattr(current_user, 'role') and current_user.role == 'super_admin'):
        raise HTTPException(status_code=403, detail="Super admin access required")
    
    # Check if username already exists
    existing_admin = crud.get_admin_by_username(db, username=admin.username)
    if existing_admin:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    return crud.create_admin(db=db, admin=admin)

@router.get("/dashboard", response_model=schemas.AnalyticsResponse)
def get_admin_dashboard(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get admin dashboard data"""
    
    if not (hasattr(current_user, 'role') and current_user.role in ['admin', 'super_admin']):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Get analytics summary
    analytics = crud.get_analytics_summary(db)
    
    # Add score distribution
    from sqlalchemy import func, case
    score_ranges = db.query(
        func.count(case(
            (crud.Submission.overall_score < 50, 1)
        )).label('below_50'),
        func.count(case(
            (crud.Submission.overall_score.between(50, 70), 1)
        )).label('50_70'),
        func.count(case(
            (crud.Submission.overall_score.between(70, 85), 1)
        )).label('70_85'),
        func.count(case(
            (crud.Submission.overall_score.between(85, 95), 1)
        )).label('85_95'),
        func.count(case(
            (crud.Submission.overall_score >= 95, 1)
        )).label('above_95'),
    ).first()
    
    analytics['score_distribution'] = {
        'below_50': score_ranges.below_50,
        '50_70': score_ranges.50_70,
        '70_85': score_ranges.70_85,
        '85_95': score_ranges.85_95,
        'above_95': score_ranges.above_95,
    }
    
    return analytics

@router.get("/submissions/pending-review")
def get_pending_submissions(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get submissions pending admin review"""
    
    if not (hasattr(current_user, 'role') and current_user.role in ['admin', 'super_admin']):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Get unverified submissions with high fraud scores
    pending = db.query(crud.Submission).filter(
        crud.Submission.is_verified == False,
        crud.Submission.fraud_score > 0.3
    ).order_by(crud.Submission.fraud_score.desc()).limit(limit).all()
    
    return pending

@router.get("/submissions/flagged")
def get_flagged_submissions(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get flagged submissions for review"""
    
    if not (hasattr(current_user, 'role') and current_user.role in ['admin', 'super_admin']):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Get submissions with high fraud scores or processing errors
    flagged = db.query(crud.Submission).filter(
        (crud.Submission.fraud_score > 0.7) | 
        (crud.Submission.forensics_status == 'failed')
    ).order_by(crud.Submission.created_at.desc()).limit(limit).all()
    
    return flagged

@router.post("/submissions/{submission_id}/approve")
def approve_submission(
    submission_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Approve a flagged submission"""
    
    if not (hasattr(current_user, 'role') and current_user.role in ['admin', 'super_admin']):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    submission = crud.get_submission(db, submission_id=submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    submission.is_verified = True
    submission.fraud_score = 0.0
    submission.forensics_status = 'completed'
    submission.updated_at = datetime.utcnow()
    
    db.commit()
    
    return {"message": "Submission approved", "submission_id": submission_id}

@router.post("/submissions/{submission_id}/reject")
def reject_submission(
    submission_id: uuid.UUID,
    reason: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Reject a submission"""
    
    if not (hasattr(current_user, 'role') and current_user.role in ['admin', 'super_admin']):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    submission = crud.get_submission(db, submission_id=submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    # Mark as rejected but keep for audit trail
    submission.is_verified = False
    submission.fraud_score = 1.0
    submission.forensics_status = 'failed'
    submission.updated_at = datetime.utcnow()
    
    # Add rejection reason to forensics data
    if not submission.forensics_data:
        submission.forensics_data = {}
    submission.forensics_data['rejection_reason'] = reason
    submission.forensics_data['rejected_by'] = str(current_user.id)
    submission.forensics_data['rejected_at'] = datetime.utcnow().isoformat()
    
    db.commit()
    
    return {"message": "Submission rejected", "submission_id": submission_id}

@router.get("/athletes/recent")
def get_recent_athletes(
    days: int = 7,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get recently registered athletes"""
    
    if not (hasattr(current_user, 'role') and current_user.role in ['admin', 'super_admin']):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    from datetime import timedelta
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    recent_athletes = db.query(crud.Athlete).filter(
        crud.Athlete.created_at >= cutoff_date
    ).order_by(crud.Athlete.created_at.desc()).limit(limit).all()
    
    return recent_athletes

@router.get("/system/health")
def get_system_health(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get system health metrics (admin only)"""
    
    if not (hasattr(current_user, 'role') and current_user.role in ['admin', 'super_admin']):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Database health
    try:
        db.execute("SELECT 1")
        db_health = "healthy"
    except:
        db_health = "error"
    
    # Processing queue health
    pending_forensics = db.query(crud.Submission).filter(
        crud.Submission.forensics_status == 'pending'
    ).count()
    
    processing_forensics = db.query(crud.Submission).filter(
        crud.Submission.forensics_status == 'processing'
    ).count()
    
    failed_forensics = db.query(crud.Submission).filter(
        crud.Submission.forensics_status == 'failed'
    ).count()
    
    return {
        "database": db_health,
        "processing_queue": {
            "pending": pending_forensics,
            "processing": processing_forensics,
            "failed": failed_forensics,
            "queue_health": "healthy" if pending_forensics < 100 else "backlogged"
        },
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/reports/exercise-metrics")
def get_exercise_metrics(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get exercise performance metrics"""
    
    if not (hasattr(current_user, 'role') and current_user.role in ['admin', 'super_admin']):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    from sqlalchemy import func
    
    metrics = db.query(
        crud.Submission.exercise_type,
        func.avg(crud.Submission.overall_score).label('avg_score'),
        func.count(crud.Submission.id).label('total_submissions'),
        func.avg(crud.Submission.form_consistency).label('avg_form_consistency'),
        func.avg(crud.Submission.stability).label('avg_stability'),
        func.avg(crud.Submission.range_of_motion).label('avg_range_of_motion')
    ).filter(
        crud.Submission.exercise_type.isnot(None)
    ).group_by(crud.Submission.exercise_type).all()
    
    results = []
    for metric in metrics:
        results.append({
            'exercise_type': metric.exercise_type,
            'avg_score': round(float(metric.avg_score), 2),
            'total_submissions': metric.total_submissions,
            'avg_form_consistency': round(float(metric.avg_form_consistency or 0), 2),
            'avg_stability': round(float(metric.avg_stability or 0), 2),
            'avg_range_of_motion': round(float(metric.avg_range_of_motion or 0), 2),
        })
    
    return results

@router.get("/audit-log")
def get_audit_log(
    limit: int = 100,
    skip: int = 0,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get system audit log (super admin only)"""
    
    if not (hasattr(current_user, 'role') and current_user.role == 'super_admin'):
        raise HTTPException(status_code=403, detail="Super admin access required")
    
    audit_logs = db.query(crud.AuditLog).order_by(
        crud.AuditLog.created_at.desc()
    ).offset(skip).limit(limit).all()
    
    return audit_logs
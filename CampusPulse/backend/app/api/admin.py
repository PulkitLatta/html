from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta

from app.main import get_db, limiter
from app.utils.auth import get_current_user, require_admin
from app import crud, schemas

router = APIRouter()

@router.get("/users", response_model=List[schemas.User])
@limiter.limit("30/minute")
async def get_all_users(
    request: Request,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Get all users (admin only)."""
    if limit > 200:
        limit = 200
    
    users = crud.get_users(db, skip=skip, limit=limit)
    return users

@router.get("/users/{user_id}", response_model=schemas.User)  
@limiter.limit("60/minute")
async def get_user_by_id(
    request: Request,
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Get user by ID (admin only)."""
    db_user = crud.get_user(db, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return db_user

@router.put("/users/{user_id}", response_model=schemas.User)
@limiter.limit("20/minute")
async def admin_update_user(
    request: Request,
    user_id: UUID,
    user_update: schemas.AdminUserUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Update any user (admin only)."""
    db_user = crud.get_user(db, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Convert AdminUserUpdate to UserUpdate
    update_dict = user_update.dict(exclude_unset=True)
    general_update = schemas.UserUpdate(**{k: v for k, v in update_dict.items() 
                                           if k in ['full_name', 'university', 'sport', 'profile_data']})
    
    # Update general fields
    if general_update.dict(exclude_unset=True):
        crud.update_user(db, user_id, general_update)
    
    # Update admin-specific fields directly
    if user_update.role is not None:
        db_user.role = user_update.role
    if user_update.is_active is not None:
        db_user.is_active = user_update.is_active
    if user_update.is_verified is not None:
        db_user.is_verified = user_update.is_verified
    
    db_user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_user)
    
    return db_user

@router.delete("/users/{user_id}")
@limiter.limit("10/minute")
async def admin_delete_user(
    request: Request,
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Delete user (admin only)."""
    success = crud.delete_user(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "User deleted successfully"}

@router.get("/submissions", response_model=List[schemas.Submission])
@limiter.limit("30/minute") 
async def get_all_submissions(
    request: Request,
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = None,
    verification_status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Get all submissions with filtering (admin only)."""
    if limit > 200:
        limit = 200
    
    # Build query
    query = db.query(crud.Submission)
    
    if status:
        query = query.filter(crud.Submission.status == status)
    
    if verification_status:
        query = query.filter(crud.Submission.verification_status == verification_status)
    
    submissions = query.order_by(crud.desc(crud.Submission.created_at)).offset(skip).limit(limit).all()
    
    return submissions

@router.get("/submissions/stats")
@limiter.limit("30/minute")
async def get_submission_stats(
    request: Request,
    days: int = 7,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Get submission statistics (admin only)."""
    if days > 365:
        days = 365
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Total submissions
    total_submissions = db.query(crud.Submission).count()
    
    # Recent submissions
    recent_submissions = db.query(crud.Submission).filter(
        crud.Submission.created_at >= start_date
    ).count()
    
    # Status breakdown
    status_stats = db.query(
        crud.Submission.status,
        crud.func.count(crud.Submission.id)
    ).group_by(crud.Submission.status).all()
    
    # Verification status breakdown  
    verification_stats = db.query(
        crud.Submission.verification_status,
        crud.func.count(crud.Submission.id)
    ).group_by(crud.Submission.verification_status).all()
    
    # Average scores
    avg_scores = db.query(
        crud.func.avg(crud.Submission.overall_score),
        crud.func.avg(crud.Submission.form_consistency),
        crud.func.avg(crud.Submission.movement_efficiency),
        crud.func.avg(crud.Submission.technique_score),
        crud.func.avg(crud.Submission.balance_score)
    ).filter(crud.Submission.overall_score.isnot(None)).first()
    
    return {
        "total_submissions": total_submissions,
        "recent_submissions": recent_submissions,
        "period_days": days,
        "status_breakdown": {status: count for status, count in status_stats},
        "verification_breakdown": {status: count for status, count in verification_stats},
        "average_scores": {
            "overall": float(avg_scores[0] or 0),
            "form_consistency": float(avg_scores[1] or 0),
            "movement_efficiency": float(avg_scores[2] or 0), 
            "technique_score": float(avg_scores[3] or 0),
            "balance_score": float(avg_scores[4] or 0)
        }
    }

@router.get("/analytics/usage", response_model=schemas.UsageAnalytics)
@limiter.limit("20/minute")
async def get_usage_analytics(
    request: Request,
    days: int = 7,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Get platform usage analytics (admin only)."""
    if days > 365:
        days = 365
    
    analytics = crud.get_usage_analytics(db, days)
    
    # Get popular endpoints from API usage logs
    start_date = datetime.utcnow() - timedelta(days=days)
    popular_endpoints = db.query(
        crud.APIUsage.endpoint,
        crud.func.count(crud.APIUsage.id).label('count')
    ).filter(
        crud.APIUsage.timestamp >= start_date
    ).group_by(crud.APIUsage.endpoint).order_by(crud.desc('count')).limit(10).all()
    
    return schemas.UsageAnalytics(
        total_users=analytics['total_users'],
        active_users_today=analytics['active_users_period'] if days == 1 else 0,
        active_users_week=analytics['active_users_period'] if days == 7 else 0,
        total_submissions=analytics['total_submissions'],
        submissions_today=analytics['submissions_period'] if days == 1 else 0,
        avg_processing_time=analytics['avg_processing_time'],
        popular_endpoints=[
            {"endpoint": ep, "count": count} for ep, count in popular_endpoints
        ]
    )

@router.get("/users/{user_id}/activity", response_model=schemas.UserActivity)
@limiter.limit("30/minute")
async def get_user_activity(
    request: Request,
    user_id: UUID,
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Get detailed user activity (admin only)."""
    if days > 365:
        days = 365
    
    db_user = crud.get_user(db, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get recent submissions
    submissions = db.query(crud.Submission).filter(
        crud.and_(
            crud.Submission.user_id == user_id,
            crud.Submission.created_at >= start_date
        )
    ).order_by(crud.desc(crud.Submission.created_at)).limit(20).all()
    
    # Get API usage
    api_usage = db.query(crud.APIUsage).filter(
        crud.and_(
            crud.APIUsage.user_id == user_id,
            crud.APIUsage.timestamp >= start_date
        )
    ).order_by(crud.desc(crud.APIUsage.timestamp)).limit(50).all()
    
    recent_activity = []
    
    # Add submissions to activity
    for sub in submissions:
        recent_activity.append({
            "type": "submission",
            "timestamp": sub.created_at.isoformat(),
            "data": {
                "submission_id": str(sub.id),
                "overall_score": sub.overall_score,
                "status": sub.status
            }
        })
    
    # Add API calls to activity (sample)
    for usage in api_usage[:10]:  # Limit to avoid too much data
        recent_activity.append({
            "type": "api_call", 
            "timestamp": usage.timestamp.isoformat(),
            "data": {
                "endpoint": usage.endpoint,
                "method": usage.method,
                "status_code": usage.status_code
            }
        })
    
    # Sort by timestamp
    recent_activity.sort(key=lambda x: x["timestamp"], reverse=True)
    
    return schemas.UserActivity(
        user_id=user_id,
        username=db_user.username,
        last_login=db_user.last_login,
        total_submissions=len(submissions),
        recent_activity=recent_activity[:20]  # Limit to 20 most recent
    )

@router.post("/system/settings", response_model=schemas.SystemSettings)
@limiter.limit("10/minute")
async def create_system_setting(
    request: Request,
    setting: schemas.SystemSettingsCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Create or update system setting (admin only)."""
    db_setting = crud.create_or_update_system_setting(
        db,
        key=setting.key,
        value=setting.value,
        description=setting.description,
        is_public=setting.is_public,
        requires_admin=setting.requires_admin
    )
    
    return db_setting

@router.get("/system/settings")
@limiter.limit("30/minute")
async def get_system_settings(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Get all system settings (admin only)."""
    settings = db.query(crud.SystemSettings).order_by(crud.SystemSettings.key).all()
    return {"settings": settings}

@router.get("/system/settings/{key}", response_model=schemas.SystemSettings)
@limiter.limit("60/minute")
async def get_system_setting(
    request: Request,
    key: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Get specific system setting (admin only)."""
    setting = crud.get_system_setting(db, key)
    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")
    
    return setting

@router.post("/bulk/submissions/update")
@limiter.limit("5/minute")
async def bulk_update_submissions(
    request: Request,
    bulk_update: schemas.BulkSubmissionUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Bulk update submissions (admin only)."""
    updated_count = 0
    errors = []
    
    for submission_id in bulk_update.submission_ids:
        try:
            result = crud.update_submission(db, submission_id, bulk_update.updates)
            if result:
                updated_count += 1
            else:
                errors.append(f"Submission {submission_id} not found")
        except Exception as e:
            errors.append(f"Error updating {submission_id}: {str(e)}")
    
    return {
        "updated_count": updated_count,
        "total_requested": len(bulk_update.submission_ids),
        "errors": errors
    }

@router.post("/bulk/users/update")
@limiter.limit("5/minute")
async def bulk_update_users(
    request: Request,
    bulk_update: schemas.BulkUserUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Bulk update users (admin only)."""
    updated_count = 0
    errors = []
    
    for user_id in bulk_update.user_ids:
        try:
            # Convert to AdminUserUpdate for individual processing
            admin_update = schemas.AdminUserUpdate(**bulk_update.updates.dict(exclude_unset=True))
            # Call the single user update endpoint logic
            db_user = crud.get_user(db, user_id)
            if db_user:
                # Update admin-specific fields
                update_dict = admin_update.dict(exclude_unset=True)
                for field, value in update_dict.items():
                    setattr(db_user, field, value)
                db_user.updated_at = datetime.utcnow()
                db.commit()
                updated_count += 1
            else:
                errors.append(f"User {user_id} not found")
        except Exception as e:
            errors.append(f"Error updating {user_id}: {str(e)}")
    
    return {
        "updated_count": updated_count,
        "total_requested": len(bulk_update.user_ids),
        "errors": errors
    }
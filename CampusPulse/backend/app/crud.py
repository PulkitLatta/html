from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc, and_, or_
from sqlalchemy.dialects.postgresql import insert
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid

from app.models import User, Submission, AthleteStats, Leaderboard, ForensicsLog, SystemSettings, APIUsage
from app.schemas import UserCreate, UserUpdate, SubmissionCreate, SubmissionUpdate, AthleteStatsUpdate
from app.utils.auth import get_password_hash, verify_password

# User CRUD operations
def get_user(db: Session, user_id: uuid.UUID) -> Optional[User]:
    """Get user by ID."""
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email."""
    return db.query(User).filter(User.email == email).first()

def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Get user by username."""
    return db.query(User).filter(User.username == username).first()

def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    """Get multiple users with pagination."""
    return db.query(User).offset(skip).limit(limit).all()

def create_user(db: Session, user: UserCreate) -> User:
    """Create a new user."""
    hashed_password = get_password_hash(user.password)
    db_user = User(
        id=uuid.uuid4(),
        email=user.email,
        username=user.username,
        hashed_password=hashed_password,
        full_name=user.full_name,
        university=user.university,
        sport=user.sport,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Create initial athlete stats
    create_athlete_stats(db, db_user.id)
    
    return db_user

def update_user(db: Session, user_id: uuid.UUID, user_update: UserUpdate) -> Optional[User]:
    """Update user information."""
    db_user = get_user(db, user_id)
    if not db_user:
        return None
    
    update_data = user_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    db_user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """Authenticate user with username and password."""
    user = get_user_by_username(db, username)
    if not user:
        user = get_user_by_email(db, username)
    
    if not user or not verify_password(password, user.hashed_password):
        return None
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    return user

def delete_user(db: Session, user_id: uuid.UUID) -> bool:
    """Soft delete user by marking as inactive."""
    db_user = get_user(db, user_id)
    if not db_user:
        return False
    
    db_user.is_active = False
    db_user.updated_at = datetime.utcnow()
    db.commit()
    return True

# Submission CRUD operations
def get_submission(db: Session, submission_id: uuid.UUID) -> Optional[Submission]:
    """Get submission by ID."""
    return db.query(Submission).filter(Submission.id == submission_id).first()

def get_user_submissions(
    db: Session, 
    user_id: uuid.UUID, 
    skip: int = 0, 
    limit: int = 100,
    status: Optional[str] = None
) -> List[Submission]:
    """Get submissions for a specific user."""
    query = db.query(Submission).filter(Submission.user_id == user_id)
    
    if status:
        query = query.filter(Submission.status == status)
    
    return query.order_by(desc(Submission.created_at)).offset(skip).limit(limit).all()

def create_submission(db: Session, submission: SubmissionCreate, user_id: uuid.UUID) -> Submission:
    """Create a new submission."""
    # Extract metrics from analysis data
    analysis_data = submission.analysis_data
    
    db_submission = Submission(
        id=uuid.uuid4(),
        user_id=user_id,
        analysis_data=analysis_data,
        submission_type=submission.submission_type,
        video_url=submission.video_url,
        overall_score=analysis_data.get('overallScore'),
        form_consistency=analysis_data.get('formConsistency'),
        movement_efficiency=analysis_data.get('movementEfficiency'),
        technique_score=analysis_data.get('techniqueScore'),
        balance_score=analysis_data.get('balance'),
        duration=analysis_data.get('duration'),
        frame_count=analysis_data.get('totalFrames'),
        avg_confidence=analysis_data.get('avgConfidence'),
        priority_score=calculate_priority_score(analysis_data),
    )
    
    db.add(db_submission)
    db.commit()
    db.refresh(db_submission)
    
    # Update athlete stats
    update_athlete_stats_after_submission(db, user_id, db_submission)
    
    return db_submission

def update_submission(
    db: Session, 
    submission_id: uuid.UUID, 
    submission_update: SubmissionUpdate
) -> Optional[Submission]:
    """Update submission."""
    db_submission = get_submission(db, submission_id)
    if not db_submission:
        return None
    
    update_data = submission_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_submission, field, value)
    
    db_submission.updated_at = datetime.utcnow()
    
    if submission_update.status == "completed":
        db_submission.processed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_submission)
    return db_submission

def calculate_priority_score(analysis_data: Dict[str, Any]) -> float:
    """Calculate priority score based on submission characteristics."""
    base_score = analysis_data.get('overallScore', 0.0)
    confidence = analysis_data.get('avgConfidence', 0.0)
    duration = analysis_data.get('duration', 0.0)
    
    # Higher scores get higher priority
    priority = base_score * 0.6
    
    # High confidence gets bonus
    if confidence > 0.8:
        priority += 10
    
    # Longer videos get slight priority boost
    if duration > 10:
        priority += 5
    
    return min(priority, 100.0)

# AthleteStats CRUD operations
def get_athlete_stats(db: Session, user_id: uuid.UUID) -> Optional[AthleteStats]:
    """Get athlete statistics."""
    return db.query(AthleteStats).filter(AthleteStats.user_id == user_id).first()

def create_athlete_stats(db: Session, user_id: uuid.UUID) -> AthleteStats:
    """Create initial athlete statistics."""
    db_stats = AthleteStats(
        id=uuid.uuid4(),
        user_id=user_id,
    )
    db.add(db_stats)
    db.commit()
    db.refresh(db_stats)
    return db_stats

def update_athlete_stats(
    db: Session, 
    user_id: uuid.UUID, 
    stats_update: AthleteStatsUpdate
) -> Optional[AthleteStats]:
    """Update athlete statistics."""
    db_stats = get_athlete_stats(db, user_id)
    if not db_stats:
        return None
    
    update_data = stats_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_stats, field, value)
    
    db_stats.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_stats)
    return db_stats

def update_athlete_stats_after_submission(
    db: Session, 
    user_id: uuid.UUID, 
    submission: Submission
) -> None:
    """Update athlete stats after a new submission."""
    db_stats = get_athlete_stats(db, user_id)
    if not db_stats:
        db_stats = create_athlete_stats(db, user_id)
    
    # Update basic counters
    db_stats.total_sessions += 1
    if submission.duration:
        db_stats.total_duration += submission.duration
    
    # Update scores
    if submission.overall_score:
        if submission.overall_score > db_stats.best_score:
            db_stats.best_score = submission.overall_score
        
        # Update average score (simple moving average)
        if db_stats.total_sessions == 1:
            db_stats.average_score = submission.overall_score
        else:
            db_stats.average_score = (
                (db_stats.average_score * (db_stats.total_sessions - 1) + submission.overall_score) 
                / db_stats.total_sessions
            )
        
        # Update recent score and trend
        if db_stats.recent_score > 0:
            db_stats.score_trend = submission.overall_score - db_stats.recent_score
        db_stats.recent_score = submission.overall_score
    
    # Update weekly/monthly counters
    now = datetime.utcnow()
    week_start = now - timedelta(days=7)
    month_start = now - timedelta(days=30)
    
    weekly_count = db.query(Submission).filter(
        and_(
            Submission.user_id == user_id,
            Submission.created_at >= week_start
        )
    ).count()
    
    monthly_count = db.query(Submission).filter(
        and_(
            Submission.user_id == user_id,
            Submission.created_at >= month_start
        )
    ).count()
    
    db_stats.weekly_sessions = weekly_count
    db_stats.monthly_sessions = monthly_count
    db_stats.last_session = datetime.utcnow()
    db_stats.updated_at = datetime.utcnow()
    
    db.commit()

# Leaderboard operations
def get_leaderboard(
    db: Session,
    period: str = "weekly",
    category: str = "overall",
    sport: Optional[str] = None,
    university: Optional[str] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """Get leaderboard entries."""
    
    # Determine time range
    now = datetime.utcnow()
    if period == "weekly":
        start_date = now - timedelta(days=7)
    elif period == "monthly":
        start_date = now - timedelta(days=30)
    else:  # all_time
        start_date = datetime.min
    
    # Base query - get users with their best scores in the period
    query = db.query(
        User.id,
        User.username,
        User.full_name,
        User.university,
        User.sport,
        func.max(Submission.overall_score).label('best_score'),
        func.count(Submission.id).label('sessions_count')
    ).join(
        Submission, User.id == Submission.user_id
    ).filter(
        and_(
            User.is_active == True,
            Submission.overall_score.isnot(None),
            Submission.created_at >= start_date,
            Submission.status == 'completed'
        )
    )
    
    # Apply category filters
    if category == "sport_specific" and sport:
        query = query.filter(User.sport == sport)
    elif category == "university" and university:
        query = query.filter(User.university == university)
    
    # Group and order
    query = query.group_by(
        User.id, User.username, User.full_name, User.university, User.sport
    ).order_by(
        desc('best_score')
    ).limit(limit)
    
    # Execute query and add ranks
    results = query.all()
    leaderboard = []
    
    for rank, row in enumerate(results, 1):
        leaderboard.append({
            'user_id': row.id,
            'username': row.username,
            'full_name': row.full_name,
            'university': row.university,
            'sport': row.sport,
            'rank': rank,
            'score': row.best_score,
            'sessions_count': row.sessions_count
        })
    
    return leaderboard

# System settings operations
def get_system_setting(db: Session, key: str) -> Optional[SystemSettings]:
    """Get system setting by key."""
    return db.query(SystemSettings).filter(SystemSettings.key == key).first()

def create_or_update_system_setting(
    db: Session,
    key: str,
    value: Dict[str, Any],
    description: Optional[str] = None,
    is_public: bool = False,
    requires_admin: bool = True
) -> SystemSettings:
    """Create or update system setting."""
    stmt = insert(SystemSettings).values(
        key=key,
        value=value,
        description=description,
        is_public=is_public,
        requires_admin=requires_admin
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=['key'],
        set_={
            'value': stmt.excluded.value,
            'description': stmt.excluded.description,
            'is_public': stmt.excluded.is_public,
            'requires_admin': stmt.excluded.requires_admin,
            'updated_at': func.now()
        }
    )
    
    db.execute(stmt)
    db.commit()
    
    return get_system_setting(db, key)

# API usage logging
def log_api_usage(
    db: Session,
    user_id: Optional[uuid.UUID],
    endpoint: str,
    method: str,
    ip_address: Optional[str],
    status_code: int,
    response_time: float
) -> None:
    """Log API usage for analytics."""
    try:
        log_entry = APIUsage(
            id=uuid.uuid4(),
            user_id=user_id,
            endpoint=endpoint,
            method=method,
            ip_address=ip_address,
            status_code=status_code,
            response_time=response_time
        )
        db.add(log_entry)
        db.commit()
    except Exception as e:
        # Don't fail the main request if logging fails
        db.rollback()

# Analytics queries
def get_usage_analytics(db: Session, days: int = 7) -> Dict[str, Any]:
    """Get usage analytics for the last N days."""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    total_users = db.query(User).filter(User.is_active == True).count()
    
    active_users_period = db.query(User.id).join(
        Submission, User.id == Submission.user_id
    ).filter(Submission.created_at >= start_date).distinct().count()
    
    total_submissions = db.query(Submission).count()
    
    submissions_period = db.query(Submission).filter(
        Submission.created_at >= start_date
    ).count()
    
    avg_processing_time = db.query(
        func.avg(APIUsage.response_time)
    ).filter(APIUsage.timestamp >= start_date).scalar() or 0.0
    
    return {
        'total_users': total_users,
        'active_users_period': active_users_period,
        'total_submissions': total_submissions,
        'submissions_period': submissions_period,
        'avg_processing_time': avg_processing_time,
        'period_days': days
    }
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from app.models import Athlete, Submission, Admin, Leaderboard, AuditLog
from app.schemas import AthleteCreate, AthleteUpdate, SubmissionCreate, AdminCreate
from app.utils.auth import get_password_hash, verify_password
from typing import Optional, List, Dict, Any
import uuid
from datetime import datetime, timedelta

# Athlete CRUD operations
def get_athlete(db: Session, athlete_id: uuid.UUID) -> Optional[Athlete]:
    return db.query(Athlete).filter(Athlete.id == athlete_id).first()

def get_athlete_by_username(db: Session, username: str) -> Optional[Athlete]:
    return db.query(Athlete).filter(Athlete.username == username).first()

def get_athlete_by_email(db: Session, email: str) -> Optional[Athlete]:
    return db.query(Athlete).filter(Athlete.email == email).first()

def get_athletes(db: Session, skip: int = 0, limit: int = 100) -> List[Athlete]:
    return db.query(Athlete).offset(skip).limit(limit).all()

def create_athlete(db: Session, athlete: AthleteCreate) -> Athlete:
    hashed_password = get_password_hash(athlete.password)
    db_athlete = Athlete(
        username=athlete.username,
        email=athlete.email,
        hashed_password=hashed_password,
        full_name=athlete.full_name,
        sport=athlete.sport,
        year=athlete.year,
    )
    db.add(db_athlete)
    db.commit()
    db.refresh(db_athlete)
    return db_athlete

def update_athlete(db: Session, athlete_id: uuid.UUID, athlete_update: AthleteUpdate) -> Optional[Athlete]:
    db_athlete = get_athlete(db, athlete_id)
    if not db_athlete:
        return None
    
    update_data = athlete_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_athlete, field, value)
    
    db_athlete.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_athlete)
    return db_athlete

def authenticate_athlete(db: Session, username: str, password: str) -> Optional[Athlete]:
    athlete = get_athlete_by_username(db, username)
    if not athlete or not verify_password(password, athlete.hashed_password):
        return None
    return athlete

# Submission CRUD operations
def get_submission(db: Session, submission_id: uuid.UUID) -> Optional[Submission]:
    return db.query(Submission).filter(Submission.id == submission_id).first()

def get_submissions_by_athlete(
    db: Session, 
    athlete_id: uuid.UUID, 
    skip: int = 0, 
    limit: int = 100
) -> List[Submission]:
    return db.query(Submission)\
        .filter(Submission.athlete_id == athlete_id)\
        .order_by(desc(Submission.created_at))\
        .offset(skip)\
        .limit(limit)\
        .all()

def get_submissions(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    exercise_type: Optional[str] = None,
    min_score: Optional[float] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> List[Submission]:
    query = db.query(Submission)
    
    if exercise_type:
        query = query.filter(Submission.exercise_type == exercise_type)
    if min_score:
        query = query.filter(Submission.overall_score >= min_score)
    if start_date:
        query = query.filter(Submission.created_at >= start_date)
    if end_date:
        query = query.filter(Submission.created_at <= end_date)
    
    return query.order_by(desc(Submission.created_at)).offset(skip).limit(limit).all()

def create_submission(db: Session, submission: SubmissionCreate, athlete_id: uuid.UUID, video_url: str) -> Submission:
    # Calculate overall score from analysis data
    analysis = submission.analysis_data
    overall_score = calculate_overall_score(analysis)
    
    # Calculate priority score (higher for better scores, recent submissions)
    priority_score = calculate_priority_score(overall_score, datetime.utcnow())
    
    db_submission = Submission(
        athlete_id=athlete_id,
        video_url=video_url,
        video_filename=f"video_{uuid.uuid4()}.mp4",
        video_hash=submission.video_hash,
        analysis_data=submission.analysis_data,
        overall_score=overall_score,
        form_consistency=analysis.get('formConsistency'),
        stability=analysis.get('stability'),
        range_of_motion=analysis.get('rangeOfMotion'),
        timing=analysis.get('timing'),
        exercise_type=submission.exercise_type,
        submission_time=submission.submission_time,
        client_version=submission.client_version,
        device_info=submission.device_info,
        priority_score=priority_score,
    )
    
    db.add(db_submission)
    db.commit()
    db.refresh(db_submission)
    
    # Update athlete stats
    update_athlete_stats(db, athlete_id, overall_score)
    
    return db_submission

def calculate_overall_score(analysis_data: Dict[str, Any]) -> float:
    """Calculate weighted overall score from analysis components"""
    consistency = analysis_data.get('formConsistency', 0.0)
    stability = analysis_data.get('stability', 0.0)
    range_motion = analysis_data.get('rangeOfMotion', 0.0)
    timing = analysis_data.get('timing', 0.0)
    
    # Normalize timing (assume optimal timing is around 2-3 seconds)
    normalized_timing = min(100.0, max(0.0, 100.0 - abs(timing - 2.5) * 20))
    
    # Weighted average
    weights = {'consistency': 0.4, 'stability': 0.3, 'range': 0.2, 'timing': 0.1}
    
    score = (
        consistency * weights['consistency'] +
        stability * weights['stability'] +
        min(range_motion / 2.0, 100.0) * weights['range'] +  # Normalize range of motion
        normalized_timing * weights['timing']
    )
    
    return round(min(max(score, 0.0), 100.0), 2)

def calculate_priority_score(overall_score: float, submission_time: datetime) -> float:
    """Calculate priority score for processing queue"""
    # Base score from performance (0-100)
    score_factor = overall_score / 100.0
    
    # Recency factor (higher for more recent submissions)
    hours_old = (datetime.utcnow() - submission_time).total_seconds() / 3600
    recency_factor = max(0.1, 1.0 - (hours_old / 24.0))  # Decay over 24 hours
    
    return score_factor * 50 + recency_factor * 50

def update_athlete_stats(db: Session, athlete_id: uuid.UUID, new_score: float):
    """Update athlete's statistics after new submission"""
    athlete = get_athlete(db, athlete_id)
    if not athlete:
        return
    
    athlete.total_sessions += 1
    athlete.best_score = max(athlete.best_score, new_score)
    
    # Calculate new average
    if athlete.total_sessions == 1:
        athlete.average_score = new_score
    else:
        # Simple moving average
        athlete.average_score = (
            (athlete.average_score * (athlete.total_sessions - 1) + new_score) / 
            athlete.total_sessions
        )
    
    athlete.updated_at = datetime.utcnow()
    db.commit()

# Admin CRUD operations
def get_admin_by_username(db: Session, username: str) -> Optional[Admin]:
    return db.query(Admin).filter(Admin.username == username).first()

def create_admin(db: Session, admin: AdminCreate) -> Admin:
    hashed_password = get_password_hash(admin.password)
    db_admin = Admin(
        username=admin.username,
        email=admin.email,
        hashed_password=hashed_password,
        full_name=admin.full_name,
        role=admin.role,
    )
    db.add(db_admin)
    db.commit()
    db.refresh(db_admin)
    return db_admin

def authenticate_admin(db: Session, username: str, password: str) -> Optional[Admin]:
    admin = get_admin_by_username(db, username)
    if not admin or not verify_password(password, admin.hashed_password):
        return None
    return admin

# Leaderboard operations
def get_leaderboard(
    db: Session,
    sport: Optional[str] = None,
    exercise_type: Optional[str] = None,
    period: str = "all_time",
    limit: int = 50
) -> List[Dict[str, Any]]:
    """Get leaderboard with athlete info"""
    query = db.query(
        Athlete.id,
        Athlete.username,
        Athlete.full_name,
        Athlete.sport,
        func.max(Submission.overall_score).label('best_score'),
        func.avg(Submission.overall_score).label('average_score'),
        func.count(Submission.id).label('total_submissions')
    ).join(Submission, Athlete.id == Submission.athlete_id)
    
    if sport:
        query = query.filter(Athlete.sport == sport)
    if exercise_type:
        query = query.filter(Submission.exercise_type == exercise_type)
    
    if period == "monthly":
        start_date = datetime.utcnow().replace(day=1)
        query = query.filter(Submission.created_at >= start_date)
    elif period == "weekly":
        start_date = datetime.utcnow() - timedelta(days=7)
        query = query.filter(Submission.created_at >= start_date)
    
    results = query.group_by(
        Athlete.id, Athlete.username, Athlete.full_name, Athlete.sport
    ).order_by(desc('best_score')).limit(limit).all()
    
    return [
        {
            'athlete_id': r.id,
            'username': r.username,
            'full_name': r.full_name,
            'sport': r.sport,
            'best_score': float(r.best_score),
            'average_score': float(r.average_score) if r.average_score else 0.0,
            'total_submissions': r.total_submissions,
            'rank': idx + 1
        }
        for idx, r in enumerate(results)
    ]

# Analytics operations
def get_analytics_summary(db: Session) -> Dict[str, Any]:
    """Get system analytics summary"""
    total_athletes = db.query(Athlete).count()
    total_submissions = db.query(Submission).count()
    avg_score = db.query(func.avg(Submission.overall_score)).scalar() or 0.0
    
    # Time-based counts
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = now - timedelta(days=7)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    submissions_today = db.query(Submission).filter(Submission.created_at >= today_start).count()
    submissions_this_week = db.query(Submission).filter(Submission.created_at >= week_start).count()
    submissions_this_month = db.query(Submission).filter(Submission.created_at >= month_start).count()
    
    # Top sports
    top_sports = db.query(
        Athlete.sport,
        func.count(Submission.id).label('submissions')
    ).join(Submission).group_by(Athlete.sport).order_by(desc('submissions')).limit(5).all()
    
    return {
        'total_athletes': total_athletes,
        'total_submissions': total_submissions,
        'avg_score': round(float(avg_score), 2),
        'submissions_today': submissions_today,
        'submissions_this_week': submissions_this_week,
        'submissions_this_month': submissions_this_month,
        'top_sports': [{'sport': s.sport, 'count': s.submissions} for s in top_sports]
    }
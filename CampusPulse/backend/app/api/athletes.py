from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from slowapi import Limiter

from app.main import get_db, limiter  
from app.utils.auth import get_current_user
from app import crud, schemas

router = APIRouter()

@router.get("/athletes/me", response_model=schemas.User)
@limiter.limit("60/minute")
async def get_my_profile(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get current user's profile."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    user_id = UUID(current_user["user_id"])
    db_user = crud.get_user(db, user_id)
    
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return db_user

@router.put("/athletes/me", response_model=schemas.User)
@limiter.limit("20/minute")
async def update_my_profile(
    request: Request,
    user_update: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update current user's profile."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    user_id = UUID(current_user["user_id"])
    
    updated_user = crud.update_user(db, user_id, user_update)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return updated_user

@router.get("/athletes/me/stats", response_model=schemas.AthleteStats)  
@limiter.limit("100/minute")
async def get_my_stats(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get current user's athlete statistics."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    user_id = UUID(current_user["user_id"])
    db_stats = crud.get_athlete_stats(db, user_id)
    
    if not db_stats:
        # Create stats if they don't exist
        db_stats = crud.create_athlete_stats(db, user_id)
    
    return db_stats

@router.put("/athletes/me/stats", response_model=schemas.AthleteStats)
@limiter.limit("10/minute") 
async def update_my_stats(
    request: Request,
    stats_update: schemas.AthleteStatsUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update current user's athlete statistics (limited fields)."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    user_id = UUID(current_user["user_id"])
    
    updated_stats = crud.update_athlete_stats(db, user_id, stats_update)
    if not updated_stats:
        raise HTTPException(status_code=404, detail="Athlete stats not found")
    
    return updated_stats

@router.get("/athletes/{athlete_id}", response_model=schemas.User)
@limiter.limit("100/minute")
async def get_athlete_profile(
    request: Request,
    athlete_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get public profile of another athlete."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    db_user = crud.get_user(db, athlete_id)
    if not db_user or not db_user.is_active:
        raise HTTPException(status_code=404, detail="Athlete not found")
    
    # Return limited public profile info
    public_profile = schemas.User(
        id=db_user.id,
        email="[hidden]",  # Hide email for privacy
        username=db_user.username,
        full_name=db_user.full_name,
        university=db_user.university,
        sport=db_user.sport,
        role=db_user.role,
        is_active=db_user.is_active,
        is_verified=db_user.is_verified,
        profile_data={},  # Hide private profile data
        created_at=db_user.created_at,
        last_login=None  # Hide last login for privacy
    )
    
    return public_profile

@router.get("/athletes/{athlete_id}/stats", response_model=schemas.AthleteStats)
@limiter.limit("100/minute")
async def get_athlete_stats(
    request: Request,
    athlete_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get public statistics of another athlete."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Verify athlete exists
    db_user = crud.get_user(db, athlete_id)
    if not db_user or not db_user.is_active:
        raise HTTPException(status_code=404, detail="Athlete not found")
    
    db_stats = crud.get_athlete_stats(db, athlete_id)
    if not db_stats:
        raise HTTPException(status_code=404, detail="Athlete stats not found")
    
    # Return limited public stats (hide private training data)
    public_stats = schemas.AthleteStats(
        id=db_stats.id,
        user_id=db_stats.user_id,
        total_sessions=db_stats.total_sessions,
        total_duration=db_stats.total_duration,
        current_rank=db_stats.current_rank,
        best_score=db_stats.best_score,
        average_score=db_stats.average_score,
        recent_score=db_stats.recent_score,
        score_trend=db_stats.score_trend,
        consistency_rating=db_stats.consistency_rating,
        weekly_sessions=db_stats.weekly_sessions,
        monthly_sessions=db_stats.monthly_sessions,
        weekly_goal=db_stats.weekly_goal,
        metrics_history={},  # Hide detailed history
        achievements=db_stats.achievements or {},
        training_patterns={},  # Hide private patterns
        created_at=db_stats.created_at,
        updated_at=db_stats.updated_at,
        last_session=db_stats.last_session
    )
    
    return public_stats

@router.get("/leaderboard", response_model=List[schemas.LeaderboardEntry])
@limiter.limit("30/minute")
async def get_leaderboard(
    request: Request,
    period: str = "weekly",
    category: str = "overall", 
    sport: Optional[str] = None,
    university: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get leaderboard for specified period and category."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Validate parameters
    if period not in ["weekly", "monthly", "all_time"]:
        raise HTTPException(status_code=400, detail="Invalid period")
    
    if category not in ["overall", "sport_specific", "university"]:
        raise HTTPException(status_code=400, detail="Invalid category")
    
    if limit > 200:
        limit = 200
    
    # Get leaderboard data
    leaderboard_data = crud.get_leaderboard(
        db, 
        period=period,
        category=category,
        sport=sport,
        university=university,
        limit=limit
    )
    
    # Convert to LeaderboardEntry schema
    entries = []
    for entry in leaderboard_data:
        entries.append(schemas.LeaderboardEntry(
            user_id=entry['user_id'],
            username=entry['username'],
            full_name=entry['full_name'],
            university=entry['university'],
            sport=entry['sport'],
            rank=entry['rank'],
            score=entry['score'],
            sessions_count=entry['sessions_count']
        ))
    
    return entries

@router.get("/athletes/search")
@limiter.limit("30/minute")
async def search_athletes(
    request: Request,
    q: str = "",
    sport: Optional[str] = None,
    university: Optional[str] = None,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Search for athletes by name, sport, or university."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    if len(q) < 2 and not sport and not university:
        raise HTTPException(status_code=400, detail="Search query too short")
    
    if limit > 100:
        limit = 100
    
    # Build search query
    query = db.query(crud.User).filter(crud.User.is_active == True)
    
    if q:
        query = query.filter(
            crud.or_(
                crud.User.username.ilike(f"%{q}%"),
                crud.User.full_name.ilike(f"%{q}%")
            )
        )
    
    if sport:
        query = query.filter(crud.User.sport == sport)
    
    if university:
        query = query.filter(crud.User.university == university)
    
    results = query.limit(limit).all()
    
    # Return limited public info
    athletes = []
    for user in results:
        athletes.append({
            "id": str(user.id),
            "username": user.username,
            "full_name": user.full_name,
            "university": user.university,
            "sport": user.sport,
            "is_verified": user.is_verified
        })
    
    return {"athletes": athletes, "count": len(athletes)}

@router.get("/athletes/me/achievements")
@limiter.limit("60/minute")
async def get_my_achievements(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get current user's achievements and badges."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    user_id = UUID(current_user["user_id"])
    db_stats = crud.get_athlete_stats(db, user_id)
    
    if not db_stats:
        return {"achievements": {}, "total_points": 0}
    
    achievements = db_stats.achievements or {}
    
    # Calculate achievement points
    total_points = 0
    for achievement in achievements.values():
        if isinstance(achievement, dict) and achievement.get("earned"):
            total_points += achievement.get("points", 0)
    
    return {
        "achievements": achievements,
        "total_points": total_points,
        "rank_based_on_points": calculate_achievement_rank(total_points)
    }

def calculate_achievement_rank(points: int) -> str:
    """Calculate achievement rank based on points."""
    if points >= 1000:
        return "Champion"
    elif points >= 500:
        return "Expert"
    elif points >= 200:
        return "Advanced"
    elif points >= 50:
        return "Intermediate"
    else:
        return "Beginner"
from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID

# Base schemas
class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = None
    university: Optional[str] = None
    sport: Optional[str] = None

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    
    @validator('password')
    def validate_password(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    university: Optional[str] = None
    sport: Optional[str] = None
    profile_data: Optional[Dict[str, Any]] = None

class User(UserBase):
    id: UUID
    role: str
    is_active: bool
    is_verified: bool
    profile_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Authentication schemas
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class TokenRefresh(BaseModel):
    refresh_token: str

class LoginRequest(BaseModel):
    username: str
    password: str

# Submission schemas  
class SubmissionCreate(BaseModel):
    analysis_data: Dict[str, Any]
    submission_type: str = "analysis"
    video_url: Optional[str] = None
    
    @validator('analysis_data')
    def validate_analysis_data(cls, v):
        required_fields = ['overallScore', 'duration', 'totalFrames']
        for field in required_fields:
            if field not in v:
                raise ValueError(f'Missing required field: {field}')
        return v

class SubmissionUpdate(BaseModel):
    status: Optional[str] = None
    priority_score: Optional[float] = None
    verification_status: Optional[str] = None
    forensics_data: Optional[Dict[str, Any]] = None

class Submission(BaseModel):
    id: UUID
    user_id: UUID
    analysis_data: Dict[str, Any]
    submission_type: str
    status: str
    priority_score: float
    overall_score: Optional[float] = None
    form_consistency: Optional[float] = None
    movement_efficiency: Optional[float] = None
    technique_score: Optional[float] = None
    balance_score: Optional[float] = None
    duration: Optional[float] = None
    frame_count: Optional[int] = None
    avg_confidence: Optional[float] = None
    verification_status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Athlete statistics schemas
class AthleteStatsUpdate(BaseModel):
    weekly_goal: Optional[int] = Field(None, ge=1, le=20)
    training_patterns: Optional[Dict[str, Any]] = None

class AthleteStats(BaseModel):
    id: UUID
    user_id: UUID
    total_sessions: int
    total_duration: float
    current_rank: Optional[int] = None
    best_score: float
    average_score: float
    recent_score: float
    score_trend: float
    consistency_rating: float
    weekly_sessions: int
    monthly_sessions: int
    weekly_goal: int
    metrics_history: Optional[Dict[str, Any]] = None
    achievements: Optional[Dict[str, Any]] = None
    training_patterns: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_session: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Leaderboard schemas
class LeaderboardQuery(BaseModel):
    period: str = Field("weekly", regex="^(weekly|monthly|all_time)$")
    category: str = Field("overall", regex="^(overall|sport_specific|university)$")
    sport: Optional[str] = None
    university: Optional[str] = None
    limit: int = Field(50, ge=1, le=200)

class LeaderboardEntry(BaseModel):
    user_id: UUID
    username: str
    full_name: Optional[str] = None
    university: Optional[str] = None
    sport: Optional[str] = None
    rank: int
    score: float
    sessions_count: int
    metadata: Optional[Dict[str, Any]] = None

class Leaderboard(BaseModel):
    period: str
    category: str
    sport: Optional[str] = None
    university: Optional[str] = None
    period_start: datetime
    period_end: datetime
    entries: List[LeaderboardEntry]
    total_participants: int
    last_updated: datetime

# Forensics schemas
class ForensicsResult(BaseModel):
    analysis_type: str
    verdict: str = Field(..., regex="^(authentic|suspicious|manipulated)$")
    confidence: float = Field(..., ge=0.0, le=1.0)
    analysis_results: Dict[str, Any]
    processing_time: float

# Admin schemas
class SystemSettingsCreate(BaseModel):
    key: str = Field(..., min_length=1, max_length=100)
    value: Dict[str, Any]
    description: Optional[str] = None
    is_public: bool = False
    requires_admin: bool = True

class SystemSettings(BaseModel):
    id: int
    key: str
    value: Dict[str, Any]
    description: Optional[str] = None
    is_public: bool
    requires_admin: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class AdminUserUpdate(BaseModel):
    role: Optional[str] = Field(None, regex="^(athlete|coach|admin)$")
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None

# Analytics schemas
class UsageAnalytics(BaseModel):
    total_users: int
    active_users_today: int
    active_users_week: int
    total_submissions: int
    submissions_today: int
    avg_processing_time: float
    popular_endpoints: List[Dict[str, Any]]

class UserActivity(BaseModel):
    user_id: UUID
    username: str
    last_login: Optional[datetime] = None
    total_submissions: int
    recent_activity: List[Dict[str, Any]]

# Response schemas for common operations
class StatusResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    per_page: int
    pages: int
    has_next: bool
    has_prev: bool

# Validation helpers
class AnalysisDataValidator(BaseModel):
    overall_score: float = Field(..., ge=0.0, le=100.0)
    form_consistency: float = Field(..., ge=0.0, le=100.0)
    movement_efficiency: float = Field(..., ge=0.0, le=100.0)
    technique_score: float = Field(..., ge=0.0, le=100.0)
    balance: float = Field(..., ge=0.0, le=100.0)
    duration: float = Field(..., gt=0.0)
    total_frames: int = Field(..., ge=1)
    avg_confidence: float = Field(..., ge=0.0, le=1.0)
    timestamp: int
    analysis_version: str = "1.0.0"

# Bulk operations schemas
class BulkSubmissionUpdate(BaseModel):
    submission_ids: List[UUID] = Field(..., min_items=1, max_items=100)
    updates: SubmissionUpdate

class BulkUserUpdate(BaseModel):
    user_ids: List[UUID] = Field(..., min_items=1, max_items=50)
    updates: AdminUserUpdate

# Health check schema
class HealthCheck(BaseModel):
    status: str
    version: str
    database: str
    redis: str
    timestamp: datetime = Field(default_factory=datetime.now)

# Error schemas
class ErrorDetail(BaseModel):
    loc: List[str]
    msg: str
    type: str

class ValidationErrorResponse(BaseModel):
    detail: List[ErrorDetail]

class HTTPErrorResponse(BaseModel):
    detail: str
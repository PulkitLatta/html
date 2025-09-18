from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid

class UserRole(str, Enum):
    athlete = "athlete"
    admin = "admin"
    super_admin = "super_admin"

class ForensicsStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"

# Base schemas
class AthleteBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=100)
    sport: Optional[str] = Field(None, max_length=50)
    year: Optional[str] = Field(None, max_length=20)

class AthleteCreate(AthleteBase):
    password: str = Field(..., min_length=6, max_length=100)

class AthleteUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    sport: Optional[str] = Field(None, max_length=50)
    year: Optional[str] = Field(None, max_length=20)
    profile_image_url: Optional[str] = None

class AthleteResponse(AthleteBase):
    id: uuid.UUID
    is_active: bool
    is_verified: bool
    created_at: datetime
    total_sessions: int
    best_score: float
    average_score: float
    
    class Config:
        from_attributes = True

class SubmissionBase(BaseModel):
    exercise_type: Optional[str] = Field(None, max_length=50)
    analysis_data: Dict[str, Any]
    
    @validator('analysis_data')
    def validate_analysis_data(cls, v):
        required_fields = ['formConsistency', 'stability', 'rangeOfMotion', 'timing']
        for field in required_fields:
            if field not in v:
                raise ValueError(f'Missing required analysis field: {field}')
        return v

class SubmissionCreate(SubmissionBase):
    video_hash: str = Field(..., min_length=32, max_length=64)
    submission_time: datetime
    client_version: Optional[str] = None
    device_info: Optional[Dict[str, Any]] = None

class SubmissionResponse(SubmissionBase):
    id: uuid.UUID
    athlete_id: uuid.UUID
    video_url: str
    overall_score: float
    form_consistency: Optional[float]
    stability: Optional[float]
    range_of_motion: Optional[float]
    timing: Optional[float]
    forensics_status: ForensicsStatus
    is_verified: bool
    fraud_score: float
    created_at: datetime
    processed_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class LeaderboardEntry(BaseModel):
    athlete_id: uuid.UUID
    username: str
    full_name: str
    sport: Optional[str]
    best_score: float
    average_score: Optional[float]
    total_submissions: int
    overall_rank: Optional[int]
    sport_rank: Optional[int]
    
    class Config:
        from_attributes = True

class AdminBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=100)
    role: UserRole = UserRole.admin

class AdminCreate(AdminBase):
    password: str = Field(..., min_length=8, max_length=100)

class AdminResponse(AdminBase):
    id: uuid.UUID
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class TokenData(BaseModel):
    user_id: Optional[uuid.UUID] = None
    user_type: Optional[str] = None

class LoginRequest(BaseModel):
    username: str
    password: str

# Analytics schemas
class AnalyticsResponse(BaseModel):
    total_athletes: int
    total_submissions: int
    avg_score: float
    submissions_today: int
    submissions_this_week: int
    submissions_this_month: int
    top_sports: List[Dict[str, Any]]
    score_distribution: Dict[str, int]

class ExerciseMetrics(BaseModel):
    exercise_type: str
    avg_score: float
    total_submissions: int
    avg_form_consistency: float
    avg_stability: float
    avg_range_of_motion: float

# Forensics schemas
class ForensicsData(BaseModel):
    video_hash: str
    frame_variance: Optional[float]
    motion_analysis: Optional[Dict[str, Any]]
    authenticity_score: Optional[float]
    processing_time: Optional[float]
    
class ForensicsResponse(BaseModel):
    submission_id: uuid.UUID
    status: ForensicsStatus
    fraud_score: float
    is_verified: bool
    forensics_data: Optional[ForensicsData]
    processed_at: Optional[datetime]
    
    class Config:
        from_attributes = True

# System settings schemas
class SystemSetting(BaseModel):
    key: str
    value: Any
    description: Optional[str] = None

class SystemSettingResponse(SystemSetting):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Pagination schemas
class PaginationParams(BaseModel):
    page: int = Field(1, ge=1)
    size: int = Field(20, ge=1, le=100)

class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    size: int
    pages: int
    
    class Config:
        from_attributes = True
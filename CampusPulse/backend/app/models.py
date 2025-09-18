from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

Base = declarative_base()

class User(Base):
    """User model for athletes and coaches."""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    university = Column(String)
    sport = Column(String)
    role = Column(String, default="athlete")  # athlete, coach, admin
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    profile_data = Column(JSONB)  # Additional profile information
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))

    # Relationships
    submissions = relationship("Submission", back_populates="user")
    athlete_stats = relationship("AthleteStats", back_populates="user", uselist=False)

class Submission(Base):
    """Model for video/analysis submissions."""
    __tablename__ = "submissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Analysis data stored as JSONB for flexibility
    analysis_data = Column(JSONB, nullable=False)
    
    # Metadata
    submission_type = Column(String, default="analysis")  # analysis, training, competition
    status = Column(String, default="pending")  # pending, processing, completed, failed
    priority_score = Column(Float, default=0.0)
    
    # File references
    video_url = Column(String)
    thumbnail_url = Column(String)
    
    # Forensics and verification
    forensics_data = Column(JSONB)  # Video forensics analysis results
    verification_status = Column(String, default="pending")  # pending, verified, flagged, rejected
    
    # Performance metrics extracted from analysis
    overall_score = Column(Float)
    form_consistency = Column(Float)
    movement_efficiency = Column(Float)
    technique_score = Column(Float)
    balance_score = Column(Float)
    
    # Timing information
    duration = Column(Float)  # Video duration in seconds
    frame_count = Column(Integer)
    avg_confidence = Column(Float)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    processed_at = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User", back_populates="submissions")

class AthleteStats(Base):
    """Aggregated statistics for each athlete."""
    __tablename__ = "athlete_stats"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)
    
    # Overall statistics
    total_sessions = Column(Integer, default=0)
    total_duration = Column(Float, default=0.0)  # Total training time in seconds
    
    # Performance metrics
    current_rank = Column(Integer)
    best_score = Column(Float, default=0.0)
    average_score = Column(Float, default=0.0)
    recent_score = Column(Float, default=0.0)
    
    # Improvement tracking
    score_trend = Column(Float, default=0.0)  # Positive = improving, negative = declining
    consistency_rating = Column(Float, default=0.0)
    
    # Weekly/Monthly stats
    weekly_sessions = Column(Integer, default=0)
    monthly_sessions = Column(Integer, default=0)
    weekly_goal = Column(Integer, default=5)
    
    # Detailed metrics breakdown stored as JSONB
    metrics_history = Column(JSONB)  # Historical performance data
    achievements = Column(JSONB)  # Earned badges and milestones
    training_patterns = Column(JSONB)  # ML insights about training patterns
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_session = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User", back_populates="athlete_stats")

class Leaderboard(Base):
    """Leaderboard entries for different time periods and categories."""
    __tablename__ = "leaderboards"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Leaderboard configuration
    period = Column(String, nullable=False)  # weekly, monthly, all_time
    category = Column(String, default="overall")  # overall, sport_specific, university
    sport = Column(String)  # For sport-specific leaderboards
    university = Column(String)  # For university-specific leaderboards
    
    # Rankings and scores
    rank = Column(Integer, nullable=False)
    score = Column(Float, nullable=False)
    sessions_count = Column(Integer, default=0)
    
    # Additional leaderboard data
    metadata = Column(JSONB)  # Extra data like streak, improvement rate, etc.
    
    # Period bounds
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class ForensicsLog(Base):
    """Log of forensics analysis for video verification."""
    __tablename__ = "forensics_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    submission_id = Column(UUID(as_uuid=True), ForeignKey("submissions.id"), nullable=False)
    
    # Forensics analysis type and results
    analysis_type = Column(String, nullable=False)  # video_hash, optical_flow, histogram_variance
    verdict = Column(String, nullable=False)  # authentic, suspicious, manipulated
    confidence = Column(Float, nullable=False)
    
    # Detailed analysis results
    analysis_results = Column(JSONB, nullable=False)
    
    # Processing information
    processing_time = Column(Float)  # Time taken for analysis in seconds
    algorithm_version = Column(String)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class SystemSettings(Base):
    """System-wide configuration settings."""
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True)
    key = Column(String, unique=True, nullable=False)
    value = Column(JSONB, nullable=False)
    description = Column(Text)
    
    # Access control
    is_public = Column(Boolean, default=False)
    requires_admin = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class APIUsage(Base):
    """Track API usage for rate limiting and analytics."""
    __tablename__ = "api_usage"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Request details
    endpoint = Column(String, nullable=False)
    method = Column(String, nullable=False)
    ip_address = Column(String)
    user_agent = Column(String)
    
    # Response details
    status_code = Column(Integer)
    response_time = Column(Float)
    
    # Usage metadata
    request_size = Column(Integer)
    response_size = Column(Integer)
    
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

# Database indexes for performance
from sqlalchemy import Index

# Indexes for common queries
Index('idx_submissions_user_created', Submission.user_id, Submission.created_at)
Index('idx_submissions_status', Submission.status)
Index('idx_leaderboards_period_category', Leaderboard.period, Leaderboard.category)
Index('idx_forensics_submission', ForensicsLog.submission_id)
Index('idx_api_usage_timestamp', APIUsage.timestamp)
Index('idx_users_email', User.email)
Index('idx_users_username', User.username)
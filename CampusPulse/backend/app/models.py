from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, Boolean, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import JSONB, UUID
from datetime import datetime
import uuid

Base = declarative_base()

class Athlete(Base):
    __tablename__ = "athletes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    sport = Column(String(50))
    year = Column(String(20))
    profile_image_url = Column(String(500))
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Stats
    total_sessions = Column(Integer, default=0)
    best_score = Column(Float, default=0.0)
    average_score = Column(Float, default=0.0)
    
    # Relationships
    submissions = relationship("Submission", back_populates="athlete")

class Submission(Base):
    __tablename__ = "submissions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    athlete_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Video data
    video_url = Column(String(500), nullable=False)
    video_filename = Column(String(255), nullable=False)
    video_size = Column(Integer)  # in bytes
    video_duration = Column(Float)  # in seconds
    video_hash = Column(String(64), unique=True, nullable=False, index=True)
    
    # Analysis data (stored as JSONB for flexibility)
    analysis_data = Column(JSONB, nullable=False)
    
    # Scores
    overall_score = Column(Float, nullable=False)
    form_consistency = Column(Float)
    stability = Column(Float)
    range_of_motion = Column(Float)
    timing = Column(Float)
    
    # Exercise details
    exercise_type = Column(String(50))
    exercise_duration = Column(Float)
    rep_count = Column(Integer)
    
    # Forensics and verification
    forensics_status = Column(String(20), default='pending')  # pending, processing, completed, failed
    forensics_data = Column(JSONB)
    is_verified = Column(Boolean, default=False)
    fraud_score = Column(Float, default=0.0)
    
    # Metadata
    submission_time = Column(DateTime, nullable=False, index=True)
    processed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Client info
    client_version = Column(String(20))
    device_info = Column(JSONB)
    
    # Priority score for processing queue
    priority_score = Column(Float, default=0.0, index=True)
    
    # Relationships
    athlete = relationship("Athlete", back_populates="submissions")

class Admin(Base):
    __tablename__ = "admins"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(String(20), default='admin')  # admin, super_admin
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)

class SystemSettings(Base):
    __tablename__ = "system_settings"
    
    id = Column(Integer, primary_key=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(JSONB, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Leaderboard(Base):
    __tablename__ = "leaderboard"
    
    id = Column(Integer, primary_key=True)
    athlete_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    sport = Column(String(50), index=True)
    exercise_type = Column(String(50), index=True)
    
    # Scores
    best_score = Column(Float, nullable=False)
    average_score = Column(Float)
    total_submissions = Column(Integer, default=0)
    
    # Rankings
    overall_rank = Column(Integer, index=True)
    sport_rank = Column(Integer, index=True)
    exercise_rank = Column(Integer, index=True)
    
    # Time period
    period = Column(String(20), default='all_time')  # all_time, monthly, weekly
    
    # Metadata
    last_updated = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(UUID(as_uuid=True), index=True)
    user_type = Column(String(20))  # athlete, admin
    action = Column(String(50), nullable=False)
    resource_type = Column(String(50))
    resource_id = Column(String(100))
    details = Column(JSONB)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
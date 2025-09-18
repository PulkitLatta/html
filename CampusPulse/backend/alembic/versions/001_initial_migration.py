"""Initial migration

Revision ID: 001_initial_migration
Revises: 
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = '001_initial_migration'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create athletes table
    op.create_table('athletes',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=100), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=100), nullable=False),
        sa.Column('sport', sa.String(length=50), nullable=True),
        sa.Column('year', sa.String(length=20), nullable=True),
        sa.Column('profile_image_url', sa.String(length=500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('is_verified', sa.Boolean(), nullable=True, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('total_sessions', sa.Integer(), nullable=True, default=0),
        sa.Column('best_score', sa.Float(), nullable=True, default=0.0),
        sa.Column('average_score', sa.Float(), nullable=True, default=0.0),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_athletes_username'), 'athletes', ['username'], unique=True)
    op.create_index(op.f('ix_athletes_email'), 'athletes', ['email'], unique=True)
    
    # Create submissions table
    op.create_table('submissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('athlete_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('video_url', sa.String(length=500), nullable=False),
        sa.Column('video_filename', sa.String(length=255), nullable=False),
        sa.Column('video_size', sa.Integer(), nullable=True),
        sa.Column('video_duration', sa.Float(), nullable=True),
        sa.Column('video_hash', sa.String(length=64), nullable=False),
        sa.Column('analysis_data', postgresql.JSONB(), nullable=False),
        sa.Column('overall_score', sa.Float(), nullable=False),
        sa.Column('form_consistency', sa.Float(), nullable=True),
        sa.Column('stability', sa.Float(), nullable=True),
        sa.Column('range_of_motion', sa.Float(), nullable=True),
        sa.Column('timing', sa.Float(), nullable=True),
        sa.Column('exercise_type', sa.String(length=50), nullable=True),
        sa.Column('exercise_duration', sa.Float(), nullable=True),
        sa.Column('rep_count', sa.Integer(), nullable=True),
        sa.Column('forensics_status', sa.String(length=20), nullable=True, default='pending'),
        sa.Column('forensics_data', postgresql.JSONB(), nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=True, default=False),
        sa.Column('fraud_score', sa.Float(), nullable=True, default=0.0),
        sa.Column('submission_time', sa.DateTime(), nullable=False),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('client_version', sa.String(length=20), nullable=True),
        sa.Column('device_info', postgresql.JSONB(), nullable=True),
        sa.Column('priority_score', sa.Float(), nullable=True, default=0.0),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_submissions_athlete_id'), 'submissions', ['athlete_id'])
    op.create_index(op.f('ix_submissions_video_hash'), 'submissions', ['video_hash'], unique=True)
    op.create_index(op.f('ix_submissions_submission_time'), 'submissions', ['submission_time'])
    op.create_index(op.f('ix_submissions_priority_score'), 'submissions', ['priority_score'])
    
    # Create admins table
    op.create_table('admins',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=100), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=100), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=True, default='admin'),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_admins_username'), 'admins', ['username'], unique=True)
    op.create_index(op.f('ix_admins_email'), 'admins', ['email'], unique=True)
    
    # Create system_settings table
    op.create_table('system_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(length=100), nullable=False),
        sa.Column('value', postgresql.JSONB(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_system_settings_key'), 'system_settings', ['key'], unique=True)
    
    # Create leaderboard table
    op.create_table('leaderboard',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('athlete_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sport', sa.String(length=50), nullable=True),
        sa.Column('exercise_type', sa.String(length=50), nullable=True),
        sa.Column('best_score', sa.Float(), nullable=False),
        sa.Column('average_score', sa.Float(), nullable=True),
        sa.Column('total_submissions', sa.Integer(), nullable=True, default=0),
        sa.Column('overall_rank', sa.Integer(), nullable=True),
        sa.Column('sport_rank', sa.Integer(), nullable=True),
        sa.Column('exercise_rank', sa.Integer(), nullable=True),
        sa.Column('period', sa.String(length=20), nullable=True, default='all_time'),
        sa.Column('last_updated', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_leaderboard_athlete_id'), 'leaderboard', ['athlete_id'])
    op.create_index(op.f('ix_leaderboard_sport'), 'leaderboard', ['sport'])
    op.create_index(op.f('ix_leaderboard_exercise_type'), 'leaderboard', ['exercise_type'])
    op.create_index(op.f('ix_leaderboard_overall_rank'), 'leaderboard', ['overall_rank'])
    op.create_index(op.f('ix_leaderboard_sport_rank'), 'leaderboard', ['sport_rank'])
    
    # Create audit_logs table
    op.create_table('audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('user_type', sa.String(length=20), nullable=True),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('resource_type', sa.String(length=50), nullable=True),
        sa.Column('resource_id', sa.String(length=100), nullable=True),
        sa.Column('details', postgresql.JSONB(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_logs_user_id'), 'audit_logs', ['user_id'])
    op.create_index(op.f('ix_audit_logs_created_at'), 'audit_logs', ['created_at'])

def downgrade() -> None:
    # Drop all tables in reverse order
    op.drop_table('audit_logs')
    op.drop_table('leaderboard')
    op.drop_table('system_settings')
    op.drop_table('admins')
    op.drop_table('submissions')
    op.drop_table('athletes')
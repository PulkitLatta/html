"""Initial database schema

Revision ID: 001
Revises: 
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create users table
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('full_name', sa.String()),
        sa.Column('university', sa.String()),
        sa.Column('sport', sa.String()),
        sa.Column('role', sa.String(), default='athlete'),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_verified', sa.Boolean(), default=False),
        sa.Column('profile_data', postgresql.JSONB()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.Column('last_login', sa.DateTime(timezone=True))
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_username', 'users', ['username'], unique=True)

    # Create submissions table
    op.create_table('submissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('analysis_data', postgresql.JSONB(), nullable=False),
        sa.Column('submission_type', sa.String(), default='analysis'),
        sa.Column('status', sa.String(), default='pending'),
        sa.Column('priority_score', sa.Float(), default=0.0),
        sa.Column('video_url', sa.String()),
        sa.Column('thumbnail_url', sa.String()),
        sa.Column('forensics_data', postgresql.JSONB()),
        sa.Column('verification_status', sa.String(), default='pending'),
        sa.Column('overall_score', sa.Float()),
        sa.Column('form_consistency', sa.Float()),
        sa.Column('movement_efficiency', sa.Float()),
        sa.Column('technique_score', sa.Float()),
        sa.Column('balance_score', sa.Float()),
        sa.Column('duration', sa.Float()),
        sa.Column('frame_count', sa.Integer()),
        sa.Column('avg_confidence', sa.Float()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.Column('processed_at', sa.DateTime(timezone=True))
    )
    op.create_index('ix_submissions_user_created', 'submissions', ['user_id', 'created_at'])
    op.create_index('ix_submissions_status', 'submissions', ['status'])

    # Create athlete_stats table
    op.create_table('athlete_stats',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False, unique=True),
        sa.Column('total_sessions', sa.Integer(), default=0),
        sa.Column('total_duration', sa.Float(), default=0.0),
        sa.Column('current_rank', sa.Integer()),
        sa.Column('best_score', sa.Float(), default=0.0),
        sa.Column('average_score', sa.Float(), default=0.0),
        sa.Column('recent_score', sa.Float(), default=0.0),
        sa.Column('score_trend', sa.Float(), default=0.0),
        sa.Column('consistency_rating', sa.Float(), default=0.0),
        sa.Column('weekly_sessions', sa.Integer(), default=0),
        sa.Column('monthly_sessions', sa.Integer(), default=0),
        sa.Column('weekly_goal', sa.Integer(), default=5),
        sa.Column('metrics_history', postgresql.JSONB()),
        sa.Column('achievements', postgresql.JSONB()),
        sa.Column('training_patterns', postgresql.JSONB()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.Column('last_session', sa.DateTime(timezone=True))
    )

    # Create leaderboards table
    op.create_table('leaderboards',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('period', sa.String(), nullable=False),
        sa.Column('category', sa.String(), default='overall'),
        sa.Column('sport', sa.String()),
        sa.Column('university', sa.String()),
        sa.Column('rank', sa.Integer(), nullable=False),
        sa.Column('score', sa.Float(), nullable=False),
        sa.Column('sessions_count', sa.Integer(), default=0),
        sa.Column('metadata', postgresql.JSONB()),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now())
    )
    op.create_index('ix_leaderboards_period_category', 'leaderboards', ['period', 'category'])

    # Create forensics_logs table
    op.create_table('forensics_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('submission_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('submissions.id'), nullable=False),
        sa.Column('analysis_type', sa.String(), nullable=False),
        sa.Column('verdict', sa.String(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('analysis_results', postgresql.JSONB(), nullable=False),
        sa.Column('processing_time', sa.Float()),
        sa.Column('algorithm_version', sa.String()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )
    op.create_index('ix_forensics_submission', 'forensics_logs', ['submission_id'])

    # Create system_settings table
    op.create_table('system_settings',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('key', sa.String(), unique=True, nullable=False),
        sa.Column('value', postgresql.JSONB(), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('is_public', sa.Boolean(), default=False),
        sa.Column('requires_admin', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now())
    )

    # Create api_usage table
    op.create_table('api_usage',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('endpoint', sa.String(), nullable=False),
        sa.Column('method', sa.String(), nullable=False),
        sa.Column('ip_address', sa.String()),
        sa.Column('user_agent', sa.String()),
        sa.Column('status_code', sa.Integer()),
        sa.Column('response_time', sa.Float()),
        sa.Column('request_size', sa.Integer()),
        sa.Column('response_size', sa.Integer()),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now())
    )
    op.create_index('ix_api_usage_timestamp', 'api_usage', ['timestamp'])

def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('api_usage')
    op.drop_table('system_settings')
    op.drop_table('forensics_logs')
    op.drop_table('leaderboards')
    op.drop_table('athlete_stats')
    op.drop_table('submissions')
    op.drop_table('users')
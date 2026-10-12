"""initial schema

Revision ID: 0001_initial
Revises: 
Create Date: 2026-10-12 10:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'meetings',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('storage_path', sa.String(length=500), nullable=False),
        sa.Column('content_type', sa.String(length=100), nullable=False),
        sa.Column('size_bytes', sa.Integer(), nullable=False),
        sa.Column('checksum', sa.String(length=64), nullable=False),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('language', sa.String(length=20), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='uploaded'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('transcription_started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('transcription_completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('analysis_started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('analysis_completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('transcription_provider', sa.String(length=50), nullable=True),
        sa.Column('transcription_model', sa.String(length=50), nullable=True),
        sa.Column('analysis_provider', sa.String(length=50), nullable=True),
        sa.Column('analysis_model', sa.String(length=50), nullable=True),
    )
    op.create_index('ix_meetings_checksum', 'meetings', ['checksum'])
    op.create_index('ix_meetings_status', 'meetings', ['status'])
    op.create_index('ix_meetings_created_at', 'meetings', ['created_at'])

    op.create_table(
        'transcript_segments',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('meeting_id', sa.String(length=36), sa.ForeignKey('meetings.id', ondelete='CASCADE'), nullable=False),
        sa.Column('segment_index', sa.Integer(), nullable=False),
        sa.Column('start_seconds', sa.Float(), nullable=False),
        sa.Column('end_seconds', sa.Float(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('speaker', sa.String(length=100), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
    )
    op.create_index('ix_transcript_segments_meeting_id', 'transcript_segments', ['meeting_id'])

    op.create_table(
        'meeting_analyses',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('meeting_id', sa.String(length=36), sa.ForeignKey('meetings.id', ondelete='CASCADE'), nullable=False),
        sa.Column('schema_version', sa.String(length=20), nullable=False, server_default='1.0.0'),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('structured_payload', sa.JSON(), nullable=False),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('model', sa.String(length=50), nullable=False),
        sa.Column('prompt_version', sa.String(length=20), nullable=False, server_default='v1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_meeting_analyses_meeting_id', 'meeting_analyses', ['meeting_id'], unique=True)

    op.create_table(
        'meeting_queries',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('meeting_id', sa.String(length=36), sa.ForeignKey('meetings.id', ondelete='CASCADE'), nullable=False),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('answer', sa.Text(), nullable=False),
        sa.Column('evidence', sa.JSON(), nullable=False),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('model', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_meeting_queries_meeting_id', 'meeting_queries', ['meeting_id'])


def downgrade() -> None:
    op.drop_table('meeting_queries')
    op.drop_table('meeting_analyses')
    op.drop_table('transcript_segments')
    op.drop_table('meetings')

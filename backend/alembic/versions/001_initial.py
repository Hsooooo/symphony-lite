"""Initial migration

Revision ID: 001
Revises:
Create Date: 2025-01-01 00:00:00.000000

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
    op.create_table(
        'teams',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('slug', sa.String(50), unique=True, nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )
    
    op.create_table(
        'projects',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('slug', sa.String(50), unique=True, nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('team_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('teams.id')),
        sa.Column('repo_url', sa.Text),
        sa.Column('workflow_config', postgresql.JSONB, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )
    
    op.create_table(
        'issues',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('identifier', sa.String(20), unique=True, nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id')),
        sa.Column('team_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('teams.id')),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('body', sa.Text),
        sa.Column('body_rendered', sa.Text),
        sa.Column('state', sa.String(50), nullable=False, server_default='todo'),
        sa.Column('state_meta', postgresql.JSONB, server_default='{}'),
        sa.Column('priority', sa.Integer, server_default='3'),
        sa.Column('labels', postgresql.ARRAY(sa.String)),
        sa.Column('assignee_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('branch_name', sa.String(255)),
        sa.Column('pr_url', sa.Text),
        sa.Column('workpad', sa.Text),
        sa.Column('workpad_updated_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )
    
    op.create_table(
        'status_proposals',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('issue_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('issues.id')),
        sa.Column('proposed_by', sa.String(50), nullable=False),
        sa.Column('from_state', sa.String(50), nullable=False),
        sa.Column('to_state', sa.String(50), nullable=False),
        sa.Column('reason', sa.Text),
        sa.Column('status', sa.String(20), server_default='pending'),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True)),
        sa.Column('approved_at', sa.DateTime(timezone=True)),
        sa.Column('rejected_reason', sa.Text),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )
    
    op.create_table(
        'work_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('issue_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('issues.id')),
        sa.Column('agent_id', sa.String(100)),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('payload', postgresql.JSONB, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )


def downgrade() -> None:
    op.drop_table('work_logs')
    op.drop_table('status_proposals')
    op.drop_table('issues')
    op.drop_table('projects')
    op.drop_table('teams')

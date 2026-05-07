"""add project repositories and environments

Revision ID: 3fa9f5b2c09a
Revises: 0f16a743f45c
Create Date: 2026-05-07 06:49:11.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '3fa9f5b2c09a'
down_revision: Union[str, None] = '0f16a743f45c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # project_repositories
    op.create_table(
        'project_repositories',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('repo_url', sa.Text(), nullable=False),
        sa.Column('team_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('teams.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )
    op.create_unique_constraint('uix_project_repo_name', 'project_repositories', ['project_id', 'name'])

    # project_environments
    op.create_table(
        'project_environments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('platform', sa.String(50), nullable=True),
        sa.Column('server_address', sa.String(255), nullable=True),
        sa.Column('port', sa.Integer(), nullable=True),
        sa.Column('urls', sa.JSON(), server_default=sa.text("'{}'")),
        sa.Column('specs', sa.JSON(), server_default=sa.text("'{}'")),
        sa.Column('deploy_script', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()')),
    )
    op.create_unique_constraint('uix_project_env_name', 'project_environments', ['project_id', 'name'])

    # drop projects.repo_url
    op.drop_column('projects', 'repo_url')


def downgrade() -> None:
    op.add_column('projects', sa.Column('repo_url', sa.Text(), nullable=True))
    op.drop_table('project_environments')
    op.drop_table('project_repositories')

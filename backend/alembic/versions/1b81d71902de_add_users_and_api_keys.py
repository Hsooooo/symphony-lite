"""add users and api keys

Revision ID: 1b81d71902de
Revises: 001
Create Date: 2025-04-29 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '1b81d71902de'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. users 테이블 생성
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('username', sa.String(50), unique=True, nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('team_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('teams.id'), nullable=True),
        sa.Column('role', sa.String(20), server_default='member'),
        sa.Column('is_active', sa.Boolean, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )

    # 2. api_keys 테이블 생성
    op.create_table(
        'api_keys',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('key_hash', sa.String(255), nullable=False, unique=True),
        sa.Column('name', sa.String(100)),
        sa.Column('last_used_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )

    # 3. 기존 데이터 정리: status_proposals.approved_by에 없는 UUID 제거
    op.execute("UPDATE status_proposals SET approved_by = NULL WHERE approved_by = '00000000-0000-0000-0000-000000000001'")

    # 4. issues 테이블에 컬럼 추가
    op.add_column('issues', sa.Column('created_by_user_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('issues', sa.Column('created_by_agent_id', sa.String(100), nullable=True))

    # 5. status_proposals 테이블에 컬럼 추가
    op.add_column('status_proposals', sa.Column('proposed_by_user_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('status_proposals', sa.Column('proposed_by_agent_id', sa.String(100), nullable=True))

    # 6. work_logs 테이블에 컬럼 추가
    op.add_column('work_logs', sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True))

    # 7. ForeignKey 제약조건 추가 (데이터 정리 후)
    op.create_foreign_key('fk_issues_assignee', 'issues', 'users', ['assignee_id'], ['id'])
    op.create_foreign_key('fk_issues_created_by_user', 'issues', 'users', ['created_by_user_id'], ['id'])
    op.create_foreign_key('fk_status_proposals_proposed_by_user', 'status_proposals', 'users', ['proposed_by_user_id'], ['id'])
    op.create_foreign_key('fk_status_proposals_approved_by', 'status_proposals', 'users', ['approved_by'], ['id'])
    op.create_foreign_key('fk_work_logs_user_id', 'work_logs', 'users', ['user_id'], ['id'])


def downgrade() -> None:
    # FK 제거
    op.drop_constraint('fk_work_logs_user_id', 'work_logs', type_='foreignkey')
    op.drop_constraint('fk_status_proposals_approved_by', 'status_proposals', type_='foreignkey')
    op.drop_constraint('fk_status_proposals_proposed_by_user', 'status_proposals', type_='foreignkey')
    op.drop_constraint('fk_issues_created_by_user', 'issues', type_='foreignkey')
    op.drop_constraint('fk_issues_assignee', 'issues', type_='foreignkey')

    # 컬럼 제거
    op.drop_column('work_logs', 'user_id')
    op.drop_column('status_proposals', 'proposed_by_agent_id')
    op.drop_column('status_proposals', 'proposed_by_user_id')
    op.drop_column('issues', 'created_by_agent_id')
    op.drop_column('issues', 'created_by_user_id')

    # 테이블 제거
    op.drop_table('api_keys')
    op.drop_table('users')

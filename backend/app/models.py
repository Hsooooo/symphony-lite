import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, ARRAY, JSON, Boolean, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(100), nullable=False)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=True)
    role = Column(String(20), default="member")  # admin, member
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    team = relationship("Team", back_populates="users")
    api_keys = relationship("ApiKey", back_populates="user", cascade="all, delete-orphan")
    project_memberships = relationship("ProjectMember", foreign_keys="ProjectMember.user_id", back_populates="user", cascade="all, delete-orphan")


class ApiKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    key_hash = Column(String(255), nullable=False, unique=True)
    name = Column(String(100))  # "Kimi Desktop", "Claude Code" 등 사용자 지정 이름
    last_used_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    user = relationship("User", back_populates="api_keys")


class Team(Base):
    __tablename__ = "teams"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    projects = relationship("Project", back_populates="team")
    issues = relationship("Issue", back_populates="team")
    users = relationship("User", back_populates="team")


class Project(Base):
    __tablename__ = "projects"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"))
    repo_url = Column(Text)
    workflow_config = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    team = relationship("Team", back_populates="projects")
    issues = relationship("Issue", back_populates="project")
    members = relationship("ProjectMember", back_populates="project", cascade="all, delete-orphan")


class ProjectMember(Base):
    __tablename__ = "project_members"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), default="member")  # admin, member
    invited_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    joined_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    project = relationship("Project", back_populates="members")
    user = relationship("User", foreign_keys=[user_id], back_populates="project_memberships")
    inviter = relationship("User", foreign_keys=[invited_by])
    
    __table_args__ = (UniqueConstraint('project_id', 'user_id', name='uix_project_user'),)


class Issue(Base):
    __tablename__ = "issues"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    identifier = Column(String(20), unique=True, nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"))
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"))
    
    title = Column(String(255), nullable=False)
    body = Column(Text)
    body_rendered = Column(Text)
    
    state = Column(String(50), nullable=False, default="todo")
    state_meta = Column(JSON, default={})
    
    priority = Column(Integer, default=3)
    labels = Column(ARRAY(String), default=[])
    reporter_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    assignee_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_by_agent_id = Column(String(100), nullable=True)  # "agent:kimi", "agent:claude"
    
    reporter = relationship("User", foreign_keys=[reporter_id])
    
    branch_name = Column(String(255))
    pr_url = Column(Text)
    
    workpad = Column(Text)
    workpad_updated_at = Column(DateTime(timezone=True))
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    project = relationship("Project", back_populates="issues")
    team = relationship("Team", back_populates="issues")
    status_proposals = relationship("StatusProposal", back_populates="issue")
    work_logs = relationship("WorkLog", back_populates="issue")
    assignee = relationship("User", foreign_keys=[assignee_id])
    created_by_user = relationship("User", foreign_keys=[created_by_user_id])
    comments = relationship("Comment", back_populates="issue", cascade="all, delete-orphan")


class Comment(Base):
    __tablename__ = "comments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    issue_id = Column(UUID(as_uuid=True), ForeignKey("issues.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    author_name = Column(String(100), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    issue = relationship("Issue", back_populates="comments")
    user = relationship("User")


class StatusProposal(Base):
    __tablename__ = "status_proposals"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    issue_id = Column(UUID(as_uuid=True), ForeignKey("issues.id"))
    proposed_by = Column(String(50), nullable=False)
    proposed_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    proposed_by_agent_id = Column(String(100), nullable=True)
    from_state = Column(String(50), nullable=False)
    to_state = Column(String(50), nullable=False)
    reason = Column(Text)
    
    status = Column(String(20), default="pending")
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True))
    rejected_reason = Column(Text)
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    issue = relationship("Issue", back_populates="status_proposals")
    proposed_by_user = relationship("User", foreign_keys=[proposed_by_user_id])
    approved_by_user = relationship("User", foreign_keys=[approved_by])


class WorkLog(Base):
    __tablename__ = "work_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    issue_id = Column(UUID(as_uuid=True), ForeignKey("issues.id"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    agent_id = Column(String(100))
    event_type = Column(String(50), nullable=False)
    payload = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    issue = relationship("Issue", back_populates="work_logs")
    user = relationship("User")

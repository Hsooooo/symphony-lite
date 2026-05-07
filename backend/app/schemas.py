from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, computed_field
from uuid import UUID


# ========== Team ==========
class TeamBase(BaseModel):
    slug: str
    name: str

class TeamCreate(TeamBase):
    pass

class TeamResponse(TeamBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    created_at: datetime


# ========== User ==========
class UserBase(BaseModel):
    username: str
    name: str
    team_id: Optional[UUID] = None

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    role: str
    is_active: bool
    created_at: datetime

class UserWithTeam(UserResponse):
    team: Optional[TeamResponse] = None

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ========== Project ==========
class ProjectBase(BaseModel):
    slug: str
    name: str

class ProjectCreate(ProjectBase):
    team_id: UUID
    workflow_config: Optional[Dict[str, Any]] = {}

class ProjectResponse(ProjectBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    team_id: UUID
    workflow_config: Dict[str, Any]
    created_at: datetime

class ProjectWithTeam(ProjectResponse):
    team: Optional[TeamResponse] = None


# ========== Project Repository ==========
class ProjectRepositoryBase(BaseModel):
    name: str
    repo_url: str

class ProjectRepositoryCreate(ProjectRepositoryBase):
    team_id: Optional[UUID] = None

class ProjectRepositoryResponse(ProjectRepositoryBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    project_id: UUID
    team_id: Optional[UUID] = None
    created_at: datetime
    team: Optional[TeamResponse] = None


# ========== Project Environment ==========
class ProjectEnvironmentBase(BaseModel):
    name: str
    platform: Optional[str] = None
    server_address: Optional[str] = None
    port: Optional[int] = None
    urls: Dict[str, Any] = {}
    specs: Dict[str, Any] = {}
    deploy_script: Optional[str] = None
    notes: Optional[str] = None

class ProjectEnvironmentCreate(ProjectEnvironmentBase):
    pass

class ProjectEnvironmentResponse(ProjectEnvironmentBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    project_id: UUID
    created_at: datetime
    updated_at: datetime


# ========== Project Member ==========
class ProjectMemberBase(BaseModel):
    role: str = "member"

class ProjectMemberCreate(ProjectMemberBase):
    user_id: UUID

class ProjectMemberResponse(ProjectMemberBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    project_id: UUID
    user_id: UUID
    invited_by: Optional[UUID] = None
    joined_at: datetime
    user: Optional[UserWithTeam] = None


# ========== Issue ==========
class IssueBase(BaseModel):
    identifier: str
    title: str
    body: Optional[str] = None
    priority: int = 3
    labels: List[str] = []
    state: str = "todo"

class IssueCreate(IssueBase):
    project_id: UUID
    team_id: UUID

class IssueUpdate(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    state: Optional[str] = None
    priority: Optional[int] = None
    labels: Optional[List[str]] = None
    assignee_id: Optional[UUID] = None
    branch_name: Optional[str] = None
    pr_url: Optional[str] = None
    workpad: Optional[str] = None

class CommentBase(BaseModel):
    content: str

class CommentCreate(CommentBase):
    pass

class CommentResponse(CommentBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    issue_id: UUID
    user_id: Optional[UUID] = None
    author_name: str
    created_at: datetime
    updated_at: datetime


class IssueResponse(IssueBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    project_id: UUID
    team_id: UUID
    state_meta: Dict[str, Any]
    branch_name: Optional[str]
    pr_url: Optional[str]
    workpad: Optional[str]
    workpad_updated_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    # 중첩 객체
    project: Optional[ProjectResponse] = None
    team: Optional[TeamResponse] = None
    reporter: Optional[UserResponse] = None
    assignee: Optional[UserResponse] = None
    created_by_user: Optional[UserResponse] = None
    comments: List[CommentResponse] = []

    @computed_field
    @property
    def creator_type(self) -> str:
        return "agent" if self.created_by_user is None else "user"


# ========== StatusProposal ==========
class StatusProposalBase(BaseModel):
    from_state: Optional[str] = None
    to_state: str
    reason: Optional[str] = None

class StatusProposalCreate(StatusProposalBase):
    proposed_by: str

class StatusProposalResponse(StatusProposalBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    issue_id: UUID
    proposed_by: str
    status: str
    approved_by: Optional[UUID]
    approved_at: Optional[datetime]
    rejected_reason: Optional[str]
    created_at: datetime

class StatusProposalApproval(BaseModel):
    approved_by: UUID
    rejected_reason: Optional[str] = None

class StatusProposalRejection(BaseModel):
    rejected_by: UUID
    rejected_reason: str


# ========== ApiKey ==========
class ApiKeyBase(BaseModel):
    name: Optional[str] = None

class ApiKeyCreate(ApiKeyBase):
    pass

class ApiKeyResponse(ApiKeyBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    user_id: UUID
    key: Optional[str] = None  # 생성 시에만 노출
    last_used_at: Optional[datetime]
    created_at: datetime


# ========== WorkLog ==========
class WorkLogBase(BaseModel):
    event_type: str
    payload: Optional[Dict[str, Any]] = {}

class WorkLogCreate(WorkLogBase):
    agent_id: Optional[str] = None

class WorkLogResponse(WorkLogBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    issue_id: UUID
    agent_id: Optional[str]
    created_at: datetime

from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from sqlalchemy.orm import joinedload
from app import models, schemas


# ========== Team CRUD ==========
def get_team(db: Session, team_id: UUID):
    return db.query(models.Team).filter(models.Team.id == team_id).first()

def get_team_by_slug(db: Session, slug: str):
    return db.query(models.Team).filter(models.Team.slug == slug).first()

def get_teams(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Team).offset(skip).limit(limit).all()

def create_team(db: Session, team: schemas.TeamCreate):
    db_team = models.Team(**team.model_dump())
    db.add(db_team)
    db.commit()
    db.refresh(db_team)
    return db_team


# ========== Project CRUD ==========
def get_project(db: Session, project_id: UUID):
    return db.query(models.Project).filter(models.Project.id == project_id).first()

def get_project_by_slug(db: Session, slug: str):
    return db.query(models.Project).filter(models.Project.slug == slug).first()

def get_projects_by_team(db: Session, team_id: UUID, skip: int = 0, limit: int = 100):
    return db.query(models.Project).filter(models.Project.team_id == team_id).offset(skip).limit(limit).all()

def create_project(db: Session, project: schemas.ProjectCreate, creator_user_id: Optional[UUID] = None):
    db_project = models.Project(**project.model_dump())
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    # 생성자를 자동으로 프로젝트 멤버(admin)로 등록
    if creator_user_id:
        db_member = models.ProjectMember(
            project_id=db_project.id,
            user_id=creator_user_id,
            role="admin"
        )
        db.add(db_member)
        db.commit()
    return db_project


def get_project_member(db: Session, project_id: UUID, user_id: UUID):
    return db.query(models.ProjectMember).filter(
        models.ProjectMember.project_id == project_id,
        models.ProjectMember.user_id == user_id
    ).first()

def get_project_members(db: Session, project_id: UUID, skip: int = 0, limit: int = 100):
    return db.query(models.ProjectMember).options(
        joinedload(models.ProjectMember.user).joinedload(models.User.team)
    ).filter(
        models.ProjectMember.project_id == project_id
    ).offset(skip).limit(limit).all()

def create_project_member(db: Session, project_id: UUID, user_id: UUID, invited_by: Optional[UUID] = None, role: str = "member"):
    db_member = models.ProjectMember(
        project_id=project_id,
        user_id=user_id,
        invited_by=invited_by,
        role=role
    )
    db.add(db_member)
    db.commit()
    db.refresh(db_member)
    return db_member

def delete_project_member(db: Session, project_id: UUID, user_id: UUID):
    db_member = db.query(models.ProjectMember).filter(
        models.ProjectMember.project_id == project_id,
        models.ProjectMember.user_id == user_id
    ).first()
    if db_member:
        db.delete(db_member)
        db.commit()
        return True
    return False


# ========== Issue CRUD ==========
def get_issue(db: Session, issue_id: UUID):
    return db.query(models.Issue).filter(models.Issue.id == issue_id).first()

def get_issue_by_identifier(db: Session, identifier: str):
    return db.query(models.Issue).options(
        joinedload(models.Issue.project),
        joinedload(models.Issue.team),
        joinedload(models.Issue.reporter),
        joinedload(models.Issue.assignee),
        joinedload(models.Issue.created_by_user),
        joinedload(models.Issue.comments),
    ).filter(models.Issue.identifier == identifier).first()

def get_issues_by_project(
    db: Session, 
    project_id: UUID, 
    state: Optional[str] = None,
    assignee_id: Optional[UUID] = None,
    skip: int = 0, 
    limit: int = 100
):
    query = db.query(models.Issue).options(
        joinedload(models.Issue.project),
        joinedload(models.Issue.team),
        joinedload(models.Issue.reporter),
        joinedload(models.Issue.assignee),
        joinedload(models.Issue.created_by_user),
    ).filter(models.Issue.project_id == project_id)
    if state:
        query = query.filter(models.Issue.state == state)
    if assignee_id:
        query = query.filter(models.Issue.assignee_id == assignee_id)
    return query.order_by(desc(models.Issue.priority), desc(models.Issue.created_at)).offset(skip).limit(limit).all()

def get_issues_by_team(
    db: Session,
    team_id: UUID,
    state: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
):
    query = db.query(models.Issue).filter(models.Issue.team_id == team_id)
    if state:
        query = query.filter(models.Issue.state == state)
    return query.order_by(desc(models.Issue.priority), desc(models.Issue.created_at)).offset(skip).limit(limit).all()

def create_issue(db: Session, issue: schemas.IssueCreate, created_by_user_id: Optional[UUID] = None, created_by_agent_id: Optional[str] = None, reporter_id: Optional[UUID] = None):
    db_issue = models.Issue(
        **issue.model_dump(),
        created_by_user_id=created_by_user_id,
        created_by_agent_id=created_by_agent_id,
        reporter_id=reporter_id
    )
    db.add(db_issue)
    db.commit()
    db.refresh(db_issue)
    return db_issue

def get_comments_by_issue(db: Session, issue_id: UUID, skip: int = 0, limit: int = 100):
    return db.query(models.Comment).filter(
        models.Comment.issue_id == issue_id
    ).order_by(asc(models.Comment.created_at)).offset(skip).limit(limit).all()

def create_comment(db: Session, issue_id: UUID, user_id: Optional[UUID], author_name: str, content: str):
    db_comment = models.Comment(
        issue_id=issue_id,
        user_id=user_id,
        author_name=author_name,
        content=content
    )
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment


def update_issue(db: Session, issue_id: UUID, update: schemas.IssueUpdate):
    db_issue = get_issue(db, issue_id)
    if not db_issue:
        return None
    
    update_data = update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_issue, field, value)
    
    # workpad가 업데이트되면 타임스탬프도 갱신
    if "workpad" in update_data:
        db_issue.workpad_updated_at = __import__('datetime').datetime.utcnow()
    
    db.commit()
    db.refresh(db_issue)
    return db_issue


# ========== StatusProposal CRUD ==========
def get_status_proposal(db: Session, proposal_id: UUID):
    return db.query(models.StatusProposal).filter(models.StatusProposal.id == proposal_id).first()

def get_pending_proposals_for_issue(db: Session, issue_id: UUID):
    return db.query(models.StatusProposal).filter(
        models.StatusProposal.issue_id == issue_id,
        models.StatusProposal.status == "pending"
    ).all()

def create_status_proposal(db: Session, issue_id: UUID, proposal: schemas.StatusProposalCreate, proposed_by_user_id: Optional[UUID] = None, proposed_by_agent_id: Optional[str] = None):
    db_proposal = models.StatusProposal(
        issue_id=issue_id,
        proposed_by_user_id=proposed_by_user_id,
        proposed_by_agent_id=proposed_by_agent_id,
        **proposal.model_dump()
    )
    db.add(db_proposal)
    db.commit()
    db.refresh(db_proposal)
    return db_proposal

def approve_status_proposal(db: Session, proposal_id: UUID, approval: schemas.StatusProposalApproval):
    db_proposal = get_status_proposal(db, proposal_id)
    if not db_proposal or db_proposal.status != "pending":
        return None
    
    db_proposal.status = "approved"
    db_proposal.approved_by = approval.approved_by
    db_proposal.approved_at = __import__('datetime').datetime.utcnow()
    
    # 실제 이슈 상태도 업데이트
    db_issue = get_issue(db, db_proposal.issue_id)
    if db_issue:
        db_issue.state = db_proposal.to_state
        # state_meta에 이력 추가
        history = db_issue.state_meta.get("history", [])
        history.append({
            "from": db_proposal.from_state,
            "to": db_proposal.to_state,
            "by": str(approval.approved_by),
            "at": db_proposal.approved_at.isoformat()
        })
        db_issue.state_meta["history"] = history
    
    db.commit()
    db.refresh(db_proposal)
    return db_proposal

def reject_status_proposal(db: Session, proposal_id: UUID, rejected_reason: str, rejected_by: UUID):
    db_proposal = get_status_proposal(db, proposal_id)
    if not db_proposal or db_proposal.status != "pending":
        return None
    
    db_proposal.status = "rejected"
    db_proposal.rejected_reason = rejected_reason
    db.commit()
    db.refresh(db_proposal)
    return db_proposal


# ========== User CRUD ==========
def get_user(db: Session, user_id: UUID):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).options(
        joinedload(models.User.team)
    ).offset(skip).limit(limit).all()

def get_users_by_team(db: Session, team_id: UUID, skip: int = 0, limit: int = 100):
    return db.query(models.User).filter(
        models.User.team_id == team_id
    ).offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.UserCreate, password_hash: str):
    db_user = models.User(
        username=user.username,
        name=user.name,
        password_hash=password_hash,
        team_id=user.team_id
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


# ========== ApiKey CRUD ==========
def get_api_key_by_hash(db: Session, key_hash: str):
    return db.query(models.ApiKey).filter(models.ApiKey.key_hash == key_hash).first()

def get_api_key_by_id(db: Session, key_id: UUID):
    return db.query(models.ApiKey).filter(models.ApiKey.id == key_id).first()

def get_api_keys_by_user(db: Session, user_id: UUID):
    return db.query(models.ApiKey).filter(models.ApiKey.user_id == user_id).all()

def create_api_key(db: Session, user_id: UUID, name: str, key_hash: str):
    db_key = models.ApiKey(user_id=user_id, name=name, key_hash=key_hash)
    db.add(db_key)
    db.commit()
    db.refresh(db_key)
    return db_key

def delete_api_key(db: Session, key_id: UUID, user_id: UUID):
    db_key = db.query(models.ApiKey).filter(
        models.ApiKey.id == key_id,
        models.ApiKey.user_id == user_id
    ).first()
    if db_key:
        db.delete(db_key)
        db.commit()
        return True
    return False


# ========== WorkLog CRUD ==========
def get_work_logs_by_issue(db: Session, issue_id: UUID, skip: int = 0, limit: int = 100):
    return db.query(models.WorkLog).filter(
        models.WorkLog.issue_id == issue_id
    ).order_by(desc(models.WorkLog.created_at)).offset(skip).limit(limit).all()

def create_work_log(db: Session, issue_id: UUID, log: schemas.WorkLogCreate, user_id: Optional[UUID] = None):
    db_log = models.WorkLog(issue_id=issue_id, user_id=user_id, **log.model_dump())
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log


# ========== Project Repository CRUD ==========
def get_project_repositories(db: Session, project_id: UUID, skip: int = 0, limit: int = 100):
    return db.query(models.ProjectRepository).options(
        joinedload(models.ProjectRepository.team)
    ).filter(
        models.ProjectRepository.project_id == project_id
    ).offset(skip).limit(limit).all()

def create_project_repository(db: Session, project_id: UUID, repo: schemas.ProjectRepositoryCreate):
    db_repo = models.ProjectRepository(project_id=project_id, **repo.model_dump())
    db.add(db_repo)
    db.commit()
    db.refresh(db_repo)
    return db_repo

def update_project_repository(db: Session, repo_id: UUID, repo: schemas.ProjectRepositoryCreate):
    db_repo = db.query(models.ProjectRepository).filter(models.ProjectRepository.id == repo_id).first()
    if not db_repo:
        return None
    for key, value in repo.model_dump().items():
        setattr(db_repo, key, value)
    db.commit()
    db.refresh(db_repo)
    return db_repo

def delete_project_repository(db: Session, repo_id: UUID):
    db_repo = db.query(models.ProjectRepository).filter(models.ProjectRepository.id == repo_id).first()
    if db_repo:
        db.delete(db_repo)
        db.commit()
        return True
    return False


# ========== Project Environment CRUD ==========
def get_project_environments(db: Session, project_id: UUID, skip: int = 0, limit: int = 100):
    return db.query(models.ProjectEnvironment).filter(
        models.ProjectEnvironment.project_id == project_id
    ).offset(skip).limit(limit).all()

def create_project_environment(db: Session, project_id: UUID, env: schemas.ProjectEnvironmentCreate):
    db_env = models.ProjectEnvironment(project_id=project_id, **env.model_dump())
    db.add(db_env)
    db.commit()
    db.refresh(db_env)
    return db_env

def update_project_environment(db: Session, env_id: UUID, env: schemas.ProjectEnvironmentCreate):
    db_env = db.query(models.ProjectEnvironment).filter(models.ProjectEnvironment.id == env_id).first()
    if not db_env:
        return None
    for key, value in env.model_dump().items():
        setattr(db_env, key, value)
    db.commit()
    db.refresh(db_env)
    return db_env

def delete_project_environment(db: Session, env_id: UUID):
    db_env = db.query(models.ProjectEnvironment).filter(models.ProjectEnvironment.id == env_id).first()
    if db_env:
        db.delete(db_env)
        db.commit()
        return True
    return False

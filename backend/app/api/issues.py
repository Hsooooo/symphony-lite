from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app import crud, schemas, models
from app.auth import get_current_user_or_api_key

router = APIRouter(prefix="/issues", tags=["issues"])


@router.get("/project/{project_slug}", response_model=List[schemas.IssueResponse])
def list_issues_by_project(
    project_slug: str,
    state: Optional[str] = None,
    assignee_id: Optional[UUID] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_user_or_api_key),
    db: Session = Depends(get_db)
):
    project = crud.get_project_by_slug(db, slug=project_slug)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return crud.get_issues_by_project(db, project_id=project.id, state=state, assignee_id=assignee_id, skip=skip, limit=limit)


@router.get("/team/{team_slug}", response_model=List[schemas.IssueResponse])
def list_issues_by_team(
    team_slug: str,
    state: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_user_or_api_key),
    db: Session = Depends(get_db)
):
    team = crud.get_team_by_slug(db, slug=team_slug)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return crud.get_issues_by_team(db, team_id=team.id, state=state, skip=skip, limit=limit)


@router.post("/project/{project_slug}", response_model=schemas.IssueResponse)
def create_issue(
    project_slug: str,
    issue: schemas.IssueCreate,
    current_user: models.User = Depends(get_current_user_or_api_key),
    db: Session = Depends(get_db)
):
    project = crud.get_project_by_slug(db, slug=project_slug)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # identifier 중복 체크
    existing = crud.get_issue_by_identifier(db, identifier=issue.identifier)
    if existing:
        raise HTTPException(status_code=400, detail="Issue identifier already exists")
    
    agent_id = None
    if hasattr(current_user, 'is_active') and not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    # API Key로 인증된 경우 (MCP 에이전트)
    if getattr(current_user, 'auth_source', None) == 'api_key':
        agent_id = "mcp"
    return crud.create_issue(
        db, issue,
        created_by_user_id=current_user.id,
        created_by_agent_id=agent_id,
        reporter_id=current_user.id
    )


@router.get("/{identifier}", response_model=schemas.IssueResponse)
def get_issue(
    identifier: str,
    current_user: models.User = Depends(get_current_user_or_api_key),
    db: Session = Depends(get_db)
):
    db_issue = crud.get_issue_by_identifier(db, identifier=identifier)
    if not db_issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    return db_issue


@router.patch("/{identifier}", response_model=schemas.IssueResponse)
def update_issue(
    identifier: str,
    update: schemas.IssueUpdate,
    current_user: models.User = Depends(get_current_user_or_api_key),
    db: Session = Depends(get_db)
):
    db_issue = crud.get_issue_by_identifier(db, identifier=identifier)
    if not db_issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    return crud.update_issue(db, issue_id=db_issue.id, update=update)


# ========== Comments ==========
@router.get("/{identifier}/comments", response_model=List[schemas.CommentResponse])
def list_comments(identifier: str, db: Session = Depends(get_db)):
    db_issue = crud.get_issue_by_identifier(db, identifier=identifier)
    if not db_issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    return db_issue.comments


@router.post("/{identifier}/comments", response_model=schemas.CommentResponse)
def create_comment(
    identifier: str,
    comment: schemas.CommentCreate,
    current_user: models.User = Depends(get_current_user_or_api_key),
    db: Session = Depends(get_db)
):
    db_issue = crud.get_issue_by_identifier(db, identifier=identifier)
    if not db_issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    
    author_name = current_user.name
    if getattr(current_user, 'auth_source', None) == 'api_key':
        author_name = f"{current_user.name}(agent)"
    
    return crud.create_comment(
        db,
        issue_id=db_issue.id,
        user_id=current_user.id,
        author_name=author_name,
        content=comment.content
    )


# ========== Status Proposals ==========
@router.get("/{identifier}/status-proposals", response_model=List[schemas.StatusProposalResponse])
def list_status_proposals(identifier: str, db: Session = Depends(get_db)):
    db_issue = crud.get_issue_by_identifier(db, identifier=identifier)
    if not db_issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    return db_issue.status_proposals


@router.post("/{identifier}/status-proposals", response_model=schemas.StatusProposalResponse)
def create_status_proposal(
    identifier: str,
    proposal: schemas.StatusProposalCreate,
    current_user: models.User = Depends(get_current_user_or_api_key),
    db: Session = Depends(get_db)
):
    db_issue = crud.get_issue_by_identifier(db, identifier=identifier)
    if not db_issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    
    # 자동으로 현재 상태를 from_state로 설정
    proposal_data = schemas.StatusProposalCreate(
        from_state=db_issue.state,
        to_state=proposal.to_state,
        reason=proposal.reason,
        proposed_by=proposal.proposed_by
    )
    agent_id = proposal.proposed_by if proposal.proposed_by.startswith("agent:") else None
    return crud.create_status_proposal(
        db,
        issue_id=db_issue.id,
        proposal=proposal_data,
        proposed_by_user_id=current_user.id,
        proposed_by_agent_id=agent_id
    )


# ========== Work Logs ==========
@router.get("/{identifier}/work-logs", response_model=List[schemas.WorkLogResponse])
def list_work_logs(identifier: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    db_issue = crud.get_issue_by_identifier(db, identifier=identifier)
    if not db_issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    return crud.get_work_logs_by_issue(db, issue_id=db_issue.id, skip=skip, limit=limit)


@router.post("/{identifier}/work-logs", response_model=schemas.WorkLogResponse)
def create_work_log(
    identifier: str,
    log: schemas.WorkLogCreate,
    current_user: models.User = Depends(get_current_user_or_api_key),
    db: Session = Depends(get_db)
):
    db_issue = crud.get_issue_by_identifier(db, identifier=identifier)
    if not db_issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    return crud.create_work_log(db, issue_id=db_issue.id, log=log, user_id=current_user.id)

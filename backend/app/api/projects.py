from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import crud, schemas, models
from app.auth import get_current_user_or_api_key

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=List[schemas.ProjectResponse])
def list_projects(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_projects(db, skip=skip, limit=limit)


@router.get("/team/{team_slug}", response_model=List[schemas.ProjectResponse])
def list_projects_by_team(team_slug: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    team = crud.get_team_by_slug(db, slug=team_slug)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return crud.get_projects_by_team(db, team_id=team.id, skip=skip, limit=limit)


@router.post("", response_model=schemas.ProjectResponse)
def create_project(
    project: schemas.ProjectCreate,
    current_user: models.User = Depends(get_current_user_or_api_key),
    db: Session = Depends(get_db)
):
    db_project = crud.get_project_by_slug(db, slug=project.slug)
    if db_project:
        raise HTTPException(status_code=400, detail="Project slug already exists")
    return crud.create_project(db, project, creator_user_id=current_user.id)


@router.get("/{slug}", response_model=schemas.ProjectWithTeam)
def get_project(slug: str, db: Session = Depends(get_db)):
    db_project = crud.get_project_by_slug(db, slug=slug)
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    return db_project


@router.post("/{slug}/members", response_model=schemas.ProjectMemberResponse)
def add_project_member(
    slug: str,
    member: schemas.ProjectMemberCreate,
    current_user: models.User = Depends(get_current_user_or_api_key),
    db: Session = Depends(get_db)
):
    project = crud.get_project_by_slug(db, slug)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    existing = crud.get_project_member(db, project.id, current_user.id)
    if not existing and project.team_id != current_user.team_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    target_user = crud.get_user(db, member.user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    already = crud.get_project_member(db, project.id, member.user_id)
    if already:
        raise HTTPException(status_code=400, detail="User is already a member")
    
    return crud.create_project_member(db, project.id, member.user_id, invited_by=current_user.id, role=member.role)


@router.get("/{slug}/members", response_model=List[schemas.ProjectMemberResponse])
def list_project_members(
    slug: str,
    current_user: models.User = Depends(get_current_user_or_api_key),
    db: Session = Depends(get_db)
):
    project = crud.get_project_by_slug(db, slug)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    existing = crud.get_project_member(db, project.id, current_user.id)
    if not existing and project.team_id != current_user.team_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return crud.get_project_members(db, project.id)


@router.delete("/{slug}/members/{user_id}")
def remove_project_member(
    slug: str,
    user_id: UUID,
    current_user: models.User = Depends(get_current_user_or_api_key),
    db: Session = Depends(get_db)
):
    project = crud.get_project_by_slug(db, slug)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if str(current_user.id) != str(user_id):
        existing = crud.get_project_member(db, project.id, current_user.id)
        if not existing or existing.role != "admin":
            raise HTTPException(status_code=403, detail="Admin permission required")
    
    success = crud.delete_project_member(db, project.id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Member not found")
    return {"ok": True}


def _require_project_admin(db: Session, project, current_user: models.User):
    """프로젝트 admin 권한이 있는지 확인하는 헬퍼"""
    existing = crud.get_project_member(db, project.id, current_user.id)
    if not existing or existing.role != "admin":
        raise HTTPException(status_code=403, detail="Admin permission required")


# ========== Project Repositories ==========
@router.get("/{slug}/repositories", response_model=List[schemas.ProjectRepositoryResponse])
def list_project_repositories(
    slug: str,
    current_user: models.User = Depends(get_current_user_or_api_key),
    db: Session = Depends(get_db)
):
    project = crud.get_project_by_slug(db, slug)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return crud.get_project_repositories(db, project.id)


@router.post("/{slug}/repositories", response_model=schemas.ProjectRepositoryResponse)
def add_project_repository(
    slug: str,
    repo: schemas.ProjectRepositoryCreate,
    current_user: models.User = Depends(get_current_user_or_api_key),
    db: Session = Depends(get_db)
):
    project = crud.get_project_by_slug(db, slug)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    _require_project_admin(db, project, current_user)
    return crud.create_project_repository(db, project.id, repo)


@router.patch("/{slug}/repositories/{repo_id}", response_model=schemas.ProjectRepositoryResponse)
def update_project_repository(
    slug: str,
    repo_id: UUID,
    repo: schemas.ProjectRepositoryCreate,
    current_user: models.User = Depends(get_current_user_or_api_key),
    db: Session = Depends(get_db)
):
    project = crud.get_project_by_slug(db, slug)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    _require_project_admin(db, project, current_user)
    db_repo = crud.update_project_repository(db, repo_id, repo)
    if not db_repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    return db_repo


@router.delete("/{slug}/repositories/{repo_id}")
def remove_project_repository(
    slug: str,
    repo_id: UUID,
    current_user: models.User = Depends(get_current_user_or_api_key),
    db: Session = Depends(get_db)
):
    project = crud.get_project_by_slug(db, slug)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    _require_project_admin(db, project, current_user)
    success = crud.delete_project_repository(db, repo_id)
    if not success:
        raise HTTPException(status_code=404, detail="Repository not found")
    return {"ok": True}


# ========== Project Environments ==========
@router.get("/{slug}/environments", response_model=List[schemas.ProjectEnvironmentResponse])
def list_project_environments(
    slug: str,
    current_user: models.User = Depends(get_current_user_or_api_key),
    db: Session = Depends(get_db)
):
    project = crud.get_project_by_slug(db, slug)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return crud.get_project_environments(db, project.id)


@router.post("/{slug}/environments", response_model=schemas.ProjectEnvironmentResponse)
def add_project_environment(
    slug: str,
    env: schemas.ProjectEnvironmentCreate,
    current_user: models.User = Depends(get_current_user_or_api_key),
    db: Session = Depends(get_db)
):
    project = crud.get_project_by_slug(db, slug)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    _require_project_admin(db, project, current_user)
    return crud.create_project_environment(db, project.id, env)


@router.patch("/{slug}/environments/{env_id}", response_model=schemas.ProjectEnvironmentResponse)
def update_project_environment(
    slug: str,
    env_id: UUID,
    env: schemas.ProjectEnvironmentCreate,
    current_user: models.User = Depends(get_current_user_or_api_key),
    db: Session = Depends(get_db)
):
    project = crud.get_project_by_slug(db, slug)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    _require_project_admin(db, project, current_user)
    db_env = crud.update_project_environment(db, env_id, env)
    if not db_env:
        raise HTTPException(status_code=404, detail="Environment not found")
    return db_env


@router.delete("/{slug}/environments/{env_id}")
def remove_project_environment(
    slug: str,
    env_id: UUID,
    current_user: models.User = Depends(get_current_user_or_api_key),
    db: Session = Depends(get_db)
):
    project = crud.get_project_by_slug(db, slug)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    _require_project_admin(db, project, current_user)
    success = crud.delete_project_environment(db, env_id)
    if not success:
        raise HTTPException(status_code=404, detail="Environment not found")
    return {"ok": True}

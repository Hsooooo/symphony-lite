from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import crud, schemas

router = APIRouter(prefix="/teams", tags=["teams"])


@router.get("", response_model=List[schemas.TeamResponse])
def list_teams(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_teams(db, skip=skip, limit=limit)


@router.post("", response_model=schemas.TeamResponse)
def create_team(team: schemas.TeamCreate, db: Session = Depends(get_db)):
    db_team = crud.get_team_by_slug(db, slug=team.slug)
    if db_team:
        raise HTTPException(status_code=400, detail="Team slug already exists")
    return crud.create_team(db, team)


@router.get("/{slug}", response_model=schemas.TeamResponse)
def get_team(slug: str, db: Session = Depends(get_db)):
    db_team = crud.get_team_by_slug(db, slug=slug)
    if not db_team:
        raise HTTPException(status_code=404, detail="Team not found")
    return db_team


@router.get("/{slug}/members", response_model=List[schemas.UserResponse])
def list_team_members(slug: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    team = crud.get_team_by_slug(db, slug=slug)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return crud.get_users_by_team(db, team_id=team.id, skip=skip, limit=limit)

from sqlalchemy.orm import Session
from app import models, schemas, crud

DEFAULT_TEAMS = [
    {"slug": "backend", "name": "백엔드"},
    {"slug": "frontend", "name": "프론트"},
    {"slug": "product", "name": "기획"},
    {"slug": "design", "name": "디자인"},
    {"slug": "executive", "name": "임원"},
]


def seed_teams(db: Session):
    """팀이 하나도 없을 때만 기본 팀 데이터를 삽입합니다."""
    existing = db.query(models.Team).count()
    if existing > 0:
        return
    for team_data in DEFAULT_TEAMS:
        team = schemas.TeamCreate(**team_data)
        crud.create_team(db, team)


def run_seed():
    """앱 시작 시 실행할 시딩 함수."""
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        seed_teams(db)
    finally:
        db.close()

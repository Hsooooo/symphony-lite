from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.api import teams, projects, issues, status_proposals, auth, mcp
from app.database import engine, Base
from app.seed import run_seed

settings = get_settings()

# 테이블 생성 (개발 환경용, 프로덕션에서는 Alembic 사용)
Base.metadata.create_all(bind=engine)

# 기본 데이터 시딩
run_seed()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 제한 필요
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(teams.router, prefix="/api/v1")
app.include_router(projects.router, prefix="/api/v1")
app.include_router(issues.router, prefix="/api/v1")
app.include_router(status_proposals.router, prefix="/api/v1")
app.include_router(mcp.router, prefix="/api/v1")


@app.get("/health")
def health_check():
    return {"status": "ok"}

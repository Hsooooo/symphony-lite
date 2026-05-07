# Symphony Lite

OpenAI Symphony의 아키텍처 패턴을 차용한 **사내 AI 에이전트 친화적 이슈 트래킹 시스템**입니다.

외부 플랫폼(Linear, Jira 등)에 의존하지 않고, 사내 개발서버에서 자체 운영하며 각 개발자의 AI 에이전트(Kimi, Claude Code 등)는 MCP(Model Context Protocol)를 통해 이슈를 읽고 상태를 제안할 수 있습니다.

## 아키텍처

```
                    ┌─────────────────────────────┐
                    │     사용자 브라우저/CLI       │
                    └─────────────┬───────────────┘
                                  │
                               18080
                                  │
                    ┌─────────────▼───────────────┐
                    │         Nginx               │
                    │   (symphony-nginx)          │
                    │                             │
                    │  /          → React 정적파일 │
                    │  /api/*     → Backend Proxy  │
                    │  /docs      → Swagger UI     │
                    └──────┬──────────────┬───────┘
                           │              │
              ┌────────────┘              └────────────┐
              │                                        │
    ┌─────────▼──────────┐                ┌───────────▼──────────┐
    │   Backend          │                │   Frontend (빌드)    │
    │   (symphony-       │                │   nginx 낸부에 포함   │
    │    backend)        │                │                      │
    │                    │                └──────────────────────┘
    │  FastAPI +         │
    │  Alembic 자동마이그레이션 │
    └─────────┬──────────┘
              │
         낸부:5432
              │
    ┌─────────▼──────────┐
    │   PostgreSQL       │
    │   (symphony-db)    │
    │                    │
    │  포트: 15432 (디버깅용) │
    └────────────────────┘
```

## 기술 스택

| 구성요소 | 기술 |
|---------|------|
| Backend | Python 3.12 + FastAPI + SQLAlchemy 2.0 + Alembic |
| Database | PostgreSQL 15 |
| Frontend | React 18 + Vite + React Router + react-markdown |
| MCP | Python MCP SDK (stdio) |
| 배포 | Docker Compose + Nginx 리버스 프록시 |

## 🚀 빠른 시작 (Docker Compose)

가장 간단한 방법은 Docker Compose로 한 번에 실행하는 것입니다.

```bash
# 1. 저장소 클론
cd /Users/ihansu/VsCodeProjects/symphony-lite

# 2. Docker Compose 실행 (빌드 + 실행)
docker-compose up --build -d

# 3. 상태 확인
docker-compose ps
docker-compose logs -f backend
```

### 접근 주소

| 서비스 | URL |
|--------|-----|
| 웹 UI | http://localhost:18080 |
| API 문서 (Swagger) | http://localhost:18080/docs |
| DB (디버깅용) | localhost:15432 |

### 중지/삭제

```bash
# 중지 (DB 데이터 유지)
docker-compose down

# 완전 삭제 (DB 데이터 포함)
docker-compose down -v
```

## 🛠️ 로컬 개발

Docker 없이 로컬에서 개발하려면:

### 1. PostgreSQL 설치 및 실행

```bash
# macOS
brew install postgresql@15
brew services start postgresql@15

# DB 및 사용자 생성
createuser -s symphony
createdb -O symphony symphony
```

### 2. 백엔드 실행

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 마이그레이션
alembic upgrade head

# 서버 실행
uvicorn app.main:app --reload
```

### 3. 프론트엔드 실행

```bash
cd frontend
npm install
npm run dev
```

## 🤖 MCP 서버 연동 (AI 에이전트)

Symphony Lite의 MCP 서버는 **표준 MCP(Model Context Protocol)**를 구현합니다. MCP를 지원하는 어떤 AI 에이전트·IDE에서도 연동할 수 있습니다.

### 가장 쉬운 방법: 웹 UI에서 가이드 확인

**👉 웹 UI → 사이드바 "MCP 연동" 메뉴**

- OS(macOS/Windows/Linux)와 AI 에이전트(Kimi/Claude/Cursor)를 선택하면
- **복붙 가능한 한 줄 설치 명령어**가 자동으로 생성됩니다
- API 키도 자동으로 채워집니다

### 수동 설정 (고급 사용자용)

모든 연동 방식에서 아래 환경 변수가 필요합니다:

| 변수 | 설명 | 예시 |
|---|---|---|
| `SYMPHONY_API_URL` | Symphony API 주소 | `http://localhost:18080/api/v1` |
| `SYMPHONY_API_KEY` | 발급받은 API 키 | `sym_xxxxxxxx` |

> API 키는 웹 UI → MCP 연동 페이지에서 발행할 수 있습니다.

**설치 스크립트:**

```bash
# macOS / Linux
curl -fsSL http://<idc-server>/scripts/install-mcp.sh | bash

# Windows
Invoke-WebRequest -Uri http://<idc-server>/scripts/install-mcp.ps1 -UseBasicParsing | Invoke-Expression
```

**지원 클라이언트:** Kimi Code CLI, Claude Code, Claude Desktop, Cursor, Windsurf

### 에이전트 작업 흐름 예시

```
개발자: "Kimi, EM-1 티켓 작업해줘"
   │
   ▼
Kimi: MCP symphony_get_issue(EM-1) 호출 → Markdown 본문 + workpad 수신
   │
   ▼
Kimi: 로컬에서 코드 작성, 테스트 실행
   │
   ▼
Kimi: MCP symphony_update_workpad(EM-1, "진행 상황...")
   │
   ▼
Kimi: MCP symphony_log_work(EM-1, "test_run", {passed: true})
   │
   ▼
Kimi: MCP symphony_propose_status_change(EM-1, "review", "테스트 통과")
   │
   ▼
개발자: 웹 UI(http://localhost:18080)에서 승인 클릭
   │
   ▼
시스템: 이슈 상태 → review로 변경
```

## 🌐 웹 UI 사용법

### 이슈 목록
- http://localhost:18080/issues
- 프로젝트 선택 → 해당 프로젝트의 이슈 목록 확인
- 상태별 색상 구분 (todo: 회색, in_progress: 노랑, review: 파랑, done: 초록)

### 이슈 상세 / 승인
- 클릭 → 상세 페이지
- **본문**: Markdown 렌더링
- **Workpad**: 에이전트가 남긴 진행 상황
- **승인 대기 중인 제안**: 노란 배경에 승인/거절 버튼
- **작업 로그 타임라인**: 에이전트의 작업 이력 시각화

## 핵심 개념

### 상태 머신

```
[Backlog] → [Todo] → [In Progress] → [Review] → [Merging] → [Done]
                              ↑            │
                              └────────────┘
                                   [Rework]
```

### 하이브리드 승인 모델

| 단계 | 주체 | 동작 |
|------|------|------|
| 작업 수행 | AI 에이전트 | 코드 작성, 테스트, workpad 기록 |
| 상태 제안 | AI 에이전트 | `symphony_propose_status_change` 호출 |
| 승인/거절 | 개발자 | 웹 UI에서 클릭 |
| 상태 반영 | 시스템 | 승인 시 DB 업데이트 + 이력 기록 |

### MCP Tools

| Tool | 설명 | 권한 |
|------|------|------|
| `symphony_list_issues` | 프로젝트 이슈 목록 조회 | 읽기 |
| `symphony_get_issue` | 이슈 상세 (Markdown + workpad) | 읽기 |
| `symphony_update_workpad` | 에이전트 진행 상황 업데이트 | 쓰기 |
| `symphony_propose_status_change` | 상태 변경 제안 (승인 필요) | 쓰기 |
| `symphony_log_work` | 작업 이벤트 기록 | 쓰기 |
| `symphony_create_issue` | 새 이슈 생성 | 쓰기 |

## API 엔드포인트

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/v1/teams` | 팀 목록 |
| GET | `/api/v1/teams/{slug}/members` | 팀별 멤버 목록 |
| GET | `/api/v1/users` | 전체 사용자 목록 |
| GET | `/api/v1/projects/team/{team_slug}` | 팀별 프로젝트 목록 |
| POST | `/api/v1/projects` | 프로젝트 생성 |
| GET | `/api/v1/projects/{slug}` | 프로젝트 상세 |
| GET | `/api/v1/projects/{slug}/members` | 프로젝트 멤버 목록 |
| POST | `/api/v1/projects/{slug}/members` | 프로젝트 멤버 추가 |
| DELETE | `/api/v1/projects/{slug}/members/{user_id}` | 프로젝트 멤버 제거 |
| GET | `/api/v1/projects/{slug}/repositories` | 프로젝트 레포지토리 목록 |
| POST | `/api/v1/projects/{slug}/repositories` | 레포지토리 추가 |
| PATCH | `/api/v1/projects/{slug}/repositories/{repo_id}` | 레포지토리 수정 |
| DELETE | `/api/v1/projects/{slug}/repositories/{repo_id}` | 레포지토리 삭제 |
| GET | `/api/v1/projects/{slug}/environments` | 배포 환경 목록 |
| POST | `/api/v1/projects/{slug}/environments` | 배포 환경 추가 |
| PATCH | `/api/v1/projects/{slug}/environments/{env_id}` | 배포 환경 수정 |
| DELETE | `/api/v1/projects/{slug}/environments/{env_id}` | 배포 환경 삭제 |
| GET | `/api/v1/issues/project/{project_slug}` | 프로젝트 이슈 목록 |
| POST | `/api/v1/issues/project/{project_slug}` | 이슈 생성 |
| GET | `/api/v1/issues/{identifier}` | 이슈 상세 |
| PATCH | `/api/v1/issues/{identifier}` | 이슈 수정 |
| POST | `/api/v1/issues/{identifier}/status-proposals` | 상태 변경 제안 |
| POST | `/api/v1/status-proposals/{id}/approve` | 상태 변경 승인 |
| POST | `/api/v1/status-proposals/{id}/reject` | 상태 변경 거절 |
| GET | `/api/v1/issues/{identifier}/work-logs` | 작업 로그 조회 |

> **이슈 생성자 구분:** 이슈 응답에 `created_by_agent_id` 필드가 포함됩니다. MCP(에이전트)를 통해 생성된 이슈는 `created_by_agent_id`가 `"mcp"`로 설정되며, 웹 UI에서 생성자 이름 옆에 `(agent)` 배지가 표시됩니다.

## 구현 단계

- [x] **Phase 1**: 핵심 API + React UI + Docker Compose 배포
- [x] **Phase 2**: MCP 서버 완성 + Kimi 연동 가이드
- [x] **Phase 3**: 상태 머신 + 하이브리드 승인 워크플로우 + 프로젝트 멤버 관리 + 프로젝트 인프라 정보 (레포/환경)
- [ ] **Phase 4**: WORKFLOW.md 파싱 및 프로젝트별 템플릿
- [ ] **Phase 5**: JWT 인증 + 팀/프로젝트 권한 제어
- [ ] **Phase 6**: 작업 로그 분석 + 에이전트 성능 메트릭 대시보드

## 라이선스

Apache 2.0

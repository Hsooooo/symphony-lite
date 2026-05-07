# Symphony Lite 아키텍처 및 로직 흐름 문서

> 본 문서는 Symphony Lite의 전체 시스템 아키텍처, 데이터 흐름, 상태 머신, MCP 통신, 승인 워크플로우를 시각적으로 설명합니다.

---

## 1. 시스템 전체 구조

### 1.1 High-Level 아키텍처

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              사용자 레이어                                     │
│  ┌─────────────────────┐    ┌─────────────────────┐    ┌──────────────────┐ │
│  │   개발자 (웹)        │    │   개발자 (터미널)    │    │   AI 에이전트     │ │
│  │   React SPA         │    │   curl/httpie       │    │   Kimi/Claude    │ │
│  └──────────┬──────────┘    └──────────┬──────────┘    └────────┬─────────┘ │
│             │                          │                        │           │
│             │ 18080                    │ 18080                  │ stdio     │
│             │                          │                        │ 18080/mcp │
│             │                          │                        │           │
└─────────────┼──────────────────────────┼────────────────────────┼───────────┘
              │                          │                        │
┌─────────────▼──────────────────────────┼────────────────────────┼───────────┐
│                           Nginx (리버스 프록시)                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  /                      → React 빌드 결과 (정적 파일)                    │ │
│  │  /api/v1/*              → Backend Proxy Pass                           │ │
│  │  /docs                  → Swagger UI                                   │ │
│  │  /mcp                   → MCP Server Proxy Pass (streamable-http)      │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└─────────────┬──────────────────────────┬────────────────────────┬───────────┘
              │                          │                        │
┌─────────────▼──────────┐  ┌────────────▼──────────┐  ┌─────────▼───────────┐
│   Frontend (React)     │  │   Backend (FastAPI)   │  │   MCP Server         │
│   - IssueList          │  │   - REST API          │  │   - Python MCP SDK   │
│   - IssueDetail        │  │   - 상태 머신 엔진     │  │   - stdio transport  │
│   - 승인/거절 UI        │  │   - 승인 워크플로우    │  │   - 6개 Tool         │
└────────────────────────┘  └───────────┬───────────┘  └─────────┬───────────┘
                                        │                        │
                                        │ SQLAlchemy              │ httpx
                                        │                        │
                              ┌─────────▼───────────┐  ┌─────────▼───────────┐
                              │   PostgreSQL 15      │  │   Backend API       │
                              │   - teams            │  │   (남부 네트워크)    │
                              │   - projects         │  └─────────────────────┘
                              │   - issues           │
                              │   - status_proposals │
                              │   - work_logs        │
                              └──────────────────────┘
```

### 1.2 Docker Compose 서비스 구조

```mermaid
graph TB
    User[사용자<br/>브라우저/터미널] -->|18080| Nginx
    Kimi[AI 에이전트<br/>Kimi/Claude] -->|stdio| MCP[MCP Server<br/>Python SDK]
    Kimi -.->|streamable-http| Nginx
    MCP -->|HTTP| Backend

    Nginx -->|/| Frontend[React SPA<br/>정적 파일]
    Nginx -->|/api/| Backend[Backend<br/>FastAPI + Alembic]
    Nginx -->|/mcp| MCP
    Backend -->|SQLAlchemy| DB[(PostgreSQL<br/>port: 15432)]

    style User fill:#e1f5e1
    style Kimi fill:#e1f5e1
    style Nginx fill:#fff3cd
    style MCP fill:#cce5ff
    style Backend fill:#cce5ff
    style DB fill:#f8d7da
```

---

## 2. 데이터 모델 (ERD)

```mermaid
erDiagram
    TEAM ||--o{ PROJECT : has
    TEAM ||--o{ ISSUE : has
    PROJECT ||--o{ ISSUE : contains
    ISSUE ||--o{ STATUS_PROPOSAL : has
    ISSUE ||--o{ WORK_LOG : has

    TEAM {
        uuid id PK
        string slug UK
        string name
        datetime created_at
    }

    PROJECT {
        uuid id PK
        string slug UK
        string name
        uuid team_id FK
        text repo_url
        jsonb workflow_config
        datetime created_at
    }

    ISSUE {
        uuid id PK
        string identifier UK
        uuid project_id FK
        uuid team_id FK
        string title
        text body
        text body_rendered
        string state
        jsonb state_meta
        int priority
        array labels
        uuid assignee_id
        string branch_name
        text pr_url
        text workpad
        datetime workpad_updated_at
        datetime created_at
        datetime updated_at
    }

    STATUS_PROPOSAL {
        uuid id PK
        uuid issue_id FK
        string proposed_by
        string from_state
        string to_state
        text reason
        string status
        uuid approved_by
        datetime approved_at
        text rejected_reason
        datetime created_at
    }

    WORK_LOG {
        uuid id PK
        uuid issue_id FK
        string agent_id
        string event_type
        jsonb payload
        datetime created_at
    }
```

---

## 3. 이슈 상태 머신

### 3.1 상태 전이 다이어그램

```mermaid
stateDiagram-v2
    [*] --> Backlog
    Backlog --> Todo
    Todo --> InProgress : 에이전트/사용자
    InProgress --> Review : 제안 → 승인
    Review --> Rework : 리뷰어
    Rework --> InProgress : 에이전트/사용자
    Review --> Merging : 승인 완료
    Merging --> Done : 머지 완료
    Todo --> Cancelled : 관리자
    InProgress --> Cancelled : 관리자
    Review --> Cancelled : 관리자
    Done --> [*]
    Cancelled --> [*]

    note right of InProgress
        에이전트가 workpad를
        업데이트하며 작업
    end note

    note right of Review
        하이브리드 승인 모델:
        에이전트 제안 →
        개발자 승인
    end note
```

### 3.2 상태 전이 규칙 매트릭스

| From → To | 제안 주체 | 승인 필요 | 실제 적용 시점 |
|-----------|----------|----------|--------------|
| Todo → In Progress | 에이전트/사용자 | ❌ 자동 | 제안 즉시 |
| In Progress → Review | 에이전트/사용자 | ✅ 수동 승인 | 개발자 승인 클릭 |
| Review → Rework | 사용자 | ❌ 자동 | 리뷰어 상태 변경 |
| Review → Merging | 사용자 | ❌ 자동 | PR 승인 완료 |
| Rework → In Progress | 에이전트/사용자 | ❌ 자동 | 재작업 시작 |
| Merging → Done | 에이전트/사용자 | ❌ 자동 | 머지 완료 |
| Any → Cancelled | 사용자(관리자) | ❌ 자동 | 즉시 |

---

## 4. 하이브리드 승인 워크플로우

### 4.1 전체 시퀀스 (성공 케이스)

```mermaid
sequenceDiagram
    autonumber
    actor Dev as 개발자
    participant UI as 웹 UI (React)
    participant API as Backend API
    participant DB as PostgreSQL
    participant Agent as AI 에이전트 (Kimi)
    participant MCP as MCP Server

    rect rgb(240, 248, 255)
        Note over Dev,DB: Phase 1: 에이전트 작업 수행
        Dev->>Agent: "EM-1 작업해"
        Agent->>MCP: symphony_get_issue(EM-1)
        MCP->>API: GET /issues/EM-1
        API->>DB: SELECT
        DB-->>API: issue row
        API-->>MCP: JSON
        MCP-->>Agent: Markdown 본문 + workpad
        Note right of Agent: 로컬에서 코드 작성
        Agent->>MCP: symphony_update_workpad(EM-1, "...")
        MCP->>API: PATCH /issues/EM-1
        API->>DB: UPDATE workpad
        Agent->>MCP: symphony_log_work(EM-1, "test_run", {...})
        MCP->>API: POST /issues/EM-1/work-logs
        API->>DB: INSERT work_logs
    end

    rect rgb(255, 243, 205)
        Note over Dev,DB: Phase 2: 상태 변경 제안
        Agent->>MCP: symphony_propose_status_change(EM-1, "review")
        MCP->>API: POST /issues/EM-1/status-proposals
        API->>DB: INSERT status_proposals (status=pending)
        DB-->>API: proposal row
        API-->>MCP: 제안 완료
        MCP-->>Agent: "개발자 승인 대기 중"
    end

    rect rgb(212, 237, 218)
        Note over Dev,DB: Phase 3: 개발자 승인
        Dev->>UI: http://localhost:18080/issues/EM-1
        UI->>API: GET /issues/EM-1
        API->>DB: SELECT + JOIN
        DB-->>API: issue + pending proposals
        API-->>UI: JSON
        UI->>Dev: 노란색 승인 대기 카드 표시
        Dev->>UI: ✅ 승인 버튼 클릭
        UI->>API: POST /status-proposals/{id}/approve
        API->>DB: UPDATE issues.state = "review"
        API->>DB: UPDATE status_proposals.status = "approved"
        API->>DB: UPDATE issues.state_meta (이력 추가)
        DB-->>API: 완료
        API-->>UI: 200 OK
        UI->>Dev: 상태 "review"로 변경 확인
    end
```

### 4.2 거절 케이스

```mermaid
sequenceDiagram
    autonumber
    actor Dev as 개발자
    participant UI as 웹 UI
    participant API as Backend API
    participant DB as PostgreSQL

    Dev->>UI: ❌ 거절 버튼 클릭 + 사유 입력
    UI->>API: POST /status-proposals/{id}/reject<br/>{rejected_reason: "아직 검토 필요"}
    API->>DB: UPDATE status_proposals<br/>status="rejected"<br/>rejected_reason="..."
    DB-->>API: 완료
    API-->>UI: 200 OK
    UI->>Dev: 빨간색 거절 이력 표시
    Note over Dev: 에이전트가 재작업 후<br/>다시 제안할 수 있음
```

---

## 5. MCP 통신 상세

### 5.1 MCP Transport 흐름

```
┌──────────────────────────────────────────────────────────────┐
│                    Kimi Code CLI 세션                         │
│                                                              │
│   사용자 입력: "EM-1 작업해"                                    │
│         │                                                    │
│         ▼                                                    │
│   ┌─────────────┐     stdio pipe      ┌──────────────┐      │
│   │  Kimi LLM   │ ◄────────────────► │  MCP Server  │      │
│   │  (내부)     │   JSON-RPC 2.0     │  (Python)    │      │
│   └──────┬──────┘                    └──────┬───────┘      │
│          │                                   │              │
│          │ 1. tools/list 요청                │              │
│          │◄──────────────────────────────────│              │
│          │                                   │              │
│          │ 2. tools/call (symphony_get_issue)│              │
│          │◄──────────────────────────────────│              │
│          │                                   │              │
│          ▼                                   ▼              │
│   ┌──────────────────────────────────────────────────┐     │
│   │              Backend API (FastAPI)                │     │
│   │         http://localhost:8000/api/v1              │     │
│   └──────────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────────┘
```

**B. streamable-http Transport (원격 연동)**
```
┌──────────────────────────────────────────────────────────────┐
│                    Kimi / Claude / Cursor                   │
│                                                              │
│   사용자 입력: "EM-1 작업해"                                    │
│         │                                                    │
│         ▼                                                    │
│   ┌─────────────┐   HTTP POST /mcp    ┌──────────────┐      │
│   │  AI 에이전트 │ ──────────────────► │    Nginx     │      │
│   │  (낶제)     │   JSON-RPC 2.0      │   :18080     │      │
│   └──────┬──────┘                     └──────┬───────┘      │
│          │                                    │              │
│          │                                    ▼              │
│          │                           ┌──────────────┐       │
│          │                           │  MCP Server  │       │
│          │                           │  :8001       │       │
│          │                           └──────┬───────┘       │
│          │                                  │               │
│          ▼                                  ▼               │
│   ┌──────────────────────────────────────────────────┐     │
│   │              Backend API (FastAPI)                │     │
│   │         http://backend:8000/api/v1               │     │
│   └──────────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────────┘
```

**인증 흐름 (HTTP)**
1. 클라이언트가 `X-API-Key` 헤더를 MCP HTTP 요청에 포함
2. nginx가 `/mcp` → mcp 서비스로 프록시
3. Starlette 미들웨어가 헤더를 `contextvars`에 저장
4. `_get_headers()`가 `contextvars`의 키를 백엔드 API 호출에 전달

### 5.2 MCP Tool 사용 흐름 예시

```mermaid
flowchart LR
    A[사용자: "EM-1 작업해"] --> B[Kimi Code CLI]
    B --> C{사용 가능한<br/>MCP Tools}
    C --> D[symphony_get_issue]
    C --> E[symphony_update_workpad]
    C --> F[symphony_propose_status_change]
    C --> G[symphony_log_work]
    C --> H[symphony_create_issue]
    C --> I[symphony_list_issues]

    D --> J[Backend API]
    E --> J
    F --> J
    G --> J
    H --> J
    I --> J

    J --> K[(PostgreSQL)]

    style A fill:#e1f5e1
    style B fill:#fff3cd
    style J fill:#cce5ff
    style K fill:#f8d7da
```

---

## 6. Workpad + 작업 로그 흐름

### 6.1 에이전트 작업 추적 구조

```mermaid
flowchart TB
    subgraph Issue["이슈 #EM-1"]
        direction TB
        Body["📄 본문 (Markdown)<br/>요구사항 + 수락 기준"]
        Workpad["🤖 Workpad (Markdown)<br/>에이전트가 업데이트하는 진행 상황"]
        Meta["📊 메타 정보<br/>상태 / 우선순위 / 라벨 / PR"]
    end

    subgraph Proposals["상태 제안"]
        P1["⏳ PENDING<br/>in_progress → review<br/>제안: agent:kimi"]
        P2["✅ APPROVED<br/>todo → in_progress<br/>승인: 개발자A"]
        P3["❌ REJECTED<br/>review → merging<br/>거절: 검토 미흡"]
    end

    subgraph Logs["작업 로그"]
        L1["📝 plan_created<br/>14:32"]
        L2["💻 code_committed<br/>abc1234<br/>14:45"]
        L3["✅ test_run<br/>passed: true<br/>14:50"]
        L4["🔀 pr_created<br/>#123<br/>15:00"]
    end

    Issue --> Proposals
    Issue --> Logs

    style Body fill:#f8f9fa
    style Workpad fill:#f0f8ff
    style P1 fill:#fff3cd
    style P2 fill:#d4edda
    style P3 fill:#f8d7da
```

### 6.2 Workpad 업데이트 타임라인

```mermaid
sequenceDiagram
    participant Agent as AI 에이전트
    participant API as Backend API
    participant DB as PostgreSQL

    rect rgb(240, 248, 255)
        Note over Agent,DB: 작업 시작
        Agent->>API: PATCH /issues/EM-1<br/>{workpad: "## Plan\n- [x] 분석"}
        API->>DB: UPDATE issues<br/>workpad = "..."<br/>workpad_updated_at = NOW()
    end

    rect rgb(240, 248, 255)
        Note over Agent,DB: 구현 중
        Agent->>API: PATCH /issues/EM-1<br/>{workpad: "## Plan\n- [x] 분석\n- [x] 구현"}
        API->>DB: UPDATE issues<br/>workpad = "..."<br/>workpad_updated_at = NOW()
    end

    rect rgb(240, 248, 255)
        Note over Agent,DB: 테스트 완료
        Agent->>API: PATCH /issues/EM-1<br/>{workpad: "## Plan\n- [x] 분석\n- [x] 구현\n- [x] 테스트"}
        API->>DB: UPDATE issues<br/>workpad = "..."<br/>workpad_updated_at = NOW()
    end
```

---

## 7. Docker Compose 내부 통신 흐름

### 7.1 컨테이너 간 네트워크

```mermaid
graph LR
    subgraph DockerCompose["Docker Compose Network: symphony-net"]
        subgraph NginxContainer["nginx 컨테이너<br/>port: 18080 → 80"]
            Nginx[Nginx]
            FE[React 빌드 결과<br/>/usr/share/nginx/html]
        end

        subgraph BEContainer["backend 컨테이너<br/>port: 8000 (내부만)"]
            Uvicorn[Uvicorn<br/>FastAPI]
            Entrypoint[entrypoint.sh<br/>alembic upgrade head]
        end

        subgraph DBContainer["db 컨테이너<br/>port: 15432 → 5432"]
            Postgres[(PostgreSQL)]
        end

        subgraph MCPContainer["mcp 컨테이너<br/>port: 8001 (낶제만)"]
            MCPServer[MCP Server<br/>FastMCP + uvicorn]
        end
    end

    User[사용자] -->|18080| Nginx
    Nginx -->|/api/| Uvicorn
    Nginx -->|/mcp| MCPServer
    Uvicorn -->|5432| Postgres
    MCPServer -->|HTTP| Uvicorn
    Entrypoint -->|시작 시 마이그레이션| Postgres

    style User fill:#e1f5e1
    style Nginx fill:#fff3cd
    style Uvicorn fill:#cce5ff
    style Postgres fill:#f8d7da
```

### 7.2 서비스 시작 순서

```mermaid
flowchart LR
    A[docker-compose up] --> B[db 시작]
    B --> C{Healthcheck?<br/>pg_isready}
    C -->|❌ 실패| D[5초 대기]
    D --> C
    C -->|✅ 성공| E[backend 시작]
    E --> F[entrypoint.sh 실행]
    F --> G[alembic upgrade head]
    G --> H[uvicorn 시작]
    H --> I[mcp 시작]
    I --> J[nginx 시작]
    J --> K[빌드된 React를<br/>정적 파일로 serve]

    style B fill:#f8d7da
    style E fill:#cce5ff
    style I fill:#fff3cd
    style J fill:#e1f5e1
```

---

## 8. API 요청 흐름 예시

### 8.1 이슈 상세 조회 (프론트엔드 → 백엔드)

```mermaid
sequenceDiagram
    autonumber
    actor User as 사용자
    participant Browser as 브라우저
    participant Nginx as Nginx
    participant React as React SPA
    participant API as FastAPI
    participant DB as PostgreSQL

    User->>Browser: /issues/EM-1 접속
    Browser->>Nginx: GET /
    Nginx->>React: index.html
    React->>Browser: SPA 렌더링
    Browser->>Nginx: GET /api/v1/issues/EM-1
    Nginx->>API: proxy_pass<br/>GET /api/v1/issues/EM-1
    API->>DB: SELECT issues<br/>JOIN projects<br/>JOIN teams<br/>LEFT JOIN status_proposals<br/>WHERE identifier = 'EM-1'
    DB-->>API: row + 관계 데이터
    API-->>Nginx: JSON (IssueDetail)
    Nginx-->>Browser: JSON
    Browser->>React: 상태 업데이트
    React->>Browser: UI 렌더링
    Browser->>User: 이슈 상세 페이지 표시
```

### 8.2 상태 제안 승인 (프론트엔드 → 백엔드 → DB)

```mermaid
sequenceDiagram
    autonumber
    actor User as 개발자
    participant React as React
    participant API as FastAPI
    participant DB as PostgreSQL

    User->>React: 승인 버튼 클릭
    React->>API: POST /status-proposals/{id}/approve<br/>{approved_by: "..."}
    API->>DB: SELECT status_proposals<br/>WHERE id = ? AND status = 'pending'
    DB-->>API: proposal row
    API->>DB: BEGIN TRANSACTION
    API->>DB: UPDATE issues<br/>SET state = proposal.to_state<br/>WHERE id = proposal.issue_id
    API->>DB: UPDATE status_proposals<br/>SET status = 'approved'<br/>approved_by = ?<br/>approved_at = NOW()
    API->>DB: UPDATE issues.state_meta<br/>JSONB 배열에 이력 추가
    API->>DB: COMMIT
    DB-->>API: 완료
    API-->>React: 200 OK (StatusProposalResponse)
    React->>React: fetchIssue() 재호출
    React->>User: UI 갱신 (상태 review로 변경)
```

---

## 9. 파일 구조 및 책임

```
symphony-lite/
│
├── docker-compose.yml          # 서비스 오케스트레이션 (db + backend + nginx)
│
├── backend/                    # FastAPI 백엔드
│   ├── Dockerfile              # Python 3.12 slim + entrypoint.sh
│   ├── entrypoint.sh           # Alembic 마이그레이션 → Uvicorn 시작
│   ├── requirements.txt        # Python 의존성
│   ├── alembic.ini             # DB 마이그레이션 설정
│   ├── alembic/
│   │   ├── env.py              # Alembic 환경 (SQLAlchemy 연동)
│   │   └── versions/
│   │       └── 001_initial.py  # 초기 테이블 생성 마이그레이션
│   └── app/
│       ├── main.py             # FastAPI 앱 팩토리 + 라우터 등록
│       ├── config.py           # Pydantic Settings (환경변수)
│       ├── database.py         # SQLAlchemy engine + session + Base
│       ├── models.py           # 5개 테이블 ORM 모델
│       ├── schemas.py          # Pydantic request/response DTO
│       ├── crud.py             # 데이터베이스 CRUD + 승인/거절 로직
│       └── api/
│           ├── teams.py        # 팀 CRUD
│           ├── projects.py     # 프로젝트 CRUD
│           ├── issues.py       # 이슈 CRUD + workpad + work_logs
│           └── status_proposals.py  # 승인/거절 API
│
├── frontend/                   # React 프론트엔드
│   ├── Dockerfile              # 없음 (nginx Dockerfile에서 multi-stage로 빌드)
│   ├── package.json            # Node 의존성
│   ├── vite.config.js          # Vite 설정 (proxy: /api → localhost:8000)
│   └── src/
│       ├── main.jsx            # ReactDOM 렌더링 + BrowserRouter
│       ├── App.jsx             # 라우팅 (Home / Projects / Issues / Settings / MCP)
│       ├── components/
│       │   ├── Layout.jsx      # 공통 max-w-6xl mx-auto wrapper
│       │   ├── Sidebar.jsx     # 낮비게이션 (홈 / 프로젝트 / MCP / 설정)
│       │   └── SearchCommand.jsx
│       └── pages/
│           ├── Home.jsx           # 대시보드
│           ├── ProjectList.jsx    # 프로젝트 목록
│           ├── ProjectDetail.jsx  # 프로젝트 이슈 목록
│           ├── IssueDetailPage.jsx # 이슈 상세 (3:1 그리드)
│           ├── Settings.jsx       # 프로필 정보
│           └── McpSettingsPage.jsx # MCP 연동 가이드 (stdio + HTTP)
│
├── nginx/
│   ├── Dockerfile              # Multi-stage: Node 빌드 → Nginx serve
│   └── default.conf            # /api/ proxy, /docs proxy, /mcp proxy, / 정적 파일
│
├── mcp/
│   ├── Dockerfile              # Python 3.12 slim + FastMCP
│   └── server.py               # Python MCP SDK (stdio / streamable-http)
│
├── mcp.json                    # Kimi Code CLI MCP 설정 샘플
│
└── docs/
    └── ARCHITECTURE.md         # 본 문서
```

---

## 10. 환경변수 매트릭스

| 변수 | 기본값 | 설정 위치 | 설명 |
|------|--------|----------|------|
| `DATABASE_URL` | `postgresql+psycopg2://symphony:symphony@localhost:5432/symphony` | `.env` / docker-compose | PostgreSQL 연결 문자열 |
| `SYMPHONY_API_URL` | `http://localhost:8000/api/v1` | `mcp.json` / shell env | MCP 서버가 호출할 API 주소 |
| `SYMPHONY_API_KEY` | - | `mcp.json` / shell env | MCP 서버 인증용 API 키 |

### 환경별 설정

| 환경 | DATABASE_URL | SYMPHONY_API_URL |
|------|-------------|------------------|
| 로컬 개발 | `postgresql+psycopg2://symphony:symphony@localhost:5432/symphony` | `http://localhost:8000/api/v1` |
| Docker Compose | `postgresql+psycopg2://symphony:symphony@db:5432/symphony` | `http://localhost:18080/api/v1` |
| Docker 내부 (MCP) | - | `http://backend:8000/api/v1` | `SYMPHONY_API_KEY` 환경변수 필요 |

---

> 문서 버전: 0.2.0 | 최종 수정: 2026-05-07

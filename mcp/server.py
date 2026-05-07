"""
Symphony Lite MCP Server

AI 에이전트(Kimi, Claude, Copilot 등)가 사내 이슈 트래커와 통신하기 위한
Model Context Protocol (MCP) 서버입니다.

실행 방법:
    # stdio transport (기본) — 로컬 에이전트 연동
    SYMPHONY_API_URL=http://localhost:8000/api/v1 SYMPHONY_API_KEY=xxx python mcp/server.py

    # streamable-http transport — 원격 연동
    SYMPHONY_API_URL=http://localhost:8000/api/v1 SYMPHONY_API_KEY=xxx \
        python mcp/server.py --transport streamable-http

    # Docker Compose 난내 (nginx 프록시 경유)
    SYMPHONY_API_URL=http://nginx/api/v1 SYMPHONY_API_KEY=xxx \
        python mcp/server.py --transport streamable-http --host 0.0.0.0
"""

import argparse
import contextvars
import os
from typing import Optional, Literal
from mcp.server.fastmcp import FastMCP
import httpx

APP_NAME = "symphony-lite-mcp"
BASE_URL = os.getenv("SYMPHONY_API_URL", "http://localhost:8000/api/v1")
ENV_API_KEY = os.getenv("SYMPHONY_API_KEY", "")

# HTTP transport 요청에서 추출한 API 키 (contextvars로 스레드/코루틴 안전)
api_key_var = contextvars.ContextVar("api_key", default="")


def _get_headers():
    headers = {"X-Agent-ID": "mcp"}
    # HTTP 헤더에서 추출한 키 우선, 없으면 환경변수 폴백
    api_key = api_key_var.get() or ENV_API_KEY
    if api_key:
        headers["X-API-Key"] = api_key
    return headers


def register_tools(mcp: FastMCP):
    @mcp.tool()
    async def symphony_list_issues(
        project_slug: str,
        state: Optional[Literal["todo", "in_progress", "review", "rework"]] = None,
        assignee_id: Optional[str] = None,
        limit: int = 20,
    ) -> str:
        """프로젝트의 활성 이슈 목록을 조회합니다. assignee_id를 지정하면 해당 사용자가 담당자인 이슈만 필터링합니다."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
            params = {"state": state, "assignee_id": assignee_id}
            resp = await client.get(
                f"/issues/project/{project_slug}",
                params={k: v for k, v in params.items() if v is not None},
                headers=_get_headers(),
            )
            resp.raise_for_status()
            data = resp.json()
            text = f"총 {len(data)}개의 이슈:\n\n"
            for issue in data:
                assignee = issue.get("assignee", {})
                assignee_name = assignee.get("name", "미지정") if assignee else "미지정"
                text += (
                    f"- {issue['identifier']}: {issue['title']} "
                    f"(상태: {issue['state']}, 우선순위: {issue['priority']}, 담당자: {assignee_name})\n"
                )
            return text

    @mcp.tool()
    async def symphony_get_issue(identifier: str) -> str:
        """특정 이슈의 상세 정보를 조회합니다. Markdown 본문과 workpad를 포함합니다"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
            resp = await client.get(
                f"/issues/{identifier}", headers=_get_headers()
            )
            resp.raise_for_status()
            issue = resp.json()
            text = f"#{issue['identifier']}: {issue['title']}\n"
            text += f"상태: {issue['state']}\n"
            text += f"우선순위: {issue['priority']}\n"
            text += f"프로젝트: {issue.get('project', {}).get('name', '-')}\n\n"
            text += f"--- 본문 ---\n{issue.get('body', '본문 없음')}\n\n"
            if issue.get("workpad"):
                text += f"--- Workpad (에이전트 진행 상황) ---\n{issue['workpad']}\n"
            return text

    @mcp.tool()
    async def symphony_update_workpad(identifier: str, workpad: str) -> str:
        """이슈의 workpad(진행 상황)를 업데이트합니다. 에이전트는 이를 통해 계획과 진행 상황을 기록합니다"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
            resp = await client.patch(
                f"/issues/{identifier}",
                json={"workpad": workpad},
                headers=_get_headers(),
            )
            resp.raise_for_status()
            return f"✅ Workpad 업데이트 완료: {identifier}"

    @mcp.tool()
    async def symphony_propose_status_change(
        identifier: str,
        to_state: Literal[
            "todo", "in_progress", "review", "rework", "merging", "done", "cancelled"
        ],
        reason: str = "",
    ) -> str:
        """이슈 상태 변경을 제안합니다. 개발자가 승인해야 실제로 반영됩니다"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
            resp = await client.post(
                f"/issues/{identifier}/status-proposals",
                json={
                    "to_state": to_state,
                    "reason": reason,
                    "proposed_by": "agent:mcp",
                },
                headers=_get_headers(),
            )
            resp.raise_for_status()
            return (
                f"✅ 상태 변경 제안 완료: {identifier} → {to_state}\n"
                f"개발자가 웹 UI에서 승인할 때까지 실제 상태는 변경되지 않습니다."
            )

    @mcp.tool()
    async def symphony_log_work(
        identifier: str,
        event_type: Literal[
            "plan_created",
            "code_committed",
            "test_run",
            "error",
            "pr_created",
            "merge_completed",
        ],
        payload: Optional[dict] = None,
    ) -> str:
        """작업 이벤트를 기록합니다 (테스트 결과, 커밋 SHA, 오류 등)"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
            resp = await client.post(
                f"/issues/{identifier}/work-logs",
                json={
                    "event_type": event_type,
                    "payload": payload or {},
                    "agent_id": "mcp-agent",
                },
                headers=_get_headers(),
            )
            resp.raise_for_status()
            return f"✅ 작업 로그 기록 완료: {event_type}"

    @mcp.tool()
    async def symphony_create_issue(
        project_slug: str,
        title: str,
        body: str,
        priority: int = 3,
        labels: Optional[list[str]] = None,
    ) -> str:
        """새로운 이슈를 생성합니다"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
            # 프로젝트 조회
            proj_resp = await client.get(
                f"/projects/{project_slug}", headers=_get_headers()
            )
            proj_resp.raise_for_status()
            project = proj_resp.json()

            # identifier 자동 생성
            list_resp = await client.get(
                f"/issues/project/{project_slug}", headers=_get_headers()
            )
            list_resp.raise_for_status()
            existing = list_resp.json()
            next_num = len(existing) + 1
            identifier = f"{project_slug.upper()}-{next_num}"

            resp = await client.post(
                f"/issues/project/{project_slug}",
                json={
                    "identifier": identifier,
                    "title": title,
                    "body": body,
                    "project_id": str(project["id"]),
                    "team_id": str(project["team_id"]),
                    "priority": priority,
                    "labels": labels or [],
                },
                headers=_get_headers(),
            )
            resp.raise_for_status()
            issue = resp.json()
            return f"✅ 이슈 생성 완료: {issue['identifier']}"


def main():
    parser = argparse.ArgumentParser(description="Symphony Lite MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default="stdio",
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="HTTP/SSE transport용 호스트 (기본: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8001,
        help="HTTP/SSE transport용 포트 (기본: 8001)",
    )
    args = parser.parse_args()

    if args.transport == "streamable-http":
        from starlette.applications import Starlette
        from starlette.routing import Mount
        import uvicorn

        _original_api_key = ENV_API_KEY

        class LoggingMiddleware:
            def __init__(self, app):
                self.app = app

            async def __call__(self, scope, receive, send):
                if scope["type"] == "http":
                    method = scope.get("method", "")
                    path = scope.get("path", "")
                    headers = dict(scope.get("headers", []))
                    api_key = headers.get(b"x-api-key", b"")
                    print(f"[MCP] >>> {method} {path} | X-API-Key={'set' if api_key else 'none'}", flush=True)

                    async def wrapped_send(message):
                        if message.get("type") == "http.response.start":
                            status = message.get("status", 0)
                            print(f"[MCP] <<< HTTP {status} {method} {path}", flush=True)
                        await send(message)

                    await self.app(scope, receive, wrapped_send)
                else:
                    await self.app(scope, receive, send)

        class APIKeyMiddleware:
            def __init__(self, app, fallback_key=""):
                self.app = app
                self.fallback_key = fallback_key

            async def __call__(self, scope, receive, send):
                global ENV_API_KEY
                if scope["type"] == "http":
                    headers = dict(scope.get("headers", []))
                    api_key = headers.get(b"x-api-key", b"").decode()
                    if api_key:
                        ENV_API_KEY = api_key
                try:
                    await self.app(scope, receive, send)
                finally:
                    ENV_API_KEY = self.fallback_key

        mcp = FastMCP(
            APP_NAME,
            host=args.host,
            port=args.port,
            stateless_http=True,
            streamable_http_path="/",
        )
        register_tools(mcp)

        import contextlib

        mcp_app = mcp.streamable_http_app()

        @contextlib.asynccontextmanager
        async def lifespan(app):
            async with mcp.session_manager.run():
                yield

        app = Starlette(routes=[Mount("/mcp", app=mcp_app)], lifespan=lifespan)
        app = APIKeyMiddleware(app, fallback_key=ENV_API_KEY)

        uvicorn.run(app, host=args.host, port=args.port)
    else:
        mcp = FastMCP(APP_NAME)
        register_tools(mcp)
        mcp.run(transport=args.transport)


if __name__ == "__main__":
    main()

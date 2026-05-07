#!/bin/bash
# Symphony Lite MCP One-Liner Installer
# Usage: curl -fsSL <url> | bash
set -e

API_URL="${SYMPHONY_API_URL:-http://localhost:18080/api/v1}"
API_KEY="${SYMPHONY_API_KEY:-}"
INSTALL_DIR="${HOME}/.symphony-mcp"
VENV_DIR="${INSTALL_DIR}/venv"

echo "🎵 Symphony Lite MCP Installer"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3이 설치되어 있지 않습니다."
    echo ""
    echo "설치 방법:"
    echo "  macOS:   brew install python@3.12"
    echo "  Ubuntu:  sudo apt update && sudo apt install python3 python3-venv python3-pip"
    echo "  CentOS:  sudo yum install python3"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "✅ Python ${PYTHON_VERSION} 확인됨"

# Create directories
mkdir -p "${INSTALL_DIR}"

# Create virtualenv
if [ ! -d "${VENV_DIR}" ]; then
    echo "📦 가상환경 생성 중..."
    python3 -m venv "${VENV_DIR}"
fi

source "${VENV_DIR}/bin/activate"

# Install packages
echo "📦 패키지 설치 중 (mcp, httpx)..."
pip install -q --upgrade pip
pip install -q mcp==1.6.0 httpx==0.27.2

# Write MCP server script
cat > "${INSTALL_DIR}/server.py" << 'PYEOF'
import asyncio
import argparse
import os
from typing import Optional
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
import httpx

APP_NAME = "symphony-lite-mcp"
BASE_URL = os.getenv("SYMPHONY_API_URL", "http://localhost:8000/api/v1")
API_KEY = os.getenv("SYMPHONY_API_KEY", "")

server = Server(APP_NAME)

def _get_headers():
    headers = {"X-Agent-ID": "mcp"}
    if API_KEY:
        headers["X-API-Key"] = API_KEY
    return headers

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(name="symphony_list_issues", description="프로젝트의 활성 이슈 목록을 조회합니다", inputSchema={"type":"object","properties":{"project_slug":{"type":"string"},"state":{"type":"string","enum":["todo","in_progress","review","rework"]},"limit":{"type":"integer","default":20}},"required":["project_slug"]}),
        Tool(name="symphony_get_issue", description="특정 이슈의 상세 정보를 조회합니다", inputSchema={"type":"object","properties":{"identifier":{"type":"string"}},"required":["identifier"]}),
        Tool(name="symphony_update_workpad", description="이슈의 workpad를 업데이트합니다", inputSchema={"type":"object","properties":{"identifier":{"type":"string"},"workpad":{"type":"string"}},"required":["identifier","workpad"]}),
        Tool(name="symphony_propose_status_change", description="이슈 상태 변경을 제안합니다", inputSchema={"type":"object","properties":{"identifier":{"type":"string"},"to_state":{"type":"string","enum":["todo","in_progress","review","rework","merging","done","cancelled"]},"reason":{"type":"string"}},"required":["identifier","to_state"]}),
        Tool(name="symphony_log_work", description="작업 이벤트를 기록합니다", inputSchema={"type":"object","properties":{"identifier":{"type":"string"},"event_type":{"type":"string","enum":["plan_created","code_committed","test_run","error","pr_created","merge_completed"]},"payload":{"type":"object"}},"required":["identifier","event_type"]}),
        Tool(name="symphony_create_issue", description="새로운 이슈를 생성합니다", inputSchema={"type":"object","properties":{"project_slug":{"type":"string"},"title":{"type":"string"},"body":{"type":"string"},"priority":{"type":"integer","default":3},"labels":{"type":"array","items":{"type":"string"}}},"required":["project_slug","title","body"]}),
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent | ImageContent | EmbeddedResource]:
    client = httpx.AsyncClient(base_url=BASE_URL, timeout=30.0)
    try:
        if name == "symphony_list_issues":
            params = {"state": arguments.get("state")}
            resp = await client.get(f"/issues/project/{arguments['project_slug']}", params={k: v for k, v in params.items() if v is not None}, headers=_get_headers())
            resp.raise_for_status()
            data = resp.json()
            text = f"총 {len(data)}개의 이슈:\n\n"
            for issue in data:
                text += f"- {issue['identifier']}: {issue['title']} (상태: {issue['state']}, 우선순위: {issue['priority']})\n"
            return [TextContent(type="text", text=text)]
        elif name == "symphony_get_issue":
            resp = await client.get(f"/issues/{arguments['identifier']}", headers=_get_headers())
            resp.raise_for_status()
            issue = resp.json()
            text = f"#{issue['identifier']}: {issue['title']}\n상태: {issue['state']}\n우선순위: {issue['priority']}\n프로젝트: {issue.get('project',{}).get('name','-')}\n\n--- 본문 ---\n{issue.get('body','본문 없음')}\n"
            if issue.get('workpad'):
                text += f"\n--- Workpad ---\n{issue['workpad']}\n"
            return [TextContent(type="text", text=text)]
        elif name == "symphony_update_workpad":
            resp = await client.patch(f"/issues/{arguments['identifier']}", json={"workpad": arguments["workpad"]}, headers=_get_headers())
            resp.raise_for_status()
            return [TextContent(type="text", text=f"✅ Workpad 업데이트 완료: {arguments['identifier']}")]
        elif name == "symphony_propose_status_change":
            resp = await client.post(f"/issues/{arguments['identifier']}/status-proposals", json={"to_state": arguments["to_state"], "reason": arguments.get("reason", ""), "proposed_by": "agent:mcp"}, headers=_get_headers())
            resp.raise_for_status()
            return [TextContent(type="text", text=f"✅ 상태 변경 제안 완료: {arguments['identifier']} → {arguments['to_state']}")]
        elif name == "symphony_log_work":
            resp = await client.post(f"/issues/{arguments['identifier']}/work-logs", json={"event_type": arguments["event_type"], "payload": arguments.get("payload", {}), "agent_id": "mcp-agent"}, headers=_get_headers())
            resp.raise_for_status()
            return [TextContent(type="text", text=f"✅ 작업 로그 기록 완료: {arguments['event_type']}")]
        elif name == "symphony_create_issue":
            proj_resp = await client.get(f"/projects/{arguments['project_slug']}", headers=_get_headers())
            proj_resp.raise_for_status()
            project = proj_resp.json()
            list_resp = await client.get(f"/issues/project/{arguments['project_slug']}", headers=_get_headers())
            list_resp.raise_for_status()
            existing = list_resp.json()
            next_num = len(existing) + 1
            identifier = f"{arguments['project_slug'].upper()}-{next_num}"
            resp = await client.post(f"/issues/project/{arguments['project_slug']}", json={"identifier": identifier, "title": arguments["title"], "body": arguments["body"], "project_id": str(project["id"]), "team_id": str(project["team_id"]), "priority": arguments.get("priority", 3), "labels": arguments.get("labels", [])}, headers=_get_headers())
            resp.raise_for_status()
            issue = resp.json()
            return [TextContent(type="text", text=f"✅ 이슈 생성 완료: {issue['identifier']}")]
        else:
            return [TextContent(type="text", text=f"❌ 알 수 없는 tool: {name}")]
    except httpx.HTTPStatusError as e:
        return [TextContent(type="text", text=f"❌ API 오류 ({e.response.status_code}): {e.response.text}")]
    except Exception as e:
        return [TextContent(type="text", text=f"❌ 오류 발생: {str(e)}")]
    finally:
        await client.aclose()

async def main():
    parser = argparse.ArgumentParser(description="Symphony Lite MCP Server")
    parser.add_argument("--transport", choices=["stdio", "sse"], default="stdio")
    args = parser.parse_args()
    if args.transport == "stdio":
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream, server.create_initialization_options())
    else:
        print("SSE transport는 아직 구현되지 않았습니다. stdio를 사용하세요.")

if __name__ == "__main__":
    asyncio.run(main())
PYEOF

echo "✅ MCP 서버 스크립트 설치 완료: ${INSTALL_DIR}/server.py"

# Write env file
cat > "${INSTALL_DIR}/.env" <<EOF
SYMPHONY_API_URL=${API_URL}
SYMPHONY_API_KEY=${API_KEY}
EOF

echo "✅ 환경 변수 파일 생성: ${INSTALL_DIR}/.env"

# Generate agent configs
KIMI_CONFIG="${INSTALL_DIR}/mcp-kimi.json"
cat > "${KIMI_CONFIG}" <<EOF
{
  "mcpServers": {
    "symphony-lite": {
      "command": "${VENV_DIR}/bin/python",
      "args": ["${INSTALL_DIR}/server.py"],
      "env": {
        "SYMPHONY_API_URL": "${API_URL}",
        "SYMPHONY_API_KEY": "${API_KEY}"
      }
    }
  }
}
EOF

CLAUDE_CONFIG="${INSTALL_DIR}/mcp-claude.json"
cat > "${CLAUDE_CONFIG}" <<EOF
{
  "mcpServers": {
    "symphony-lite": {
      "command": "${VENV_DIR}/bin/python",
      "args": ["${INSTALL_DIR}/server.py"],
      "env": {
        "SYMPHONY_API_URL": "${API_URL}",
        "SYMPHONY_API_KEY": "${API_KEY}"
      }
    }
  }
}
EOF

echo ""
echo "🎉 설치 완료!"
echo ""
echo "📁 설치 위치: ${INSTALL_DIR}"
echo ""
echo "🔗 연동 방법:"
echo ""
echo "  [Kimi Code CLI]"
echo "  kimi mcp add --transport stdio symphony-lite -- \\"
echo "    ${VENV_DIR}/bin/python ${INSTALL_DIR}/server.py"
echo ""
echo "  [Claude Code]"
echo "  ~/.mcp.json 에 아래 내용을 추가하세요:"
echo "  ${CLAUDE_CONFIG}"
echo ""
echo "  [또는 직접 실행]"
echo "  ${VENV_DIR}/bin/python ${INSTALL_DIR}/server.py"
echo ""

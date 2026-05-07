from fastapi import APIRouter

router = APIRouter(prefix="/mcp", tags=["mcp"])


@router.get("/install-guide")
def get_install_guide():
    """MCP 설치 가이드 기본 정보"""
    return {
        "script_url": "/scripts/install-mcp.sh",
        "script_url_windows": "/scripts/install-mcp.ps1",
        "note": "상세 가이드는 웹 UI의 MCP 연동 페이지(/mcp-settings)에서 확인하세요",
    }

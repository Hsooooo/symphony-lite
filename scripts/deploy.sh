#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "${PROJECT_DIR}"

echo "🚀 Symphony Lite 배포 시작..."

# 1. Git 최신화 (필요시 주석 해제)
# echo "📥 Git pull..."
# git pull origin main

# 2. Docker Compose 빌드 & 배포
# BuildKit이 container에 추가적인 thread/PID 제한을 걸어서
# pip/apt가 실패할 수 있으므로 비활성화
export DOCKER_BUILDKIT=0
echo "🐳 Docker Compose build & up (BuildKit disabled)..."
docker compose up --build -d

# 3. Health check
echo "⏳ 서비스 기동 대기 중..."
sleep 5

MAX_RETRIES=30
RETRY=0
while ! curl -sf http://localhost:18080/api/v1/teams >/dev/null 2>&1; do
    RETRY=$((RETRY + 1))
    if [ "$RETRY" -ge "$MAX_RETRIES" ]; then
        echo "❌ Health check 실패. 로그를 확인하세요:"
        echo "   docker compose logs --tail 50 backend"
        exit 1
    fi
    echo "   ...(${RETRY}/${MAX_RETRIES})"
    sleep 2
done
echo "✅ Backend health check 통과"

# 4. Cleanup
echo "🧹 Docker 리소스 정리..."

# Dangling 이미지 (<none>:<none>) 정리 — 빌드 후 남는 중간 레이어
DANGLING=$(docker images -f "dangling=true" -q | wc -l | tr -d ' ')
if [ "$DANGLING" -gt 0 ]; then
    docker image prune -f
    echo "   🗑️  Dangling 이미지 ${DANGLING}개 삭제"
else
    echo "   ✓  Dangling 이미지 없음"
fi

# 프로젝트 관련 사용되지 않는 이미지 정리 (현재 실행 중인 컨테이너 제외)
OLD_IMAGES=$(docker images --format "{{.Repository}}" | grep -c "^symphony-lite" || true)
if [ "$OLD_IMAGES" -gt 0 ]; then
    docker images --format "{{.Repository}}:{{.Tag}} {{.ID}}" | \
        grep "^symphony-lite" | \
        awk '{print $2}' | \
        sort -u | \
        xargs -r docker rmi 2>/dev/null || true
    echo "   🗑️  프로젝트 미사용 이미지 정리"
fi

# 사용되지 않는 볼륨 정리
VOLUMES=$(docker volume ls -q | wc -l | tr -d ' ')
UNUSED_VOLUMES=$(docker volume ls -f dangling=true -q | wc -l | tr -d ' ')
if [ "$UNUSED_VOLUMES" -gt 0 ]; then
    docker volume prune -f
    echo "   🗑️  사용되지 않는 볼륨 ${UNUSED_VOLUMES}개 삭제"
else
    echo "   ✓  사용되지 않는 볼륨 없음"
fi

# 사용되지 않는 네트워크 정리
UNUSED_NETWORKS=$(docker network ls -f dangling=true -q | wc -l | tr -d ' ')
if [ "$UNUSED_NETWORKS" -gt 0 ]; then
    docker network prune -f
    echo "   🗑️  사용되지 않는 네트워크 정리"
else
    echo "   ✓  사용되지 않는 네트워크 없음"
fi

# BuildKit 빌드 캐시 정리 (5GB 이하로 유지)
docker builder prune -f --keep-storage=5GB 2>/dev/null || true
echo "   🗑️  BuildKit 캐시 정리 (5GB 이하 유지)"

echo ""
echo "✅ 배포 완료!"
echo "   🌐 http://localhost:18080"

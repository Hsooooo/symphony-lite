#Requires -Version 5.1
$ErrorActionPreference = "Stop"

$PROJECT_DIR = Split-Path -Parent $PSScriptRoot
Set-Location $PROJECT_DIR

Write-Host "🚀 Symphony Lite 배포 시작..." -ForegroundColor Cyan

# 1. Git 최신화 (필요시 주석 해제)
# Write-Host "📥 Git pull..." -ForegroundColor Cyan
# git pull origin main

# 2. Docker Compose 빌드 & 배포
Write-Host "🐳 Docker Compose build & up..." -ForegroundColor Cyan
docker compose up --build -d

# 3. Health check
Write-Host "⏳ 서비스 기동 대기 중..." -ForegroundColor Cyan
Start-Sleep -Seconds 5

$MAX_RETRIES = 30
$RETRY = 0
$HEALTHY = $false

while ($RETRY -lt $MAX_RETRIES) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:18080/api/v1/teams" -UseBasicParsing -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            $HEALTHY = $true
            break
        }
    } catch {
        $RETRY++
        Write-Host "   ...(${RETRY}/${MAX_RETRIES})" -ForegroundColor Gray
        Start-Sleep -Seconds 2
    }
}

if (-not $HEALTHY) {
    Write-Host "❌ Health check 실패." -ForegroundColor Red
    Write-Host "   docker compose logs --tail 50 backend" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Backend health check 통과" -ForegroundColor Green

# 4. Cleanup
Write-Host "🧹 Docker 리소스 정리..." -ForegroundColor Cyan

$dangling = @($(docker images -f "dangling=true" -q) | Where-Object { $_ } | Measure-Object).Count
if ($dangling -gt 0) {
    docker image prune -f | Out-Null
    Write-Host "   🗑️  Dangling 이미지 ${dangling}개 삭제" -ForegroundColor Green
} else {
    Write-Host "   ✓  Dangling 이미지 없음" -ForegroundColor Gray
}

$oldImages = @($(docker images --format "{{.Repository}}") | Where-Object { $_ -match "^symphony-lite" } | Measure-Object).Count
if ($oldImages -gt 0) {
    docker images --format "{{.Repository}}:{{.Tag}} {{.ID}}" | Where-Object { $_ -match "^symphony-lite" } | ForEach-Object {
        $id = ($_ -split " ")[1]
        docker rmi $id 2>$null | Out-Null
    }
    Write-Host "   🗑️  프로젝트 미사용 이미지 정리" -ForegroundColor Green
}

docker volume prune -f | Out-Null
$volDeleted = $?
docker network prune -f | Out-Null
$netDeleted = $?
docker builder prune -f --keep-storage=5GB 2>$null | Out-Null

Write-Host "   ✓  볼륨/네트워크/빌드캐시 정리 완료" -ForegroundColor Gray

Write-Host ""
Write-Host "✅ 배포 완료!" -ForegroundColor Green
Write-Host "   🌐 http://localhost:18080" -ForegroundColor Cyan

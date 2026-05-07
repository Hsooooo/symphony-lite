FROM python:3.12-slim-bullseye

WORKDIR /app

# psycopg2-binary가 pre-compiled wheel을 제공하므로 시스템 빌드 도구 불필요.
# 소스 빌드가 필요한 환경(예: ARM 등)에서는 아래 주석을 해제하세요.
# RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --progress-bar off --upgrade pip && \
    pip install --no-cache-dir --progress-bar off -r requirements.txt

COPY . .

# entrypoint 스크립트 실행 권한 부여
RUN chmod +x entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]

FROM python:3.12-slim-bookworm

WORKDIR /app

# PostgreSQL 클라이언트 및 빌드 도구 설치
RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# entrypoint 스크립트 실행 권한 부여
RUN chmod +x entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]

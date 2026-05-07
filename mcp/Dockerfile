FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir 'mcp>=1.10.0' 'httpx>=0.27.0'

COPY mcp/server.py .

EXPOSE 8001

CMD ["python", "server.py", "--transport", "streamable-http", "--host", "0.0.0.0", "--port", "8001"]

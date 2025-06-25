FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY . /app

WORKDIR /app

RUN uv sync --frozen --no-cache

# Render 不需要 EXPOSE，但保留也沒關係
EXPOSE 8000

# ✅ 使用 sh -c 來取得 $PORT（Render 必須）
CMD ["sh", "-c", "/app/.venv/bin/uvicorn main:app --host 0.0.0.0 --port $PORT"]

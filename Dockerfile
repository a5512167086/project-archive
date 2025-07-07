FROM python:3.13-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set work directory and copy app
WORKDIR /app
COPY . /app

# Install dependencies
RUN uv sync --frozen --no-cache

# Run FastAPI app using uvicorn
CMD ["/app/.venv/bin/uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]

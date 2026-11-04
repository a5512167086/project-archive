# Step 1: Start from an official NVIDIA CUDA base image
FROM nvidia/cuda:12.1.1-base-ubuntu22.04

# Step 2: Install Python, pip, and other essentials
# Note: Ubuntu 22.04's default python3 is 3.10. Let's use that for stability.
RUN apt-get update && \
    apt-get install -y \
    python3.10 \
    python3-pip \
    python3-venv && \
    rm -rf /var/lib/apt/lists/*

# Make python3 point to python3.10
RUN ln -s /usr/bin/python3 /usr/bin/python

# Install uv.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy the application into the container.
COPY . /app

# Install the application dependencies.
WORKDIR /app
RUN uv sync --frozen --no-cache

# Run the application.
CMD ["/app/.venv/bin/fastapi", "run", "app/main.py", "--port", "8531", "--host", "0.0.0.0"]
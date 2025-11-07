# syntax=docker/dockerfile:1.7-labs

# --- Builder Stage ---
# Use a full Python image to install build dependencies
FROM python:3.12-slim AS builder

RUN apt-get update \
    && apt-get install --no-install-recommends -y \
        git \
        openssh-client \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /root/.ssh && ssh-keyscan github.com >> /root/.ssh/known_hosts

RUN --mount=type=ssh ssh -vT git@github.com

# Set environment variables for Poetry
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache \
    VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Install Poetry itself
RUN pip install poetry==2.2.0

# Copy pyproject.toml and poetry.lock to leverage Docker cache
COPY pyproject.toml poetry.lock ./

# Install project dependencies (excluding dev dependencies)
RUN --mount=type=ssh \
    poetry install --no-root --only main

# --- Runtime Stage ---
# Use a slim, secure image for the final deployment
FROM python:3.12-slim AS runtime

# Copy the virtual environment and source code from the builder stage
COPY --from=builder /app/.venv /app/.venv
COPY . /app

# Set the PATH to include the virtual environment's bin directory
ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

CMD ["python", "src/testbenchmanager/main.py"]
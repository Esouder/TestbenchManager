
# --- Build Stage ---
FROM python:3.12-slim AS builder

# 1. Install git (Required for your 'epcomms' dependency)
RUN apt-get update && \
    apt-get install -y --no-install-recommends git

WORKDIR /app

# 2. Create a dedicated virtual environment for Poetry tools
#    This keeps Poetry's dependencies completely separate from your app's.
RUN python -m venv /opt/poetry-tools

# 3. Install Poetry + Plugin into that isolated tool venv
RUN /opt/poetry-tools/bin/pip install --no-cache-dir poetry poetry-plugin-bundle

# 4. Copy project files
COPY pyproject.toml poetry.lock README.md ./
COPY src ./src

# 5. Run the bundle command using the ISOLATED poetry executable
#    --python=/usr/local/bin/python ensures the bundled venv targets the main Docker python
RUN /opt/poetry-tools/bin/poetry bundle venv --only=main --python=/usr/local/bin/python /venv

# --- Runtime Stage ---
FROM python:3.12-slim AS runtime

WORKDIR /app

# 6. Copy the bundled environment
COPY --from=builder /venv /venv

# 7. Verify the symlink (It should point to /usr/local/bin/python)
RUN ls -l /venv/bin/python

# 8. Entrypoint
ENTRYPOINT ["/venv/bin/python", "-m", "testbenchmanager.main"]

LABEL org.opencontainers.image.source=https://github.com/Esouder/testbenchmanager

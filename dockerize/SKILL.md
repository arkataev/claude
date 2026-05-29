---
description: Scaffold Docker setup — Dockerfile, docker-compose, env vars, Makefile targets
user_invocable: true
argument: Optional description of services needed (e.g. "app + postgres + redis")
---

# Dockerize Project

Scaffold a production-ready Docker setup for the current project.

## Process

### 1. Analyze the Project

- Read the package manager config (pyproject.toml, package.json, go.mod, etc.)
- Identify the entry point and runtime command
- Find hardcoded URLs, paths, or config that should become env vars
- Identify external service dependencies

### 2. Make Configuration Configurable

Before writing Docker files, ensure the app reads config from environment variables with sensible defaults:
- Database URLs
- External service URLs
- File paths that differ between local and container

Default values must preserve existing local development behavior (no breakage without Docker).

### 3. Create Dockerfile

Principles:
- Use the official slim image for the project's language/runtime
- Install dependencies before copying source (layer caching)
- No virtual environments inside containers — install to system Python/Node/etc.
- No dev dependencies in the final image
- Use the standard package manager for dependency installation
- Expose the correct port
- CMD with the production server command

For Python + Poetry projects:
```dockerfile
FROM python:X.Y-slim
RUN pip install --no-cache-dir poetry==X.Y.Z
WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false \
    && poetry install --only main --no-interaction --no-ansi --no-root
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 4. Create .dockerignore

Exclude: `.venv`, `__pycache__`, `.git`, `.idea`, `*.db`, `tests`, dev config files, documentation.

### 5. Create docker-compose.yml

- One service per component (app, database, external services)
- Environment variables for service-to-service communication (use Docker DNS names, not localhost)
- Volumes for persistent data (databases)
- `depends_on` for startup ordering
- Only expose ports that external clients need

### 6. Update Makefile

Add targets:
- `docker-up` — build and start all services
- `docker-down` — stop and remove containers

Update existing targets if they reference external services (e.g. `test-integration` should use `docker compose` instead of raw `docker run`).

### 7. Verify

- Run `docker compose up --build -d`
- Check all containers are running (`docker compose ps`)
- Test the app responds (curl the health/main endpoint)
- Run `docker compose down`

### 8. Update Documentation

- Add Docker commands to README.md and CLAUDE.md
- Document environment variables (name, default, description)

## Output

Report:
- Files created/modified
- Environment variables introduced
- Services in the compose stack
- Verification result (containers up, app responding)

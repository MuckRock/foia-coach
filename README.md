# FOIA Coach

A RAG-powered assistant that helps users navigate Freedom of Information Act (FOIA) processes, with jurisdiction-specific guidance based on uploaded resources.

## Architecture

- **API** (`api/`) — Django REST Framework backend with pluggable RAG providers (OpenAI, Gemini, Mock)
- **UI** (`ui/`) — SvelteKit frontend (Svelte 5)
- **Database** — PostgreSQL 15

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose

## Local Setup

### 1. Create environment files

```bash
mkdir -p .envs/.local
```

Create `.envs/.local/.postgres`:

```
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=foia_coach
POSTGRES_USER=foia_coach_user
POSTGRES_PASSWORD=foia_coach_dev_password_change_in_production
```

Create `.envs/.local/.api`:

```
DJANGO_SETTINGS_MODULE=config.settings.local
DJANGO_SECRET_KEY=change-me-in-production
RAG_PROVIDER=mock
MUCKROCK_API_URL=http://localhost:8000
MUCKROCK_API_TOKEN=your-muckrock-api-token
GEMINI_API_KEY=your-gemini-api-key
GEMINI_FILE_SEARCH_STORE_NAME=StatePublicRecordsStore
GEMINI_MODEL=gemini-2.0-flash
GEMINI_REAL_API_ENABLED=false
OPENAI_API_KEY=your-openai-api-key
OPENAI_VECTOR_STORE_NAME=StatePublicRecordsStore
OPENAI_MODEL=gpt-4o-mini
OPENAI_REAL_API_ENABLED=false
```

`RAG_PROVIDER=mock` lets you run the app without real API keys. To use a real LLM provider, set `RAG_PROVIDER` to `openai` or `gemini`, supply a valid API key, and set the corresponding `*_REAL_API_ENABLED=true`.

### 2. Start the services

```bash
docker compose up --build
```

This starts three containers:

| Service    | URL                   |
| ---------- | --------------------- |
| API        | http://localhost:8001 |
| UI         | http://localhost:5173 |
| PostgreSQL | localhost:5433        |

### 3. Run migrations

```bash
docker compose exec api python manage.py migrate
```

## Testing

```bash
# Run all API tests
docker compose exec api pytest

# Run a specific test file
docker compose exec api pytest apps/jurisdiction/tests/test_providers.py
```

Tests use the Mock provider by default, so no API keys are needed.

## Code Quality

```bash
# Format
docker compose exec api black .
docker compose exec api isort .

# Lint
docker compose exec api pylint apps/
```

## Further Reading

- [API documentation](api/README.md)
- [RAG provider safety settings](api/README_GEMINI_SAFETY.md)

# Claude Code Instructions for FOIA Coach

## Project Structure
- `api/` — Django REST API backend (Python 3.11, Django 4.2, DRF)
- `ui/` — SvelteKit frontend (Svelte 5, Vite 7, Node 20)
- `docker-compose.yml` — Docker Compose for local development

## Quick Start
```bash
# Start all services
docker compose up --build

# API: http://localhost:8001/api/v1/
# UI:  http://localhost:5173
# DB:  localhost:5433
```

## Testing

### API Tests
Run tests inside the API container:
```bash
docker compose exec api pytest
```

Or run specific tests:
```bash
docker compose exec api pytest apps/jurisdiction/tests/test_providers.py
docker compose exec api pytest apps/api/tests/test_api.py::TestQueryViewSet
```

Test settings are in `api/config/settings/test.py`. Tests use `--nomigrations` and `--create-db` by default (see `api/pytest.ini`).

### Testing Best Practices
- Follow TDD: write test first, confirm failure, implement, confirm pass
- Use `factory_boy` factories from `apps/jurisdiction/factories.py`
- Use `create_batch()` instead of loops for multiple instances
- Use `requests_mock` for HTTP mocking
- Use `MockProvider` (RAG_PROVIDER=mock) for tests that don't need real API calls

## Code Quality

### Format
```bash
docker compose exec api black .
docker compose exec api isort .
```

### Lint
```bash
docker compose exec api pylint apps/
```

## Architecture

### RAG Provider System
The API supports multiple LLM providers via an abstract provider interface:
- **OpenAI** — Vector Stores + Responses API
- **Gemini** — File Search API
- **Mock** — For testing (no real API calls)

Set via `RAG_PROVIDER` env var. Provider code lives in `api/apps/jurisdiction/services/providers/`.

### Key Models
- `JurisdictionResource` — Knowledge files per state
- `ResourceProviderUpload` — Tracks uploads to each provider
- `ExampleResponse` — Few-shot examples for query context
- `NFOICPartner` — State partner organization info

### API Endpoints
- `POST /api/v1/query/` — Query the RAG system
- `GET  /api/v1/jurisdictions/` — List states
- `GET  /api/v1/resources/` — List resources
- `POST /api/v1/resources/upload/` — Upload resource files

### Communication with MuckRock
The API fetches jurisdiction data from MuckRock's REST API. Set `MUCKROCK_API_URL` to point to a running MuckRock instance (defaults to `http://localhost:8000`).

## Environment Variables
See `.env.example` for all required variables. Local dev env files go in `.envs/.local/`.

## Management Commands
```bash
docker compose exec api python manage.py test_rag_provider --provider openai
docker compose exec api python manage.py upload_resources_to_provider --provider openai
docker compose exec api python manage.py gemini_query "your question" --state CO
```

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Structure

- `api/` — Django REST API backend (Python 3.11, Django 4.2, DRF)
- `ui/` — SvelteKit frontend (Svelte 5, Vite 7, Node 20)
- `docker-compose.yml` — local dev stack (api, ui, postgres)
- `render.yml` — Render.com deployment blueprint (api + ui + db)
- `docs/` — design docs (`architecture.md`, `CACHING.md`, `openai-provider-plan.md`, `render-deploy.md`)
- `api/README.md` — deeper API docs; `api/MIGRATION_GUIDE.md`, `api/API_DOCUMENTATION.md`, `api/SETUP.md` cover specifics

## Quick Start

```bash
# Local env files live in .envs/.local/.api and .envs/.local/.postgres
# (see top-level README for required keys)
docker compose up --build

# API: http://localhost:8001/api/v1/
# UI:  http://localhost:5173
# DB:  localhost:5433
```

Run migrations the first time: `docker compose exec api python manage.py migrate`.

## Testing

API tests run inside the api container:

```bash
docker compose exec api pytest
docker compose exec api pytest apps/jurisdiction/tests/test_providers.py
docker compose exec api pytest apps/api/tests/test_api.py::TestQueryViewSet
```

`api/pytest.ini` sets `DJANGO_SETTINGS_MODULE=config.settings.test` and runs with `--nomigrations --create-db`. The `test` settings module force-disables real provider API calls — tests should never hit OpenAI/Gemini.

### Testing conventions

- TDD: write a failing test, implement, confirm green.
- Use `factory_boy` factories from `apps/jurisdiction/factories.py`; prefer `create_batch()` over loops.
- Mock HTTP with `requests_mock`.
- Use `MockProvider` (`RAG_PROVIDER=mock`) for anything that doesn't need a real LLM.
- Disconnect the `post_save` upload signal in tests that create `JurisdictionResource` instances directly — otherwise the signal will try to upload.

## Code Quality

```bash
# API
docker compose exec api black .
docker compose exec api isort .
docker compose exec api pylint apps/

# UI (run from host or `docker compose exec ui ...`)
cd ui && npm run check    # svelte-check / TS
cd ui && npm run lint     # prettier + eslint
cd ui && npm run format   # prettier --write
```

## Architecture

### RAG Provider System

The API queries an LLM through a pluggable provider interface (`api/apps/jurisdiction/services/providers/`):

- `base.py` — `RAGProviderBase` ABC, plus `ProviderError` / `ProviderConfigError` / `ProviderAPIError`.
- `factory.py` — `RAGProviderFactory.get_provider(name)` returns an instance, pulling per-provider config (API key, model, store name, `*_REAL_API_ENABLED` flag) from Django settings.
- `helpers.py` — `query_with_fallback(...)` is what the API viewset calls; it tries the requested provider then falls back.
- `openai_provider.py` — OpenAI Vector Stores + Responses API.
- `gemini_provider.py` — Gemini File Search API.
- `mock_provider.py` — deterministic fake responses; used for tests and `RAG_PROVIDER=mock` dev.

**Safety flag:** real OpenAI/Gemini calls are gated on `OPENAI_REAL_API_ENABLED` / `GEMINI_REAL_API_ENABLED` (default `false`). The query view returns 503 with `error_type: api_disabled` when the flag is off — don't paper over this; flip the flag explicitly when you actually want a real call.

### Multi-provider uploads

`JurisdictionResource` is the file. `ResourceProviderUpload` is the through model that tracks per-provider upload state (`provider_file_id`, `provider_store_id`, `index_status`, etc.) so the same resource can live in OpenAI and Gemini stores simultaneously. A `post_save` signal on `JurisdictionResource` kicks off uploads via `transaction.on_commit()`.

### Key Models (`apps/jurisdiction/models.py`)

- `JurisdictionResource` — knowledge file for a state (jurisdiction is referenced by id/abbrev only; the canonical record lives in MuckRock).
- `ResourceProviderUpload` — per-provider upload tracking (above).
- `ExampleResponse` — few-shot Q/A examples used in query context.
- `NFOICPartner` — state partner-org info.

### API Endpoints

Routes live in `api/apps/api/urls.py`. The `QueryViewSet` exposes `status` and `query` as DRF `@action`s, so the URLs are nested:

- `GET  /api/v1/query/status/` — provider availability + `*_REAL_API_ENABLED` state
- `POST /api/v1/query/query/` — RAG query (body: `question`, optional `state`, `provider`, `model`, `system_prompt`, `context`)
- `GET  /api/v1/jurisdictions/` and `/api/v1/jurisdictions/{abbrev}/` — proxied from MuckRock
- `GET  /api/v1/resources/` — list `JurisdictionResource`
- `POST /api/v1/resources/upload/` — multipart upload (creates resource + triggers provider upload)
- `GET  /api/v1/examples/`, `GET /api/v1/nfoic-partners/` — read-only

### Communication with MuckRock

`apps/jurisdiction/services/muckrock_client.py` fetches jurisdiction data from a running MuckRock REST API. Set `MUCKROCK_API_URL` (defaults to `http://localhost:8000`) and `MUCKROCK_API_TOKEN`.

### Django settings layout (`api/config/settings/`)

- `base.py` — shared.
- `local.py` — docker-compose dev (the default).
- `test.py` — test runs (forces all `*_REAL_API_ENABLED=False`).
- `render.py` — production on Render.

`DJANGO_SETTINGS_MODULE` is set per environment (`.envs/.local/.api` for dev, `render.yml` for prod, `pytest.ini` for tests).

## Environment Variables

See top-level `README.md` for the canonical list. The minimum to run with the mock provider:

```
DJANGO_SETTINGS_MODULE=config.settings.local
DJANGO_SECRET_KEY=...
RAG_PROVIDER=mock
MUCKROCK_API_URL=http://localhost:8000
```

Real providers also need `OPENAI_API_KEY` + `OPENAI_REAL_API_ENABLED=true` (or the Gemini equivalents).

## Management Commands (`apps/jurisdiction/management/commands/`)

```bash
docker compose exec api python manage.py test_rag_provider --provider openai     # config check
docker compose exec api python manage.py test_rag_provider --all                  # check all
docker compose exec api python manage.py upload_resources_to_provider --provider openai
docker compose exec api python manage.py gemini_create_store --provider openai
docker compose exec api python manage.py gemini_upload_resource <id> --provider openai
docker compose exec api python manage.py gemini_sync_all --provider openai --state CO
docker compose exec api python manage.py gemini_query "your question" --state CO --provider openai
```

Despite the `gemini_` prefix, all of these accept `--provider` and work with any registered provider.

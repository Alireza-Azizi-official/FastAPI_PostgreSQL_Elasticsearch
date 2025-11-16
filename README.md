# FastAPI + PostgreSQL + Elasticsearch Example

A production-like FastAPI project demonstrating:

- Async SQLAlchemy with PostgreSQL
- Contextmanager-based DB session dependency
- Full CRUD for `Camera` model with soft & hard deletes
- Elasticsearch for fast searching and indexing
- JWT authentication (login, token, get_current_user)
- Routers separated from CRUD logic
- Pydantic schemas in `schemas.py`, ORM models in `models.py`
- Logging with rotating file handler and console
- Templated 404 page linking to `/docs`
- Docker & docker-compose setup (Postgres + Elasticsearch + app)

## Quick start (development)

1. Copy `.env` file from the example and set secrets. Example `.env` keys:
   - `DATABASE_URL`
   - `ELASTICSEARCH_HOST`
   - `ELASTICSEARCH_INDEX`
   - `JWT_SECRET_KEY`
   - `ACCESS_TOKEN_EXPIRE_MINUTES`
   - `LOG_LEVEL`

2. With Docker (recommended):
```bash
docker compose up --build
```
The app will be available at `http://127.0.0.1:8000`. Open `http://127.0.0.1:8000/docs`.

3. Create DB tables (dev only):
POST to `http://127.0.0.1:8000/create-tables` (or run alembic migrations for production).

## Endpoints summary

- `POST /api/token` — get JWT token (form data `username`, `password`)
- `POST /api/users` — register a user
- `GET /api/users/me` — current user
- `POST /api/cameras` — create camera (auth required)
- `GET /api/cameras` — list cameras (auth required) — supports `q` param for search
- `GET /api/cameras/{camera_id}` — get camera by camera_id
- `PUT /api/cameras/{camera_id}` — update camera
- `DELETE /api/cameras/{camera_id}` — soft delete
- `DELETE /api/cameras/{camera_id}/hard` — hard delete (owner or superuser)

## Design notes

- Routers only call `crud.*` functions: separation of concerns (controllers vs persistence).
- `db.get_db` is an `asynccontextmanager` used as a dependency; avoids relying on app startup/shutdown events for sessions.
- Elasticsearch keeps a search index that complements PostgreSQL: ideal for full-text queries and multi-field search.
- Soft delete is modeled with `is_deleted` boolean to avoid accidental data loss. Hard delete removes DB row and ES document.
- Security: use environment variables to keep secrets out of source control.

## PostgreSQL primer (brief)
- PostgreSQL is an ACID-compliant RDBMS. Use `psql` or GUI (pgAdmin) to manage.
- `asyncpg` is a fast Postgres driver used for async SQLAlchemy operations.
- Use migrations (alembic) in production. The `create-tables` endpoint is for quick dev iteration only.

## Next steps (production)
- Setup alembic migrations and CI/CD.
- Secure Elasticsearch and Postgres (do not disable security).
- Add tests (pytest + httpx AsyncClient).
- Add role-based permissions, rate limiting, CORS, and monitoring (Sentry or similar).


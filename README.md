# DealRadar Flask Ingestion Prototype

This project is the Python-side prototype for Assignment 1. Its role is upstream listing ingestion and rule matching for DealRadar, while the final served application backend will be built in Kotlin with Spring Boot.

## Scope

- Register and authenticate users
- Manage alert rules
- Store ingested marketplace listings
- Generate persisted matches when listings satisfy active rules
- Expose a health endpoint for delivery checks

## Tech Stack

- Flask
- Flask-SQLAlchemy
- Flask-Migrate
- Flask-JWT-Extended
- PostgreSQL for local development via Docker
- SQLite in automated tests
- Pytest
- Ruff

## Setup

1. Create a virtual environment.
2. Install dependencies.
3. Copy `.env.example` to `.env`.
4. Start PostgreSQL with Docker Compose.
5. Run migrations.
6. Start the app.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r reqs.txt
cp .env.example .env
docker compose up -d postgres
export $(grep -v '^#' .env | xargs)
flask --app app:app db upgrade
flask --app app:app run
```

## Environment Variables

```env
APP_ENV=development
SECRET_KEY=change-me
JWT_SECRET_KEY=change-me-too
DATABASE_URL=postgresql+psycopg://dealradar:dealradar@localhost:5432/dealradar
```

## Quality Commands

Run linting:

```bash
ruff check .
```

Install git hooks:

```bash
pip install -r reqs.txt
bash scripts/install_commit_msg_hook.sh
```

The commit hook enforces Conventional Commits, for example `feat: add listing ingestion endpoint`.

Run tests:

```bash
pytest
```

## Example Flow

1. Register a user with `POST /auth/register`.
2. Log in with `POST /auth/login`.
3. Create an alert rule with `POST /alert-rules`.
4. Ingest scraped listings with `POST /ingestion/listings`.
5. Review created matches through `GET /matches`.

## API Summary

- `GET /health`
- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/profile`
- `PUT /auth/profile`
- `DELETE /auth/profile`
- `GET /alert-rules`
- `POST /alert-rules`
- `GET /alert-rules/<id>`
- `PUT /alert-rules/<id>`
- `DELETE /alert-rules/<id>`
- `GET /listings`
- `POST /listings`
- `GET /listings/<id>`
- `PUT /listings/<id>`
- `DELETE /listings/<id>`
- `POST /ingestion/listings`
- `GET /matches`
- `POST /matches`
- `GET /matches/<id>`
- `PUT /matches/<id>`
- `DELETE /matches/<id>`

## Notes

- This prototype focuses on the scraping and matching side of DealRadar.
- The Kotlin/Spring Boot backend remains the target served backend for Assignment 2.

# Churn Insight — Backend API

A B2B SaaS backend that ingests churn survey data from Typeform and Delighted, classifies responses with Claude AI, clusters them into themes, and generates ad creative briefs.

The frontend is built separately in Lovable (React) and connects via this REST API.

## Stack

- **FastAPI** — async REST API
- **SQLAlchemy 2.0** — ORM with async-ready session management
- **Alembic** — database migrations
- **Claude (Haiku/Sonnet)** — response classification + brief generation
- **OpenAI** — text embeddings (text-embedding-3-small)
- **HDBSCAN** — density-based clustering of response embeddings
- **spaCy** — PII detection before sending text to LLMs
- **SQLite** (dev) / **PostgreSQL** (prod)

## Quick start

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# 3. Copy and fill in environment variables
cp .env.example .env

# 4. Run migrations
alembic upgrade head

# 5. Start the dev server
uvicorn app.main:app --reload
```

The API will be available at http://localhost:8000.
Interactive docs: http://localhost:8000/docs

## Project layout

```
app/
  api/          Route handlers (one file per domain)
  core/         Config and security utilities
  db/           SQLAlchemy models and session
  integrations/ API clients for Typeform and Delighted
  services/     Core processing pipeline (PII, classify, embed, cluster, brief)
  main.py       FastAPI app entrypoint
data/
  embeddings/   Per-account .npy embedding arrays
tests/          pytest suite
alembic/        Database migration scripts
```

## Environment variables

See `.env.example` for a full list with descriptions.

## Running tests

```bash
pytest tests/ -v
```

FROM python:3.12-slim

WORKDIR /app

# System deps needed to compile hdbscan / scikit-learn C extensions
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy model via pip wheel — avoids the spacy CLI / typer version conflict
RUN pip install --no-cache-dir \
    https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl

# Copy application code
COPY . .

# Create data directories (embeddings are ephemeral in Railway — use object storage in prod)
RUN mkdir -p data/embeddings

EXPOSE 8000

# Run migrations then start the server.
# $PORT is injected by Railway; fall back to 8000 for local docker run.
CMD alembic upgrade head && python -c "import sys; exec(open('/app/startup_test.py').read())" && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}

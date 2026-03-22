FROM python:3.12-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1

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

# Generate start.sh directly to guarantee Unix line endings regardless of the host OS
RUN printf '#!/bin/bash\necho "=== STARTING ===" >&2\nalembic upgrade head >&2 2>&1 || echo "Migration done" >&2\necho "=== STARTING UVICORN ===" >&2\nexec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --log-level debug 2>&1\n' > /app/start.sh && chmod +x /app/start.sh

EXPOSE 8000

CMD ["./start.sh"]

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN pip install --no-cache-dir uv && uv sync --frozen
COPY agromet ./agromet
COPY main.py .
RUN mkdir -p /app/data /app/models /app/config
EXPOSE 8000
# Seed demo accounts + synthetic demo dataset (set AGROMET_DEMO_SEED=0 to skip), then start the portal
CMD ["sh", "-c", "uv run python scripts/seed_demo_accounts.py && (uv run python scripts/seed_demo_data.py || echo 'demo data seed failed - continuing without it') && uv run uvicorn agromet.main:app --host 0.0.0.0 --port 8000"]

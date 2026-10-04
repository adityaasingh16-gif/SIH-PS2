FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN pip install --no-cache-dir uv && uv sync --frozen
COPY agromet ./agromet
COPY config ./config
COPY scripts ./scripts
COPY main.py .
RUN mkdir -p /app/data /app/models /app/config
EXPOSE 8000
# Seed demo accounts then start the portal
CMD ["sh", "-c", "uv run python scripts/seed_demo_accounts.py && uv run uvicorn agromet.main:app --host 0.0.0.0 --port 8000"]

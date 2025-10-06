FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml README.md LICENSE /app/
COPY src /app/src

RUN python -m pip install --upgrade pip && \
    python -m pip install -e .

EXPOSE 8000
CMD ["python", "-m", "persona_by_text.webapp"]

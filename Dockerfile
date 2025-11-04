FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_VERSION=1.8.3 \
    APP_HOME=/app

WORKDIR $APP_HOME

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libssl-dev \
    libffi-dev \
    curl \
    git \
    rustc \
    cargo \
  && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir "poetry==${POETRY_VERSION}"

COPY pyproject.toml $APP_HOME/

RUN poetry lock --no-interaction

RUN poetry install --no-interaction --no-ansi --no-root

COPY . $APP_HOME/

CMD sh -c "alembic upgrade head && uvicorn ${APP_MODULE:-main:app} --host 0.0.0.0 --port ${PORT:-8000}"
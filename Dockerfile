FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    NODE_VERSION=22.x \
    DEBIAN_FRONTEND=noninteractive \
    TZ=Europe/Lisbon

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    gnupg \
    bash \
    netcat-traditional \
    && curl -fsSL https://deb.nodesource.com/setup_${NODE_VERSION} | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN python -m pip install --no-cache-dir uv==0.6.14

RUN useradd --create-home --shell /bin/bash appuser && \
    mkdir -p /app/media /app/static /app/frontend /app/bot_data && \
    chown -R appuser:appuser /app

COPY requirements.txt .
RUN uv pip install --system -r requirements.txt

COPY frontend/package*.json ./frontend/
WORKDIR /app/frontend
RUN npm ci

WORKDIR /app
COPY . .

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh && sed -i 's/\r$//g' /entrypoint.sh && chown appuser:appuser /entrypoint.sh

USER appuser
ENTRYPOINT ["/entrypoint.sh"]

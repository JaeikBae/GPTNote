# syntax=docker/dockerfile:1.7

FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app ./app
COPY README.md ./README.md

# Create storage directory for attachments
RUN mkdir -p /app/app/storage/attachments

EXPOSE 8000

ENV MINDDOCK_PROJECT_NAME="MindDock API" \
    MINDDOCK_API_V1_PREFIX="/api/v1" \
    MINDDOCK_STORAGE_DIR="/app/app/storage" \
    MINDDOCK_SQL_DATABASE_URL="sqlite:////app/app/minddock.db"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

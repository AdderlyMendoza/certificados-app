# ---- Backend: FastAPI + Celery + LibreOffice ----
FROM python:3.13-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Dependencias del sistema:
# - libreoffice: conversión docx -> pdf
# - build-essential / default-libmysqlclient-dev: compilar asyncmy
# - fonts: tipografías para los PDF generados
RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice-writer \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    fonts-dejavu \
    fonts-liberation \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

RUN mkdir -p /app/uploads /app/generated

EXPOSE 8000

# Comando por defecto (la API). El worker Celery sobrescribe este CMD en compose.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

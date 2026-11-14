FROM python:3.12-slim

WORKDIR /app

# Install system dependencies including PROJ and GDAL
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libproj-dev \
    proj-bin \
    gdal-bin \
    libgdal-dev \
    python3-gdal \
    && rm -rf /var/lib/apt/lists/*

# Set up non-root user for Hugging Face Spaces / cloud environments (UID 1000)
RUN useradd -m -u 1000 user && \
    mkdir -p /app && \
    chown -R user:user /app

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

COPY src/ /app/src/
COPY README.md /app/

RUN chown -R 1000:1000 /app
USER 1000

ENV PYTHONPATH=/app/src:/usr/lib/python3/dist-packages
ENV PORT=10000
EXPOSE 10000 7860 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:${PORT:-10000}/api/v1/health/liveness || exit 1

CMD ["sh", "-c", "uvicorn zuhura.api.main:app --host 0.0.0.0 --port ${PORT:-10000}"]

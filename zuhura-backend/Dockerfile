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

COPY pyproject.toml README.md ./
COPY src/ /app/src/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

ENV PYTHONPATH=/app/src:/usr/lib/python3/dist-packages
ENV PORT=10000
ENV TILES_CACHE_DIR=/tmp/tiles
EXPOSE 10000 7860 8000

CMD ["sh", "-c", "python -m uvicorn zuhura.api.main:app --host 0.0.0.0 --port ${PORT:-10000}"]

# ===== Base image =====
FROM python:3.11-slim

# ---- Environment ----
ENV PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=Asia/Jakarta

WORKDIR /app

# ---- System dependencies ----
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        default-libmysqlclient-dev \
        tzdata && \
    rm -rf /var/lib/apt/lists/*

# ---- Install Python deps ----
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# (Optional) Remove build packages for smaller image
RUN apt-get purge -y build-essential default-libmysqlclient-dev && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

# ---- Copy source code ----
COPY . .

# ---- Create non-root user ----
RUN useradd -m -u 10001 appuser && chown -R appuser:appuser /app
USER appuser

# ---- Expose port ----
EXPOSE 8000

# ---- Run with Gunicorn + Uvicorn workers ----
# (multi-worker, auto graceful, production-safe)
ENV GUNICORN_WORKERS=2
CMD ["bash", "-lc", "gunicorn app.main:app -k uvicorn.workers.UvicornWorker --workers ${GUNICORN_WORKERS} --bind 0.0.0.0:8000 --timeout 120 --keep-alive 5"]

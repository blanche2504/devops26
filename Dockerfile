# v4 produzione: multi-stage, non-root, gunicorn, healthcheck, versione
# ---- Stage 1: builder ----
FROM python:3.12-slim AS builder
RUN python -m venv /venv
ENV PATH="/venv/bin:$PATH"
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---- Stage 2: runtime ----
FROM python:3.12-slim
ARG APP_VERSION=dev
ENV APP_VERSION=${APP_VERSION} \
    PATH="/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

RUN useradd --create-home app
WORKDIR /app
COPY --from=builder /venv /venv
COPY app.py .
USER app

EXPOSE 8080

# Nella slim non c'è curl: l'healthcheck è scritto in Python
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health', timeout=2)"

# gunicorn vuole file:variabile -> app:app
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]

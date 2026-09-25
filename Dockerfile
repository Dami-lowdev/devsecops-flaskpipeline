# --- Version v0 (non durcie), conservée pour comparaison ---
# FROM python:3.9
# WORKDIR /app
# COPY requirements.txt .
# RUN pip install -r requirements.txt
# COPY . .
# EXPOSE 5000
# CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]

# --- Étape 1 : installation des dépendances ---
FROM python:3.13-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# --- Étape 2 : image finale, minimale ---
FROM python:3.13-slim
# v1/v2 : RUN useradd --create-home --uid 10001 appuser
# v3 : pip retiré de l'image finale (inutile à l'exécution, embarque msgpack et setuptools vulnérables)
RUN python -m pip uninstall -y pip && useradd --create-home --uid 10001 appuser
WORKDIR /app
RUN mkdir /app/data && chown appuser:appuser /app/data
COPY --from=builder /install /usr/local
COPY app.py .
ENV DB_PATH=/app/data/notes.db
USER 10001
EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]

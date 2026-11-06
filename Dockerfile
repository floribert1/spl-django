# Image Python légère
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SQLITE_PATH=/app/data/db.sqlite3

WORKDIR /app

# 1. Dépendances (mises en cache tant que requirements.txt ne change pas)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2. Code du projet
COPY . .

# 3. Fichiers statiques (CSS de l'admin Django) + dossier de la base SQLite
RUN python manage.py collectstatic --noinput && mkdir -p /app/data

EXPOSE 8000

# 4. Au démarrage : migrations -> données de démo -> serveur web
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py init_demo && exec gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 2"]

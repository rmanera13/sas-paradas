FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
# --preload: o app (e a criação do banco) roda 1 vez antes de abrir os workers
CMD ["sh", "-c", "gunicorn --preload -w 2 -b 0.0.0.0:${PORT:-8000} wsgi:app"]

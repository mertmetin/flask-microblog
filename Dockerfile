FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 FLASK_ENV=production
COPY pyproject.toml README.md ./
COPY microblog ./microblog
RUN pip install --no-cache-dir . && useradd --create-home app && mkdir -p /app/instance && chown app /app/instance
USER app
EXPOSE 8000
# SECRET_KEY must be set at runtime; the SQLite database lives in /app/instance (mount a volume there).
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "microblog:create_app()"]

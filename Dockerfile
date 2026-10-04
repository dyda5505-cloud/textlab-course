FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && useradd --uid 10001 --create-home app     && mkdir /data && chown app:app /data
COPY textlab/ textlab/
USER app
ENV PYTHONUNBUFFERED=1 DATABASE_PATH=/data/jobs.db
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "1", "--access-logfile", "-", "textlab.api:create_app()"]

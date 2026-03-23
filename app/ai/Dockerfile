FROM python:3.11.8-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -s /bin/bash appuser

WORKDIR /app

COPY app/ai/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY app/__init__.py ./app/__init__.py
COPY app/ai ./app/ai
COPY app/com ./app/com

RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8090

CMD ["uvicorn", "app.ai.main:app", "--host", "0.0.0.0", "--port", "8090"]

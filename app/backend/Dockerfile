FROM python:3.11.8-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -s /bin/bash appuser

WORKDIR /app

COPY app/backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY app/__init__.py ./app/__init__.py
COPY app/backend ./app/backend
COPY app/com ./app/com
COPY app/config.py ./app/config.py
COPY app/ai_bridge.py ./app/ai_bridge.py
COPY app/ai ./app/ai   
# 아래는 테스트용 
COPY data ./data 

RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8080

CMD ["uvicorn", "app.backend.main:app", "--host", "0.0.0.0", "--port", "8080"]

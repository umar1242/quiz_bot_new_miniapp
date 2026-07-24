
FROM python:3.12-slim
 
WORKDIR /app
 
# Системные зависимости для asyncpg и pdfminer
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*
 
COPY requirements.txt .
 
# Увеличенные таймауты и автоповтор при обрыве соединения
RUN pip install --no-cache-dir \
    --timeout=120 \
    --retries=10 \
    -r requirements.txt
 
COPY . .
 
CMD ["python", "bot.py"]

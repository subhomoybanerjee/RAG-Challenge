FROM python:3.13-slim

RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*
    
WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip

RUN pip install --no-cache-dir -r requirements.txt

RUN pip install gunicorn

COPY . .

ENV PORT=8080

CMD ["gunicorn", "--bind", ":8080", "--workers", "1", "--threads", "1", "--timeout", "0", "prod_server:app"]
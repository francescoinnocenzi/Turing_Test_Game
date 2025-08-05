FROM python:3.10-slim

WORKDIR /app

COPY backend/requirements.txt .

RUN apt-get update && apt-get install -y libmariadb-dev build-essential && apt-get clean

RUN pip install --no-cache-dir -r requirements.txt

COPY backend/src /app

ENV PYTHONPATH=/app

EXPOSE 8003

CMD ["python", "main.py"]

FROM python:3.10-slim

WORKDIR /app

COPY frontend/requirements.txt .

RUN apt-get update && apt-get install -y libmariadb-dev build-essential && apt-get clean

RUN pip install --no-cache-dir -r requirements.txt

COPY frontend/src /app
COPY frontend/src/templates /app/templates
COPY frontend/src/static /app/static

ENV PYTHONPATH=/app

EXPOSE 8001

CMD [ "python", "main.py"]

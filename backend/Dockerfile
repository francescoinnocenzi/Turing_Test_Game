FROM python:3.10-slim

WORKDIR /app

COPY backend/requirements.txt .

RUN apt-get update && apt-get install -y libmariadb-dev build-essential && apt-get clean

RUN pip install --no-cache-dir -r requirements.txt

# 🔽 Pre-carica il modello (così è disponibile subito al runtime)
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('nickprock/sentence-bert-base-italian-uncased')"


COPY backend/src /app

ENV PYTHONPATH=/app

EXPOSE 8003

CMD ["python", "main.py"]

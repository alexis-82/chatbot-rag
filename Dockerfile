FROM python:3.11-slim

WORKDIR /app

# Dipendenze di sistema minime (per PDF parsing)
RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Copia requirements e installa
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-scarica il modello di embedding durante la build
# (evita il download di 500MB al primo run in produzione)
ENV HF_HOME=/app/.cache/huggingface
RUN python -c "from sentence_transformers import SentenceTransformer; \
    SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')"

# Copia il codice applicativo
COPY . .

# Crea cartelle persistenti (saranno montate come volume)
RUN mkdir -p /app/documents /app/index

# Utente non-root per sicurezza
RUN useradd -m -u 1000 chatbot && \
    chown -R chatbot:chatbot /app
USER chatbot

EXPOSE 7860

# Healthcheck sulla UI Gradio
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:7860')" || exit 1

CMD ["python", "app.py"]
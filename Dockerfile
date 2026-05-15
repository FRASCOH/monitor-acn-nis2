# Usa un'immagine base leggera di Python
FROM python:3.10-slim

# Imposta la directory di lavoro nel container
WORKDIR /app

# Installa le dipendenze di sistema necessarie (opzionale, ma utile per alcune librerie)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copia il file delle dipendenze
COPY requirements.txt .

# Installa le dipendenze Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia il resto del codice nel container
COPY . .

# Crea la directory archive se non esiste
RUN mkdir -p archive

# Comando di default per eseguire lo script
CMD ["python", "monitor_acn.py"]

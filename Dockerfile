# Dockerfile
FROM python:3.11-slim

# Evitar prompts e acelerar install
ENV PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    PATH="/root/.local/bin:${PATH}"

WORKDIR /app

# Dependências do sistema (ajuste se precisar de snmp, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl netcat-openbsd ca-certificates gcc build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copia somente requirements primeiro (cache de layer)
COPY requirements.txt ./
RUN pip install -r requirements.txt

# Copia código
COPY . .

# Pasta de dados persistente
RUN mkdir -p /app/data

# Expor a porta interna do Streamlit
EXPOSE 8501

# Healthcheck simples (opcional)
HEALTHCHECK --interval=30s --timeout=5s --retries=5 CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Inicia o Streamlit ouvindo na 8501
CMD ["streamlit", "run", "app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]

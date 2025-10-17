FROM python:3.11-slim

ENV PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    PATH="/root/.local/bin:${PATH}"

WORKDIR /app

# Dependências do sistema (ajuste se seu app precisar de libs extras)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates gcc build-essential netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Instala libs Python
COPY requirements.txt ./
RUN pip install -r requirements.txt

# Código do app
COPY . .

# Pasta de dados persistente (volume)
RUN mkdir -p /app/data

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --retries=5 CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Sobe o Streamlit ouvindo na 8501
CMD ["streamlit", "run", "app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]

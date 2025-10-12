# ===== Base Python slim =====
FROM python:3.12-slim

# Evita .pyc e buffer em logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Pacotes do sistema (compilers só se necessários)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ===== Cache de dependências =====
# Se usar requirements.txt
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt || true

# Se usar Poetry/pyproject, descomente o bloco abaixo e ajuste seu projeto:
# COPY pyproject.toml poetry.lock* /app/
# RUN pip install --no-cache-dir poetry && \
#     cd /app && poetry config virtualenvs.create false && \
#     poetry install --no-interaction --no-ansi

# ===== Código =====
COPY . /app

# Usuário não-root
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Porta padrão (pode ser sobrescrita no EasyPanel)
# Streamlit: 8501 | FastAPI: 8000
ENV PORT=8501

# Comando de inicialização flexível:
#   START_CMD="streamlit" -> Dashboard Streamlit (default)
#   START_CMD="api"       -> API FastAPI (uvicorn)
ENV START_CMD=streamlit

# HEALTHCHECK (ajuste o endpoint caso use API)
# HEALTHCHECK --interval=30s --timeout=3s --start-period=20s \
#   CMD curl -f http://localhost:${PORT}/ || exit 1

# Exponha a porta (documental; o mapeamento real é do orquestrador)
EXPOSE 8501
EXPOSE 8000

# ENTRYPOINT escolhe o modo em runtime
CMD ["/bin/bash", "-lc", "\
  if [ \"$START_CMD\" = \"api\" ]; then \
     echo '>> Starting API (uvicorn api:app) on port ' ${PORT:-8000} ';' \
     python -m uvicorn api:app --host 0.0.0.0 --port ${PORT:-8000}; \
  else \
     echo '>> Starting Streamlit (app.py) on port ' ${PORT:-8501} ';' \
     python -m streamlit run app.py --server.port ${PORT:-8501} --server.address 0.0.0.0; \
  fi \
"]

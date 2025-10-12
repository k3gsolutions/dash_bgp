FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# + libcap para setcap
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl libcap2-bin && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt || true
COPY . /app

# DÁ CAPABILITY AO PYTHON PARA BINDAR <1024
RUN setcap 'cap_net_bind_service=+ep' "$(python -c 'import sys; print(sys.executable)')"

# segue não-root
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

ENV START_CMD=streamlit
ENV PORT=80
EXPOSE 80

CMD ["/bin/bash","-lc","\
  if [ \"$START_CMD\" = \"api\" ]; then \
     python -m uvicorn api:app --host 0.0.0.0 --port ${PORT:-8000}; \
  else \
     python -m streamlit run app.py --server.port ${PORT:-8501} --server.address 0.0.0.0; \
  fi \
"]

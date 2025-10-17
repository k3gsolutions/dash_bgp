# core/paths.py
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent  # raiz do repo (onde está app.py)
DB_PATH = BASE_DIR / "dash_bgp.db"                 # /app/dash_bgp.db no container

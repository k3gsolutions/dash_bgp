# core/db.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from .paths import DB_PATH

# sqlite: /// caminho absoluto
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

# check_same_thread=False para uso em apps web/streamlit
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Cria as tabelas se não existirem."""
    from . import models  # garante que as classes estejam importadas
    Base.metadata.create_all(bind=engine)

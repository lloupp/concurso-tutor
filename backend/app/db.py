"""Conexão e sessão SQLAlchemy (SQLite, portátil)."""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DB = os.path.join(BASE_DIR, "data", "concurso.db")
DATABASE_URL = os.environ.get("DATABASE_URL")
DB_PATH = os.environ.get("DB_PATH", DEFAULT_DB)

if DATABASE_URL:
    _url = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
    _url = _url.replace("postgresql://", "postgresql+psycopg://", 1)
    # O pooler do Supabase (Supavisor, modo transaction) não suporta prepared
    # statements nomeados entre conexões reaproveitadas; prepare_threshold=None
    # desliga o auto-prepare do psycopg e evita erro "DuplicatePreparedStatement".
    # Usa QueuePool com conexões reutilizáveis para evitar cold-start lento em
    # cada requisição (NullPool criava conexão nova por request, causando lentidão
    # e race condition no cadastro/login com pooler Supabase).
    engine = create_engine(
        _url, pool_pre_ping=True, pool_size=5, max_overflow=10,
        connect_args={"prepare_threshold": None},
    )
else:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    engine = create_engine(
        f"sqlite:///{DB_PATH}",
        connect_args={"check_same_thread": False},
    )
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

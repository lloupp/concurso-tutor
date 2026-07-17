"""Configuração compartilhada dos testes.

Isola cada execução de pytest em um arquivo SQLite temporário (definindo
DB_PATH antes de importar `app.db`), para nunca tocar em data/concurso.db.
"""
import os
import sys
import tempfile

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

_tmp_dir = tempfile.mkdtemp(prefix="concurso_tutor_test_")
os.environ["DB_PATH"] = os.path.join(_tmp_dir, "test.db")

import pytest
from fastapi.testclient import TestClient

from app.db import SessionLocal, engine, Base
from app import models, auth
from app.main import app


@pytest.fixture(autouse=True)
def _clean_db():
    """Limpa todas as tabelas após cada teste, mantendo o schema."""
    yield
    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def concurso(db):
    c = models.Concurso(nome="Concurso Teste", cargo="Analista", banca="Banca X")
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


@pytest.fixture
def topico(db, concurso):
    t = models.Topico(concurso_id=concurso.id, nome="Tópico Teste")
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


@pytest.fixture
def admin_user(db):
    return auth.criar_usuario(db, "admin_teste", "senha123", "Admin Teste", role="admin")


@pytest.fixture
def aluno_user(db, concurso):
    return auth.criar_usuario(db, "aluno_teste", "senha123", "Aluno Teste",
                               role="aluno", concurso_id=concurso.id)


def _auth_headers(db, user):
    token = auth.criar_sessao(db, user.id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers(db, admin_user):
    return _auth_headers(db, admin_user)


@pytest.fixture
def aluno_headers(db, aluno_user):
    return _auth_headers(db, aluno_user)

"""Testes de app.auth: hashing de senha, sessões e get_current_user."""
from datetime import datetime, timedelta

import pytest
from fastapi import HTTPException

from app import auth, models


# ---------- criar_usuario / verificar_senha ----------

def test_criar_usuario_gera_salt_e_hash_unicos(db):
    u1 = auth.criar_usuario(db, "u1", "senha123")
    u2 = auth.criar_usuario(db, "u2", "senha123")
    assert u1.salt != u2.salt
    assert u1.password_hash != u2.password_hash  # mesma senha, hashes diferentes (salt distinto)


def test_verificar_senha_correta(db):
    auth.criar_usuario(db, "joao", "correta123")
    u = auth.verificar_senha(db, "joao", "correta123")
    assert u is not None
    assert u.username == "joao"


def test_verificar_senha_incorreta(db):
    auth.criar_usuario(db, "joao", "correta123")
    u = auth.verificar_senha(db, "joao", "errada")
    assert u is None


def test_verificar_senha_usuario_inexistente(db):
    u = auth.verificar_senha(db, "ninguem", "qualquer")
    assert u is None


def test_criar_usuario_define_role_e_concurso(db, concurso):
    u = auth.criar_usuario(db, "aluno1", "senha123", "Aluno Um", "aluno", concurso.id)
    assert u.role == "aluno"
    assert u.concurso_id == concurso.id


# ---------- criar_sessao ----------

def test_criar_sessao_gera_token_valido(db):
    u = auth.criar_usuario(db, "joao", "senha123")
    token = auth.criar_sessao(db, u.id)
    s = db.query(models.Sessao).filter_by(token=token).first()
    assert s is not None
    assert s.user_id == u.id
    assert s.expires_at > datetime.utcnow()


def test_criar_sessao_tokens_diferentes_a_cada_chamada(db):
    u = auth.criar_usuario(db, "joao", "senha123")
    t1 = auth.criar_sessao(db, u.id)
    t2 = auth.criar_sessao(db, u.id)
    assert t1 != t2


# ---------- get_current_user ----------

def test_get_current_user_sem_header_levanta_401(db):
    with pytest.raises(HTTPException) as exc:
        auth.get_current_user(authorization=None, db=db)
    assert exc.value.status_code == 401


def test_get_current_user_header_sem_bearer_levanta_401(db):
    with pytest.raises(HTTPException) as exc:
        auth.get_current_user(authorization="Token abc123", db=db)
    assert exc.value.status_code == 401


def test_get_current_user_token_invalido_levanta_401(db):
    with pytest.raises(HTTPException) as exc:
        auth.get_current_user(authorization="Bearer token-que-nao-existe", db=db)
    assert exc.value.status_code == 401


def test_get_current_user_token_valido_retorna_usuario(db):
    u = auth.criar_usuario(db, "joao", "senha123")
    token = auth.criar_sessao(db, u.id)
    resolved = auth.get_current_user(authorization=f"Bearer {token}", db=db)
    assert resolved.id == u.id


def test_get_current_user_sessao_expirada_levanta_401(db):
    u = auth.criar_usuario(db, "joao", "senha123")
    s = models.Sessao(user_id=u.id, token="token-expirado",
                      expires_at=datetime.utcnow() - timedelta(days=1))
    db.add(s)
    db.commit()
    with pytest.raises(HTTPException) as exc:
        auth.get_current_user(authorization="Bearer token-expirado", db=db)
    assert exc.value.status_code == 401


def test_get_current_user_sessao_sem_expiracao_eh_valida(db):
    """expires_at=None é permitido pelo schema (nullable) e não deve expirar."""
    u = auth.criar_usuario(db, "joao", "senha123")
    s = models.Sessao(user_id=u.id, token="token-sem-validade", expires_at=None)
    db.add(s)
    db.commit()
    resolved = auth.get_current_user(authorization="Bearer token-sem-validade", db=db)
    assert resolved.id == u.id

"""Autenticação simples e portátil (sem dependências externas de hashing)."""
import hashlib
import os
import secrets
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, Header
from sqlalchemy.orm import Session
from .db import get_db
from .models import User, Sessao


def _hash(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt.encode(), 100_000
    ).hex()


def criar_usuario(db: Session, username: str, password: str,
                  full_name: str = "", role: str = "aluno",
                  concurso_id: int = None) -> User:
    salt = secrets.token_hex(16)
    u = User(
        username=username,
        full_name=full_name,
        salt=salt,
        password_hash=_hash(password, salt),
        role=role,
        concurso_id=concurso_id,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


def verificar_senha(db: Session, username: str, password: str) -> User | None:
    u = db.query(User).filter_by(username=username).first()
    if not u:
        return None
    if _hash(password, u.salt) != u.password_hash:
        return None
    return u


def criar_sessao(db: Session, user_id: int, dias: int = 30) -> str:
    token = secrets.token_hex(32)
    exp = datetime.utcnow() + timedelta(days=dias)
    s = Sessao(user_id=user_id, token=token, expires_at=exp)
    db.add(s)
    db.commit()
    return token


def get_current_user(authorization: str = Header(None),
                     db: Session = Depends(get_db)) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Token ausente")
    token = authorization.split(" ", 1)[1]
    s = db.query(Sessao).filter_by(token=token).first()
    if not s:
        raise HTTPException(401, "Token inválido")
    if s.expires_at and s.expires_at < datetime.utcnow():
        raise HTTPException(401, "Sessão expirada")
    u = db.query(User).filter_by(id=s.user_id).first()
    if not u:
        raise HTTPException(401, "Usuário não encontrado")
    return u

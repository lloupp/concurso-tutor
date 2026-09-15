"""Entrypoint completo da aplicação, incluindo integrações administrativas."""
from __future__ import annotations

import hashlib
import hmac

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from .main import app
from .db import get_db
from . import models
from .quest_api_routes import router as quest_api_router, importar_questoes


app.include_router(quest_api_router)

# Endpoint temporário e de uso único para a primeira carga controlada da Quest API.
# A chave em texto puro nunca é armazenada no repositório; apenas seu SHA-256.
_BOOTSTRAP_HASH = "bc5a55e6db18895a2f75c0738d157f74c25c343cb4968d21f916e98051dcd979"


@app.get("/api/internal/quest-bootstrap-rs-20260915", include_in_schema=False)
def quest_bootstrap_rs_20260915(key: str, db: Session = Depends(get_db)):
    recebido = hashlib.sha256((key or "").encode()).hexdigest()
    if not hmac.compare_digest(recebido, _BOOTSTRAP_HASH):
        raise HTTPException(404, "Não encontrado")

    existente = (
        db.query(models.Questao)
        .join(models.Fonte, models.Fonte.id == models.Questao.fonte_id)
        .join(models.Bloco, models.Bloco.id == models.Questao.bloco_id)
        .filter(models.Fonte.tipo == "quest_api", models.Bloco.concurso_id == 52)
        .first()
    )
    if existente:
        return {"status": "already_done"}

    admin = db.query(models.User).filter_by(role="admin").order_by(models.User.id).first()
    if not admin:
        raise HTTPException(503, "Admin indisponível")

    resultado = importar_questoes(
        concurso_id=52,
        topico_id=38,
        limite=5,
        cargo="Técnico em Enfermagem",
        uf="RS",
        assunto="SUS",
        db=db,
        u=admin,
    )
    return {"status": "ok", **resultado}


__all__ = ["app"]

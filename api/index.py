"""Entry point for Vercel Python Functions."""
import hashlib
import hmac

from fastapi import Depends, HTTPException

from backend.app.main import app
from backend.app.db import get_db
from backend.app import models
from backend.app.quest_api_routes import router as quest_api_router, importar_questoes

# main.py monta o frontend estático em "/" por último. Para registrar novas
# rotas depois da importação sem deixá-las atrás desse catch-all, removemos o
# mount, incluímos as rotas e recolocamos o frontend no fim.
_front_routes = [route for route in app.router.routes if getattr(route, "name", None) == "front"]
if _front_routes:
    app.router.routes = [route for route in app.router.routes if route not in _front_routes]
app.include_router(quest_api_router)

# Gatilho temporário e de uso único para a primeira carga controlada da Quest API.
# Apenas o SHA-256 da chave está no repositório; o texto puro não é persistido.
_BOOTSTRAP_HASH = "bc5a55e6db18895a2f75c0738d157f74c25c343cb4968d21f916e98051dcd979"


@app.get("/api/internal/quest-bootstrap-rs-20260915", include_in_schema=False)
def quest_bootstrap_rs_20260915(key: str, db=Depends(get_db)):
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


app.router.routes.extend(_front_routes)

__all__ = ["app"]

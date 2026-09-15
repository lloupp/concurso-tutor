"""Entry point for Vercel Python Functions."""
import hashlib
import hmac
import os

import httpx
from fastapi import Depends, HTTPException

from backend.app.main import app
from backend.app.db import get_db
from backend.app import models
from backend.app.quest_api_routes import router as quest_api_router, importar_questoes

_front_routes = [route for route in app.router.routes if getattr(route, "name", None) == "front"]
if _front_routes:
    app.router.routes = [route for route in app.router.routes if route not in _front_routes]
app.include_router(quest_api_router)

_BOOTSTRAP_HASH = "bc5a55e6db18895a2f75c0738d157f74c25c343cb4968d21f916e98051dcd979"


def _validar_bootstrap(key: str):
    recebido = hashlib.sha256((key or "").encode()).hexdigest()
    if not hmac.compare_digest(recebido, _BOOTSTRAP_HASH):
        raise HTTPException(404, "Não encontrado")


def _resumo_resposta(response: httpx.Response):
    try:
        body = response.json()
        resumo = {
            "status": response.status_code,
            "message": body.get("message") if isinstance(body, dict) else None,
            "error": body.get("error") if isinstance(body, dict) else None,
            "correlation_id": body.get("correlationId") if isinstance(body, dict) else None,
            "path": body.get("path") if isinstance(body, dict) else None,
            "tem_data": isinstance(body, dict) and "data" in body,
        }
        if response.status_code < 400 and isinstance(body, dict):
            data = body.get("data")
            if isinstance(data, dict):
                resumo["data_keys"] = list(data.keys())[:20]
                items = data.get("items") or []
                if items and isinstance(items[0], dict):
                    resumo["item_keys"] = list(items[0].keys())[:30]
        return resumo
    except ValueError:
        return {"status": response.status_code, "message": response.text[:300]}


def _metadados_items(response: httpx.Response):
    if response.status_code >= 400:
        return {"resumo": _resumo_resposta(response), "items": []}
    try:
        data = response.json().get("data") or {}
        items = data.get("items") or []
    except (ValueError, AttributeError):
        return {"resumo": _resumo_resposta(response), "items": []}
    out = []
    for item in items[:20]:
        prova = item.get("prova") or {}
        classificacao = item.get("classificacao") or {}
        out.append({
            "id": item.get("id"),
            "orgao": prova.get("orgao"),
            "cargo": prova.get("cargo"),
            "ano": prova.get("ano"),
            "banca": prova.get("banca"),
            "prova_keys": list(prova.keys())[:30],
            "materia": classificacao.get("materia"),
            "assunto": classificacao.get("assunto"),
            "classificacao_keys": list(classificacao.keys())[:20],
            "anulada": item.get("anulada"),
            "desatualizada": item.get("desatualizada"),
            "n_alternativas": len(item.get("alternativas") or []),
            "tem_gabarito": bool(item.get("gabarito")),
        })
    return {"resumo": _resumo_resposta(response), "total": data.get("total"), "items": out}


@app.get("/api/internal/quest-diagnose-rs-20260915", include_in_schema=False)
def quest_diagnose_rs_20260915(key: str):
    _validar_bootstrap(key)
    api_key = os.environ.get("QUEST_API_KEY", "").strip()
    if not api_key:
        return {"key_configurada": False}
    base = os.environ.get("QUEST_API_BASE_URL", "https://api.quest.api.br").rstrip("/")
    headers = {"X-API-Key": api_key, "Accept": "application/json"}
    try:
        with httpx.Client(timeout=15.0) as client:
            v1 = client.get(f"{base}/v1/questoes", params={"per_page": 1}, headers=headers)
            v1_poa = client.get(
                f"{base}/v1/questoes",
                params={
                    "per_page": 20,
                    "cargo": "Técnico em Enfermagem",
                    "orgao": "Porto Alegre",
                    "tem_gabarito": "true",
                    "include_gabarito": "true",
                },
                headers=headers,
            )
            minimo = client.get(f"{base}/v2/questoes", params={"per_page": 1}, headers=headers)
    except httpx.RequestError as exc:
        return {"key_configurada": True, "erro_rede": type(exc).__name__}
    return {
        "key_configurada": True,
        "base_padrao": base == "https://api.quest.api.br",
        "v1": _resumo_resposta(v1),
        "v1_porto_alegre": _metadados_items(v1_poa),
        "v2": _resumo_resposta(minimo),
    }


@app.get("/api/internal/quest-bootstrap-rs-20260915", include_in_schema=False)
def quest_bootstrap_rs_20260915(key: str, db=Depends(get_db)):
    _validar_bootstrap(key)
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

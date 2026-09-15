"""Rotas administrativas para importar questões reais da Quest API."""
from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from . import auth, models, quest_api
from .db import get_db

router = APIRouter(prefix="/api/admin/quest", tags=["admin-quest"])


def _texto_filtro(valor: Optional[str]) -> Optional[str]:
    valor = (valor or "").strip()
    return valor or None


@router.post("/importar")
def importar_questoes(
    concurso_id: int,
    topico_id: int,
    limite: int = 20,
    banca: Optional[str] = None,
    ano: Optional[str] = None,
    materia: Optional[str] = None,
    assunto: Optional[str] = None,
    orgao: Optional[str] = None,
    cargo: Optional[str] = None,
    nivel_escolaridade: Optional[str] = None,
    uf: Optional[str] = None,
    esfera: Optional[str] = None,
    alternative_type: Optional[str] = None,
    after_id: Optional[str] = None,
    db: Session = Depends(get_db),
    u: models.User = Depends(auth.get_current_user),
):
    """Busca, valida, deduplica e persiste questões da Quest API.

    A chamada nunca adapta enunciado ou alternativas. Itens que a interface
    ainda não reproduz fielmente, como questões com anexos/imagens, são
    rejeitados em vez de publicados parcialmente.
    """
    if u.role != "admin":
        raise HTTPException(403, "Apenas admin")
    if limite < 1 or limite > 100:
        raise HTTPException(422, "limite deve estar entre 1 e 100")

    concurso = db.query(models.Concurso).filter_by(id=concurso_id).first()
    if not concurso:
        raise HTTPException(404, "Perfil não encontrado")
    topico = db.query(models.Topico).filter_by(id=topico_id).first()
    if not topico or topico.concurso_id != concurso_id:
        raise HTTPException(400, "Tópico não pertence ao perfil informado")

    cargo_consulta = _texto_filtro(cargo) or _texto_filtro(concurso.cargo)
    filtros = {
        "banca": _texto_filtro(banca),
        "ano": _texto_filtro(ano),
        "materia": _texto_filtro(materia),
        "assunto": _texto_filtro(assunto),
        "orgao": _texto_filtro(orgao),
        "cargo": cargo_consulta,
        "nivel_escolaridade": _texto_filtro(nivel_escolaridade),
        "uf": _texto_filtro(uf),
        "esfera": _texto_filtro(esfera),
        "alternative_type": _texto_filtro(alternative_type),
        "after_id": _texto_filtro(after_id),
        "per_page": limite,
    }

    try:
        resultado = quest_api.buscar_questoes(filtros)
    except quest_api.QuestApiError as exc:
        raise HTTPException(exc.status_code, str(exc)) from exc

    api_version = resultado.get("api_version") if resultado.get("api_version") in {"v1", "v2"} else "v2"
    bloco = None
    importadas = 0
    duplicadas = 0
    rejeitadas = []

    for item in resultado["items"]:
        quest_id = str(item.get("id") or "").strip()
        urls_questao = [
            f"https://api.quest.api.br/v1/questoes/{quest_id}",
            f"https://api.quest.api.br/v2/questoes/{quest_id}",
        ] if quest_id else []
        source_url = f"https://api.quest.api.br/{api_version}/questoes/{quest_id}" if quest_id else ""

        if urls_questao:
            fonte_existente = db.query(models.Fonte).filter(models.Fonte.url.in_(urls_questao)).first()
            if fonte_existente and db.query(models.Questao).filter_by(fonte_id=fonte_existente.id).first():
                duplicadas += 1
                continue

        try:
            normalizada = quest_api.normalizar_questao(item)
        except ValueError as exc:
            rejeitadas.append({"id": quest_id or None, "motivo": str(exc)})
            continue

        if bloco is None:
            bloco = models.Bloco(
                concurso_id=concurso_id,
                data=date.today(),
                titulo="Banco de questões reais · Quest API",
                introducao="Questões reais importadas da Quest API e armazenadas localmente.",
                duracao_min=60,
                criado_por="quest_api",
                status="banco",
            )
            db.add(bloco)
            db.flush()

        fonte = db.query(models.Fonte).filter(models.Fonte.url.in_(urls_questao)).first() if urls_questao else None
        if fonte is None:
            fonte = models.Fonte(
                titulo=normalizada["fonte_titulo"] or f"Quest API · {normalizada['quest_api_id']}",
                url=source_url,
                tipo="quest_api",
                orgao=normalizada["fonte_orgao"],
                ano=normalizada["fonte_ano"],
            )
            db.add(fonte)
            db.flush()

        db.add(models.Questao(
            bloco_id=bloco.id,
            topico_id=topico_id,
            tipo=normalizada["tipo"],
            enunciado=normalizada["enunciado"],
            alternativas=normalizada["alternativas"],
            gabarito=normalizada["gabarito"],
            explicacao=None,
            fonte_id=fonte.id,
            banca_estilo=normalizada["banca_estilo"],
            materia=normalizada["materia"],
            trilha=normalizada["trilha"],
            texto_base=normalizada["texto_base"],
            dificuldade=normalizada["dificuldade"],
        ))
        importadas += 1

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "Conflito ao persistir questões importadas") from exc

    return {
        "consultadas": len(resultado["items"]),
        "total_api": resultado["total"],
        "importadas": importadas,
        "duplicadas": duplicadas,
        "rejeitadas": rejeitadas,
        "next_cursor": resultado["next_cursor"],
        "api_version": api_version,
        "bloco_banco_id": bloco.id if bloco else None,
    }

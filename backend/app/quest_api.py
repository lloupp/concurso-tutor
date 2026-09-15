"""Cliente e normalização da Quest API.

A Quest API é usada somente como fonte de aquisição. O Concurso Tutor persiste
as questões localmente e nunca expõe a API key ao navegador.
"""
from __future__ import annotations

import os
from typing import Any

import httpx

DEFAULT_BASE_URL = "https://api.quest.api.br"


class QuestApiError(RuntimeError):
    """Erro controlado ao consultar a Quest API."""

    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.status_code = status_code


def _api_key() -> str:
    key = os.environ.get("QUEST_API_KEY", "").strip()
    if not key:
        raise QuestApiError("QUEST_API_KEY não configurada no backend", 503)
    return key


def _v2_search_indisponivel(response: httpx.Response) -> bool:
    if response.status_code != 503:
        return False
    try:
        body = response.json()
    except ValueError:
        return False
    return isinstance(body, dict) and body.get("message") == "Search V2 não está configurado."


def _validar_resposta(response: httpx.Response) -> dict[str, Any]:
    if response.status_code == 401:
        raise QuestApiError("Chave da Quest API inválida ou não autorizada", 502)
    if response.status_code == 402:
        raise QuestApiError("Cota da Quest API esgotada", 503)
    if response.status_code == 403:
        raise QuestApiError("Plano da Quest API sem permissão para este recurso", 503)
    if response.status_code == 429:
        raise QuestApiError("Rate limit da Quest API atingido; tente novamente depois", 503)
    if response.status_code >= 400:
        try:
            body = response.json()
            detalhe = body.get("message") if isinstance(body, dict) else None
        except ValueError:
            detalhe = None
        sufixo = f": {detalhe}" if detalhe else ""
        raise QuestApiError(f"Quest API retornou HTTP {response.status_code}{sufixo}", 502)

    try:
        payload = response.json()
        data = payload.get("data") or {}
        items = data.get("items") or []
    except (ValueError, AttributeError) as exc:
        raise QuestApiError("Resposta inválida da Quest API", 502) from exc
    if not isinstance(items, list):
        raise QuestApiError("Formato inesperado da Quest API", 502)
    return {
        "items": items,
        "total": int(data.get("total") or len(items)),
        "next_cursor": data.get("next_cursor"),
    }


def buscar_questoes(filtros: dict[str, Any] | None = None, *, client: httpx.Client | None = None) -> dict[str, Any]:
    """Consulta o catálogo da Quest API, preferindo V2 e usando V1 como fallback.

    O fallback só ocorre para o erro explícito do fornecedor
    ``Search V2 não está configurado.``. Outros erros continuam falhando de forma
    segura, sem mascarar problemas de chave, cota, plano ou rate limit.
    """
    filtros = dict(filtros or {})
    permitidos = {
        "banca", "ano", "materia", "assunto", "assunto_id", "dificuldade",
        "tipo", "area", "carreira", "nivel_escolaridade", "uf", "esfera",
        "orgao", "cargo", "codigo", "alternative_type", "tem_anexos",
        "after_id", "page", "per_page",
    }
    params = {k: v for k, v in filtros.items() if k in permitidos and v not in (None, "")}
    params.update({
        "tem_gabarito": "true",
        "include_gabarito": "true",
        "anulada": "false",
        "desatualizada": "false",
    })
    params["per_page"] = max(1, min(int(params.get("per_page", 20)), 100))

    base_url = os.environ.get("QUEST_API_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
    headers = {"X-API-Key": _api_key(), "Accept": "application/json"}

    owns_client = client is None
    http = client or httpx.Client(timeout=15.0)
    api_version = "v2"
    try:
        response = http.get(f"{base_url}/v2/questoes", params=params, headers=headers)
        if _v2_search_indisponivel(response):
            api_version = "v1"
            response = http.get(f"{base_url}/v1/questoes", params=params, headers=headers)
        resultado = _validar_resposta(response)
    except httpx.RequestError as exc:
        raise QuestApiError("Falha de comunicação com a Quest API", 502) from exc
    finally:
        if owns_client:
            http.close()

    resultado["api_version"] = api_version
    return resultado


def _tem_imagens(item: dict[str, Any]) -> bool:
    if item.get("anexos"):
        return True
    for alternativa in item.get("alternativas") or []:
        if isinstance(alternativa, dict) and alternativa.get("imagens"):
            return True
    return False


def _dificuldade(valor: Any) -> int:
    try:
        numero = int(valor)
    except (TypeError, ValueError):
        return 2
    return numero if 1 <= numero <= 5 else 2


def normalizar_questao(item: dict[str, Any]) -> dict[str, Any]:
    """Converte uma questão da Quest API sem alterar conteúdo ou alternativas.

    Questões com imagens/anexos são rejeitadas por enquanto, pois a interface
    atual não garante reprodução fiel desses recursos.
    """
    questao_id = str(item.get("id") or "").strip()
    enunciado = str(item.get("enunciado") or "").strip()
    gabarito = str(item.get("gabarito") or "").strip()
    prova = item.get("prova") or {}
    classificacao = item.get("classificacao") or {}
    alternativas_raw = item.get("alternativas") or []

    if not questao_id:
        raise ValueError("questão sem id")
    if not enunciado:
        raise ValueError("questão sem enunciado")
    if not gabarito:
        raise ValueError("questão sem gabarito")
    if _tem_imagens(item):
        raise ValueError("questão possui imagem/anexo ainda não suportado pela interface")
    if not isinstance(alternativas_raw, list) or not alternativas_raw:
        raise ValueError("questão sem alternativas")

    alternative_type = str(prova.get("alternative_type") or "").upper()
    letras = [str((a or {}).get("letra") or "").strip().upper() for a in alternativas_raw]
    textos = [str((a or {}).get("texto") or "").strip() for a in alternativas_raw]
    if any(not texto for texto in textos):
        raise ValueError("alternativa vazia")

    gab = gabarito.upper()
    if alternative_type == "CERTO_ERRADO":
        if gab in {"C", "CERTO", "V", "VERDADEIRO"}:
            tipo = "verdadeiro_falso"
            gabarito_local = "true"
        elif gab in {"E", "ERRADO", "F", "FALSO"}:
            tipo = "verdadeiro_falso"
            gabarito_local = "false"
        else:
            raise ValueError("gabarito certo/errado não reconhecido")
        alternativas = None
    else:
        try:
            indice = letras.index(gab)
        except ValueError as exc:
            raise ValueError("gabarito não corresponde às alternativas") from exc
        tipo = "mcq"
        gabarito_local = str(indice)
        alternativas = textos

    textos_associados = [str(t).strip() for t in item.get("textos_associados") or [] if str(t).strip()]
    prova_id = str(prova.get("id") or "").strip()
    numero = str(item.get("numero") or "").strip()
    banca = str(prova.get("banca") or "").strip()
    orgao = str(prova.get("orgao") or "").strip()
    cargo = str(prova.get("cargo") or "").strip()
    ano = str(prova.get("ano") or "").strip()
    materia = str(classificacao.get("materia") or "").strip()
    assunto = str(classificacao.get("assunto") or "").strip()

    referencia = " · ".join(p for p in [
        "Quest API",
        f"prova {prova_id}" if prova_id else "",
        f"Q{numero}" if numero else "",
        banca, orgao, cargo, ano,
    ] if p)

    return {
        "quest_api_id": questao_id,
        "tipo": tipo,
        "enunciado": enunciado,
        "alternativas": alternativas,
        "gabarito": gabarito_local,
        "banca_estilo": banca or None,
        "materia": materia or None,
        "trilha": assunto or None,
        "texto_base": "\n\n".join(textos_associados) or None,
        "dificuldade": _dificuldade(item.get("dificuldade")),
        "fonte_titulo": referencia[:300],
        "fonte_orgao": orgao or None,
        "fonte_ano": int(ano) if ano.isdigit() else None,
        "prova_id": prova_id or None,
        "numero": numero or None,
    }

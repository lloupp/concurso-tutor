"""Testes da integração com a Quest API."""
import httpx
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app import models, quest_api
from app.quest_api_routes import router as quest_router


def _item_mcq(questao_id="2500000001"):
    return {
        "id": questao_id,
        "numero": "12",
        "enunciado": "Assinale a alternativa correta.",
        "alternativas": [
            {"letra": "A", "texto": "Alternativa A", "imagens": []},
            {"letra": "B", "texto": "Alternativa B", "imagens": []},
            {"letra": "C", "texto": "Alternativa C", "imagens": []},
            {"letra": "D", "texto": "Alternativa D", "imagens": []},
            {"letra": "E", "texto": "Alternativa E", "imagens": []},
        ],
        "gabarito": "E",
        "prova": {
            "id": "2500000",
            "orgao": "Prefeitura de Porto Alegre",
            "cargo": "Técnico em Enfermagem",
            "ano": "2025",
            "banca": "FUNDATEC",
            "alternative_type": "MULTIPLA_ESCOLHA",
        },
        "classificacao": {"materia": "Enfermagem", "assunto": "SUS"},
        "textos_associados": [],
        "anexos": [],
        "sinalizadores": {"tem_imagem": False, "tem_gabarito": True},
    }


def test_normalizacao_preserva_cinco_alternativas():
    q = quest_api.normalizar_questao(_item_mcq())
    assert q["tipo"] == "mcq"
    assert q["alternativas"] == [
        "Alternativa A", "Alternativa B", "Alternativa C", "Alternativa D", "Alternativa E"
    ]
    assert q["gabarito"] == "4"


def test_normalizacao_certo_errado():
    item = _item_mcq()
    item["prova"]["alternative_type"] = "CERTO_ERRADO"
    item["alternativas"] = [
        {"letra": "C", "texto": "Certo", "imagens": []},
        {"letra": "E", "texto": "Errado", "imagens": []},
    ]
    item["gabarito"] = "C"
    q = quest_api.normalizar_questao(item)
    assert q["tipo"] == "verdadeiro_falso"
    assert q["gabarito"] == "true"
    assert q["alternativas"] is None


def test_normalizacao_rejeita_imagem():
    item = _item_mcq()
    item["anexos"] = [{"url": "https://example.invalid/figura.png"}]
    try:
        quest_api.normalizar_questao(item)
    except ValueError as exc:
        assert "imagem/anexo" in str(exc)
    else:
        raise AssertionError("questão com imagem deveria ser rejeitada")


def test_cliente_envia_chave_e_gabarito(monkeypatch):
    monkeypatch.setenv("QUEST_API_KEY", "qk_teste")
    monkeypatch.setenv("QUEST_API_BASE_URL", "https://api.quest.test")

    def responder(request: httpx.Request):
        assert request.headers["X-API-Key"] == "qk_teste"
        assert request.url.params["include_gabarito"] == "true"
        assert request.url.params["tem_gabarito"] == "true"
        assert request.url.params["anulada"] == "false"
        assert request.url.params["cargo"] == "Técnico em Enfermagem"
        return httpx.Response(
            200,
            request=request,
            json={"data": {"total": 1, "next_cursor": "abc", "items": [_item_mcq()]}},
        )

    client = httpx.Client(transport=httpx.MockTransport(responder))
    try:
        out = quest_api.buscar_questoes({"cargo": "Técnico em Enfermagem", "per_page": 20}, client=client)
    finally:
        client.close()
    assert out["total"] == 1
    assert out["next_cursor"] == "abc"
    assert len(out["items"]) == 1


def test_importacao_admin_persiste_e_deduplica(monkeypatch, db, concurso, topico, admin_headers):
    monkeypatch.setattr(
        quest_api,
        "buscar_questoes",
        lambda filtros: {"items": [_item_mcq()], "total": 1, "next_cursor": None},
    )
    test_app = FastAPI()
    test_app.include_router(quest_router)
    client = TestClient(test_app)

    params = {
        "concurso_id": concurso.id,
        "topico_id": topico.id,
        "limite": 20,
        "cargo": "Técnico em Enfermagem",
        "uf": "RS",
    }
    r = client.post("/api/admin/quest/importar", params=params, headers=admin_headers)
    assert r.status_code == 200, r.text
    assert r.json()["importadas"] == 1
    assert r.json()["duplicadas"] == 0

    questao = db.query(models.Questao).one()
    assert questao.alternativas == [
        "Alternativa A", "Alternativa B", "Alternativa C", "Alternativa D", "Alternativa E"
    ]
    assert questao.gabarito == "4"
    assert questao.banca_estilo == "FUNDATEC"
    assert questao.fonte_id is not None
    fonte = db.query(models.Fonte).filter_by(id=questao.fonte_id).one()
    assert fonte.tipo == "quest_api"
    assert "prova 2500000" in fonte.titulo
    assert fonte.url.endswith("/v2/questoes/2500000001")

    r2 = client.post("/api/admin/quest/importar", params=params, headers=admin_headers)
    assert r2.status_code == 200, r2.text
    assert r2.json()["importadas"] == 0
    assert r2.json()["duplicadas"] == 1
    assert db.query(models.Questao).count() == 1

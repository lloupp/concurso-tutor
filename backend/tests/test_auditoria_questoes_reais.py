"""Regressão da auditoria de questões reais (AUDITORIA_QUESTOES_REAIS.md).

Estes testes existem para NUNCA MAIS deixar: (a) uma questão sem origem
comprovada ser servida como 'valida'; (b) conteúdo estático sem fonte
voltar a aparecer nos JSONs do simulado; (c) os prompts/skills voltarem a
instruir geração/formulação de questões por IA.
"""
import glob
import json
import os

import pytest
from sqlalchemy.exc import IntegrityError

from app import models

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

METADADOS_COMPROVACAO = dict(
    banca="Cebraspe", orgao="Órgão Teste", concurso_prova="Concurso Teste 2024",
    cargo="Analista", ano_prova=2024, prova="Caderno 1", numero_questao="12",
    url_prova="https://exemplo.org/prova.pdf", gabarito_oficial="1",
)


# ---------- bloqueio técnico no schema (SQLite local) ----------

def test_questao_valida_sem_metadados_e_rejeitada_pelo_banco(db, topico):
    bloco = models.Bloco(concurso_id=topico.concurso_id, titulo="B")
    db.add(bloco); db.commit(); db.refresh(bloco)
    q = models.Questao(bloco_id=bloco.id, topico_id=topico.id, tipo="mcq",
                       enunciado="?", alternativas=["a", "b"], gabarito="0",
                       situacao="valida", origem_verificada=True,
                       classificacao_auditoria="VERIFICADA_REAL")
    # metadados de comprovação (banca, orgao, ...) ausentes de propósito
    db.add(q)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


def test_questao_valida_sem_origem_verificada_e_rejeitada_mesmo_com_resto_completo(db, topico):
    bloco = models.Bloco(concurso_id=topico.concurso_id, titulo="B")
    db.add(bloco); db.commit(); db.refresh(bloco)
    q = models.Questao(bloco_id=bloco.id, topico_id=topico.id, tipo="mcq",
                       enunciado="?", alternativas=["a", "b"], gabarito="0",
                       situacao="valida", origem_verificada=False,  # <- o ponto crítico
                       classificacao_auditoria="VERIFICADA_REAL", **METADADOS_COMPROVACAO)
    db.add(q)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


def test_questao_valida_com_comprovacao_completa_e_aceita(db, topico):
    bloco = models.Bloco(concurso_id=topico.concurso_id, titulo="B")
    db.add(bloco); db.commit(); db.refresh(bloco)
    q = models.Questao(bloco_id=bloco.id, topico_id=topico.id, tipo="mcq",
                       enunciado="?", alternativas=["a", "b"], gabarito="0",
                       situacao="valida", origem_verificada=True,
                       classificacao_auditoria="VERIFICADA_REAL", **METADADOS_COMPROVACAO)
    db.add(q)
    db.commit()  # não deve levantar
    assert q.id is not None


def test_questao_nova_fica_em_quarentena_por_padrao(db, topico):
    bloco = models.Bloco(concurso_id=topico.concurso_id, titulo="B")
    db.add(bloco); db.commit(); db.refresh(bloco)
    q = models.Questao(bloco_id=bloco.id, topico_id=topico.id, tipo="mcq",
                       enunciado="?", alternativas=["a", "b"], gabarito="0")
    db.add(q); db.commit()
    assert q.situacao == "quarentena"
    assert q.origem_verificada is False


# ---------- bloqueio na API (/bloco/gerar e /bloco/hoje) ----------

def test_gerar_bloco_rejeita_questao_valida_sem_comprovacao(client, admin_headers, concurso, topico):
    payload = {
        "concurso_id": concurso.id,
        "bloco": {"titulo": "B", "questoes": [
            {"topico_id": topico.id, "tipo": "mcq", "enunciado": "?",
             "alternativas": ["a", "b"], "gabarito": "0",
             "situacao": "valida", "origem_verificada": True,
             "classificacao_auditoria": "VERIFICADA_REAL"},
        ]},
    }
    resp = client.post("/api/bloco/gerar", headers=admin_headers, json=payload)
    assert resp.status_code == 400


def test_gerar_bloco_aceita_questao_valida_com_comprovacao_completa(client, admin_headers, concurso, topico):
    payload = {
        "concurso_id": concurso.id,
        "bloco": {"titulo": "B", "questoes": [
            {"topico_id": topico.id, "tipo": "mcq", "enunciado": "?",
             "alternativas": ["a", "b"], "gabarito": "0",
             "situacao": "valida", "origem_verificada": True,
             "classificacao_auditoria": "VERIFICADA_REAL", **METADADOS_COMPROVACAO},
        ]},
    }
    resp = client.post("/api/bloco/gerar", headers=admin_headers, json=payload)
    assert resp.status_code == 200


def test_bloco_hoje_so_expoe_questoes_verificadas_e_validas(client, db, aluno_headers, aluno_user, topico):
    from datetime import date
    bloco = models.Bloco(concurso_id=aluno_user.concurso_id, titulo="B", data=date.today())
    db.add(bloco); db.commit(); db.refresh(bloco)
    valida = models.Questao(bloco_id=bloco.id, topico_id=topico.id, tipo="mcq",
                            enunciado="Real", alternativas=["a", "b"], gabarito="0",
                            situacao="valida", origem_verificada=True,
                            classificacao_auditoria="VERIFICADA_REAL", **METADADOS_COMPROVACAO)
    quarentena = models.Questao(bloco_id=bloco.id, topico_id=topico.id, tipo="mcq",
                                enunciado="Não comprovada", alternativas=["a", "b"], gabarito="0")
    db.add_all([valida, quarentena]); db.commit()

    resp = client.get("/api/bloco/hoje", headers=aluno_headers)
    enunciados = [q["enunciado"] for q in resp.json()["bloco"]["questoes"]]
    assert enunciados == ["Real"]


# ---------- conteúdo estático (simulado GitHub Pages) ----------

def test_docs_data_nao_tem_questao_sem_fonte():
    arquivos = sorted(glob.glob(os.path.join(REPO_ROOT, "docs", "data", "*.json")))
    assert arquivos, "docs/data/*.json não encontrados"
    for caminho in arquivos:
        with open(caminho, encoding="utf-8") as fh:
            dados = json.load(fh)
        for questao in dados.get("questoes", []):
            assert questao.get("fonte"), (
                f"{caminho}: questão sem 'fonte' (comprovação de prova real) — "
                "NÃO adicione questão sem fonte, ver docs/CONTRIBUINDO.md"
            )


# ---------- prompts/skills não podem voltar a instruir geração por IA ----------

_FRASES_PROIBIDAS_ATIVAS = [
    "formule a questão",
    "crie as questões",
    "gere as questões",
    "invente",
]


def test_skill_tutor_concurso_nao_instrui_formulacao():
    caminho = os.path.join(REPO_ROOT, "skills", "tutor-concurso", "SKILL.md")
    with open(caminho, encoding="utf-8") as fh:
        conteudo = fh.read().lower()
    assert "nunca formula, gera, cria, adapta, parafraseia" in conteudo
    for frase in _FRASES_PROIBIDAS_ATIVAS:
        assert frase not in conteudo, f"SKILL.md voltou a instruir: '{frase}'"


def test_grok_populate_prompt_esta_deprecado():
    caminho = os.path.join(REPO_ROOT, "grok_populate_prompt.md")
    with open(caminho, encoding="utf-8") as fh:
        conteudo = fh.read()
    assert conteudo.startswith("> **DEPRECADO")

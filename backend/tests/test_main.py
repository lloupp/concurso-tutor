"""Testes de integração da API (app.main) via TestClient."""
from datetime import date

import pytest

from app import models


# ---------- login / me ----------

def test_login_sucesso_retorna_token_e_usuario(client, db):
    from app import auth
    auth.criar_usuario(db, "joao", "senha123", "João Silva", "aluno")
    resp = client.post("/api/login", json={"username": "joao", "password": "senha123"})
    assert resp.status_code == 200
    body = resp.json()
    assert "token" in body
    assert body["user"]["username"] == "joao"


def test_login_senha_incorreta_retorna_401(client, db):
    from app import auth
    auth.criar_usuario(db, "joao", "senha123")
    resp = client.post("/api/login", json={"username": "joao", "password": "errada"})
    assert resp.status_code == 401


def test_login_usuario_inexistente_retorna_401(client):
    resp = client.post("/api/login", json={"username": "fantasma", "password": "x"})
    assert resp.status_code == 401


def test_me_sem_token_retorna_401(client):
    resp = client.get("/api/me")
    assert resp.status_code == 401


def test_me_com_token_valido_retorna_dados_do_usuario(client, aluno_headers, aluno_user):
    resp = client.get("/api/me", headers=aluno_headers)
    assert resp.status_code == 200
    assert resp.json()["username"] == aluno_user.username


# ---------- bloco/hoje, blocos ----------

def test_bloco_hoje_aluno_sem_concurso_retorna_400(client, db):
    from app import auth
    u = auth.criar_usuario(db, "sem_concurso", "senha123", role="aluno")
    token = auth.criar_sessao(db, u.id)
    resp = client.get("/api/bloco/hoje", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 400


def test_bloco_hoje_sem_bloco_retorna_none(client, aluno_headers):
    resp = client.get("/api/bloco/hoje", headers=aluno_headers)
    assert resp.status_code == 200
    assert resp.json()["bloco"] is None


def test_bloco_hoje_retorna_bloco_com_questoes(client, db, aluno_headers, aluno_user, topico):
    bloco = models.Bloco(concurso_id=aluno_user.concurso_id, titulo="Bloco 1",
                         introducao="Intro", data=date.today())
    db.add(bloco)
    db.commit()
    db.refresh(bloco)
    q = models.Questao(bloco_id=bloco.id, topico_id=topico.id, tipo="mcq",
                       enunciado="2+2=?", alternativas=["3", "4"], gabarito="1")
    db.add(q)
    db.commit()

    resp = client.get("/api/bloco/hoje", headers=aluno_headers)
    assert resp.status_code == 200
    body = resp.json()["bloco"]
    assert body["titulo"] == "Bloco 1"
    assert len(body["questoes"]) == 1
    # mcq: gabarito exposto, resposta_modelo não
    assert body["questoes"][0]["gabarito"] == "1"
    assert body["questoes"][0]["resposta_modelo"] is None


def test_listar_blocos_retorna_apenas_do_concurso_do_usuario(client, db, aluno_headers, aluno_user, concurso):
    outro_concurso = models.Concurso(nome="Outro", cargo="X", banca="Y")
    db.add(outro_concurso)
    db.commit()
    db.refresh(outro_concurso)

    b1 = models.Bloco(concurso_id=concurso.id, titulo="Meu bloco", data=date.today())
    b2 = models.Bloco(concurso_id=outro_concurso.id, titulo="Bloco de outro concurso", data=date.today())
    db.add_all([b1, b2])
    db.commit()

    resp = client.get("/api/blocos", headers=aluno_headers)
    titulos = [b["titulo"] for b in resp.json()["blocos"]]
    assert "Meu bloco" in titulos
    assert "Bloco de outro concurso" not in titulos


# ---------- bloco/responder ----------

def test_responder_mcq_correta_e_atualiza_progresso(client, db, aluno_headers, aluno_user, topico):
    bloco = models.Bloco(concurso_id=aluno_user.concurso_id, titulo="B", data=date.today())
    db.add(bloco)
    db.commit()
    db.refresh(bloco)
    q = models.Questao(bloco_id=bloco.id, topico_id=topico.id, tipo="mcq",
                       enunciado="?", alternativas=["a", "b"], gabarito="1")
    db.add(q)
    db.commit()
    db.refresh(q)

    resp = client.post("/api/bloco/responder", headers=aluno_headers,
                       json={"respostas": [{"questao_id": q.id, "resposta": "1", "tempo_seg": 30}]})
    assert resp.status_code == 200
    resultado = resp.json()["resultados"][0]
    assert resultado["correta"] is True

    prog = db.query(models.Progresso).filter_by(user_id=aluno_user.id, topico_id=topico.id).first()
    assert prog is not None
    assert prog.tentativas == 1


def test_responder_mcq_incorreta_retorna_feedback_com_gabarito(client, db, aluno_headers, aluno_user, topico):
    bloco = models.Bloco(concurso_id=aluno_user.concurso_id, titulo="B", data=date.today())
    db.add(bloco)
    db.commit()
    db.refresh(bloco)
    q = models.Questao(bloco_id=bloco.id, topico_id=topico.id, tipo="mcq",
                       enunciado="?", alternativas=["a", "b"], gabarito="1")
    db.add(q)
    db.commit()
    db.refresh(q)

    resp = client.post("/api/bloco/responder", headers=aluno_headers,
                       json={"respostas": [{"questao_id": q.id, "resposta": "0"}]})
    resultado = resp.json()["resultados"][0]
    assert resultado["correta"] is False
    assert "Gabarito" in resultado["feedback"]


def test_responder_discursiva_fica_pendente_de_correcao(client, db, aluno_headers, aluno_user, topico):
    bloco = models.Bloco(concurso_id=aluno_user.concurso_id, titulo="B", data=date.today())
    db.add(bloco)
    db.commit()
    db.refresh(bloco)
    q = models.Questao(bloco_id=bloco.id, topico_id=topico.id, tipo="discursiva",
                       enunciado="Disserte...", resposta_modelo="modelo", rubric="critérios")
    db.add(q)
    db.commit()
    db.refresh(q)

    resp = client.post("/api/bloco/responder", headers=aluno_headers,
                       json={"respostas": [{"questao_id": q.id, "resposta": "minha resposta"}]})
    resultado = resp.json()["resultados"][0]
    assert resultado["correta"] is None
    assert resultado["nota"] is None
    assert resultado["feedback"] == "Aguardando correção."

    r = db.query(models.Resposta).filter_by(questao_id=q.id).first()
    assert r.corrigido_por is None


def test_responder_questao_inexistente_eh_ignorada(client, aluno_headers):
    resp = client.post("/api/bloco/responder", headers=aluno_headers,
                       json={"respostas": [{"questao_id": 999999, "resposta": "x"}]})
    assert resp.status_code == 200
    assert resp.json()["resultados"] == []


# ---------- respostas/pendentes & corrigir (admin only) ----------

def test_respostas_pendentes_bloqueado_para_aluno(client, aluno_headers):
    resp = client.get("/api/respostas/pendentes", headers=aluno_headers)
    assert resp.status_code == 403


def test_respostas_pendentes_lista_discursivas_nao_corrigidas(client, db, admin_headers, aluno_user, topico):
    bloco = models.Bloco(concurso_id=aluno_user.concurso_id, titulo="B", data=date.today())
    db.add(bloco)
    db.commit()
    db.refresh(bloco)
    q = models.Questao(bloco_id=bloco.id, topico_id=topico.id, tipo="discursiva",
                       enunciado="Disserte...", resposta_modelo="modelo", rubric="c")
    db.add(q)
    db.commit()
    db.refresh(q)
    r = models.Resposta(questao_id=q.id, user_id=aluno_user.id, resposta="minha resposta")
    db.add(r)
    db.commit()

    resp = client.get("/api/respostas/pendentes", headers=admin_headers)
    assert resp.status_code == 200
    assert len(resp.json()["pendentes"]) == 1


def test_corrigir_discursiva_bloqueado_para_aluno(client, aluno_headers):
    resp = client.post("/api/bloco/responder/corrigir", headers=aluno_headers,
                       params={"resposta_id": 1, "nota": 0.8, "feedback": "ok"})
    assert resp.status_code == 403


def test_corrigir_discursiva_resposta_inexistente_404(client, admin_headers):
    resp = client.post("/api/bloco/responder/corrigir", headers=admin_headers,
                       params={"resposta_id": 999999, "nota": 0.8, "feedback": "ok"})
    assert resp.status_code == 404


def test_corrigir_discursiva_atualiza_nota_e_progresso(client, db, admin_headers, aluno_user, topico):
    bloco = models.Bloco(concurso_id=aluno_user.concurso_id, titulo="B", data=date.today())
    db.add(bloco)
    db.commit()
    db.refresh(bloco)
    q = models.Questao(bloco_id=bloco.id, topico_id=topico.id, tipo="discursiva",
                       enunciado="Disserte...", resposta_modelo="modelo", rubric="c")
    db.add(q)
    db.commit()
    db.refresh(q)
    r = models.Resposta(questao_id=q.id, user_id=aluno_user.id, resposta="minha resposta")
    db.add(r)
    db.commit()
    db.refresh(r)

    resp = client.post("/api/bloco/responder/corrigir", headers=admin_headers,
                       params={"resposta_id": r.id, "nota": 0.75, "feedback": "Bom, mas...", "correta": True})
    assert resp.status_code == 200

    db.refresh(r)
    assert r.nota == 0.75
    assert r.corrigido_por == "hermes"
    prog = db.query(models.Progresso).filter_by(user_id=aluno_user.id, topico_id=topico.id).first()
    assert prog.dominio == pytest.approx(0.75 * 0.3)  # EMA a partir de domínio 0


# ---------- progresso / plano ----------

def test_progresso_aluno_sem_concurso_retorna_400(client, db):
    from app import auth
    u = auth.criar_usuario(db, "sem_concurso2", "senha123", role="aluno")
    token = auth.criar_sessao(db, u.id)
    resp = client.get("/api/progresso", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 400


def test_progresso_retorna_dominancia_e_cobertura(client, aluno_headers, topico):
    resp = client.get("/api/progresso", headers=aluno_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert "dominancia" in body
    assert "cobertura" in body


def test_plano_retorna_proximos_topicos(client, aluno_headers, topico):
    resp = client.get("/api/plano", headers=aluno_headers)
    assert resp.status_code == 200
    assert len(resp.json()["proximos_topicos"]) >= 1


# ---------- bloco/gerar (admin only) ----------

def test_gerar_bloco_bloqueado_para_aluno(client, aluno_headers, concurso):
    resp = client.post("/api/bloco/gerar", headers=aluno_headers,
                       json={"concurso_id": concurso.id, "bloco": {"titulo": "X"}})
    assert resp.status_code == 403


def test_gerar_bloco_corpo_vazio_retorna_400(client, admin_headers, concurso):
    resp = client.post("/api/bloco/gerar", headers=admin_headers,
                       json={"concurso_id": concurso.id})
    assert resp.status_code == 400


def test_gerar_bloco_cria_bloco_questoes_e_marca_cobertura(client, db, admin_headers, concurso, topico):
    payload = {
        "concurso_id": concurso.id,
        "bloco": {
            "titulo": "Bloco gerado",
            "introducao": "Intro",
            "duracao_min": 45,
            "questoes": [
                {"topico_id": topico.id, "tipo": "mcq", "enunciado": "?",
                 "alternativas": ["a", "b"], "gabarito": "0", "dificuldade": 3},
            ],
            "topicos_ids": [topico.id],
        },
    }
    resp = client.post("/api/bloco/gerar", headers=admin_headers, json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["questoes"] == 1

    bloco = db.query(models.Bloco).filter_by(id=body["bloco_id"]).first()
    assert bloco.titulo == "Bloco gerado"
    assert bloco.duracao_min == 45

    db.refresh(topico)
    assert topico.estudado is True


# ---------- admin: concurso / topico / topicos-selecao / alunos / usuario ----------

def test_criar_concurso_bloqueado_para_aluno(client, aluno_headers):
    resp = client.post("/api/admin/concurso", headers=aluno_headers,
                       params={"nome": "X", "cargo": "Y"})
    assert resp.status_code == 403


def test_criar_concurso_admin_ok(client, admin_headers):
    resp = client.post("/api/admin/concurso", headers=admin_headers,
                       params={"nome": "Novo Concurso", "cargo": "Analista"})
    assert resp.status_code == 200
    assert "concurso_id" in resp.json()


def test_criar_topico_admin_ok(client, admin_headers, concurso):
    resp = client.post("/api/admin/topico", headers=admin_headers,
                       params={"concurso_id": concurso.id, "nome": "Novo Tópico"})
    assert resp.status_code == 200
    assert "topico_id" in resp.json()


def test_topicos_selecao_bloqueado_para_aluno(client, aluno_headers, concurso):
    resp = client.get("/api/admin/topicos-selecao", headers=aluno_headers,
                      params={"concurso_id": concurso.id})
    assert resp.status_code == 403


def test_topicos_selecao_admin_ok(client, admin_headers, concurso, topico):
    resp = client.get("/api/admin/topicos-selecao", headers=admin_headers,
                      params={"concurso_id": concurso.id, "n": 1})
    assert resp.status_code == 200
    assert len(resp.json()["topicos"]) == 1


def test_listar_alunos_bloqueado_para_aluno(client, aluno_headers):
    resp = client.get("/api/admin/alunos", headers=aluno_headers)
    assert resp.status_code == 403


def test_listar_alunos_filtra_por_concurso(client, admin_headers, aluno_user, concurso):
    resp = client.get("/api/admin/alunos", headers=admin_headers,
                      params={"concurso_id": concurso.id})
    assert resp.status_code == 200
    usernames = [a["username"] for a in resp.json()["alunos"]]
    assert aluno_user.username in usernames


def test_criar_usuario_bloqueado_para_aluno(client, aluno_headers):
    resp = client.post("/api/admin/usuario", headers=aluno_headers,
                       params={"username": "novo", "password": "senha123"})
    assert resp.status_code == 403


def test_criar_usuario_duplicado_retorna_400(client, admin_headers, aluno_user):
    resp = client.post("/api/admin/usuario", headers=admin_headers,
                       params={"username": aluno_user.username, "password": "senha123"})
    assert resp.status_code == 400


def test_criar_usuario_admin_ok(client, admin_headers):
    resp = client.post("/api/admin/usuario", headers=admin_headers,
                       params={"username": "novo_aluno", "password": "senha123"})
    assert resp.status_code == 200
    assert "user_id" in resp.json()

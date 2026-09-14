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


def test_cadastro_escolhe_trilha_e_tempo(client, db, concurso):
    resp = client.post("/api/cadastro", json={
        "username": "novo_aluno", "password": "senha123",
        "full_name": "Novo Aluno", "concurso_id": concurso.id,
        "tempo_diario": 45,
    })
    assert resp.status_code == 200
    user = db.query(models.User).filter_by(username="novo_aluno").one()
    assert user.concurso_id == concurso.id
    assert user.tempo_diario == 45


def test_dashboard_tem_metricas_individuais(client, aluno_headers, aluno_user, concurso, topico):
    resp = client.get("/api/dashboard", headers=aluno_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["questoes_respondidas"] == 0
    assert body["cobertura"]["estudados"] == 0
    assert body["materias_total"] >= 1


def test_responder_repetido_nao_duplica_progresso(client, db, aluno_headers, aluno_user, topico):
    bloco = models.Bloco(concurso_id=aluno_user.concurso_id, titulo="Idempotência", data=date.today())
    db.add(bloco); db.commit(); db.refresh(bloco)
    q = models.Questao(bloco_id=bloco.id, topico_id=topico.id, tipo="mcq",
                       enunciado="?", alternativas=["a", "b"], gabarito="1", explicacao="Teste")
    db.add(q); db.commit(); db.refresh(q)
    corpo = {"respostas": [{"questao_id": q.id, "resposta": "1"}]}
    assert client.post("/api/bloco/responder", headers=aluno_headers, json=corpo).status_code == 200
    repetida = client.post("/api/bloco/responder", headers=aluno_headers, json=corpo)
    assert repetida.status_code == 200
    assert repetida.json()["resultados"][0]["duplicada"] is True
    assert db.query(models.Resposta).filter_by(user_id=aluno_user.id, questao_id=q.id).count() == 1
    assert db.query(models.Progresso).filter_by(user_id=aluno_user.id, topico_id=topico.id).one().tentativas == 1


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
    # correção 3: o payload do aluno NÃO expõe gabarito/resposta_modelo/rubric
    assert "gabarito" not in body["questoes"][0]
    assert body["questoes"][0]["resposta_modelo"] is None
    assert body["questoes"][0]["rubric"] is None


def test_bloco_banco_nao_e_exibido_inteiro_como_bloco_do_dia(
        client, db, aluno_headers, aluno_user, topico):
    banco = models.Bloco(concurso_id=aluno_user.concurso_id, titulo="Banco editorial",
                         introducao="Acervo", data=date.today(), status="banco")
    db.add(banco)
    db.commit()
    db.add(models.Questao(bloco_id=banco.id, topico_id=topico.id, tipo="mcq",
                          enunciado="Questão do acervo", alternativas=["a", "b"], gabarito="1"))
    db.commit()

    resp = client.get("/api/bloco/hoje", headers=aluno_headers)
    assert resp.status_code == 200
    assert resp.json()["bloco"]["titulo"] == "Próximo bloco adaptativo"
    assert len(resp.json()["bloco"]["questoes"]) == 1

    listagem = client.get("/api/blocos", headers=aluno_headers).json()["blocos"]
    assert all(item["titulo"] != "Banco editorial" for item in listagem)


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


@pytest.mark.parametrize("tipo,gabarito,resposta,correta", [
    ("verdadeiro_falso", "true", "Certo", True),
    ("verdadeiro_falso", "false", "true", False),
    ("numerica", "12.5", "12,50", True),
    ("numerica", "12.5", "12.52", False),
])
def test_responder_tipos_automaticos(client, db, aluno_headers, aluno_user, topico,
                                     tipo, gabarito, resposta, correta):
    bloco = models.Bloco(concurso_id=aluno_user.concurso_id, titulo="Automáticas", data=date.today())
    db.add(bloco)
    db.commit()
    db.refresh(bloco)
    q = models.Questao(bloco_id=bloco.id, topico_id=topico.id, tipo=tipo,
                       enunciado="Questão automática", gabarito=gabarito,
                       explicacao="Explicação didática.", tolerancia=0.01 if tipo == "numerica" else None,
                       unidade="mL" if tipo == "numerica" else None)
    db.add(q)
    db.commit()
    db.refresh(q)

    resp = client.post("/api/bloco/responder", headers=aluno_headers,
                       json={"respostas": [{"questao_id": q.id, "resposta": resposta}]})
    assert resp.status_code == 200
    resultado = resp.json()["resultados"][0]
    assert resultado["correta"] is correta
    assert resultado["explicacao"] == "Explicação didática."
    assert "Resposta correta" in resultado["feedback"] or correta


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


def test_responder_questao_de_outro_concurso_retorna_403(client, db, aluno_headers, aluno_user):
    """Correção 2: aluno não pode responder questão de outro concurso."""
    outro = models.Concurso(nome="Outro", cargo="X", banca="Y")
    db.add(outro); db.commit(); db.refresh(outro)
    top = models.Topico(concurso_id=outro.id, nome="Top")
    db.add(top); db.commit(); db.refresh(top)
    bloco = models.Bloco(concurso_id=outro.id, titulo="B", data=date.today())
    db.add(bloco); db.commit(); db.refresh(bloco)
    q = models.Questao(bloco_id=bloco.id, topico_id=top.id, tipo="mcq",
                       enunciado="?", alternativas=["a", "b"], gabarito="1")
    db.add(q); db.commit(); db.refresh(q)

    resp = client.post("/api/bloco/responder", headers=aluno_headers,
                       json={"respostas": [{"questao_id": q.id, "resposta": "1"}]})
    assert resp.status_code == 403
    assert db.query(models.Resposta).filter_by(questao_id=q.id).count() == 0


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


# ---------- concursos (livre acesso) ----------

def test_concursos_lista_disponiveis_sem_token(client, db, concurso):
    outro = models.Concurso(nome="PF", cargo="Agente", banca="Cebraspe")
    db.add(outro)
    db.commit()
    resp = client.get("/api/concursos")
    assert resp.status_code == 200
    nomes = [c["nome"] for c in resp.json()["concursos"]]
    assert concurso.nome in nomes
    assert "PF" in nomes


def test_bloco_hoje_bloqueia_trilha_diferente(client, db, aluno_headers, aluno_user, concurso):
    """Livro acesso: aluno padrão vê bloco de outro perfil passando concurso_id."""
    outro = models.Concurso(nome="Outro Perfil", cargo="Cargo", banca="B")
    db.add(outro)
    db.commit()
    db.refresh(outro)
    b = models.Bloco(concurso_id=outro.id, titulo="Bloco de outro", data=date.today())
    db.add(b)
    db.commit()
    resp = client.get("/api/bloco/hoje", headers=aluno_headers,
                      params={"concurso_id": outro.id})
    assert resp.status_code == 403


def test_listar_blocos_bloqueia_trilha_diferente(client, db, aluno_headers, aluno_user, concurso):
    outro = models.Concurso(nome="Outro", cargo="X", banca="Y")
    db.add(outro)
    db.commit()
    db.refresh(outro)
    b = models.Bloco(concurso_id=outro.id, titulo="BlocoOutro", data=date.today())
    db.add(b)
    db.commit()
    resp = client.get("/api/blocos", headers=aluno_headers, params={"concurso_id": outro.id})
    assert resp.status_code == 403


def test_responder_bloqueia_trilha_diferente(client, db, aluno_headers, aluno_user, concurso):
    """Com o perfil ativo certo, o aluno responde questão de outro concurso."""
    outro = models.Concurso(nome="Outro", cargo="X", banca="Y")
    db.add(outro)
    db.commit()
    db.refresh(outro)
    top = models.Topico(concurso_id=outro.id, nome="Top")
    db.add(top)
    db.commit()
    db.refresh(top)
    bloco = models.Bloco(concurso_id=outro.id, titulo="B", data=date.today())
    db.add(bloco)
    db.commit()
    db.refresh(bloco)
    q = models.Questao(bloco_id=bloco.id, topico_id=top.id, tipo="mcq",
                       enunciado="?", alternativas=["a", "b"], gabarito="1")
    db.add(q)
    db.commit()
    db.refresh(q)
    resp = client.post("/api/bloco/responder", headers=aluno_headers,
                       params={"concurso_id": outro.id},
                       json={"respostas": [{"questao_id": q.id, "resposta": "1"}]})
    assert resp.status_code == 403
    assert db.query(models.Resposta).count() == 0


def test_responder_com_perfil_errado_retorna_403(client, db, aluno_headers, aluno_user, concurso):
    outro = models.Concurso(nome="Outro", cargo="X", banca="Y")
    db.add(outro)
    db.commit()
    db.refresh(outro)
    top = models.Topico(concurso_id=outro.id, nome="Top")
    db.add(top)
    db.commit()
    bloco = models.Bloco(concurso_id=outro.id, titulo="B", data=date.today())
    db.add(bloco)
    db.commit()
    q = models.Questao(bloco_id=bloco.id, topico_id=top.id, tipo="mcq",
                       enunciado="?", alternativas=["a", "b"], gabarito="1")
    db.add(q)
    db.commit()
    db.refresh(q)
    # concurso_id aponta para o concurso padrão do usuário, mas a questão é de outro
    resp = client.post("/api/bloco/responder", headers=aluno_headers,
                       params={"concurso_id": concurso.id},
                       json={"respostas": [{"questao_id": q.id, "resposta": "1"}]})
    assert resp.status_code == 403


# ---------- bloco por id (conteúdo completo) ----------

def test_bloco_por_id_do_perfil_ativo(client, db, aluno_headers, aluno_user, concurso):
    bloco = models.Bloco(concurso_id=concurso.id, titulo="Bloco X", data=date.today())
    db.add(bloco)
    db.commit()
    db.refresh(bloco)
    resp = client.get(f"/api/bloco/{bloco.id}", headers=aluno_headers)
    assert resp.status_code == 200
    assert resp.json()["bloco"]["titulo"] == "Bloco X"


def test_bloco_por_id_de_outro_perfil_retorna_403(client, db, aluno_headers, aluno_user, concurso):
    outro = models.Concurso(nome="Outro", cargo="X", banca="Y")
    db.add(outro)
    db.commit()
    db.refresh(outro)
    bloco = models.Bloco(concurso_id=outro.id, titulo="Outro bloco", data=date.today())
    db.add(bloco)
    db.commit()
    db.refresh(bloco)
    resp = client.get(f"/api/bloco/{bloco.id}", headers=aluno_headers)
    assert resp.status_code == 403


def test_bloco_por_id_inexistente_retorna_404(client, aluno_headers):
    resp = client.get("/api/bloco/999999", headers=aluno_headers)
    assert resp.status_code == 404


def test_progresso_bloqueia_trilha_diferente(client, db, aluno_headers, aluno_user, concurso):
    outro = models.Concurso(nome="Outro", cargo="X", banca="Y")
    db.add(outro)
    db.commit()
    db.refresh(outro)
    resp = client.get("/api/progresso", headers=aluno_headers, params={"concurso_id": outro.id})
    assert resp.status_code == 403


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
                       json={"username": "novo", "password": "senha123"})
    assert resp.status_code == 403


def test_criar_usuario_duplicado_retorna_400(client, admin_headers, aluno_user):
    resp = client.post("/api/admin/usuario", headers=admin_headers,
                       json={"username": aluno_user.username, "password": "senha123"})
    assert resp.status_code == 400


def test_criar_usuario_admin_ok(client, admin_headers):
    resp = client.post("/api/admin/usuario", headers=admin_headers,
                       json={"username": "novo_aluno", "password": "senha123"})
    assert resp.status_code == 200
    assert "user_id" in resp.json()

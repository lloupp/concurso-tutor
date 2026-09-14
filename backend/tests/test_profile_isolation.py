"""Regressões de isolamento entre trilhas/perfis."""
from datetime import date

from app import models


def _outro_concurso(db):
    c = models.Concurso(nome="Outro Concurso", cargo="Outro", banca="Outra")
    db.add(c); db.commit(); db.refresh(c)
    t = models.Topico(concurso_id=c.id, nome="Outra matéria — Outro tópico")
    db.add(t); db.commit(); db.refresh(t)
    b = models.Bloco(concurso_id=c.id, titulo="Bloco estrangeiro", data=date.today())
    db.add(b); db.commit(); db.refresh(b)
    q = models.Questao(bloco_id=b.id, topico_id=t.id, tipo="mcq",
                       enunciado="Questão de outra trilha", alternativas=["a", "b"],
                       gabarito="0", materia="Outra matéria")
    db.add(q); db.commit(); db.refresh(q)
    return c, t, b, q


def test_proximo_bloco_retorna_apenas_questoes_da_trilha_do_aluno(
        client, db, aluno_headers, aluno_user, topico):
    bloco = models.Bloco(concurso_id=aluno_user.concurso_id,
                         titulo="Meu bloco", data=date.today())
    db.add(bloco); db.commit(); db.refresh(bloco)
    minha = models.Questao(bloco_id=bloco.id, topico_id=topico.id, tipo="mcq",
                            enunciado="Questão da minha trilha", alternativas=["a", "b"],
                            gabarito="0", materia="Minha matéria")
    db.add(minha); db.commit(); db.refresh(minha)
    _, _, _, estrangeira = _outro_concurso(db)

    resp = client.get("/api/bloco/proximo", headers=aluno_headers)
    assert resp.status_code == 200
    ids = {q["id"] for q in resp.json()["bloco"]["questoes"]}
    assert minha.id in ids
    assert estrangeira.id not in ids


def test_dashboard_ignora_historico_de_outra_trilha(
        client, db, aluno_headers, aluno_user, topico):
    bloco = models.Bloco(concurso_id=aluno_user.concurso_id,
                         titulo="Meu bloco", data=date.today())
    db.add(bloco); db.commit(); db.refresh(bloco)
    minha = models.Questao(bloco_id=bloco.id, topico_id=topico.id, tipo="mcq",
                            enunciado="Questão da minha trilha", alternativas=["a", "b"],
                            gabarito="0", materia="Minha matéria")
    db.add(minha); db.commit(); db.refresh(minha)
    _, top_estrangeiro, _, estrangeira = _outro_concurso(db)

    db.add(models.Resposta(user_id=aluno_user.id, questao_id=minha.id,
                           resposta="0", correta=True, nota=1.0))
    db.add(models.Resposta(user_id=aluno_user.id, questao_id=estrangeira.id,
                           resposta="0", correta=False, nota=0.0))
    db.add(models.Progresso(user_id=aluno_user.id, topico_id=topico.id,
                            tentativas=1, acertos=1, dominio=0.7))
    db.add(models.Progresso(user_id=aluno_user.id, topico_id=top_estrangeiro.id,
                            tentativas=20, acertos=0, dominio=0.0))
    db.commit()

    resp = client.get("/api/dashboard", headers=aluno_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["questoes_respondidas"] == 1
    assert body["acertos"] == 1
    assert body["erros"] == 0
    assert body["questoes_banco"] == 1
    assert body["ineditas_restantes"] == 0
    assert body["dominio_medio"] == 70.0


def test_resposta_de_outra_trilha_continua_bloqueada(
        client, db, aluno_headers, aluno_user):
    _, _, _, estrangeira = _outro_concurso(db)
    resp = client.post("/api/bloco/responder", headers=aluno_headers,
                       json={"respostas": [{"questao_id": estrangeira.id,
                                             "resposta": "0"}]})
    assert resp.status_code == 403
    assert db.query(models.Resposta).filter_by(
        user_id=aluno_user.id, questao_id=estrangeira.id).count() == 0

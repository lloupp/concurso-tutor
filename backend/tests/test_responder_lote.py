"""O envio de um bloco deve usar consultas e transação em lote."""
from datetime import date

from sqlalchemy import event

from app import models
from app.db import engine


def test_dez_respostas_nao_geram_n_mais_um(client, db, aluno_headers,
                                            aluno_user, topico):
    bloco = models.Bloco(concurso_id=aluno_user.concurso_id,
                         titulo="Lote eficiente", data=date.today())
    db.add(bloco); db.commit(); db.refresh(bloco)
    questoes = []
    for indice in range(10):
        q = models.Questao(
            bloco_id=bloco.id, topico_id=topico.id, tipo="mcq",
            enunciado=f"Questão {indice}", alternativas=["a", "b"],
            gabarito=str(indice % 2), explicacao="Explicação",
        )
        db.add(q)
        questoes.append(q)
    db.commit()
    ids = [q.id for q in questoes]

    consultas = []

    def registrar(_conn, _cursor, statement, *_args):
        consultas.append(statement.lstrip().split(None, 1)[0].upper())

    event.listen(engine, "before_cursor_execute", registrar)
    try:
        resposta = client.post("/api/bloco/responder", headers=aluno_headers, json={
            "respostas": [
                {"questao_id": qid, "resposta": str(indice % 2)}
                for indice, qid in enumerate(ids)
            ]
        })
    finally:
        event.remove(engine, "before_cursor_execute", registrar)

    assert resposta.status_code == 200
    assert len(resposta.json()["resultados"]) == 10
    assert consultas.count("SELECT") <= 7
    assert len(consultas) <= 20

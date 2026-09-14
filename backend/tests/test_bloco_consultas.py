"""Regressões de consultas para a montagem do bloco adaptativo."""
from datetime import date

from sqlalchemy import event

from app import models
from app.main import _bloco_adaptado_out
from app.db import engine


def test_bloco_adaptativo_serializa_dez_questoes_sem_n_mais_um(
        db, aluno_user, concurso):
    """Uma tela de 10 questões não pode gerar uma consulta por questão/tópico."""
    for indice in range(12):
        topico = models.Topico(concurso_id=concurso.id, nome=f"Matéria {indice}")
        db.add(topico)
        db.flush()
        bloco = models.Bloco(concurso_id=concurso.id, titulo=f"Bloco {indice}",
                             data=date.today())
        db.add(bloco)
        db.flush()
        db.add(models.Questao(
            bloco_id=bloco.id, topico_id=topico.id, tipo="mcq",
            enunciado=f"Questão {indice}", alternativas=["a", "b"],
            gabarito="0", materia=f"Matéria {indice}",
        ))
    db.commit()
    user_id = aluno_user.id
    concurso_id = concurso.id
    concurso_atual = db.get(models.Concurso, concurso_id)

    consultas = []

    def registrar(*_args):
        consultas.append(1)

    event.listen(engine, "before_cursor_execute", registrar)
    try:
        bloco = _bloco_adaptado_out(db, user_id, concurso_atual)
    finally:
        event.remove(engine, "before_cursor_execute", registrar)

    assert len(bloco["questoes"]) == 10
    # Tópicos, progresso, respostas, questões e respostas exibidas: consultas
    # em lote. O limite impede o retorno da regressão N+1.
    assert len(consultas) <= 6

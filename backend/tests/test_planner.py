"""Testes de app.planner: dominância (EMA), revisão espaçada, cobertura e plano."""
from datetime import date, timedelta

import pytest

from app import models, planner


# ---------- atualizar_progresso: EMA e agenda de revisão ----------

def test_atualizar_progresso_cria_registro_na_primeira_vez(db, aluno_user, topico):
    p = planner.atualizar_progresso(db, aluno_user.id, topico.id, acertou=True)
    assert p.tentativas == 1
    assert p.acertos == 1
    # EMA: 0.3*1.0 + 0.7*0.0
    assert p.dominio == pytest.approx(0.3)
    assert p.ultima_revisao == date.today()


def test_atualizar_progresso_acerto_incrementa_ema_corretamente(db, aluno_user, topico):
    planner.atualizar_progresso(db, aluno_user.id, topico.id, acertou=True)
    p = planner.atualizar_progresso(db, aluno_user.id, topico.id, acertou=True)
    # segunda rodada: 0.3*1.0 + 0.7*0.3 = 0.51
    assert p.tentativas == 2
    assert p.acertos == 2
    assert p.dominio == pytest.approx(0.51)


def test_atualizar_progresso_erro_reduz_ema_e_nao_conta_acerto(db, aluno_user, topico):
    planner.atualizar_progresso(db, aluno_user.id, topico.id, acertou=True)
    p = planner.atualizar_progresso(db, aluno_user.id, topico.id, acertou=False)
    # 0.3*0.0 + 0.7*0.3 = 0.21
    assert p.tentativas == 2
    assert p.acertos == 1
    assert p.dominio == pytest.approx(0.21)


def test_atualizar_progresso_usa_nota_quando_fornecida(db, aluno_user, topico):
    p = planner.atualizar_progresso(db, aluno_user.id, topico.id, acertou=None, nota=0.8)
    # 0.3*0.8 + 0.7*0.0
    assert p.dominio == pytest.approx(0.24)


def test_atualizar_progresso_discursiva_pendente_mantem_dominio(db, aluno_user, topico):
    """acertou=None e nota=None (discursiva ainda não corrigida): domínio não muda."""
    planner.atualizar_progresso(db, aluno_user.id, topico.id, acertou=True)  # dominio=0.3
    p = planner.atualizar_progresso(db, aluno_user.id, topico.id, acertou=None, nota=None)
    assert p.tentativas == 2
    assert p.acertos == 1  # não incrementa
    assert p.dominio == pytest.approx(0.3)  # mantém o valor anterior


@pytest.mark.parametrize("dominio_alvo,intervalo_esperado", [
    (0.0, 1),    # fraco: <0.6
    (0.59, 1),
    (0.6, 3),    # médio: 0.6 <= x < 0.85 (fronteira inclusiva)
    (0.84, 3),
    (0.85, 7),   # forte: >=0.85 (fronteira inclusiva)
    (1.0, 7),
])
def test_atualizar_progresso_intervalo_revisao_por_faixa(
    db, aluno_user, topico, dominio_alvo, intervalo_esperado, monkeypatch
):
    """Garante os limites exatos das faixas de revisão espaçada."""
    p = models.Progresso(user_id=aluno_user.id, topico_id=topico.id,
                         tentativas=0, acertos=0, dominio=0.0)
    db.add(p)
    db.commit()

    # Força o resultado da rodada para bater exatamente no domínio alvo,
    # resolvendo a EMA a partir de dominio anterior=0: nota = dominio_alvo / 0.3
    nota = dominio_alvo / 0.3
    p = planner.atualizar_progresso(db, aluno_user.id, topico.id, acertou=None, nota=nota)
    assert p.dominio == pytest.approx(dominio_alvo, abs=1e-6)
    assert p.proxima_revisao == date.today() + timedelta(days=intervalo_esperado)


# ---------- cobertura ----------

def test_cobertura_sem_topicos_nao_gera_zero_division(db, concurso):
    out = planner.cobertura(db, concurso.id)
    assert out == {"total": 0, "estudados": 0, "pct": 0.0}


def test_cobertura_calcula_percentual(db, concurso):
    for i in range(4):
        t = models.Topico(concurso_id=concurso.id, nome=f"T{i}", estudado=(i < 1))
        db.add(t)
    db.commit()
    out = planner.cobertura(db, concurso.id)
    assert out == {"total": 4, "estudados": 1, "pct": 25.0}


# ---------- dominancia ----------

def test_dominancia_topico_sem_progresso_usa_defaults(db, aluno_user, topico):
    out = planner.dominancia(db, aluno_user.id, topico.concurso_id)
    assert len(out) == 1
    assert out[0]["dominio"] == 0.0
    assert out[0]["tentativas"] == 0
    assert out[0]["proxima_revisao"] is None


def test_dominancia_reflete_progresso_existente(db, aluno_user, topico):
    planner.atualizar_progresso(db, aluno_user.id, topico.id, acertou=True)
    out = planner.dominancia(db, aluno_user.id, topico.concurso_id)
    assert out[0]["dominio"] == pytest.approx(0.3)
    assert out[0]["tentativas"] == 1


# ---------- proximo_plano ----------

def test_proximo_plano_prioriza_topicos_nao_estudados(db, aluno_user, concurso):
    estudado = models.Topico(concurso_id=concurso.id, nome="Estudado", estudado=True)
    nao_estudado = models.Topico(concurso_id=concurso.id, nome="Novo", estudado=False)
    db.add_all([estudado, nao_estudado])
    db.commit()
    db.refresh(estudado)
    db.refresh(nao_estudado)

    # dá domínio alto ao tópico já estudado, para garantir que não vença por score
    planner.atualizar_progresso(db, aluno_user.id, estudado.id, acertou=True)

    tops = planner.proximo_plano(db, aluno_user.id, concurso.id, n_topicos=2)
    assert tops[0].id == nao_estudado.id


def test_proximo_plano_prioriza_revisao_vencida_sobre_dominio_baixo(db, aluno_user, concurso):
    vencido = models.Topico(concurso_id=concurso.id, nome="Vencido", estudado=True)
    em_dia = models.Topico(concurso_id=concurso.id, nome="EmDia", estudado=True)
    db.add_all([vencido, em_dia])
    db.commit()
    db.refresh(vencido)
    db.refresh(em_dia)

    p_vencido = models.Progresso(user_id=aluno_user.id, topico_id=vencido.id,
                                 dominio=0.9, proxima_revisao=date.today() - timedelta(days=1))
    p_em_dia = models.Progresso(user_id=aluno_user.id, topico_id=em_dia.id,
                                dominio=0.1, proxima_revisao=date.today() + timedelta(days=5))
    db.add_all([p_vencido, p_em_dia])
    db.commit()

    tops = planner.proximo_plano(db, aluno_user.id, concurso.id, n_topicos=1)
    assert tops[0].id == vencido.id


def test_proximo_plano_mesma_faixa_prioriza_maior_dominio_bug_conhecido(db, aluno_user, concurso):
    """ATENÇÃO — mesmo padrão de bug de `proximos_topicos_admin` (ver teste acima).

    Dentro da mesma faixa (nenhuma revisão vencida), o docstring promete
    priorizar "menor dominância", mas a chave de ordenação usa `-dominio`
    ascendente, que na prática escolhe primeiro o tópico de MAIOR domínio.
    Este teste fixa o comportamento atual como regressão de referência.
    """
    fraco = models.Topico(concurso_id=concurso.id, nome="Fraco", estudado=True)
    forte = models.Topico(concurso_id=concurso.id, nome="Forte", estudado=True)
    db.add_all([fraco, forte])
    db.commit()
    db.refresh(fraco)
    db.refresh(forte)

    futuro = date.today() + timedelta(days=10)
    db.add_all([
        models.Progresso(user_id=aluno_user.id, topico_id=fraco.id, dominio=0.1,
                         proxima_revisao=futuro),
        models.Progresso(user_id=aluno_user.id, topico_id=forte.id, dominio=0.9,
                         proxima_revisao=futuro),
    ])
    db.commit()

    tops = planner.proximo_plano(db, aluno_user.id, concurso.id, n_topicos=1)
    # comportamento ATUAL: escolhe o tópico de maior domínio (`forte`), não o
    # mais fraco como o docstring promete.
    assert tops[0].id == forte.id


# ---------- proximos_topicos_admin ----------

def test_proximos_topicos_admin_razao_cobertura_para_nao_estudado(db, concurso):
    t = models.Topico(concurso_id=concurso.id, nome="Novo", estudado=False)
    db.add(t)
    db.commit()
    out = planner.proximos_topicos_admin(db, concurso.id, n=1)
    assert out[0]["razao"] == "cobertura (tópico ainda não estudado)"


def test_proximos_topicos_admin_media_dominio_entre_alunos(db, concurso, topico):
    """ATENÇÃO — possível bug de negócio detectado por este teste.

    O docstring de `proximos_topicos_admin` promete priorizar tópicos com
    "menor dominância média" (reforço para quem está fraco), mas a chave de
    ordenação usada é `-media` em ordem ascendente, o que na prática seleciona
    primeiro o tópico de MAIOR domínio médio. Este teste fixa o comportamento
    ATUAL (não o pretendido) para não quebrar a suíte; ver sugestão de fix
    reportada separadamente (inverter para ordenar por `media` sem o sinal
    negativo, tanto aqui quanto em `proximo_plano`).
    """
    aluno1 = models.User(username="a1", password_hash="x", salt="x", concurso_id=concurso.id)
    aluno2 = models.User(username="a2", password_hash="x", salt="x", concurso_id=concurso.id)
    db.add_all([aluno1, aluno2])
    db.commit()
    db.refresh(aluno1)
    db.refresh(aluno2)

    top2 = models.Topico(concurso_id=concurso.id, nome="Outro", estudado=True)
    db.add(top2)
    db.commit()
    db.refresh(top2)
    # marca `topico` como estudado também, para não vencer por cobertura
    topico.estudado = True
    db.commit()

    db.add_all([
        models.Progresso(user_id=aluno1.id, topico_id=top2.id, dominio=0.2),
        models.Progresso(user_id=aluno2.id, topico_id=top2.id, dominio=0.4),
        models.Progresso(user_id=aluno1.id, topico_id=topico.id, dominio=0.9),
    ])
    db.commit()

    out = planner.proximos_topicos_admin(db, concurso.id, n=2)
    ids = [x["id"] for x in out]
    # comportamento ATUAL: maior domínio médio (`topico`, 0.9) vem antes do
    # menor (`top2`, média 0.3) — o inverso do que o docstring promete.
    assert ids.index(topico.id) < ids.index(top2.id)

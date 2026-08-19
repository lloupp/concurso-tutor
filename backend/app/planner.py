"""Lógica de progresso, dominância e plano de estudo.

Regras de negócio (definidas com o Eduardo):
- Progresso medido por tópico: acerto%, tentativas, dominância (EMA).
- Dominância apontada (heatmap), mas TUDO é estudado (cobertura 100%).
- Tópicos fracos entram em revisão espaçada com prioridade; fortes também rodam.
"""
from datetime import date, timedelta
from sqlalchemy.orm import Session
from .models import Progresso, Topico, User, Questao, Resposta, Concurso


def atualizar_progresso(db: Session, user_id: int, topico_id: int,
                        acertou: bool | None, nota: float | None = None):
    """Atualiza dominância (EMA) e agenda de revisão espaçada."""
    p = db.query(Progresso).filter_by(user_id=user_id, topico_id=topico_id).first()
    if not p:
        p = Progresso(user_id=user_id, topico_id=topico_id,
                      tentativas=0, acertos=0, dominio=0.0)
        db.add(p)

    p.tentativas += 1
    if acertou is True:
        p.acertos += 1
    # nota 0..1 válida para discursiva; senão usa binário
    if nota is not None:
        resultado = nota
    elif acertou is True:
        resultado = 1.0
    elif acertou is False:
        resultado = 0.0
    else:
        resultado = p.dominio  # discursiva ainda não corrigida: mantém

    # EMA: domínio novo = 0.3*resultado + 0.7*anterior
    p.dominio = round(0.3 * resultado + 0.7 * (p.dominio or 0.0), 3)
    p.ultima_revisao = date.today()

    # Revisão espaçada simples: intervalo cresce com o domínio.
    # fraco (<0.6) revisita em 1 dia; médio (0.6-0.85) 3 dias; forte 7 dias.
    if p.dominio < 0.6:
        intervalo = 1
    elif p.dominio < 0.85:
        intervalo = 3
    else:
        intervalo = 7
    p.proxima_revisao = date.today() + timedelta(days=intervalo)
    db.commit()
    db.refresh(p)
    return p


def dominancia(db: Session, user_id: int, concurso_id: int):
    """Retorna lista de tópicos com dominância e status de cobertura."""
    topicos = db.query(Topico).filter_by(concurso_id=concurso_id).all()
    out = []
    for t in topicos:
        p = db.query(Progresso).filter_by(user_id=user_id, topico_id=t.id).first()
        out.append({
            "topico_id": t.id,
            "nome": t.nome,
            "dominio": p.dominio if p else 0.0,
            "tentativas": p.tentativas if p else 0,
            "estudado": t.estudado,
            "proxima_revisao": p.proxima_revisao.isoformat() if (p and p.proxima_revisao) else None,
        })
    return out


def cobertura(db: Session, concurso_id: int):
    total = db.query(Topico).filter_by(concurso_id=concurso_id).count()
    estudados = db.query(Topico).filter_by(concurso_id=concurso_id, estudado=True).count()
    return {"total": total, "estudados": estudados,
            "pct": round(100 * estudados / total, 1) if total else 0.0}


def proximo_plano(db: Session, user_id: int, concurso_id: int, n_topicos: int = 2):
    """Seleciona tópicos para o próximo bloco (visão do aluno).

    Prioridade: (1) não estudados (garante 100% de cobertura),
    (2) vencidos para revisão (proxima_revisao <= hoje),
    (3) menor dominância. Tudo estudado, nada esquecido.
    """
    topicos = db.query(Topico).filter_by(concurso_id=concurso_id).all()
    hoje = date.today()

    def score(t):
        p = db.query(Progresso).filter_by(user_id=user_id, topico_id=t.id).first()
        if not t.estudado:
            return (0, 0)
        if p and p.proxima_revisao and p.proxima_revisao <= hoje:
            return (1, p.dominio or 0)
        return (2, p.dominio if p else 0)

    ordenados = sorted(topicos, key=score)
    return ordenados[:n_topicos]


def proximos_topicos_admin(db: Session, concurso_id: int, n: int = 2):
    """Seleção de tópicos para geração (visão do Hermes/admin).

    Usa média de dominância de TODOS os alunos do concurso. Prioridade:
    (0) não estudado -> cobertura 100%; (1) revisão espaçada vencida;
    (2) menor dominância média. Retorna razão legível p/ o Hermes.
    """
    topicos = db.query(Topico).filter_by(concurso_id=concurso_id).all()
    hoje = date.today()
    out = []
    for t in topicos:
        progs = db.query(Progresso).filter_by(topico_id=t.id).all()
        media = sum(p.dominio for p in progs) / len(progs) if progs else 0.0
        vencido = any((p.proxima_revisao and p.proxima_revisao <= hoje) for p in progs)
        if not t.estudado:
            ordem, razao = 0, "cobertura (tópico ainda não estudado)"
        elif vencido:
            ordem, razao = 1, "revisão espaçada vencida"
        else:
            ordem, razao = 2, "reforço (baixa dominância média)"
        out.append({"id": t.id, "nome": t.nome, "estudado": t.estudado,
                    "dominio_medio": round(media, 3), "razao": razao,
                    "_ordem": ordem, "_media": media})
    out.sort(key=lambda x: (x["_ordem"], x["_media"]))
    return [{"id": x["id"], "nome": x["nome"], "razao": x["razao"]} for x in out[:n]]

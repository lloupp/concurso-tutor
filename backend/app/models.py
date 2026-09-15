"""Modelos de dados da plataforma de estudo para concursos.

Design de domínio:
- Concurso: um certame (PF Agente Admin, Téc. Enfermagem, ...).
- Topico: nó do edital (árvore simples). `estudado` = cobertura 100%.
- Bloco: "aula do dia" com introdução + 10 questões (misto).
- Questao: mcq (alternativas+gabarito) ou discursiva (resposta_modelo+rubric).
- Resposta: submissão do aluno; mcq corrige só, discursiva precisa LLM/Hermes.
- Progresso: dominância por (aluno, tópico) + agenda de revisão espaçada.
"""
from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Float, DateTime, Date,
    ForeignKey, JSON, UniqueConstraint, CheckConstraint,
)
from .db import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True, index=True)
    full_name = Column(String(120))
    password_hash = Column(String(200))
    salt = Column(String(64))
    role = Column(String(20), default="aluno")  # aluno | admin
    concurso_id = Column(Integer, ForeignKey("concursos.id"), nullable=True)


class Sessao(Base):
    __tablename__ = "sessoes"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    token = Column(String(64), unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)


class Concurso(Base):
    __tablename__ = "concursos"
    id = Column(Integer, primary_key=True)
    nome = Column(String(200))
    cargo = Column(String(200))
    banca = Column(String(100))
    edital_url = Column(String(500), nullable=True)
    edital_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Topico(Base):
    __tablename__ = "topicos"
    id = Column(Integer, primary_key=True)
    concurso_id = Column(Integer, ForeignKey("concursos.id"))
    nome = Column(String(200))
    pai_id = Column(Integer, ForeignKey("topicos.id"), nullable=True)
    ordem = Column(Integer, default=0)
    estudado = Column(Boolean, default=False)  # cobertura do edital


class Bloco(Base):
    __tablename__ = "blocos"
    id = Column(Integer, primary_key=True)
    concurso_id = Column(Integer, ForeignKey("concursos.id"))
    data = Column(Date, default=date.today)
    titulo = Column(String(200))
    introducao = Column(Text)
    duracao_min = Column(Integer, default=60)
    criado_por = Column(String(40), default="hermes")
    status = Column(String(20), default="ativo")


class Questao(Base):
    """Uma questão só pode ser exibida ao aluno (situacao='valida') se tiver
    origem comprovada numa prova real aplicada — ver AUDITORIA_QUESTOES_REAIS.md
    e a CheckConstraint chk_valida_exige_comprovacao abaixo. Nunca gerar/
    formular questões: apenas recuperar questões reais e preencher estes
    campos de proveniência."""
    __tablename__ = "questoes"
    __table_args__ = (
        CheckConstraint(
            "situacao != 'valida' OR ("
            "origem_verificada = 1"
            " AND classificacao_auditoria = 'VERIFICADA_REAL'"
            " AND banca IS NOT NULL AND trim(banca) != ''"
            " AND orgao IS NOT NULL AND trim(orgao) != ''"
            " AND concurso_prova IS NOT NULL AND trim(concurso_prova) != ''"
            " AND cargo IS NOT NULL AND trim(cargo) != ''"
            " AND ano_prova IS NOT NULL"
            " AND prova IS NOT NULL AND trim(prova) != ''"
            " AND numero_questao IS NOT NULL AND trim(numero_questao) != ''"
            " AND url_prova IS NOT NULL AND trim(url_prova) != ''"
            " AND gabarito_oficial IS NOT NULL AND trim(gabarito_oficial) != ''"
            ")",
            name="chk_valida_exige_comprovacao",
        ),
    )
    id = Column(Integer, primary_key=True)
    bloco_id = Column(Integer, ForeignKey("blocos.id"))
    topico_id = Column(Integer, ForeignKey("topicos.id"))
    tipo = Column(String(20))  # mcq | discursiva
    enunciado = Column(Text)
    alternativas = Column(JSON, nullable=True)   # list[str] (mcq)
    gabarito = Column(String(10), nullable=True)  # índice "0".."n" (mcq)
    resposta_modelo = Column(Text, nullable=True)  # discursiva
    rubric = Column(Text, nullable=True)            # critérios de correção
    dificuldade = Column(Integer, default=2)

    # ---- Proveniência (auditoria de questões reais) ----
    origem_verificada = Column(Boolean, default=False, nullable=False)
    banca = Column(String(100), nullable=True)
    orgao = Column(String(200), nullable=True)
    concurso_prova = Column(String(200), nullable=True)
    cargo = Column(String(200), nullable=True)
    ano_prova = Column(Integer, nullable=True)
    prova = Column(String(200), nullable=True)
    numero_questao = Column(String(20), nullable=True)
    pagina = Column(Integer, nullable=True)
    url_prova = Column(String(500), nullable=True)
    url_gabarito = Column(String(500), nullable=True)
    gabarito_oficial = Column(String(10), nullable=True)
    situacao = Column(String(20), default="quarentena", nullable=False)  # valida | quarentena | invalida
    verificacao = Column(String(200), nullable=True)
    classificacao_auditoria = Column(String(30), nullable=True)
    motivo_quarentena = Column(Text, nullable=True)


class Resposta(Base):
    __tablename__ = "respostas"
    id = Column(Integer, primary_key=True)
    questao_id = Column(Integer, ForeignKey("questoes.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    resposta = Column(Text)
    correta = Column(Boolean, nullable=True)
    nota = Column(Float, nullable=True)  # 0..1 (discursiva)
    feedback = Column(Text, nullable=True)
    corrigido_por = Column(String(40), nullable=True)  # hermes | admin | auto
    tempo_seg = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Progresso(Base):
    __tablename__ = "progresso"
    __table_args__ = (UniqueConstraint("user_id", "topico_id", name="uq_prog"),)
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    topico_id = Column(Integer, ForeignKey("topicos.id"))
    tentativas = Column(Integer, default=0)
    acertos = Column(Integer, default=0)
    dominio = Column(Float, default=0.0)  # 0..1 (média móvel exponencial)
    ultima_revisao = Column(Date, nullable=True)
    proxima_revisao = Column(Date, nullable=True)

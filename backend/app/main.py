"""API FastAPI da plataforma de estudo para concursos."""
from datetime import date, datetime
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import os

from .db import get_db, engine
from . import models, auth, planner
from .schemas import LoginIn, ResponderIn, GerarBlocoIn

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Concurso Tutor", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

API = "/api"


# ---------- Auth ----------
@app.post(f"{API}/login")
def login(payload: LoginIn, db: Session = Depends(get_db)):
    u = auth.verificar_senha(db, payload.username, payload.password)
    if not u:
        raise HTTPException(401, "Usuário ou senha inválidos")
    token = auth.criar_sessao(db, u.id)
    return {"token": token, "user": {
        "id": u.id, "username": u.username, "full_name": u.full_name,
        "role": u.role, "concurso_id": u.concurso_id,
    }}


@app.get(f"{API}/me")
def me(u: models.User = Depends(auth.get_current_user)):
    return {"id": u.id, "username": u.username, "full_name": u.full_name,
            "role": u.role, "concurso_id": u.concurso_id}


# ---------- Perfis (concursos) em livre acesso ----------
@app.get(f"{API}/concursos")
def listar_concursos(db: Session = Depends(get_db)):
    """Lista os perfis disponíveis (PF, Enfermagem, Perícias...).
    Qualquer pessoa usa para selecionar o perfil que quer estudar."""
    conc = db.query(models.Concurso).order_by(models.Concurso.id).all()
    return {"concursos": [{"id": c.id, "nome": c.nome, "cargo": c.cargo,
                            "banca": c.banca} for c in conc]}


def _resolver_concurso(db, u, concurso_id):
    """Define o concurso ativo: query param > concurso_fixo do usuário > 400.
    Permite a um aluno acessar qualquer perfil (livre acesso)."""
    cid = concurso_id if concurso_id is not None else u.concurso_id
    if cid is None:
        raise HTTPException(400, "Selecione um perfil")
    c = db.query(models.Concurso).filter_by(id=cid).first()
    if not c:
        raise HTTPException(404, "Perfil não encontrado")
    return c


# ---------- Bloco de estudo ----------
def _bloco_out(db, bloco):
    questoes = db.query(models.Questao).filter_by(bloco_id=bloco.id).all()
    qs = []
    for q in questoes:
        qs.append({
            "id": q.id, "tipo": q.tipo, "enunciado": q.enunciado,
            "alternativas": q.alternativas, "dificuldade": q.dificuldade,
            "topico_id": q.topico_id,
            # correção 3: não expõe gabarito/resposta_modelo no payload do aluno.
            # A checagem continua no backend; o front só confirma após responder.
            "resposta_modelo": None,
            "rubric": None,
        })
    return {"id": bloco.id, "titulo": bloco.titulo,
            "introducao": bloco.introducao, "duracao_min": bloco.duracao_min,
            "data": bloco.data.isoformat(), "questoes": qs}


@app.get(f"{API}/bloco/hoje")
def bloco_hoje(concurso_id: int = None,
               u: models.User = Depends(auth.get_current_user),
               db: Session = Depends(get_db)):
    c = _resolver_concurso(db, u, concurso_id)
    bloco = (db.query(models.Bloco)
             .filter_by(concurso_id=c.id, data=date.today())
             .order_by(models.Bloco.id.desc()).first())
    if not bloco:
        return {"bloco": None, "msg": f"Nenhum bloco para hoje em {c.nome}. Peça ao Hermes gerar."}
    return {"bloco": _bloco_out(db, bloco)}


@app.get(f"{API}/bloco/{{bloco_id}}")
def bloco_por_id(bloco_id: int,
                 concurso_id: int = None,
                 u: models.User = Depends(auth.get_current_user),
                 db: Session = Depends(get_db)):
    """Abre um bloco específico do perfil ativo (read-only, payload de aluno)."""
    c = _resolver_concurso(db, u, concurso_id)
    bloco = db.query(models.Bloco).filter_by(id=bloco_id).first()
    if not bloco:
        raise HTTPException(404, "Bloco não encontrado")
    if bloco.concurso_id != c.id:
        raise HTTPException(403, "Bloco não pertence ao perfil selecionado")
    return {"bloco": _bloco_out(db, bloco)}


@app.get(f"{API}/blocos")
def listar_blocos(concurso_id: int = None,
                  u: models.User = Depends(auth.get_current_user),
                  db: Session = Depends(get_db)):
    c = _resolver_concurso(db, u, concurso_id)
    blocos = db.query(models.Bloco).filter_by(concurso_id=c.id) \
        .order_by(models.Bloco.data.desc(), models.Bloco.id.desc()).all()
    return {"blocos": [{"id": b.id, "titulo": b.titulo, "data": b.data.isoformat(),
                        "introducao": b.introducao} for b in blocos]}


@app.post(f"{API}/bloco/responder")
def responder(concurso_id: int = None,
               payload: ResponderIn = None,
               u: models.User = Depends(auth.get_current_user),
               db: Session = Depends(get_db)):
    c = _resolver_concurso(db, u, concurso_id)
    resultados = []
    for r in payload.respostas:
        q = db.query(models.Questao).filter_by(id=r["questao_id"]).first()
        if not q:
            continue
        # valida que a questão pertence ao perfil ativo escolhido
        bloco = db.query(models.Bloco).filter_by(id=q.bloco_id).first()
        if not bloco or bloco.concurso_id != c.id:
            raise HTTPException(403, "Questão não pertence ao perfil selecionado")
        correta, nota, feedback = None, None, None
        if q.tipo == "mcq":
            correta = str(r["resposta"]).strip() == str(q.gabarito)
            feedback = "Correto!" if correta else f"Gabarito: {q.gabarito}"
        else:
            # discursiva: pendente de correção por Hermes/admin
            correta, nota, feedback = None, None, "Aguardando correção."
        res = models.Resposta(
            questao_id=q.id, user_id=u.id, resposta=str(r["resposta"]),
            correta=correta, nota=nota, feedback=feedback,
            corrigido_por="auto" if q.tipo == "mcq" else None,
            tempo_seg=r.get("tempo_seg"),
        )
        db.add(res)
        db.commit()
        planner.atualizar_progresso(db, u.id, q.topico_id, correta, nota)
        resultados.append({"questao_id": q.id, "correta": correta,
                           "nota": nota, "feedback": feedback})
    return {"resultados": resultados}


@app.get(f"{API}/respostas/pendentes")
def respostas_pendentes(db: Session = Depends(get_db),
                        u: models.User = Depends(auth.get_current_user)):
    """Lista discursivas aguardando correção (corrigido_por=null)."""
    if u.role != "admin":
        raise HTTPException(403, "Apenas admin/Hermes")
    pend = (db.query(models.Resposta)
            .join(models.Questao, models.Resposta.questao_id == models.Questao.id)
            .filter(models.Questao.tipo == "discursiva",
                    models.Resposta.corrigido_por.is_(None))
            .all())
    out = []
    for r in pend:
        q = db.query(models.Questao).filter_by(id=r.questao_id).first()
        out.append({
            "resposta_id": r.id, "questao_id": r.questao_id,
            "user_id": r.user_id, "resposta": r.resposta,
            "enunciado": q.enunciado, "resposta_modelo": q.resposta_modelo,
            "rubric": q.rubric,
        })
    return {"pendentes": out}


@app.post(f"{API}/bloco/responder/corrigir")
def corrigir_discursiva(resposta_id: int, nota: float, feedback: str,
                        correta: bool = None,
                        db: Session = Depends(get_db),
                        u: models.User = Depends(auth.get_current_user)):
    if u.role != "admin":
        raise HTTPException(403, "Apenas admin/Hermes")
    r = db.query(models.Resposta).filter_by(id=resposta_id).first()
    if not r:
        raise HTTPException(404, "Resposta não encontrada")
    r.nota = nota
    r.feedback = feedback
    r.correta = correta
    r.corrigido_por = "hermes"
    db.commit()
    q = db.query(models.Questao).filter_by(id=r.questao_id).first()
    planner.atualizar_progresso(db, r.user_id, q.topico_id, correta, nota)
    return {"ok": True, "resposta_id": resposta_id}
@app.get(f"{API}/progresso")
def progresso(concurso_id: int = None,
              u: models.User = Depends(auth.get_current_user),
              db: Session = Depends(get_db)):
    c = _resolver_concurso(db, u, concurso_id)
    return {"dominancia": planner.dominancia(db, u.id, c.id),
            "cobertura": planner.cobertura(db, c.id)}


@app.get(f"{API}/plano")
def plano(concurso_id: int = None,
          u: models.User = Depends(auth.get_current_user),
          db: Session = Depends(get_db)):
    c = _resolver_concurso(db, u, concurso_id)
    tops = planner.proximo_plano(db, u.id, c.id)
    return {"proximos_topicos": [{"id": t.id, "nome": t.nome} for t in tops]}


# ---------- Admin / Hermes: criação de conteúdo ----------
@app.post(f"{API}/bloco/gerar")
def gerar_bloco(payload: GerarBlocoIn,
                u: models.User = Depends(auth.get_current_user),
                db: Session = Depends(get_db)):
    """Recebe um bloco já montado (pelo Hermes via skill 'tutor').
    O corpo JSON deve seguir BlocoSchema. Validação mínima + persistência.
    """
    if u.role != "admin":
        raise HTTPException(403, "Apenas admin/Hermes pode gerar blocos")
    bloco_data = payload.bloco or {}
    if not bloco_data:
        raise HTTPException(400, "Corpo 'bloco' ausente")
    bloco = models.Bloco(
        concurso_id=payload.concurso_id,
        titulo=bloco_data.get("titulo", "Bloco de estudo"),
        introducao=bloco_data.get("introducao", ""),
        duracao_min=bloco_data.get("duracao_min", 60),
        criado_por="hermes",
    )
    db.add(bloco)
    db.commit()
    db.refresh(bloco)
    for q in bloco_data.get("questoes", []):
        questao = models.Questao(
            bloco_id=bloco.id,
            topico_id=q.get("topico_id"),
            tipo=q.get("tipo", "mcq"),
            enunciado=q.get("enunciado", ""),
            alternativas=q.get("alternativas"),
            gabarito=q.get("gabarito"),
            resposta_modelo=q.get("resposta_modelo"),
            rubric=q.get("rubric"),
            dificuldade=q.get("dificuldade", 2),
        )
        db.add(questao)
    # marca tópicos como estudados (cobertura)
    for t in bloco_data.get("topicos_ids", []):
        top = db.query(models.Topico).filter_by(id=t).first()
        if top:
            top.estudado = True
    db.commit()
    return {"bloco_id": bloco.id, "questoes": len(bloco_data.get("questoes", []))}


@app.post(f"{API}/admin/concurso")
def criar_concurso(nome: str, cargo: str, banca: str = "",
                   edital_url: str = "", db: Session = Depends(get_db),
                   u: models.User = Depends(auth.get_current_user)):
    if u.role != "admin":
        raise HTTPException(403, "Apenas admin")
    c = models.Concurso(nome=nome, cargo=cargo, banca=banca, edital_url=edital_url)
    db.add(c); db.commit(); db.refresh(c)
    return {"concurso_id": c.id}


@app.post(f"{API}/admin/topico")
def criar_topico(concurso_id: int, nome: str, pai_id: int = None,
                 db: Session = Depends(get_db),
                 u: models.User = Depends(auth.get_current_user)):
    if u.role != "admin":
        raise HTTPException(403, "Apenas admin")
    t = models.Topico(concurso_id=concurso_id, nome=nome, pai_id=pai_id)
    db.add(t); db.commit(); db.refresh(t)
    return {"topico_id": t.id}


@app.get(f"{API}/admin/topicos-selecao")
def topicos_selecao(concurso_id: int, n: int = 2,
                    db: Session = Depends(get_db),
                    u: models.User = Depends(auth.get_current_user)):
    """Hermes usa para saber QUAIS tópicos gerar (baseado em cobertura + domínio)."""
    if u.role != "admin":
        raise HTTPException(403, "Apenas admin/Hermes")
    return {"topicos": planner.proximos_topicos_admin(db, concurso_id, n)}


@app.get(f"{API}/admin/alunos")
def listar_alunos(concurso_id: int = None,
                  db: Session = Depends(get_db),
                  u: models.User = Depends(auth.get_current_user)):
    """Hermes usa para saber quais alunos (e concursos) gerar blocos."""
    if u.role != "admin":
        raise HTTPException(403, "Apenas admin/Hermes")
    q = db.query(models.User).filter_by(role="aluno")
    if concurso_id:
        q = q.filter_by(concurso_id=concurso_id)
    alunos = q.all()
    return {"alunos": [{"id": a.id, "username": a.username,
                        "full_name": a.full_name, "concurso_id": a.concurso_id}
                       for a in alunos]}


@app.post(f"{API}/admin/usuario")
def criar_usuario(username: str, password: str, full_name: str = "",
                  concurso_id: int = None,
                  db: Session = Depends(get_db),
                  u: models.User = Depends(auth.get_current_user)):
    if u.role != "admin":
        raise HTTPException(403, "Apenas admin")
    if db.query(models.User).filter_by(username=username).first():
        raise HTTPException(400, "Usuário já existe")
    user = auth.criar_usuario(db, username, password, full_name, "aluno", concurso_id)
    return {"user_id": user.id}


# ---------- Frontend (estático) ----------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FRONT = os.path.join(BASE_DIR, "frontend")
if os.path.isdir(FRONT):
    app.mount("/", StaticFiles(directory=FRONT, html=True), name="front")

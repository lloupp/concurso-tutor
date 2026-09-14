"""API FastAPI da plataforma de estudo para concursos."""
from datetime import date, datetime
import json
import re
from time import perf_counter
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import os

from .db import get_db, engine
from . import models, auth, planner
from .schemas import LoginIn, ResponderIn, GerarBlocoIn, CriarUsuarioIn, CadastroIn

# Em PostgreSQL/Supabase, o schema é aplicado por migration, não em cada
# cold start da Function. O create_all continua útil no SQLite local/demo.
if not os.environ.get("DATABASE_URL") or os.environ.get("AUTO_CREATE_SCHEMA") == "true":
    models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Concurso Tutor", version="0.1.0")

# CORS_ORIGINS: lista separada por vírgula (ex.: "http://localhost:8000,https://meuapp.com").
# A auth usa Bearer token (não cookie), então allow_credentials fica False mesmo com
# origens abertas — não há cookie de sessão para vazar entre origens.
_cors_origins = os.environ.get("CORS_ORIGINS", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _cors_origins.split(",")] if _cors_origins != "*" else ["*"],
    allow_credentials=False,
    allow_methods=["*"], allow_headers=["*"],
)


@app.middleware("http")
async def registrar_tempo_requisicao(request: Request, call_next):
    """Expõe e registra a duração do app sem incluir dados de alunos."""
    inicio = perf_counter()
    try:
        resposta = await call_next(request)
    except Exception as exc:
        if request.url.path.startswith(API):
            print(json.dumps({
                "level": "error", "event": "api_request", "path": request.url.path,
                "method": request.method, "status": 500,
                "duration_ms": round((perf_counter() - inicio) * 1000, 1),
                "error": type(exc).__name__,
                "request_id": request.headers.get("x-vercel-id"),
            }))
        raise

    duracao_ms = round((perf_counter() - inicio) * 1000, 1)
    if request.url.path.startswith(API):
        resposta.headers["Server-Timing"] = f"app;dur={duracao_ms}"
        print(json.dumps({
            "level": "info", "event": "api_request", "path": request.url.path,
            "method": request.method, "status": resposta.status_code,
            "duration_ms": duracao_ms,
            "request_id": request.headers.get("x-vercel-id"),
        }))
    return resposta

API = "/api"

TIPOS_AUTOMATICOS = {"mcq", "verdadeiro_falso", "numerica"}


def _numero(valor):
    """Aceita números digitados com ponto ou vírgula decimal."""
    if isinstance(valor, (int, float)):
        return float(valor)
    texto = str(valor or "").strip().replace(" ", "").replace(",", ".")
    if not re.fullmatch(r"[-+]?\d+(?:\.\d+)?", texto):
        return None
    return float(texto)


def _corrigir_automaticamente(q, resposta):
    """Retorna (correta, nota, feedback) sem depender de IA."""
    recebido = str(resposta or "").strip()
    if q.tipo == "mcq":
        correta = recebido == str(q.gabarito).strip()
        indice = int(str(q.gabarito).strip())
        alternativa = (q.alternativas or [])[indice] if 0 <= indice < len(q.alternativas or []) else ""
        esperado = f"{chr(65 + indice)}) {alternativa}".strip()
    elif q.tipo == "verdadeiro_falso":
        normalizado = recebido.lower() in {"true", "verdadeiro", "v", "sim", "1", "certo"}
        esperado_bool = str(q.gabarito).strip().lower() in {"true", "verdadeiro", "v", "sim", "1"}
        correta = normalizado == esperado_bool
        esperado = "Verdadeiro" if esperado_bool else "Falso"
    elif q.tipo == "numerica":
        valor = _numero(recebido)
        esperado_num = _numero(q.gabarito)
        tolerancia = q.tolerancia if q.tolerancia is not None else 0.01
        correta = valor is not None and esperado_num is not None and abs(valor - esperado_num) <= tolerancia
        esperado = f"{q.gabarito}{(' ' + q.unidade) if q.unidade else ''}"
    else:
        return None, None, "Questão legada sem correção automática."
    feedback = "Correto." if correta else f"Gabarito: {esperado}. Resposta correta."
    if q.explicacao:
        feedback += f" {q.explicacao}"
    return correta, (1.0 if correta else 0.0), feedback


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
        "tempo_diario": u.tempo_diario,
    }}


@app.post(f"{API}/cadastro")
def cadastro(payload: CadastroIn, db: Session = Depends(get_db)):
    """Cria um aluno escolhendo apenas a trilha e o tempo diário."""
    if len(payload.username.strip()) < 3 or len(payload.password) < 6:
        raise HTTPException(400, "Usuário deve ter 3+ caracteres e senha 6+ caracteres")
    if payload.tempo_diario not in {20, 30, 45, 60, 90}:
        raise HTTPException(400, "Tempo diário inválido")
    if not db.query(models.Concurso).filter_by(id=payload.concurso_id).first():
        raise HTTPException(404, "Trilha não encontrada")
    if db.query(models.User).filter_by(username=payload.username.strip()).first():
        raise HTTPException(400, "Usuário já existe")
    user = auth.criar_usuario(db, payload.username.strip(), payload.password,
                              payload.full_name.strip(), "aluno", payload.concurso_id)
    user.tempo_diario = payload.tempo_diario
    db.commit()
    return {"user_id": user.id, "username": user.username}


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
    if u.role == "aluno" and concurso_id is not None and concurso_id != u.concurso_id:
        raise HTTPException(403, "O aluno só pode acessar a trilha escolhida no cadastro")
    cid = u.concurso_id if u.role == "aluno" else (concurso_id if concurso_id is not None else u.concurso_id)
    if cid is None:
        raise HTTPException(400, "Selecione um perfil")
    c = db.query(models.Concurso).filter_by(id=cid).first()
    if not c:
        raise HTTPException(404, "Perfil não encontrado")
    return c


# ---------- Bloco de estudo ----------
def _questoes_out(db, questoes, user_id=None):
    """Serializa questões sem fazer uma consulta de respostas por item."""
    anteriores = {}
    if user_id is not None and questoes:
        ids = [q.id for q in questoes]
        # A ordenação descendente permite preservar somente a última tentativa
        # de cada questão em uma única consulta.
        for resposta in (db.query(models.Resposta)
                         .filter(models.Resposta.user_id == user_id,
                                 models.Resposta.questao_id.in_(ids))
                         .order_by(models.Resposta.id.desc()).all()):
            anteriores.setdefault(resposta.questao_id, resposta)

    qs = []
    for q in questoes:
        anterior = anteriores.get(q.id)
        qs.append({
            "id": q.id, "tipo": q.tipo, "enunciado": q.enunciado,
            "alternativas": q.alternativas, "dificuldade": q.dificuldade,
            "topico_id": q.topico_id,
            "explicacao": q.explicacao,
            "fonte_id": q.fonte_id,
            "tolerancia": q.tolerancia,
            "unidade": q.unidade,
            "banca_estilo": q.banca_estilo,
            "materia": q.materia,
            "trilha": q.trilha,
            "texto_base": q.texto_base,
            # correção 3: não expõe gabarito/resposta_modelo no payload do aluno.
            # A checagem continua no backend; o front só confirma após responder.
            "resposta_modelo": None,
            "rubric": None,
            "resposta_anterior": ({
                "resposta": anterior.resposta, "correta": anterior.correta,
                "nota": anterior.nota, "feedback": anterior.feedback,
                "gabarito": q.gabarito if q.tipo in TIPOS_AUTOMATICOS else None,
            } if anterior else None),
        })
    return qs


def _bloco_out(db, bloco, user_id=None):
    questoes = db.query(models.Questao).filter_by(bloco_id=bloco.id).all()
    return {"id": bloco.id, "titulo": bloco.titulo,
            "introducao": bloco.introducao, "duracao_min": bloco.duracao_min,
            "data": bloco.data.isoformat(),
            "questoes": _questoes_out(db, questoes, user_id)}


def _bloco_adaptado_out(db, user_id, concurso):
    """Monta um bloco sempre utilizável, com prioridade adaptativa por camadas."""
    hoje = date.today()
    topicos = planner.proximo_plano(db, user_id, concurso.id, n_topicos=1000)
    prioridade_topico = {t.id: i for i, t in enumerate(topicos)}
    topico_ids = [t.id for t in topicos]
    progresso = {p.topico_id: p for p in db.query(models.Progresso)
                 .filter(models.Progresso.user_id == user_id,
                         models.Progresso.topico_id.in_(topico_ids) if topico_ids else False).all()}
    respostas = (db.query(models.Resposta)
                 .join(models.Questao, models.Questao.id == models.Resposta.questao_id)
                 .join(models.Bloco, models.Bloco.id == models.Questao.bloco_id)
                 .filter(models.Resposta.user_id == user_id,
                         models.Bloco.concurso_id == concurso.id)
                 .order_by(models.Resposta.id.desc()).all())
    ultima = {}
    for r in respostas:
        ultima.setdefault(r.questao_id, r)
    base = (db.query(models.Questao)
            .join(models.Bloco, models.Bloco.id == models.Questao.bloco_id)
            .filter(models.Bloco.concurso_id == concurso.id).all())

    def camada(q):
        r = ultima.get(q.id)
        p = progresso.get(q.topico_id)
        if r is None:
            return 0  # inédita para este aluno
        if p and p.proxima_revisao and p.proxima_revisao <= hoje:
            return 1  # revisão vencida
        if r.correta is False:
            return 2  # erro recente
        if p and (p.dominio or 0) < 0.6:
            return 3  # baixa dominância
        return 4  # reforço/reutilização

    base.sort(key=lambda q: (camada(q), prioridade_topico.get(q.topico_id, 9999),
                             ultima[q.id].id if q.id in ultima else 0, q.id))
    selecionadas = []
    materias = {}
    # Garante diversidade entre matérias quando houver alternativas disponíveis.
    for q in base:
        if len(selecionadas) >= 10:
            break
        if materias.get(q.materia, 0) >= 3:
            continue
        selecionadas.append(q)
        materias[q.materia] = materias.get(q.materia, 0) + 1
    if len(selecionadas) < min(10, len(base)):
        escolhidas = {q.id for q in selecionadas}
        selecionadas.extend(q for q in base if q.id not in escolhidas)
        selecionadas = selecionadas[:10]
    questoes = _questoes_out(db, selecionadas, user_id)
    return {"id": None, "titulo": "Próximo bloco adaptativo",
            "introducao": "Prioriza tópicos inéditos, revisões vencidas e menor domínio sem excluir as demais matérias.",
            "duracao_min": 60, "data": hoje.isoformat(), "questoes": questoes,
            "estrategia": {"camadas": ["inéditas", "revisões vencidas", "erros", "baixa dominância", "reforço"],
                           "fallback_usado": any(camada(q) == 4 for q in selecionadas),
                           "topicos_priorizados": [t.id for t in topicos[:3]]}}


@app.get(f"{API}/bloco/hoje")
def bloco_hoje(concurso_id: int = None,
               u: models.User = Depends(auth.get_current_user),
               db: Session = Depends(get_db)):
    c = _resolver_concurso(db, u, concurso_id)
    bloco = (db.query(models.Bloco)
             .filter_by(concurso_id=c.id, data=date.today())
             .order_by(models.Bloco.id.desc()).first())
    if not bloco:
        adaptado = _bloco_adaptado_out(db, u.id, c)
        if not adaptado["questoes"]:
            return {"bloco": None, "msg": f"Nenhuma questão disponível em {c.nome}."}
        return {"bloco": adaptado}
    return {"bloco": _bloco_out(db, bloco, u.id)}


@app.get(f"{API}/bloco/proximo")
def bloco_proximo(concurso_id: int = None,
                  u: models.User = Depends(auth.get_current_user),
                  db: Session = Depends(get_db)):
    """Gera o próximo bloco do aluno, inclusive após esgotar os inéditos."""
    c = _resolver_concurso(db, u, concurso_id)
    return {"bloco": _bloco_adaptado_out(db, u.id, c)}


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
    return {"bloco": _bloco_out(db, bloco, u.id)}


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
        anterior = (db.query(models.Resposta)
                    .filter_by(questao_id=q.id, user_id=u.id)
                    .order_by(models.Resposta.id.desc()).first())
        if anterior:
            resultados.append({"questao_id": q.id, "correta": anterior.correta,
                               "nota": anterior.nota, "feedback": anterior.feedback,
                               "gabarito": q.gabarito if q.tipo in TIPOS_AUTOMATICOS else None,
                               "explicacao": q.explicacao, "duplicada": True})
            continue
        correta, nota, feedback = None, None, None
        if q.tipo in TIPOS_AUTOMATICOS:
            correta, nota, feedback = _corrigir_automaticamente(q, r["resposta"])
        else:
            # Compatibilidade: dados discursivos antigos continuam preservados,
            # mas não participam do fluxo normal após a migração de conversão.
            correta, nota, feedback = None, None, "Aguardando correção."
        res = models.Resposta(
            questao_id=q.id, user_id=u.id, resposta=str(r["resposta"]),
            correta=correta, nota=nota, feedback=feedback,
            corrigido_por="auto" if q.tipo in TIPOS_AUTOMATICOS else None,
            tempo_seg=r.get("tempo_seg"),
        )
        db.add(res)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            anterior = (db.query(models.Resposta)
                        .filter_by(questao_id=q.id, user_id=u.id)
                        .order_by(models.Resposta.id.desc()).first())
            resultados.append({"questao_id": q.id, "correta": anterior.correta,
                               "nota": anterior.nota, "feedback": anterior.feedback,
                               "gabarito": q.gabarito if q.tipo in TIPOS_AUTOMATICOS else None,
                               "explicacao": q.explicacao, "duplicada": True})
            continue
        planner.atualizar_progresso(db, u.id, q.topico_id, correta, nota)
        resultados.append({"questao_id": q.id, "correta": correta,
                           "nota": nota, "feedback": feedback,
                           "gabarito": q.gabarito if q.tipo in TIPOS_AUTOMATICOS else None,
                           "explicacao": q.explicacao})
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
            "cobertura": planner.cobertura(db, c.id, u.id),
            "dashboard": planner.painel(db, u.id, c.id)}


@app.get(f"{API}/dashboard")
def dashboard(concurso_id: int = None,
              u: models.User = Depends(auth.get_current_user),
              db: Session = Depends(get_db)):
    c = _resolver_concurso(db, u, concurso_id)
    return planner.painel(db, u.id, c.id)


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
        tipo = q.get("tipo", "mcq")
        if tipo not in TIPOS_AUTOMATICOS:
            raise HTTPException(400, "Novos blocos aceitam apenas questões corrigíveis automaticamente")
        banca_estilo = q.get("banca_estilo")
        alternativas = q.get("alternativas")
        if banca_estilo == "Cebraspe" and tipo != "verdadeiro_falso":
            raise HTTPException(400, "Questões no estilo Cebraspe devem usar certo/errado")
        if banca_estilo in {"FUNDATEC", "FAURGS"} and tipo == "mcq" and len(alternativas or []) not in {4, 5}:
            raise HTTPException(400, "Questões objetivas desse estilo devem ter 4 ou 5 alternativas")
        questao = models.Questao(
            bloco_id=bloco.id,
            topico_id=q.get("topico_id"),
            tipo=tipo,
            enunciado=q.get("enunciado", ""),
            alternativas=q.get("alternativas"),
            gabarito=q.get("gabarito"),
            resposta_modelo=q.get("resposta_modelo"),
            rubric=q.get("rubric"),
            explicacao=q.get("explicacao"),
            fonte_id=q.get("fonte_id"),
            tolerancia=q.get("tolerancia"),
            unidade=q.get("unidade"),
            banca_estilo=q.get("banca_estilo"),
            materia=q.get("materia"),
            trilha=q.get("trilha"),
            texto_base=q.get("texto_base"),
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
def criar_usuario(payload: CriarUsuarioIn,
                  db: Session = Depends(get_db),
                  u: models.User = Depends(auth.get_current_user)):
    if u.role != "admin":
        raise HTTPException(403, "Apenas admin")
    if db.query(models.User).filter_by(username=payload.username).first():
        raise HTTPException(400, "Usuário já existe")
    user = auth.criar_usuario(db, payload.username, payload.password,
                              payload.full_name, "aluno", payload.concurso_id)
    return {"user_id": user.id}


# ---------- Frontend (estático) ----------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FRONT = os.path.join(BASE_DIR, "frontend")
if os.path.isdir(FRONT):
    app.mount("/", StaticFiles(directory=FRONT, html=True), name="front")

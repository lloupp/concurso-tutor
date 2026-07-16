"""Popula o banco com dados de demonstração para validar o fluxo.

Cria: 2 concursos (PF Agente Admin, Téc. Enfermagem), tópicos,
1 admin, 2 alunos e 1 bloco de exemplo com 10 questões mistas.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db import SessionLocal, engine
from app import models, auth
from app.planner import atualizar_progresso

models.Base.metadata.create_all(bind=engine)


def main():
    db = SessionLocal()
    # Limpa (demo)
    db.query(models.Resposta).delete()
    db.query(models.Questao).delete()
    db.query(models.Bloco).delete()
    db.query(models.Progresso).delete()
    db.query(models.Topico).delete()
    db.query(models.User).delete()
    db.query(models.Sessao).delete()
    db.query(models.Concurso).delete()
    db.commit()

    # Admin
    admin = auth.criar_usuario(db, "admin", "admin123", "Administrador", "admin")

    # Concurso PF
    pf = models.Concurso(nome="PF Agente Administrativo", cargo="Agente Administrativo",
                         banca="Cebraspe", edital_url="")
    db.add(pf); db.commit(); db.refresh(pf)
    pf_tops = []
    for i, nome in enumerate(["Português", "Raciocínio Lógico", "Direito Administrativo",
                              "Direito Constitucional", "Informática"]):
        t = models.Topico(concurso_id=pf.id, nome=nome, ordem=i)
        db.add(t); db.commit(); db.refresh(t)
        pf_tops.append(t)

    # Concurso Enfermagem
    enf = models.Concurso(nome="Técnico em Enfermagem", cargo="Técnico em Enfermagem",
                          banca="Conselho/Autarquia", edital_url="")
    db.add(enf); db.commit(); db.refresh(enf)
    enf_tops = []
    for i, nome in enumerate(["Anatomia", "Fisiologia", "Procedimentos de Enfermagem",
                              "Ética/SUS", "Farmácia/Medicação"]):
        t = models.Topico(concurso_id=enf.id, nome=nome, ordem=i)
        db.add(t); db.commit(); db.refresh(t)
        enf_tops.append(t)

    # Alunos
    a1 = auth.criar_usuario(db, "aluno_pf", "123456", "Aluno PF", "aluno", pf.id)
    a2 = auth.criar_usuario(db, "aluno_enf", "123456", "Aluno Enfermagem", "aluno", enf.id)

    # Bloco de exemplo (PF) - 7 MCQ + 3 discursivas
    bloco = models.Bloco(concurso_id=pf.id, titulo="Bloco Demo: Português + Raciocínio",
                         introducao="Estudo diário demo. 10 questões (1h).",
                         duracao_min=60, criado_por="hermes")
    db.add(bloco); db.commit(); db.refresh(bloco)

    mcq = [
        {"topico": pf_tops[0], "en": "Assinale a alternativa com erro de concordância.",
         "alt": ["A casa estão limpas.", "As casas estão limpas.", "A casa está limpa.", "O livro é bom."],
         "gab": "0"},
        {"topico": pf_tops[0], "en": "A palavra 'porque' é usada em:", 
         "alt": ["Resposta a 'por quê'", "Causa com pronome", "Dúvida", "Substantivo"], "gab": "0"},
        {"topico": pf_tops[1], "en": "Se A>B e B>C, então:",
         "alt": ["A<C", "A>C", "A=B", "indeterminado"], "gab": "1"},
        {"topico": pf_tops[1], "en": "Sequência 2,4,8,16... próximo:",
         "alt": ["20", "24", "32", "30"], "gab": "2"},
        {"topico": pf_tops[2], "en": "Princípio da legalidade (Admin):",
         "alt": ["Só faz o previsto em lei", "Faz o que quiser", "Não precisa de lei", "É discricionário total"],
         "gab": "0"},
        {"topico": pf_tops[3], "en": "A CF/88 foi promulgada em:",
         "alt": ["1988", "1989", "1990", "1985"], "gab": "0"},
        {"topico": pf_tops[4], "en": "HTTP significa:",
         "alt": ["HyperText Transfer Protocol", "Home Tool", "Host Text", "Hyper Link"], "gab": "0"},
    ]
    disc = [
        {"topico": pf_tops[2], "en": "Explique o princípio da eficiência na admin pública.",
         "modelo": "A admin pública deve usar recursos de forma econômica e produtiva, buscando resultados com menor custo.",
         "rubric": "Citar economicidade, produtividade, resultados."},
        {"topico": pf_tops[3], "en": "Cite 3 direitos fundamentais.",
         "modelo": "Vida, liberdade, igualdade, propriedade, etc.", "rubric": "Citou 3 direitos válidos."},
        {"topico": pf_tops[4], "en": "O que é um firewall?",
         "modelo": "Dispositivo/software que controla o tráfego de rede por regras de segurança.",
         "rubric": "Mencionar controle de tráfego e segurança."},
    ]
    for q in mcq:
        db.add(models.Questao(bloco_id=bloco.id, topico_id=q["topico"].id, tipo="mcq",
                              enunciado=q["en"], alternativas=q["alt"], gabarito=q["gab"]))
    for q in disc:
        db.add(models.Questao(bloco_id=bloco.id, topico_id=q["topico"].id, tipo="discursiva",
                              enunciado=q["en"], resposta_modelo=q["modelo"], rubric=q["rubric"]))
    for t in pf_tops[:2]:
        t.estudado = True
    db.commit()

    # Simula progresso do aluno PF (para dominância aparecer)
    atualizar_progresso(db, a1.id, pf_tops[0].id, True)
    atualizar_progresso(db, a1.id, pf_tops[1].id, False)
    atualizar_progresso(db, a1.id, pf_tops[0].id, True)

    print("Seed OK.")
    print(f"  admin/admin123 | aluno_pf/123456 | aluno_enf/123456")
    print(f"  PF concurso_id={pf.id} | Enf concurso_id={enf.id}")
    db.close()


if __name__ == "__main__":
    main()

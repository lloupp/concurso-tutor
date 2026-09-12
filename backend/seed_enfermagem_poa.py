"""Cadastra a trilha Técnico em Enfermagem — Porto Alegre e Região.

Conteúdo baseado nos editais oficiais de Porto Alegre 77/2021 (FUNDATEC) e
Canoas/FMSC 01/2020 (FUNDATEC). O script é aditivo e idempotente.
"""
import os
import sys
from datetime import date, timedelta
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db import SessionLocal, engine
from app import models, auth

models.Base.metadata.create_all(bind=engine)
NOME = "Técnico em Enfermagem — Porto Alegre e Região"

TOPICOS = [
    ("SUS", "Princípios, diretrizes e organização", 1),
    ("SUS", "Leis 8.080/1990 e 8.142/1990", 1),
    ("Legislação profissional", "Lei 7.498/1986 e Decreto 94.406/1987", 1),
    ("Legislação profissional", "Código de Ética da Enfermagem", 1),
    ("Fundamentos de enfermagem", "Sinais vitais, higiene e conforto", 1),
    ("Fundamentos de enfermagem", "Preparo, vias e administração de medicamentos", 1),
    ("Cálculo de medicação", "Diluição, unidades, doses, gotas e tempo", 1),
    ("Biossegurança", "Precauções, esterilização, desinfecção e infecção", 1),
    ("Urgência e emergência", "Suporte básico de vida, PCR e trauma", 1),
    ("Saúde pública", "Imunização, vigilância e notificação compulsória", 1),
    ("Atenção básica", "PNAB, ESF, acolhimento e redes de atenção", 2),
    ("Cuidados clínicos", "Cardiovasculares, respiratórios, endócrinos e neurológicos", 2),
    ("Cuidados clínicos", "Infectocontagiosas, IST, HIV e hepatites", 2),
    ("Saúde da mulher", "Pré-natal, parto e puerpério", 2),
    ("Saúde da criança e do adolescente", "Crescimento, desenvolvimento e cuidados", 2),
    ("Saúde do idoso", "Envelhecimento, quedas e cuidados", 2),
    ("Saúde mental", "Acolhimento, crise e rede de atenção psicossocial", 2),
    ("Clínica cirúrgica", "Pré, trans e pós-operatório, drenos e sondas", 2),
    ("Cuidados especializados", "Curativos, feridas, ostomias, oxigenoterapia e UTI", 2),
    ("Conhecimentos gerais", "Português e legislação do órgão", 3),
]

FONTES = [
    ("Edital 77/2021 — Anexo III, Técnico em Enfermagem", "https://lproweb.procempa.com.br/pmpa/prefpoa/concursos/usu_doc/edital_77-2021_anexo_iii.pdf", "edital", "Prefeitura de Porto Alegre", 2021),
    ("Edital FMSC 01/2020 — Técnico de Enfermagem", "https://www.fmsc.rs.gov.br/wp-content/uploads/2020/03/edital_6451207017.pdf", "edital", "Fundação Municipal de Saúde de Canoas", 2020),
    ("Lei 7.498/1986 — exercício da enfermagem", "https://www.planalto.gov.br/ccivil_03/leis/l7498.htm", "legislacao", "Planalto", 1986),
    ("PNAB — Portaria 2.436/2017", "https://bvsms.saude.gov.br/bvs/saudelegis/gm/2017/MatrizesConsolidacao/comum/250584.html", "protocolo", "Ministério da Saúde", 2017),
    ("Manual de normas e procedimentos para vacinação — 2ª ed.", "https://www.gov.br/saude/pt-br/centrais-de-conteudo/publicacoes/guias-e-manuais/2024/manual-de-normas-e-procedimentos-para-vacinacao.pdf", "protocolo", "Ministério da Saúde", 2024),
]


def get_or_create(db, model, filters, values):
    obj = db.query(model).filter_by(**filters).first()
    if obj:
        return obj
    obj = model(**values)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def main():
    db = SessionLocal()
    concurso = db.query(models.Concurso).filter(
        (models.Concurso.nome == NOME) |
        (models.Concurso.cargo == "Técnico em Enfermagem")
    ).order_by(models.Concurso.id).first()
    if not concurso:
        concurso = get_or_create(
        db, models.Concurso, {"nome": NOME},
        {"nome": NOME, "cargo": "Técnico em Enfermagem",
         "banca": "FUNDATEC (editais-base 2020 e 2021)",
         "edital_url": FONTES[0][1],
         "edital_text": "Trilha comparativa baseada em editais oficiais e protocolos vigentes; não substitui edital específico."},
        )
    fontes = {}
    for titulo, url, tipo, orgao, ano in FONTES:
        fontes[titulo] = get_or_create(
            db, models.Fonte, {"url": url},
            {"titulo": titulo, "url": url, "tipo": tipo, "orgao": orgao, "ano": ano},
        )
    tops = {}
    for ordem, (materia, nome, prioridade) in enumerate(TOPICOS, 1):
        chave = materia + " — " + nome
        top = get_or_create(
            db, models.Topico, {"concurso_id": concurso.id, "nome": chave},
            {"concurso_id": concurso.id, "nome": chave, "ordem": ordem},
        )
        tops[chave] = top
        fonte = fontes[FONTES[0][0] if prioridade == 1 else FONTES[1][0]]
        if not db.query(models.TopicoFonte).filter_by(topico_id=top.id, fonte_id=fonte.id).first():
            db.add(models.TopicoFonte(topico_id=top.id, fonte_id=fonte.id))
    db.commit()
    get_or_create(db, models.User, {"username": "aluno_enf"},
                  {"username": "aluno_enf", "full_name": "Aluno Enfermagem",
                   "password_hash": auth._hash("123456", "seed-enf-pao"),
                   "salt": "seed-enf-pao", "role": "aluno", "concurso_id": concurso.id})

    def add_block(offset, title, intro, items, topic_names):
        block = db.query(models.Bloco).filter_by(concurso_id=concurso.id, titulo=title).first()
        if block:
            return
        block = models.Bloco(concurso_id=concurso.id, data=date.today() + timedelta(days=offset),
                             titulo=title, introducao=intro, duracao_min=60, criado_por="hermes")
        db.add(block); db.commit(); db.refresh(block)
        for item in items:
            db.add(models.Questao(bloco_id=block.id, topico_id=tops[item["topico"]].id,
                                  tipo=item["tipo"], enunciado=item["enunciado"],
                                  alternativas=item.get("alternativas"), gabarito=item.get("gabarito"),
                                  resposta_modelo=item.get("modelo"), rubric=item.get("rubric"),
                                  dificuldade=item.get("dificuldade", 2)))
        for name in topic_names:
            tops[name].estudado = True
        db.commit()

    sus = "SUS — Princípios, diretrizes e organização"
    leis = "SUS — Leis 8.080/1990 e 8.142/1990"
    leg = "Legislação profissional — Lei 7.498/1986 e Decreto 94.406/1987"
    etica = "Legislação profissional — Código de Ética da Enfermagem"
    sinais = "Fundamentos de enfermagem — Sinais vitais, higiene e conforto"
    meds = "Fundamentos de enfermagem — Preparo, vias e administração de medicamentos"
    calc = "Cálculo de medicação — Diluição, unidades, doses, gotas e tempo"
    bio = "Biossegurança — Precauções, esterilização, desinfecção e infecção"
    urg = "Urgência e emergência — Suporte básico de vida, PCR e trauma"
    imuno = "Saúde pública — Imunização, vigilância e notificação compulsória"

    add_block(0, "Enfermagem 1: SUS, legislação e fundamentos",
      "Mini-aula de 1 hora, 10 questões progressivas. Fontes: editais oficiais de Porto Alegre 77/2021 e Canoas 01/2020.",
      [
       {"topico": sus, "tipo": "mcq", "dificuldade": 1, "enunciado": "No SUS, universalidade significa:", "alternativas": ["A) acesso de todas as pessoas", "B) atendimento apenas hospitalar", "C) cobrança proporcional", "D) exclusão da atenção básica"], "gabarito": "0"},
       {"topico": leis, "tipo": "mcq", "dificuldade": 1, "enunciado": "A Lei 8.080/1990 trata principalmente:", "alternativas": ["A) da organização e funcionamento dos serviços de saúde", "B) do código penal", "C) do ensino técnico", "D) apenas da previdência"], "gabarito": "0"},
       {"topico": leg, "tipo": "mcq", "dificuldade": 2, "enunciado": "Segundo a Lei 7.498/1986, o técnico de enfermagem exerce atividades:", "alternativas": ["A) sob orientação e supervisão de enfermeiro", "B) somente administrativas", "C) sem habilitação", "D) exclusivamente médicas"], "gabarito": "0"},
       {"topico": etica, "tipo": "mcq", "dificuldade": 2, "enunciado": "O sigilo profissional protege:", "alternativas": ["A) informações obtidas no exercício profissional", "B) somente dados financeiros", "C) apenas informações públicas", "D) qualquer erro sem exceção"], "gabarito": "0"},
       {"topico": sinais, "tipo": "mcq", "dificuldade": 1, "enunciado": "São sinais vitais tradicionalmente aferidos:", "alternativas": ["A) temperatura, pulso, respiração e pressão arterial", "B) peso e altura apenas", "C) glicemia apenas", "D) acuidade visual"], "gabarito": "0"},
       {"topico": meds, "tipo": "mcq", "dificuldade": 2, "enunciado": "Antes de administrar medicamento, a conduta segura inclui:", "alternativas": ["A) conferir paciente, medicamento, dose, via e horário", "B) administrar sem prescrição", "C) omitir registro", "D) trocar a via conforme preferência"], "gabarito": "0"},
       {"topico": sus, "tipo": "discursiva", "dificuldade": 3, "enunciado": "Explique universalidade, integralidade e equidade no SUS.", "modelo": "Universalidade é acesso de todos; integralidade articula promoção, prevenção, tratamento e reabilitação; equidade considera necessidades diferentes para reduzir desigualdades.", "rubric": "Definir corretamente os três princípios."},
       {"topico": leg, "tipo": "discursiva", "dificuldade": 3, "enunciado": "Qual é o papel do técnico de enfermagem na equipe?", "modelo": "Participar da assistência de enfermagem conforme sua formação e sob orientação e supervisão do enfermeiro.", "rubric": "Mencionar formação, limites legais e supervisão."},
       {"topico": sinais, "tipo": "discursiva", "dificuldade": 2, "enunciado": "Por que a identificação do paciente deve preceder um cuidado?", "modelo": "Para reduzir o risco de realizar procedimento ou administrar medicamento na pessoa errada.", "rubric": "Relacionar identificação à segurança do paciente."},
       {"topico": etica, "tipo": "discursiva", "dificuldade": 3, "enunciado": "Dê um exemplo de situação em que o sigilo profissional deve ser preservado.", "modelo": "Informações clínicas devem ser compartilhadas apenas com a equipe autorizada e para finalidade assistencial, observadas as exceções legais.", "rubric": "Exemplo coerente e menção às exceções legais."},
      ], [sus, leis, leg, etica, sinais, meds])

    add_block(1, "Enfermagem 2: medicamentos, cálculo e biossegurança",
      "Mini-aula de 1 hora com cálculo passo a passo. Resultado de cálculo é conteúdo de prova e não orientação clínica individual.",
      [
       {"topico": calc, "tipo": "mcq", "dificuldade": 1, "enunciado": "Prescrição: 500 mg; disponível: 250 mg por comprimido. Quantos comprimidos?", "alternativas": ["A) 1", "B) 2", "C) 3", "D) 4"], "gabarito": "1"},
       {"topico": calc, "tipo": "mcq", "dificuldade": 2, "enunciado": "Para 1000 mL em 8 horas, usando equipo de 20 gotas/mL, a vazão aproximada em gotas/min é:", "alternativas": ["A) 21", "B) 42", "C) 60", "D) 80"], "gabarito": "1"},
       {"topico": meds, "tipo": "mcq", "dificuldade": 2, "enunciado": "A via intramuscular deposita o medicamento:", "alternativas": ["A) no músculo", "B) na derme", "C) no estômago", "D) na conjuntiva"], "gabarito": "0"},
       {"topico": bio, "tipo": "mcq", "dificuldade": 1, "enunciado": "A higienização das mãos é medida essencial para:", "alternativas": ["A) reduzir a transmissão de microrganismos", "B) substituir todos os EPIs", "C) eliminar a necessidade de limpeza", "D) esterilizar instrumentos"], "gabarito": "0"},
       {"topico": bio, "tipo": "mcq", "dificuldade": 2, "enunciado": "Esterilização é o processo que:", "alternativas": ["A) destrói todas as formas de vida microbiana, incluindo esporos", "B) remove apenas sujeira visível", "C) reduz odor", "D) substitui embalagem"], "gabarito": "0"},
       {"topico": calc, "tipo": "mcq", "dificuldade": 3, "enunciado": "Prescrição: 750 mg; solução: 250 mg/5 mL. Qual volume?", "alternativas": ["A) 5 mL", "B) 10 mL", "C) 15 mL", "D) 20 mL"], "gabarito": "2"},
       {"topico": calc, "tipo": "discursiva", "dificuldade": 3, "enunciado": "Mostre o cálculo para 750 mg quando há 250 mg em 5 mL.", "modelo": "750 x 5 / 250 = 15 mL. A unidade deve ser conferida e a resposta é apenas um exercício matemático de prova.", "rubric": "Montar proporção e chegar a 15 mL."},
       {"topico": bio, "tipo": "discursiva", "dificuldade": 2, "enunciado": "Diferencie limpeza, desinfecção e esterilização.", "modelo": "Limpeza remove sujidade; desinfecção reduz microrganismos patogênicos em objetos; esterilização busca eliminar todas as formas de vida microbiana.", "rubric": "Diferenciar os três processos sem trocar conceitos."},
       {"topico": meds, "tipo": "discursiva", "dificuldade": 3, "enunciado": "Liste verificações de segurança antes de administrar um medicamento.", "modelo": "Conferir prescrição, paciente, medicamento, dose, via, horário, validade, alergias, registro e resposta do paciente, conforme protocolo institucional.", "rubric": "Citar pelo menos cinco verificações pertinentes."},
       {"topico": calc, "tipo": "discursiva", "dificuldade": 3, "enunciado": "Explique como converter horas em minutos em um cálculo de gotejamento.", "modelo": "Multiplica-se o número de horas por 60; depois aplica-se a fórmula volume x fator de gotas / tempo em minutos.", "rubric": "Converter corretamente e indicar a fórmula."},
      ], [calc, meds, bio])

    add_block(2, "Enfermagem 3: urgência, imunização e atenção básica",
      "Mini-aula de 1 hora. Fontes: edital de Porto Alegre, PNAB e Manual de Vacinação do Ministério da Saúde.",
      [
       {"topico": urg, "tipo": "mcq", "dificuldade": 1, "enunciado": "Na suspeita de parada cardiorrespiratória, a prioridade inicial é:", "alternativas": ["A) reconhecer a situação e acionar ajuda", "B) oferecer alimento", "C) aguardar evolução", "D) transportar sem avaliação"], "gabarito": "0"},
       {"topico": urg, "tipo": "mcq", "dificuldade": 2, "enunciado": "O suporte básico de vida integra medidas de:", "alternativas": ["A) reconhecimento, compressões e desfibrilação quando indicada", "B) apenas medicação", "C) somente curativo", "D) apenas transporte"], "gabarito": "0"},
       {"topico": imuno, "tipo": "mcq", "dificuldade": 1, "enunciado": "A vacinação é uma ação de:", "alternativas": ["A) prevenção de doenças e proteção coletiva", "B) tratamento exclusivo", "C) diagnóstico por imagem", "D) reabilitação motora"], "gabarito": "0"},
       {"topico": imuno, "tipo": "mcq", "dificuldade": 2, "enunciado": "A notificação compulsória contribui para:", "alternativas": ["A) vigilância e resposta a doenças e agravos", "B) dispensar registros", "C) substituir vacinação", "D) impedir investigação"], "gabarito": "0"},
       {"topico": sus, "tipo": "mcq", "dificuldade": 2, "enunciado": "A atenção básica é descrita na PNAB como:", "alternativas": ["A) porta de entrada preferencial e coordenadora do cuidado", "B) serviço sem território", "C) atendimento apenas de urgência", "D) setor isolado da rede"], "gabarito": "0"},
       {"topico": urg, "tipo": "mcq", "dificuldade": 3, "enunciado": "Na avaliação inicial do trauma, a equipe deve priorizar:", "alternativas": ["A) ameaças imediatas à vida", "B) documentação antes da segurança", "C) detalhes não urgentes", "D) alta imediata"], "gabarito": "0"},
       {"topico": urg, "tipo": "discursiva", "dificuldade": 3, "enunciado": "Descreva a sequência de resposta diante de uma vítima inconsciente que não respira normalmente.", "modelo": "Garantir segurança, reconhecer a emergência, acionar ajuda/serviço de emergência, iniciar suporte básico conforme protocolo vigente e usar DEA quando disponível e indicado.", "rubric": "Sequência coerente, acionamento de ajuda e suporte básico."},
       {"topico": imuno, "tipo": "discursiva", "dificuldade": 2, "enunciado": "Qual a importância do registro adequado da vacinação?", "modelo": "Permite comprovar doses, orientar o esquema, monitorar coberturas e apoiar a vigilância.", "rubric": "Relacionar registro a cuidado individual e vigilância."},
       {"topico": sus, "tipo": "discursiva", "dificuldade": 3, "enunciado": "Explique o papel da equipe de saúde da família no território.", "modelo": "A equipe acompanha população adscrita, promove prevenção, cuidado contínuo, educação em saúde e coordenação com a rede.", "rubric": "Mencionar território, continuidade e coordenação."},
       {"topico": urg, "tipo": "discursiva", "dificuldade": 3, "enunciado": "Por que protocolos são importantes no atendimento de urgência?", "modelo": "Padronizam prioridades e condutas baseadas em evidências, reduzem omissões e favorecem comunicação e segurança.", "rubric": "Relacionar padronização, prioridade e segurança."},
      ], [urg, imuno, sus])
    print("Trilha de enfermagem cadastrada:", concurso.id, len(tops), "tópicos, 3 blocos")
    db.close()


if __name__ == "__main__":
    main()

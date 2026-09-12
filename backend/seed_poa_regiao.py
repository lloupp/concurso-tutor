"""Cadastra o concurso-base "Concursos Nível Médio — Porto Alegre e Região".

Script ADITIVO: não apaga dados existentes (diferente de seed.py, que é só
para demo). Cria o concurso, a árvore de tópicos (matriz de matérias validada
em PESQUISA_EDITAIS_POA_REGIAO.md, com prioridade refletida na ordem de
inserção) e os 3 primeiros blocos de estudo (maior incidência primeiro:
Português + Matemática + Raciocínio Lógico + Informática, misturados).

Idempotente: se o concurso já existir (mesmo nome), não duplica.
"""
import os, sys
from datetime import date, timedelta
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db import SessionLocal, engine
from app import models, auth

models.Base.metadata.create_all(bind=engine)

NOME_CONCURSO = "Concursos Nível Médio — Porto Alegre e Região"

# Matriz de tópicos: (matéria, tópico, prioridade). Ordem da lista = ordem de
# estudo (P1 intercalando matérias, depois P2, depois P3), conforme
# PESQUISA_EDITAIS_POA_REGIAO.md.
TOPICOS = [
    # ---- Prioridade 1 (fundamental, muito recorrente) ----
    ("Língua Portuguesa", "Interpretação e compreensão de textos", 1),
    ("Matemática", "Operações fundamentais", 1),
    ("Raciocínio Lógico", "Proposições e valores lógicos", 1),
    ("Informática", "Conceitos básicos de hardware e software", 1),
    ("Língua Portuguesa", "Ortografia oficial", 1),
    ("Matemática", "Números inteiros e decimais", 1),
    ("Raciocínio Lógico", "Conectivos lógicos", 1),
    ("Informática", "Windows: área de trabalho, arquivos e pastas", 1),
    ("Língua Portuguesa", "Acentuação gráfica", 1),
    ("Matemática", "Frações", 1),
    ("Raciocínio Lógico", "Negação de proposições", 1),
    ("Informática", "Microsoft Word", 1),
    ("Língua Portuguesa", "Classes de palavras", 1),
    ("Matemática", "Razão e proporção", 1),
    ("Raciocínio Lógico", "Sequências lógicas e numéricas", 1),
    ("Informática", "Microsoft Excel", 1),
    ("Língua Portuguesa", "Concordância verbal e nominal", 1),
    ("Matemática", "Regra de três simples e composta", 1),
    ("Raciocínio Lógico", "Problemas de lógica (verdades, mentiras, parentesco)", 1),
    ("Informática", "Internet e navegadores", 1),
    ("Língua Portuguesa", "Regência verbal e nominal", 1),
    ("Matemática", "Porcentagem", 1),
    ("Informática", "Correio eletrônico", 1),
    ("Língua Portuguesa", "Crase", 1),
    ("Matemática", "Equações de 1º grau", 1),
    ("Informática", "Segurança da informação, malware e phishing", 1),
    ("Língua Portuguesa", "Pontuação", 1),
    ("Matemática", "Problemas matemáticos (aplicação)", 1),
    ("Direito Constitucional", "Administração Pública — art. 37 da CF/88 (LIMPE)", 1),
    ("Direito Administrativo", "Princípios da Administração Pública (LIMPE)", 1),
    # ---- Prioridade 2 (recorrente) ----
    ("Língua Portuguesa", "Tipologia e gêneros textuais", 2),
    ("Língua Portuguesa", "Pronomes (colocação pronominal)", 2),
    ("Língua Portuguesa", "Verbos (conjugação, tempos e modos)", 2),
    ("Língua Portuguesa", "Sintaxe (termos da oração e do período)", 2),
    ("Língua Portuguesa", "Semântica (significação de palavras)", 2),
    ("Língua Portuguesa", "Coesão e coerência", 2),
    ("Língua Portuguesa", "Reescrita de frases e textos", 2),
    ("Matemática", "Juros simples", 2),
    ("Matemática", "Médias", 2),
    ("Matemática", "Sistemas de equações simples", 2),
    ("Matemática", "Unidades de medida", 2),
    ("Matemática", "Interpretação de tabelas e gráficos", 2),
    ("Raciocínio Lógico", "Equivalências lógicas", 2),
    ("Raciocínio Lógico", "Argumentação lógica", 2),
    ("Raciocínio Lógico", "Conjuntos", 2),
    ("Raciocínio Lógico", "Análise combinatória básica", 2),
    ("Raciocínio Lógico", "Probabilidade básica", 2),
    ("Informática", "Armazenamento em nuvem", 2),
    ("Informática", "Backups", 2),
    ("Informática", "Atalhos de teclado", 2),
    ("Informática", "Noções de Inteligência Artificial no cotidiano", 2),
    ("Direito Constitucional", "Princípios fundamentais (art. 1º ao 4º da CF/88)", 2),
    ("Direito Constitucional", "Direitos e garantias fundamentais (art. 5º da CF/88)", 2),
    ("Direito Constitucional", "Direitos sociais (art. 6º da CF/88)", 2),
    ("Direito Constitucional", "Organização do Estado e Poderes (arts. 2º, 44 e segs.)", 2),
    ("Direito Administrativo", "Administração direta e indireta", 2),
    ("Direito Administrativo", "Poderes administrativos", 2),
    ("Direito Administrativo", "Atos administrativos", 2),
    ("Direito Administrativo", "Agentes públicos e servidores", 2),
    ("Direito Administrativo", "Ética no serviço público", 2),
    ("Rotinas Administrativas", "Atendimento ao público", 2),
    ("Rotinas Administrativas", "Protocolo e arquivo de documentos", 2),
    ("Rotinas Administrativas", "Redação oficial", 2),
    ("Legislação", "Lei de Acesso à Informação (Lei 12.527/2011)", 2),
    ("Legislação", "LGPD — noções gerais (Lei 13.709/2018)", 2),
    # ---- Prioridade 3 (complementar / depende do edital escolhido) ----
    ("Rotinas Administrativas", "Comunicação administrativa", 3),
    ("Rotinas Administrativas", "Organização do ambiente de trabalho", 3),
    ("Atualidades e Conhecimentos Gerais", "Atualidades institucionais estáveis (ONU, Mercosul, SUS, IBGE)", 3),
]


def get_or_create_concurso(db):
    c = db.query(models.Concurso).filter_by(nome=NOME_CONCURSO).first()
    if c:
        return c, False
    c = models.Concurso(
        nome=NOME_CONCURSO,
        cargo="Cargos administrativos de nível médio (Assistente/Auxiliar/Agente Administrativo)",
        banca="Múltiplas (FUNDATEC, FAFIPA, Fundação La Salle, IBFC, Cebraspe, FGV — ver PESQUISA_EDITAIS_POA_REGIAO.md)",
        edital_url="",
        edital_text=(
            "Base de preparação para concursos de nível médio da Região Metropolitana "
            "de Porto Alegre. Não representa um edital único: matriz de matérias e "
            "tópicos construída a partir de editais reais pesquisados (Gravataí, "
            "Câmara de Canoas, Banrisul, TJ-RS, INSS, Correios, Polícia Federal). "
            "Ver PESQUISA_EDITAIS_POA_REGIAO.md na raiz do repositório para o "
            "dossiê completo de fontes e o ranking de incidência por disciplina."
        ),
    )
    db.add(c); db.commit(); db.refresh(c)
    return c, True


def get_or_create_topicos(db, concurso_id):
    """Cria os tópicos que ainda não existem (nome 'Matéria — Tópico').
    Retorna dict nome_completo -> Topico."""
    existentes = {t.nome: t for t in db.query(models.Topico).filter_by(concurso_id=concurso_id).all()}
    out = {}
    ordem = 0
    for materia, topico, prioridade in TOPICOS:
        nome = f"{materia} — {topico}"
        ordem += 1
        if nome in existentes:
            out[nome] = existentes[nome]
            continue
        t = models.Topico(concurso_id=concurso_id, nome=nome, ordem=ordem)
        db.add(t); db.commit(); db.refresh(t)
        out[nome] = t
    return out


def get_or_create_aluno(db, concurso_id):
    u = db.query(models.User).filter_by(username="aluno_poa").first()
    if u:
        return u, False
    u = auth.criar_usuario(db, "aluno_poa", "estudar123", "Eduardo", "aluno", concurso_id)
    return u, True


def get_or_create_admin(db):
    u = db.query(models.User).filter_by(username="admin").first()
    if u:
        return u
    return auth.criar_usuario(db, "admin", "admin123", "Administrador", "admin")


def bloco_ja_existe(db, concurso_id, titulo):
    return db.query(models.Bloco).filter_by(concurso_id=concurso_id, titulo=titulo).first() is not None


def criar_bloco(db, concurso_id, titulo, introducao, questoes, topicos_nomes, tops, dia_offset=0):
    """dia_offset: 0 = hoje, 1 = amanhã, etc. — garante 1 bloco por dia,
    para que /api/bloco/hoje sempre mostre o próximo da sequência, não o
    último criado."""
    if bloco_ja_existe(db, concurso_id, titulo):
        print(f"  (já existe) {titulo}")
        return None
    bloco = models.Bloco(concurso_id=concurso_id, titulo=titulo, introducao=introducao,
                         duracao_min=60, criado_por="hermes",
                         data=date.today() + timedelta(days=dia_offset))
    db.add(bloco); db.commit(); db.refresh(bloco)
    for q in questoes:
        db.add(models.Questao(
            bloco_id=bloco.id, topico_id=tops[q["topico"]].id, tipo=q["tipo"],
            enunciado=q["enunciado"], alternativas=q.get("alternativas"),
            gabarito=q.get("gabarito"), resposta_modelo=q.get("resposta_modelo"),
            rubric=q.get("rubric"), dificuldade=q.get("dificuldade", 2),
        ))
    for nome in topicos_nomes:
        tops[nome].estudado = True
    db.commit()
    print(f"  criado: {titulo} ({len(questoes)} questões)")
    return bloco


def main():
    db = SessionLocal()
    admin = get_or_create_admin(db)
    concurso, novo = get_or_create_concurso(db)
    print(f"Concurso: {concurso.nome} (id={concurso.id}, {'novo' if novo else 'já existia'})")
    tops = get_or_create_topicos(db, concurso.id)
    print(f"Tópicos cadastrados: {len(tops)}")
    aluno, aluno_novo = get_or_create_aluno(db, concurso.id)
    print(f"Aluno: {aluno.username} (id={aluno.id}, {'novo' if aluno_novo else 'já existia'})")

    FONTE = ("Fontes: edital Gravataí CP 03/2025 (FUNDATEC, retificação 45-A/2025), "
             "edital Câmara de Canoas 01.01/2025 (FAFIPA), edital Correios 270/2024 "
             "(IBFC), edital Banrisul 01/2022 (Escriturário), Planalto (CF/88) e banco "
             "de questões já validado em docs/data/ desta própria plataforma. Ver "
             "PESQUISA_EDITAIS_POA_REGIAO.md para o dossiê completo.")

    print("\nGerando blocos iniciais (maior incidência primeiro)...")

    # ---- Bloco 1 ----
    criar_bloco(
        db, concurso.id,
        "Bloco 1: Interpretação de texto + Operações fundamentais + Lógica proposicional + Hardware/Software",
        "Mini-aula (1h). 10 questões (7 objetivas + 3 discursivas curtas), dificuldade "
        "progressiva. " + FONTE,
        [
            {"topico": "Língua Portuguesa — Interpretação e compreensão de textos", "tipo": "mcq", "dificuldade": 1,
             "enunciado": ("Leia o texto: \"O concurso público é a principal via de acesso a cargos efetivos na "
                           "Administração Pública brasileira. Por meio dele, busca-se selecionar candidatos com base "
                           "no mérito, e não em indicações pessoais, garantindo tratamento igualitário a todos os "
                           "interessados.\"\nO texto defende principalmente que o concurso público:"),
             "alternativas": ["A) deve ser abolido por ser burocrático.",
                               "B) seleciona candidatos por mérito, promovendo igualdade de condições.",
                               "C) é usado apenas para cargos de confiança.",
                               "D) depende de indicação política para ser válido."],
             "gabarito": "1"},
            {"topico": "Língua Portuguesa — Interpretação e compreensão de textos", "tipo": "mcq", "dificuldade": 2,
             "enunciado": "No mesmo texto, a expressão 'e não em indicações pessoais' tem a função de:",
             "alternativas": ["A) reforçar uma condição necessária.",
                               "B) estabelecer uma contraposição ao critério de mérito.",
                               "C) apresentar uma dúvida do autor.",
                               "D) introduzir uma nova ideia sem relação com a anterior."],
             "gabarito": "1"},
            {"topico": "Matemática — Operações fundamentais", "tipo": "mcq", "dificuldade": 1,
             "enunciado": "Um servidor atende 24 pessoas pela manhã e 18 à tarde. Quantas pessoas ele atendeu no dia?",
             "alternativas": ["A) 32", "B) 38", "C) 42", "D) 46"], "gabarito": "2"},
            {"topico": "Matemática — Operações fundamentais", "tipo": "mcq", "dificuldade": 2,
             "enunciado": "Um setor recebeu 156 processos e distribuiu igualmente entre 4 servidores. Quantos processos cada um recebeu?",
             "alternativas": ["A) 36", "B) 38", "C) 39", "D) 41"], "gabarito": "2"},
            {"topico": "Raciocínio Lógico — Proposições e valores lógicos", "tipo": "mcq", "dificuldade": 1,
             "enunciado": "Assinale a alternativa que apresenta uma proposição lógica (frase que pode ser julgada como verdadeira ou falsa):",
             "alternativas": ["A) Que horas são?", "B) Porto Alegre é a capital do Rio Grande do Sul.",
                               "C) Estude mais!", "D) Talvez chova amanhã."],
             "gabarito": "1"},
            {"topico": "Raciocínio Lógico — Proposições e valores lógicos", "tipo": "mcq", "dificuldade": 2,
             "enunciado": "Certo ou errado: a frase \"Este enunciado é uma pergunta.\" é uma proposição lógica.",
             "alternativas": ["Certo", "Errado"], "gabarito": "1"},
            {"topico": "Informática — Conceitos básicos de hardware e software", "tipo": "mcq", "dificuldade": 1,
             "enunciado": "São exemplos de dispositivos de hardware de um computador:",
             "alternativas": ["A) Windows e Word", "B) Teclado, mouse e monitor",
                               "C) Navegador e antivírus", "D) Planilha e apresentação de slides"],
             "gabarito": "1"},
            {"topico": "Informática — Conceitos básicos de hardware e software", "tipo": "discursiva", "dificuldade": 2,
             "enunciado": "Explique, em poucas linhas, a diferença entre hardware e software, dando um exemplo de cada.",
             "resposta_modelo": "Hardware é a parte física do computador (ex.: teclado, monitor, processador); "
                                 "software é o conjunto de programas que rodam sobre o hardware (ex.: Windows, Word).",
             "rubric": "Deve diferenciar parte física de programas e citar ao menos um exemplo de cada."},
            {"topico": "Matemática — Operações fundamentais", "tipo": "discursiva", "dificuldade": 3,
             "enunciado": "Um almoxarifado tinha 340 unidades de um material. Foram usadas 125 unidades em uma semana e "
                          "chegaram mais 80 unidades. Quantas unidades há agora? Mostre o cálculo.",
             "resposta_modelo": "340 - 125 + 80 = 295 unidades.",
             "rubric": "Deve mostrar a subtração e a soma corretas, chegando a 295."},
            {"topico": "Raciocínio Lógico — Proposições e valores lógicos", "tipo": "discursiva", "dificuldade": 3,
             "enunciado": "Explique por que a frase \"Feche a porta.\" não é considerada uma proposição lógica.",
             "resposta_modelo": "Porque é uma ordem/imperativo, não podendo receber valor lógico verdadeiro ou falso — "
                                 "proposições precisam ser frases declarativas julgáveis como V ou F.",
             "rubric": "Deve citar que ordens/perguntas não têm valor V/F e que proposição exige frase declarativa."},
        ],
        ["Língua Portuguesa — Interpretação e compreensão de textos", "Matemática — Operações fundamentais",
         "Raciocínio Lógico — Proposições e valores lógicos", "Informática — Conceitos básicos de hardware e software"],
        tops, dia_offset=0,
    )

    # ---- Bloco 2 ----
    criar_bloco(
        db, concurso.id,
        "Bloco 2: Ortografia + Números inteiros/decimais + Conectivos lógicos + Windows",
        "Mini-aula (1h). 10 questões (7 objetivas + 3 discursivas curtas), dificuldade "
        "progressiva. " + FONTE,
        [
            {"topico": "Língua Portuguesa — Ortografia oficial", "tipo": "mcq", "dificuldade": 1,
             "enunciado": "Assinale a alternativa com todas as palavras grafadas corretamente.",
             "alternativas": ["A) Excessão, previlégio, benefício", "B) Exceção, privilégio, benefício",
                               "C) Exceção, privilégio, beneficio", "D) Excesão, previlégio, benefício"],
             "gabarito": "1"},
            {"topico": "Língua Portuguesa — Ortografia oficial", "tipo": "mcq", "dificuldade": 2,
             "enunciado": "Assinale a alternativa em que todas as palavras estão grafadas corretamente.",
             "alternativas": ["A) Ascensão, prazeroso, ansioso", "B) Assenção, prazeirozo, ansioso",
                               "C) Ascenção, prazeroso, ansioso", "D) Ascensão, prazeiroso, anssioso"],
             "gabarito": "0"},
            {"topico": "Matemática — Números inteiros e decimais", "tipo": "mcq", "dificuldade": 1,
             "enunciado": "Qual o resultado de -8 + 15?", "alternativas": ["A) -23", "B) -7", "C) 7", "D) 23"],
             "gabarito": "2"},
            {"topico": "Matemática — Números inteiros e decimais", "tipo": "mcq", "dificuldade": 2,
             "enunciado": "O resultado de 12,5 - 4,75 é:", "alternativas": ["A) 7,75", "B) 8,25", "C) 7,25", "D) 8,75"],
             "gabarito": "0"},
            {"topico": "Raciocínio Lógico — Conectivos lógicos", "tipo": "mcq", "dificuldade": 1,
             "enunciado": "A conjunção \"e\" (símbolo ∧), na lógica proposicional, resulta verdadeira quando:",
             "alternativas": ["A) pelo menos uma das proposições é verdadeira",
                               "B) ambas as proposições são verdadeiras",
                               "C) ambas as proposições são falsas",
                               "D) exatamente uma das proposições é falsa"],
             "gabarito": "1"},
            {"topico": "Raciocínio Lógico — Conectivos lógicos", "tipo": "mcq", "dificuldade": 2,
             "enunciado": "Considere p = \"Está chovendo\" (falsa) e q = \"Faz frio\" (verdadeira). O valor lógico de p ∨ q (disjunção) é:",
             "alternativas": ["Verdadeiro", "Falso"], "gabarito": "0"},
            {"topico": "Informática — Windows: área de trabalho, arquivos e pastas", "tipo": "mcq", "dificuldade": 1,
             "enunciado": "No Windows, a combinação de teclas Ctrl+C é utilizada para:",
             "alternativas": ["A) copiar o item selecionado", "B) colar o item copiado",
                               "C) fechar o programa", "D) criar uma nova pasta"],
             "gabarito": "0"},
            {"topico": "Informática — Windows: área de trabalho, arquivos e pastas", "tipo": "discursiva", "dificuldade": 2,
             "enunciado": "Explique a diferença entre 'copiar' (Ctrl+C) e 'recortar' (Ctrl+X) um arquivo no Windows.",
             "resposta_modelo": "Copiar mantém o arquivo original no local de origem e cria uma cópia no destino; "
                                 "recortar remove o arquivo do local de origem ao colá-lo no destino (move o arquivo).",
             "rubric": "Deve indicar que copiar duplica e recortar move (remove da origem)."},
            {"topico": "Matemática — Números inteiros e decimais", "tipo": "discursiva", "dificuldade": 3,
             "enunciado": "A temperatura era de -3°C às 6h e subiu 9°C até o meio-dia. Qual a temperatura ao meio-dia? Explique o raciocínio.",
             "resposta_modelo": "-3 + 9 = 6°C.",
             "rubric": "Deve somar corretamente números com sinais, chegando a 6°C."},
            {"topico": "Raciocínio Lógico — Conectivos lógicos", "tipo": "discursiva", "dificuldade": 3,
             "enunciado": "Considerando p verdadeira e q falsa, explique por que p ∧ q é falsa, mas p ∨ q é verdadeira.",
             "resposta_modelo": "A conjunção (∧) exige que ambas sejam verdadeiras; como q é falsa, p ∧ q é falsa. "
                                 "A disjunção (∨) exige que ao menos uma seja verdadeira; como p é verdadeira, p ∨ q é verdadeira.",
             "rubric": "Deve explicar a regra da conjunção (ambas V) e da disjunção (ao menos uma V) corretamente."},
        ],
        ["Língua Portuguesa — Ortografia oficial", "Matemática — Números inteiros e decimais",
         "Raciocínio Lógico — Conectivos lógicos", "Informática — Windows: área de trabalho, arquivos e pastas"],
        tops, dia_offset=1,
    )

    # ---- Bloco 3 ----
    criar_bloco(
        db, concurso.id,
        "Bloco 3: Acentuação gráfica + Frações + Negação de proposições + Microsoft Word",
        "Mini-aula (1h). 10 questões (7 objetivas + 3 discursivas curtas), dificuldade "
        "progressiva. " + FONTE,
        [
            {"topico": "Língua Portuguesa — Acentuação gráfica", "tipo": "mcq", "dificuldade": 1,
             "enunciado": "Assinale a alternativa em que todas as palavras seguem a mesma regra de acentuação "
                          "(oxítonas terminadas em 'a(s)', 'e(s)' ou 'o(s)'):",
             "alternativas": ["A) café, você, avó", "B) lâmpada, árvore, público",
                               "C) fácil, éter, tórax", "D) rápido, número, âmbar"],
             "gabarito": "0"},
            {"topico": "Língua Portuguesa — Acentuação gráfica", "tipo": "mcq", "dificuldade": 2,
             "enunciado": "Assinale a alternativa em que a palavra está acentuada corretamente por ser paroxítona terminada em ditongo:",
             "alternativas": ["A) família", "B) história", "C) água", "D) todas as anteriores"],
             "gabarito": "3"},
            {"topico": "Matemática — Frações", "tipo": "mcq", "dificuldade": 1,
             "enunciado": "O resultado de 1/4 + 1/2 é:", "alternativas": ["A) 1/6", "B) 2/6", "C) 3/4", "D) 1/2"],
             "gabarito": "2"},
            {"topico": "Matemática — Frações", "tipo": "mcq", "dificuldade": 2,
             "enunciado": "Em um setor com 40 servidores, 3/8 estão de férias. Quantos servidores estão de férias?",
             "alternativas": ["A) 12", "B) 15", "C) 18", "D) 20"], "gabarito": "1"},
            {"topico": "Raciocínio Lógico — Negação de proposições", "tipo": "mcq", "dificuldade": 1,
             "enunciado": "A negação da proposição \"Todos os servidores compareceram à reunião\" é:",
             "alternativas": ["A) Nenhum servidor compareceu à reunião.",
                               "B) Pelo menos um servidor não compareceu à reunião.",
                               "C) Todos os servidores faltaram à reunião.",
                               "D) Alguns servidores compareceram à reunião."],
             "gabarito": "1"},
            {"topico": "Raciocínio Lógico — Negação de proposições", "tipo": "mcq", "dificuldade": 2,
             "enunciado": "Certo ou errado: a negação de \"Existe um funcionário que fala inglês\" é \"Nenhum funcionário fala inglês\".",
             "alternativas": ["Certo", "Errado"], "gabarito": "0"},
            {"topico": "Informática — Microsoft Word", "tipo": "mcq", "dificuldade": 1,
             "enunciado": "No Microsoft Word, qual atalho de teclado é usado para salvar um documento?",
             "alternativas": ["A) Ctrl+P", "B) Ctrl+S", "C) Ctrl+C", "D) Ctrl+Z"], "gabarito": "1"},
            {"topico": "Informática — Microsoft Word", "tipo": "discursiva", "dificuldade": 2,
             "enunciado": "Explique para que serve a ferramenta de 'Localizar e Substituir' no Microsoft Word.",
             "resposta_modelo": "Permite buscar uma palavra/trecho no documento e substituí-la automaticamente por "
                                 "outra, em uma ou todas as ocorrências, agilizando revisões.",
             "rubric": "Deve mencionar busca de texto e substituição automática."},
            {"topico": "Matemática — Frações", "tipo": "discursiva", "dificuldade": 3,
             "enunciado": "Um documento tem 60 páginas. Se 2/5 já foram revisadas, quantas páginas ainda faltam revisar? Mostre o cálculo.",
             "resposta_modelo": "2/5 de 60 = 24 revisadas; faltam 60 - 24 = 36 páginas.",
             "rubric": "Deve calcular 2/5 de 60 corretamente e subtrair para achar as páginas restantes (36)."},
            {"topico": "Raciocínio Lógico — Negação de proposições", "tipo": "discursiva", "dificuldade": 3,
             "enunciado": "Explique por que a negação de uma proposição do tipo \"Todo A é B\" não é \"Nenhum A é B\", e sim \"Existe A que não é B\".",
             "resposta_modelo": "Para que \"Todo A é B\" seja falsa, basta um único caso de A que não seja B — não é "
                                 "necessário que nenhum A seja B. Por isso a negação lógica correta é existencial: "
                                 "\"existe pelo menos um A que não é B\".",
             "rubric": "Deve explicar que basta um contraexemplo para negar um 'todo', logo a negação é existencial, não universal."},
        ],
        ["Língua Portuguesa — Acentuação gráfica", "Matemática — Frações",
         "Raciocínio Lógico — Negação de proposições", "Informática — Microsoft Word"],
        tops, dia_offset=2,
    )

    db.close()
    print("\nSeed concluído.")


if __name__ == "__main__":
    main()

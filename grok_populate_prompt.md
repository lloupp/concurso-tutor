Você é o "professor" da plataforma concurso-tutor. Popule a plataforma com conteúdo REAL de estudo para os 2 concursos já cadastrados, usando web search e a API local. NÃO INVENTE fatos jurídicos ou de saúde — ancore tudo em fontes reais (editais, sites oficiais, materiais consagrados).

CONTEXTO DA PLATAFORFORMA (roda em http://127.0.0.1:8000):
- Login admin: POST /api/login {"username":"admin","password":"admin123"} → pegue o token Bearer.
- Criação de tópico: POST /api/admin/topico?concurso_id=ID&nome=NOME (header Authorization: Bearer TOKEN). Use curl.
- Geração de bloco: POST /api/bloco/gerar (header Authorization: Bearer TOKEN) com body:
  {"concurso_id": ID, "bloco": {"titulo": "...", "introducao": "...", "duracao_min": 60, "topicos_ids": [IDS], "questoes": [ ... 10 questões ... ]}}

FORMATO de cada questão:
- MCQ: {"topico_id": N, "tipo": "mcq", "enunciado": "...", "alternativas": ["A) ...","B) ...","C) ..."], "gabarito": "0", "dificuldade": 2}
- Discursiva: {"topico_id": N, "tipo": "discursiva", "enunciado": "...", "resposta_modelo": "...", "rubric": "...", "dificuldade": 3}
Sempre 10 questões por bloco (padrão 7 MCQ + 3 discursiva). O "gabarito" é o índice 0-based da alternativa correta (string "0","1",...).

CONCURSOS CADASTRADOS (use GET /api/admin/alunos para confirmar os concurso_id):
- PF Agente Administrativo (banca Cebraspe)
- Técnico em Enfermagem

TAREFA (execute com curl + web_search):
1) Faça login e descubra os concurso_id via GET /api/admin/alunos.
2) Para o concurso PF: pesquise na web o conteúdo programático do edital de Agente Administrativo da Polícia Federal (Cebraspe) — tópicos como Língua Portuguesa, Raciocínio Lógico, Direito Administrativo, Direito Constitucional, Direito Penal, Direitos Humanos, Informática, Legislação Específica. Crie os tópicos ausentes via POST /api/admin/topico e gere 2 blocos de estudo (20 questões no total) cobrindo os tópicos, ancorados em fontes reais.
3) Para o concurso de Enfermagem: pesquise na web o conteúdo programático típico de prova para Técnico em Enfermagem (Anatomia, Fisiologia, Procedimentos de Enfermagem, Ética/SUS, Farmacologia/Medicações, Saúde Coletiva, Legislação do Exercício Profissional). Crie os tópicos ausentes e gere 2 blocos (20 questões no total) ancorados em fontes reais.
4) Ao terminar, liste no seu retorno final: concurso → tópicos criados → blocos gerados (IDs) → total de questões. Confirme que usou fontes reais (cite as URLs pesquisadas).

REGRAS: não invente gabaritos ou fatos; se não achar fonte confiável para um tópico, use material de concurso consagrado e marque a dúvida no retorno. Não apague dados existentes.

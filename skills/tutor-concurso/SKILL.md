---
name: tutor-concurso
description: Busca e cadastra questões REAIS (efetivamente aplicadas em provas de concurso, com origem comprovada) para a plataforma concurso-tutor, e corrige questões discursivas. Use quando Eduardo pedir para adicionar/repor exercícios para os alunos de concurso, ou para corrigir discursivas pendentes. NUNCA formula, gera ou inventa questões — apenas recupera questões reais de provas aplicadas.
---

# Tutor de Concurso (skill do Hermes)

Esta skill conecta o Hermes à plataforma `concurso-tutor` (FastAPI + SQLite
local, e Supabase/Postgres em produção — ver seção específica abaixo).
O Hermes é o "professor": monta o bloco do dia (mini-aula + questões) e
corrige as discursivas que a plataforma não consegue sozinha.

## Princípio central — REGRA ABSOLUTA

**O Hermes NUNCA formula, gera, cria, adapta, parafraseia ou escreve
questões "no estilo" de uma banca.** O Hermes apenas **busca e recupera**
questões que foram **efetivamente aplicadas** em uma prova real de
concurso público, e transcreve o enunciado/alternativas/gabarito
exatamente como constam na prova original.

Uma questão só pode ser cadastrada com `situacao='valida'` se for possível
comprovar, para aquela questão específica:

- banca, órgão, concurso, cargo, ano e caderno/prova;
- número (ou posição) da questão na prova;
- URL ou arquivo da prova original (idealmente com a página);
- gabarito oficial (definitivo, pós-recursos quando houver);
- que o texto cadastrado corresponde ao texto original da prova.

Lei, edital, manual, protocolo ou apostila **não são prova de origem de uma
questão** — só provam que o assunto é cobrado, não que aquela questão
específica existe numa prova aplicada.

Se não for encontrada uma questão real adequada para um tópico: **não
cadastre nada nesse tópico**. Registrar a lacuna é sempre preferível a
inventar. Ver `AUDITORIA_QUESTOES_REAIS.md` para o histórico completo e o
que ainda está pendente de reposição.

Isso vale tanto para MCQ quanto para certo/errado e discursivas. Uma
questão discursiva "real" é uma que a banca de fato aplicou (com o padrão
de resposta/critérios oficiais, quando publicados) — não um enunciado novo
inspirado num tema do edital.

## Fluxo: buscar/recuperar questões reais

1. Login admin para obter token:
   - `POST /api/login` → `{"username":"admin","password":"admin123"}` → guarda `token`.
2. Descobrir alunos e concursos:
   - `GET /api/admin/alunos` → lista `[{id, username, full_name, concurso_id}]`.
3. Selecionar tópicos com lacuna real (sem questões válidas suficientes):
   - `GET /api/admin/topicos-selecao?concurso_id=ID&n=2` →
     `[{id, nome, razao}]`.
4. Para cada tópico, **pesquisar na web a prova oficial já aplicada**
   (PDF do caderno de prova + gabarito oficial definitivo) da banca/órgão
   relevante — via `web_search`/navegação real, nunca de memória. Fontes
   preferenciais: site da própria banca/órgão, ou repositórios que hospedem
   o PDF oficial da prova.
5. Localizada a prova, abrir o PDF e localizar a(s) questão(ões) sobre o
   tópico. Transcrever o enunciado e as alternativas **exatamente como
   aparecem** (sem corrigir português, sem simplificar, sem reordenar
   alternativas). Conferir o gabarito oficial (definitivo/pós-recursos) e
   anotar se a questão foi anulada ou teve gabarito alterado.
6. Cadastrar a questão com **todos** os metadados de comprovação (ver
   schema abaixo). Se qualquer metadado obrigatório não puder ser
   comprovado, cadastrar com `situacao='quarentena'` (ou não cadastrar) —
   nunca com `situacao='valida'`. O banco tem uma constraint
   (`chk_valida_exige_comprovacao`) que rejeita o INSERT/UPDATE se faltar
   qualquer metadado obrigatório para `situacao='valida'`.
7. Confirmar e avisar o Eduardo no Telegram quais questões reais foram
   adicionadas (com a fonte de cada uma).

### Formato de questão real (BlocoSchema local, backend FastAPI)
```json
{
  "topico_id": 11,
  "tipo": "mcq",
  "enunciado": "(texto EXATO da prova aplicada)",
  "alternativas": ["A) ...", "B) ..."],
  "gabarito": "1",
  "dificuldade": 2,
  "origem_verificada": true,
  "banca": "Cebraspe",
  "orgao": "Polícia Federal",
  "concurso_prova": "PF Agente Administrativo 2021",
  "cargo": "Agente Administrativo",
  "ano_prova": 2021,
  "prova": "Caderno 577_PF_001_01",
  "numero_questao": "23",
  "url_prova": "https://cdn.cebraspe.org.br/concursos/PF_21/Provas/577_PF_001_01.pdf",
  "url_gabarito": "https://cebraspe.org.br/.../gabarito_definitivo.pdf",
  "gabarito_oficial": "1",
  "situacao": "valida",
  "classificacao_auditoria": "VERIFICADA_REAL",
  "verificacao": "correspondencia_textual_com_prova_original"
}
```
- `gabarito`/`gabarito_oficial` = índice 0-based da alternativa correta
  (string "0","1",...) para MCQ, ou "C"/"E" para certo/errado.
- Sem correspondência de todos os campos de proveniência, use
  `"situacao": "quarentena"` e preencha `motivo_quarentena` explicando o
  que falta — nunca force `"valida"`.

## Fluxo: corrigir discursivas pendentes
A plataforma marca `corrigido_por=null` para discursivas. O Hermes:
1. `GET /api/respostas/pendentes` → lista de respostas.
2. Para cada uma, comparar com a resposta/rubric oficiais da questão (se a
   banca publicou padrão de resposta, usar o padrão oficial; nunca inventar
   um critério novo).
3. `POST /api/bloco/responder/corrigir` com `{resposta_id, nota (0..1), feedback, correta}`.
4. A plataforma atualiza o progresso (dominância) do aluno.

## Nudge diário (cron do Hermes)
Se houver cron configurado para rodar diariamente, seu prompt deve:
1) logar como admin; 2) checar `topicos-selecao` para tópicos com lacuna;
3) pesquisar questões REAIS aplicadas para esses tópicos (nunca formular);
4) cadastrar apenas o que for comprovável, com `situacao='valida'` só
quando os metadados estiverem completos; 5) avisar o Eduardo no Telegram
com a lista de questões reais adicionadas (fonte de cada uma) e os
tópicos que continuam sem questão real disponível.

## Usuários demo
- admin / admin123 (role admin — cadastra conteúdo)
- aluno_pf / 123456, aluno_enf / 123456 (role aluno)

## Credenciais de API
- Token admin obtido via `POST /api/login` (admin/admin123).
- Guardar o token em memória ou passar inline nos comandos curl.

## Pitfalls
- **Nunca formular, adaptar ou parafrasear uma questão.** Se não achar a
  prova real, não cadastre nada para aquele tópico.
- **Mas não confunda isso com descartar questão real por causa do formato.**
  Não adaptar ≠ não aproveitar. Prova oficial com gabarito que tenha número
  de alternativas diferente do `n_alternativas` da trilha entra como está —
  ver passo 6 do fluxo de concurso específico.
- `gabarito` é índice numérico string, não a letra (exceto certo/errado).
- Edital/lei/manual/protocolo servem para *localizar o tópico*, nunca como
  fonte de uma questão.
- Sempre marcar `topicos_ids` para a cobertura do edital ser contabilizada
  — mas só depois de haver questão real válida no tópico.

## Fluxo: adicionar concurso específico (produção — Supabase/Postgres)

A plataforma em produção (Vercel + Supabase, projeto `supibsarclnlhsgjukrh`)
é distinta do backend FastAPI/SQLite descrito acima; o código-fonte do app
Vercel não está neste repositório. Lá, o Eduardo e a Laryssa têm duas
modalidades de estudo:

- **Geral**: as trilhas de base de cada um (`concurso_id=51` Eduardo,
  `concurso_id=52` Laryssa). NUNCA alterar o conteúdo dessas trilhas ao
  trabalhar em um concurso específico, a menos que peçam explicitamente.
- **Específico**: qualquer concurso público real que um dos dois pedir
  para estudar (ex.: EPTC Porto Alegre 2026 → `concurso_id=53`/`54`).

Desde a auditoria de 2026-09-15, **todas** as questões existentes em
`questoes` estão com `situacao='quarentena'` (nenhuma tinha comprovação de
origem real — ver `AUDITORIA_QUESTOES_REAIS.md`). A tabela tem uma
constraint (`chk_valida_exige_comprovacao`) e uma view de consumo seguro
(`questoes_verificadas`) que só expõe questões com
`origem_verificada=true AND situacao='valida' AND classificacao_auditoria='VERIFICADA_REAL'`.
**Qualquer código que sirva questões ao aluno deve ler dessa view, nunca da
tabela bruta.**

Passo a passo para repor questões reais em um concurso (usar
`mcp__Supabase__execute_sql`, projeto `supibsarclnlhsgjukrh`):

1. **Buscar a prova oficial já aplicada** (busca web: "\<banca\> \<órgão\>
   \<cargo\> prova aplicada PDF gabarito"). Se o concurso ainda não tiver
   prova aplicada (edital recém-publicado, prova futura), buscar provas
   reais **anteriores** da mesma banca para cargo/nível equivalente — é
   aceitável usar uma prova real de outro concurso da mesma família
   (regra 9 da auditoria: tópico > nível > cargo/área > banca >
   dificuldade), mas NUNCA formular uma questão nova "no estilo" da banca.
   - Se o WebFetch recusar por ser binário, ele salva o PDF localmente
     (`tool-results/webfetch-*.pdf`); usar `Read` nesse caminho extrai o
     texto completo, página a página.
2. **Confirmar/criar a linha em `concursos`**: nome, `edital_url`, `ano`,
   `tipo_prova`, `banca`, `n_alternativas`, `usa_certo_errado`,
   `tem_texto_base`, `estilo_enunciado`, `dificuldade_tipica`,
   `distribuicao_materias` (jsonb) — extraído do edital, nunca suposto.
3. **Criar/conferir uma linha em `fontes`** com `tipo='prova_referencia'`
   apontando para o PDF da prova real usada (não o edital) — essa é a
   `fonte_id` das questões novas.
   - Checar a sequência antes de inserir:
     `SELECT setval('fontes_id_seq', (SELECT MAX(id) FROM fontes));`
4. **Criar/conferir a árvore de `topicos`** (nomeados exatamente como o
   programa do edital). Reaproveitar tópicos já existentes.
5. **Criar um `blocos`** (`criado_por='hermes'`, `status='ativo'`).
6. **Cadastrar as `questoes`** transcritas literalmente da prova, com:
   `tipo`, `enunciado`, `alternativas` (jsonb, ordem A,B,C… da prova),
   `gabarito`, `explicacao` (opcional), `fonte_id`, `materia`, e **todos**
   os campos de proveniência: `origem_verificada=true`, `banca`, `orgao`,
   `concurso_prova`, `cargo`, `ano_prova`, `prova`, `numero_questao`,
   `pagina` (quando possível), `url_prova`, `url_gabarito`,
   `gabarito_oficial`, `situacao='valida'`,
   `classificacao_auditoria='VERIFICADA_REAL'`,
   `verificacao='correspondencia_textual_com_prova_original'`.
   - **A prova real manda no formato.** Transcreva a questão com o número de
     alternativas que ela tem. `n_alternativas` do concurso é referência de
     *preferência na busca* (procure primeiro provas no formato da banca-alvo),
     NUNCA critério de descarte: achou questão real, oficial, com gabarito,
     mas com 4 alternativas onde o alvo eram 5 (ou vice-versa)? **Cadastre
     como está.** Descartar questão real comprovada por causa da contagem de
     alternativas é perda pura — o banco já convive com formatos mistos.
     `n_alternativas = 0` significa "formato livre" (trilhas gerais 51/52).
     O que continua proibido é o oposto: adaptar, cortar ou acrescentar
     alternativa para a questão "caber" no formato — isso falsifica a fonte.
   - Se qualquer campo de proveniência não puder ser comprovado, usar
     `situacao='quarentena'` e preencher `motivo_quarentena` — o INSERT com
     `situacao='valida'` incompleto será **rejeitado pelo banco**
     (constraint `chk_valida_exige_comprovacao`).
7. **Validar antes de reportar pronto**:
   ```sql
   SELECT c.id, c.n_alternativas,
     count(*) FILTER (WHERE q.situacao='valida') AS validas,
     count(*) FILTER (WHERE q.situacao='valida' AND q.tipo='mcq'
       AND c.n_alternativas > 0
       AND jsonb_array_length(q.alternativas) <> c.n_alternativas) AS fora_do_formato_alvo
   FROM questoes q JOIN blocos b ON b.id=q.bloco_id JOIN concursos c ON c.id=b.concurso_id
   WHERE c.id = <concurso_id> GROUP BY c.id, c.n_alternativas;
   ```
   `fora_do_formato_alvo` é **informativo**, não erro: diz quanto do banco
   está no formato da banca-alvo, para orientar onde buscar mais provas
   daquela banca. Nunca remova nem "conserte" questão real por causa dele.
   Confirmar que nenhum `enunciado` novo duplica um já existente no banco.
8. **Nunca alterar dados de outros concursos** ao trabalhar em um específico.

### Bancas conhecidas (referência para priorizar a busca, não para descartar)
- Instituto Objetiva: 5 alternativas, `mcq` puro.
- Cebraspe: certo/errado (`usa_certo_errado=true`), sem alternativas múltiplas.
- FUNDATEC, FGV, IBFC e outras: não assumir padrão — cada edital define o
  próprio número de alternativas e estilo de enunciado.

Use esta tabela para escolher **por onde começar** a procurar prova real.
Esgotada a banca-alvo, prova real de outra banca para o mesmo tópico/nível
vale mais do que tópico vazio (regra 9 da auditoria) — cadastre no formato
original dela e registre a banca de origem em `banca`.

### Concorrência
O banco Supabase de produção é editado por múltiplos agentes em paralelo —
já observados em `blocos.criado_por`: `'chatgpt'`, `'auditoria'`, `'hermes'`.
Antes de inserir, sempre reconferir o estado atual (tópicos/blocos podem já
ter sido criados por outro agente) para não duplicar conteúdo, e checar as
sequências (`fontes_id_seq` e afins) se acontecer erro de chave duplicada.

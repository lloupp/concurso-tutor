# Auditoria de Questões Reais — 2026-09-15

Auditoria completa do projeto `concurso-tutor` para eliminar questões
inventadas/autorais/adaptadas/parafraseadas e substituí-las por questões
efetivamente aplicadas em provas de concurso reais, com origem comprovável.

## Resumo executivo

| Métrica | Valor |
|---|---|
| Total de questões auditadas (banco de produção Supabase) | **1689** |
| Classificadas VERIFICADA_REAL (já existentes antes da auditoria) | **0** |
| Classificadas AUTORAL_INVENTADA | **1243** |
| Classificadas ORIGEM_INCONSISTENTE | **446** |
| Classificadas ADAPTADA | 0 |
| Classificadas NAO_COMPROVADA (residual) | 0 (absorvidas nas duas classes acima — ver metodologia) |
| Questões colocadas em quarentena (`situacao='quarentena'`) | **1689** |
| Questões estáticas (GitHub Pages, `docs/data/*.json`) removidas | **60** |
| Arquivos de payload fabricados removidos do repositório (`bloco*.json`) | **10** |
| Questões reais novas inseridas nesta sessão (`VERIFICADA_REAL`, `situacao='valida'`) | **12** |
| Total ainda pendente de substituição por questão real | **1689** |
| Provas reais usadas como fonte das questões novas | **1** (Cebraspe PF Agente Administrativo 2025) |

**Conclusão da auditoria: 0% das 1689 questões pré-existentes no banco de
produção tinham origem comprovada em prova real aplicada.** Todas foram
colocadas em quarentena. Um lote inicial de 12 questões reais, com
comprovação completa, foi inserido para demonstrar e validar o novo fluxo
— mas a reposição integral (idealmente cobrindo os mesmos tópicos das 1689
quarentenadas) é um trabalho de pesquisa que não cabe em uma única sessão e
continua pendente. **Não declaro esta auditoria "concluída"**: ela deixou
a plataforma tecnicamente incapaz de servir questão sem comprovação, mas a
reposição de conteúdo real segue em aberto (ver "Pendências").

## 1. Onde questões foram auditadas

- **Banco de produção (Supabase, projeto `supibsarclnlhsgjukrh`, tabela
  `public.questoes`)**: 1689 linhas, único repositório real de conteúdo
  usado pelos alunos (Eduardo e Laryssa) na plataforma Vercel. Todas
  auditadas.
- **`docs/data/*.json`** (6 arquivos, simulado estático publicado em
  GitHub Pages): 60 questões, nenhuma com campo `fonte` preenchido.
- **`bloco*.json`** (10 arquivos na raiz do repo): payloads de exemplo do
  fluxo de geração por IA já deprecado (`grok_populate_prompt.md`).
- **`backend/data/concurso.db`** (SQLite local, não versionado): banco de
  demonstração/dev, 30 questões fictícias — não serve alunos reais.
- **Seeds**: `backend/seed.py` (demo, 10 questões fictícias) e
  `backend/seed_poa_regiao.py` (~30 questões formuladas manualmente,
  `criado_por="hermes"`).
- **Skills/prompts**: `skills/tutor-concurso/SKILL.md` e
  `grok_populate_prompt.md` — ambos instruíam uma IA a **formular**
  questões ancoradas em pesquisa geral (não em provas aplicadas).
- **Migrations**: não havia migrations com conteúdo de questões — o
  histórico (`list_migrations` do Supabase) só tem alterações de schema.

Nenhuma questão com `fonte_id` apontando exclusivamente para lei/edital/
manual/protocolo foi aceita como comprovação de origem (regra 2).

## 2. Metodologia de classificação

Cada uma das 1689 questões pré-existentes tinha `fonte_id` preenchido
(`com_fonte=1689`, `sem_fonte=0`), mas a tabela `fontes` (62 linhas) é
composta quase inteiramente por documentos genéricos:

| tipo de fonte | quantidade |
|---|---|
| legislacao | 33 |
| manual | 10 |
| protocolo | 8 |
| edital | 5 |
| norma | 3 |
| estatuto | 1 |
| referencia | 1 |
| **prova_referencia** | **1** |

Apenas **1 fonte em 62** era uma prova real aplicada (um caderno Cebraspe
PF 2021, cuja URL cadastrada — `.../PF_21/Provas/577_PF_001_01.pdf` —
está **morta/404**, confirmado nesta auditoria). Mesmo as questões que
citam essa fonte são paráfrases genéricas (ex.: id 14, "Se A>B e B>C,
então:" — um enunciado de lógica genérico, não uma transcrição de item
real), sem número de questão, página ou gabarito oficial associados.

Classificação aplicada (via SQL, com base em `blocos.criado_por` e
`fontes.tipo`, já que a ausência de comprovação é estrutural e vale para
o lote inteiro, não caso a caso):

- **AUTORAL_INVENTADA** (1243): fonte do tipo edital/lei/manual/protocolo/
  norma/estatuto/referência — formulada por processo editorial/IA
  (`criado_por` ∈ {hermes, revisao-editorial-balanceado, auditoria-legalle,
  auditoria-conteudo, implantacao-alvorada, chatgpt-auditoria, auditoria,
  chatgpt, curadoria}). Nenhuma é extraída de uma prova aplicada.
- **ORIGEM_INCONSISTENTE** (446): fonte do tipo `prova_referencia`
  (aponta para uma prova real), mas o texto foi formulado/parafraseado
  pelo mesmo processo editorial, sem número/página/gabarito oficial
  confirmados — viola a regra 8 ("texto não existir na prova indicada").
- **VERIFICADA_REAL** (0 pré-existentes / 12 novas): nenhuma questão
  pré-existente atendia ao critério; as 12 novas foram transcritas
  literalmente de uma prova real com todos os metadados comprovados.

Um sinal adicional de que o processo nunca extraía questões reais: a
própria tabela tinha uma coluna `banca_estilo` (não `banca`) — nome que já
admite ser uma aproximação de estilo, não a banca real de uma prova
aplicada. Isso está agora coberto por teste de regressão.

## 3. Bloqueio técnico implementado (regra 7)

Como o código-fonte do app de produção (Vercel) **não está neste
repositório** — só o Supabase e este backend FastAPI/SQLite local estão
acessíveis — o bloqueio foi implementado na camada mais forte possível: o
próprio banco de dados, para valer independentemente de qual aplicação
(atual ou futura) leia a tabela.

**Migrations aplicadas no Supabase** (`supibsarclnlhsgjukrh`):
1. `provenance_schema_questoes` — adiciona a `questoes`: `origem_verificada`,
   `banca`, `orgao`, `concurso_prova`, `cargo`, `ano_prova`, `prova`,
   `numero_questao`, `pagina`, `url_prova`, `url_gabarito`,
   `gabarito_oficial`, `situacao`, `verificacao`, `classificacao_auditoria`,
   `motivo_quarentena`; constraints `chk_situacao_valores`,
   `chk_classificacao_valores` e, principal, **`chk_valida_exige_comprovacao`**
   — impede `UPDATE`/`INSERT` com `situacao='valida'` a menos que
   `origem_verificada=true`, `classificacao_auditoria='VERIFICADA_REAL'` e
   banca/órgão/concurso/cargo/ano/prova/número/URL da prova/gabarito
   oficial estejam todos preenchidos. **Testado e confirmado**: um INSERT
   de sanity-check com `situacao='valida'` sem metadados foi rejeitado
   pelo Postgres (`ERRO 23514`).
2. Alteração de `verificacao` para `varchar(200)` (o valor descritivo não
   cabia em 60 chars).
3. UPDATE em massa: todas as 1689 questões pré-existentes →
   `origem_verificada=false`, `situacao='quarentena'`, classificação e
   `motivo_quarentena` preenchidos (texto específico por classe, citando
   `criado_por` e a fonte original).
4. `questoes_verificadas_view` — view `questoes_verificadas` (só expõe
   `origem_verificada=true AND situacao='valida' AND
   classificacao_auditoria='VERIFICADA_REAL'`) como única fonte seura de
   leitura para qualquer app.

**Limitação registrada**: as políticas RLS atuais (`deny_api_roles`)
bloqueiam totalmente as chaves `anon`/`authenticated` — ou seja, o app de
produção já lê via `service_role`, que **ignora RLS**. Isso significa que
o bloqueio efetivo depende de o código do app (fora deste repositório)
consultar a view `questoes_verificadas` em vez da tabela bruta. Isso está
documentado em `skills/tutor-concurso/SKILL.md` e deve ser corrigido no
repositório do frontend Vercel, que esta sessão não tinha acesso para
alterar.

**Backend FastAPI/SQLite local** (`backend/app/models.py`,
`backend/app/main.py`): mesmo schema replicado via `CheckConstraint`
(`chk_valida_exige_comprovacao`); `_bloco_out()` agora só retorna questões
com `origem_verificada=True AND situacao='valida'`; `/api/bloco/gerar`
rejeita (HTTP 400) qualquer questão com `situacao='valida'` sem todos os
campos de comprovação.

## 4. Prompts/skills que instruíam geração de questões (regra 7)

- `grok_populate_prompt.md`: continha um prompt completo pedindo a uma IA
  para **formular** 40 questões "ancoradas" no conteúdo programático.
  Marcado `DEPRECADO`, conteúdo original preservado só como registro
  histórico do que não fazer mais.
- `skills/tutor-concurso/SKILL.md`: reescrita completa. Antes: "O Hermes
  faz a curadoria e a **formulação** das questões". Agora: "O Hermes NUNCA
  formula, gera, cria, adapta, parafraseia ou escreve questões". O fluxo
  passou de "gerar bloco" para "buscar/recuperar questões reais", com
  passo a passo de comprovação (banca, órgão, concurso, cargo, ano, prova,
  número, URL, gabarito oficial) e menção explícita à constraint do banco.
- `README.md`: removida a afirmação falsa "Conteúdo NUNCA é inventado" (a
  auditoria mostrou que era 100% inventado/inconsistente) e a descrição do
  simulado como "questões no estilo de concursos públicos".
- `backend/seed_poa_regiao.py`: mantido (é aditivo, só roda contra SQLite
  local), mas com aviso explícito de que suas ~30 questões fictícias nunca
  devem ser marcadas `valida`.

## 5. Conteúdo estático removido (`docs/`, GitHub Pages)

`docs/data/*.json` (Português, Matemática, Informática, Direito
Constitucional, Direito Administrativo, Atualidades) tinham 60 questões
sem nenhum campo de fonte. Todas removidas — arquivos ficaram
`{"materia": "...", "questoes": []}`. `docs/app.js` foi ajustado para
mostrar um aviso claro em vez de quebrar com banco vazio.
`docs/CONTRIBUINDO.md` foi reescrito com a mesma regra absoluta (só
questão real, com `fonte` estruturada obrigatória — banca, órgão,
concurso, ano, prova, número, URL, gabarito oficial).

## 6. Questões reais inseridas nesta sessão

Fonte usada: **Cebraspe, Concurso Público PF — Provimento de Vagas e
Formação de Cadastro de Reserva, Edital nº 1 – PF – Administrativo (25/04/
2025), aplicação em 29/06/2025**, caderno de **Conhecimentos Básicos para
o cargo de nível médio (094_PF_CB2_01)**, cargo Agente Administrativo —
exatamente o cargo/banca/ano já configurados na trilha `concurso_id=51`.

- Prova: https://cdn.cebraspe.org.br/concursos/pf_25_adm/arquivos/094_PF_CB2_01.pdf
- Gabarito oficial definitivo: https://cdn.cebraspe.org.br/concursos/pf_25_adm/arquivos/Gab_Definitivo_094_PF_CB2_01.pdf
- Texto e gabarito extraídos diretamente do PDF oficial (via leitura do
  arquivo, não resumo) e conferidos item a item.

12 itens certo/errado transcritos literalmente (enunciado e, quando
aplicável, texto-base), cobrindo Português, Raciocínio Lógico, Ética no
Serviço Público, Direito Administrativo e Informática — os mesmos tópicos
mais cobertos pelas questões agora quarentenadas dessa trilha.

| ID antiga (exemplo quarentenado no mesmo tópico) | Status antigo | Motivo | Nova questão (id) | Banca | Concurso | Ano | Prova | Nº | Gabarito |
|---|---|---|---|---|---|---|---|---|---|
| 12 | AUTORAL_INVENTADA | Formulada, fonte=lei/edital, sem prova real | 2096 | Cebraspe | PF Administrativo | 2025 | 094_PF_CB2_01 | 1 | E |
| 12 | AUTORAL_INVENTADA | idem | 2097 | Cebraspe | PF Administrativo | 2025 | 094_PF_CB2_01 | 4 | E |
| 14 | ORIGEM_INCONSISTENTE | Fonte prova_referencia, mas parafraseada | 2098 | Cebraspe | PF Administrativo | 2025 | 094_PF_CB2_01 | 21 | C |
| 14 | ORIGEM_INCONSISTENTE | idem | 2099 | Cebraspe | PF Administrativo | 2025 | 094_PF_CB2_01 | 22 | E |
| 14 | ORIGEM_INCONSISTENTE | idem | 2100 | Cebraspe | PF Administrativo | 2025 | 094_PF_CB2_01 | 23 | E |
| 1023 | AUTORAL_INVENTADA | Formulada, fonte=protocolo/manual | 2101 | Cebraspe | PF Administrativo | 2025 | 094_PF_CB2_01 | 27 | C |
| 1023 | AUTORAL_INVENTADA | idem | 2102 | Cebraspe | PF Administrativo | 2025 | 094_PF_CB2_01 | 30 | C |
| 16 | AUTORAL_INVENTADA | Formulada, fonte=lei | 2103 | Cebraspe | PF Administrativo | 2025 | 094_PF_CB2_01 | 33 | C |
| 16 | AUTORAL_INVENTADA | idem | 2104 | Cebraspe | PF Administrativo | 2025 | 094_PF_CB2_01 | 36 | C |
| 18 | AUTORAL_INVENTADA | Formulada, fonte=lei/edital | 2105 | Cebraspe | PF Administrativo | 2025 | 094_PF_CB2_01 | 41 | C |
| 18 | AUTORAL_INVENTADA | idem | 2106 | Cebraspe | PF Administrativo | 2025 | 094_PF_CB2_01 | 44 | C |
| 18 | AUTORAL_INVENTADA | idem | 2107 | Cebraspe | PF Administrativo | 2025 | 094_PF_CB2_01 | 50 | E |

> Nota: a "ID antiga" é ilustrativa (uma questão quarentenada representativa
> do mesmo tópico) — as 1689 questões antigas continuam em quarentena
> (preservadas no banco, não apagadas), não foram substituídas 1:1. As 12
> novas são adições comprovadas, não trocas automáticas.

## 7. Inconsistências de origem encontradas

- URL da única fonte `prova_referencia` pré-existente (PF Cebraspe 2021)
  está morta (HTTP 404) — nunca foi de fato conferida contra a prova.
- Campo `banca_estilo` sendo usado no lugar de uma banca real comprovada
  em centenas de questões.
- `blocos.criado_por` só tem valores de processo editorial/IA (`hermes`,
  `chatgpt`, `auditoria*`, `revisao-editorial-balanceado`,
  `implantacao-alvorada`, `curadoria`) — nenhum valor indica "extraído da
  prova X".
- README afirmava "Conteúdo NUNCA é inventado" enquanto 100% das questões
  auditadas eram, na melhor hipótese, ancoradas em fontes genéricas.

## 8. Testes automatizados (regra 11)

`backend/tests/test_auditoria_questoes_reais.py` (novo) +
atualizações em `backend/tests/test_main.py`. Total: **88 testes, todos
passando** (`python3 -m pytest backend/tests/ -q`). Cobrem:

- Rejeição pelo banco (constraint) de questão `valida` sem qualquer um
  dos metadados obrigatórios, mesmo com o resto completo.
- Questão nova sem metadados cai em `quarentena` por padrão.
- `/api/bloco/gerar` rejeita (400) questão `valida` sem comprovação e
  aceita quando a comprovação está completa.
- `/api/bloco/hoje` nunca expõe questão não verificada, mesmo que exista
  no mesmo bloco de uma verificada.
- `docs/data/*.json` não pode conter questão sem campo `fonte`.
- `skills/tutor-concurso/SKILL.md` contém a regra absoluta e não contém
  frases que voltem a instruir formulação ("formule a questão", "crie as
  questões", "invente"...).
- `grok_populate_prompt.md` começa com aviso de depreciação.

No Supabase, a constraint `chk_valida_exige_comprovacao` foi testada
diretamente com um INSERT de sanity-check (rejeitado com sucesso) — é a
proteção mais forte porque vale para qualquer agente/processo que escreva
na tabela no futuro, não só para este backend.

## 9. Mudanças no código (resumo)

- `backend/app/models.py`, `backend/app/main.py`, `backend/seed.py`,
  `backend/seed_poa_regiao.py`, `backend/tests/test_main.py`,
  `backend/tests/test_auditoria_questoes_reais.py` (novo)
- `skills/tutor-concurso/SKILL.md`, `grok_populate_prompt.md`, `README.md`
- `docs/app.js`, `docs/CONTRIBUINDO.md`, `docs/data/*.json` (6 arquivos)
- Removidos: `bloco1_enf.json`, `bloco1_pericia.json`, `bloco1_pf.json`,
  `bloco2_enf.json`, `bloco2_pericia.json`, `bloco2_pf.json`,
  `bloco3_enf.json`, `bloco3_pericia.json`, `bloco4_enf.json`,
  `bloco4_pf.json`

## 10. Pendências (SEM_QUESTAO_REAL_LOCALIZADA / não executado)

- **1689 questões continuam em quarentena** sem substituto real. Cobrem 6
  trilhas: PF Agente Administrativo (580), Técnico em Enfermagem (600),
  EPTC Porto Alegre — Nível Médio (111), EPTC — Enfermagem do Trabalho
  (156), Alvorada — Técnico em Enfermagem (121), Alvorada — Auxiliar
  Administrativo (121). Nenhuma tem questão real de reposição ainda,
  exceto as 12 novas na trilha PF (id 51).
- Sourcing de questões reais para Enfermagem, EPTC e Alvorada não foi
  feito nesta sessão — não foram localizadas (nem buscadas
  exaustivamente) provas aplicadas correspondentes. Registrar como
  `SEM_QUESTAO_REAL_LOCALIZADA` até que alguém (Hermes, seguindo o novo
  fluxo do SKILL.md, ou Eduardo) faça essa busca.
- O código do app Vercel de produção (que efetivamente renderiza questões
  para Eduardo/Laryssa) não está neste repositório e não pôde ser alterado
  para consumir `questoes_verificadas` — isso precisa ser feito no
  repositório correto para o bloqueio ter efeito visível na UI real.
- `backend/data/concurso.db` (SQLite local) não foi migrado com o novo
  schema além de ter sido apagado e recriado vazio na raiz do teste; ele é
  regenerado automaticamente na próxima execução do backend/seed.

**A auditoria não está concluída** no sentido do "quality bar" definido na
missão (100% das questões exibidas com origem comprovada) — ela deixou o
sistema **incapaz de exibir** questão sem comprovação (bloqueio técnico
ativo e testado) e substituiu uma primeira fração real, mas a reposição de
conteúdo para as ~1689 questões quarentenadas é trabalho contínuo.

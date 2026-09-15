# MISSÃO: buscar e cadastrar QUESTÕES REAIS no concurso-tutor

> Prompt operacional para o agente (Hermes/Pi/outro) que vai repor o banco de
> questões após a auditoria de 2026-09-15. Cole o conteúdo abaixo como
> instrução do agente, ou peça para ele ler este arquivo do repositório.

Você vai repor o banco de questões da plataforma `concurso-tutor` com questões
**efetivamente aplicadas em provas de concurso público reais**.

## REGRA ABSOLUTA — leia antes de qualquer coisa

**É PROIBIDO gerar, formular, criar, adaptar, parafrasear, "melhorar" ou
escrever questões "no estilo" de uma banca.** Você é um BUSCADOR de questões
reais, não um autor.

Em 2026-09-15 uma auditoria (ver `AUDITORIA_QUESTOES_REAIS.md` neste
repositório) descobriu que TODAS as 1689 questões do banco tinham sido
formuladas por IA ancoradas em editais/leis/manuais — nenhuma vinha de uma
prova aplicada. Todas foram colocadas em quarentena. Não repita esse erro:
uma questão com fatos corretos, citando a lei certa, AINDA É INVENTADA se não
for a transcrição de um item que caiu numa prova real.

Se não achar questão real para um tópico: **não cadastre nada nesse tópico.**
Ficar com menos questões é o resultado desejado. Inventar é falha total.

**Atenção — não confunda "não adaptar" com "não aproveitar".** Esta regra
proíbe você de *criar ou alterar* questão. Ela NÃO manda descartar questão
real que você já encontrou. Se a prova é oficial e tem gabarito definitivo, a
questão entra — mesmo que o número de alternativas, a banca ou o ano sejam
diferentes do que a trilha pedia. Ver "Convenções de gabarito" adiante.

## Acesso

- Supabase MCP, project_id: `supibsarclnlhsgjukrh` (`mcp__Supabase__execute_sql`).
- Tabelas: `concursos` → `topicos` / `blocos` → `questoes`, mais `fontes`.

## Estado atual (pós-auditoria)

| concurso_id | Trilha | Banca | Formato | Em quarentena | Válidas |
|---|---|---|---|---|---|
| 51 | PF Agente Administrativo | Cebraspe | Certo/Errado (`usa_certo_errado=true`) | 580 | 12 |
| 52 | Técnico em Enfermagem | (genérica) | MCQ, **formato livre** (`n_alternativas=0`) | 600 | 0 |
| 53 | EPTC Porto Alegre 2026 — Nível Médio | Instituto Objetiva | MCQ, 5 alternativas | 111 | 0 |
| 54 | EPTC 2026 — Téc. Enfermagem do Trabalho | Instituto Objetiva | MCQ, 5 alternativas | 156 | 0 |
| 55 | Alvorada 2026 — Técnico em Enfermagem | Instituto Legalle | MCQ, 5 alternativas | 121 | 0 |
| 56 | Alvorada 2026 — Auxiliar Administrativo | Instituto Legalle | MCQ, 5 alternativas | 121 | 0 |

Prioridade: **52 (Laryssa) e 51 (Eduardo)** primeiro — são as trilhas em uso
diário. Depois 53–56.

Meta realista: 20–40 questões reais por trilha. Qualidade > quantidade.

Liste os tópicos de cada trilha antes de começar:
```sql
SELECT id, nome FROM topicos WHERE concurso_id = <ID> ORDER BY ordem, id;
```

## O que conta como comprovação de origem

Só cadastre com `situacao='valida'` se você tiver TODOS estes dados **daquela
questão específica**:

banca · órgão · concurso/edição · cargo · ano · caderno/prova · número da
questão · URL do PDF da prova · gabarito oficial **definitivo** (pós-recursos).

**NÃO são prova de origem:** lei, edital, manual, protocolo, norma, apostila,
site de cursinho, resumo, blog. Eles mostram que o assunto cai — não que a
questão existe.

## Onde procurar (por banca)

- **Cebraspe (51):** `https://cdn.cebraspe.org.br/concursos/<slug>/arquivos/`
  — padrão `<CODIGO>_CB2_01.pdf` (caderno) e `Gab_Definitivo_<CODIGO>.pdf`.
  Já usado: `pf_25_adm` (caderno `094_PF_CB2_01`, itens 1–50, aplicada
  29/06/2025). Itens 1–50 já foram parcialmente aproveitados (itens 1, 4, 21,
  22, 23, 27, 30, 33, 36, 41, 44, 50 já estão no banco — **não duplicar**).
  Os itens restantes desse mesmo caderno são material real disponível.
  Outras edições PF/PRF têm slugs análogos (`pf_21`, `prf_21`…).
- **Instituto Objetiva (53, 54):** site da banca publica provas e gabaritos de
  concursos encerrados — procure "Instituto Objetiva prova gabarito <órgão>
  <cargo> PDF".
- **Instituto Legalle (55, 56):** idem, `institutolegalle.com.br`.
- **Enfermagem (52):** a banca cadastrada é genérica ("Conselho/Autarquia").
  Use provas REAIS de qualquer banca que aplique concurso de Técnico em
  Enfermagem (FUNDATEC, Objetiva, Legalle, IBFC, FGV, AOCP, Instituto Mais…)
  e **registre a banca real da prova usada**, não "Conselho/Autarquia".
- pciconcursos / qconcursos hospedam provas, mas o download costuma ser
  bloqueado por verificação. **Prefira sempre o CDN da própria banca.**

### ⚠ Provas de 2026 podem não existir ainda

EPTC 2026 e Alvorada 2026 provavelmente ainda não foram aplicadas. Nesse caso
**use provas reais ANTERIORES da mesma banca** para cargo/nível equivalente —
e nos metadados registre **o concurso real de onde a questão saiu** (ex.:
"Prefeitura de X 2023 — Instituto Objetiva"), NUNCA "EPTC 2026". A questão
continua sendo VERIFICADA_REAL; o que não pode é mentir a procedência.

## Como ler os PDFs (importante)

`WebFetch` **não consegue** converter PDF binário — ele devolve lixo, mas
**salva o arquivo localmente** e mostra o caminho. Extraia assim:

```bash
python3 -c "
import fitz
doc = fitz.open('<caminho_salvo>.pdf')
for i in range(len(doc)):
    print(f'--- page {i+1} ---'); print(doc[i].get_text())
"
```

Leia o caderno **e** o gabarito definitivo. Confira item por item.

## Como cadastrar

**1. Crie a fonte** (uma por prova usada), sincronizando a sequência antes:

```sql
SELECT setval('fontes_id_seq', (SELECT MAX(id) FROM fontes));

INSERT INTO fontes (titulo, url, tipo, orgao, ano)
VALUES ('<Descrição da prova: banca, órgão, cargo, ano, caderno, data de aplicação>',
        '<URL do PDF da prova>', 'prova_referencia', '<Banca>', <ano>)
RETURNING id;
```

**2. Crie um bloco** por prova/trilha:

```sql
INSERT INTO blocos (concurso_id, titulo, introducao, duracao_min, criado_por, status)
VALUES (<concurso_id>, 'Questões reais verificadas — <banca> <órgão> <ano>',
        '<origem do lote>', 60, 'busca-questoes-reais', 'ativo')
RETURNING id;
```

**3. Insira cada questão** com proveniência completa:

```sql
INSERT INTO questoes (
  bloco_id, topico_id, tipo, enunciado, texto_base, alternativas, gabarito,
  dificuldade, fonte_id, materia,
  origem_verificada, banca, orgao, concurso_prova, cargo, ano_prova, prova,
  numero_questao, pagina, url_prova, url_gabarito, gabarito_oficial,
  situacao, verificacao, classificacao_auditoria
) VALUES (
  <bloco_id>, <topico_id>, 'mcq',
  '<enunciado LITERAL da prova>',
  '<texto-base literal, ou NULL>',
  '["<alt A literal>","<alt B>","<alt C>","<alt D>","<alt E>"]'::jsonb,
  '<índice 0-based da correta>',
  2, <fonte_id>, '<matéria>',
  true, '<Banca>', '<Órgão>', '<Concurso/edição>', '<Cargo>', <ano>,
  '<nome/código do caderno>', '<nº da questão>', <página ou NULL>,
  '<url da prova>', '<url do gabarito definitivo>', '<gabarito oficial: A/B/C/D/E ou C/E>',
  'valida', 'correspondencia_textual_com_prova_original', 'VERIFICADA_REAL'
);
```

### Convenções de gabarito
- `tipo='mcq'` → `gabarito` = índice 0-based **string**: `"0"`=A, `"1"`=B, …
- `tipo='verdadeiro_falso'` (Cebraspe C/E) → `gabarito` = `'true'` (Certo) ou
  `'false'` (Errado); `alternativas` fica NULL.
- `gabarito_oficial` guarda a letra/sigla **como está no gabarito da banca**
  (`A`…`E`, ou `C`/`E`).
- **O formato da prova real manda — `n_alternativas` NUNCA descarta questão.**
  Transcreva a questão com o número de alternativas que ela tem. O
  `n_alternativas` da trilha serve para você **priorizar a busca** (comece
  pelas provas da banca-alvo), não para filtrar o que já encontrou. Achou
  questão real, oficial, com gabarito definitivo, mas com 5 alternativas onde
  a trilha dizia 4 (ou o contrário)? **Cadastre como está.** O banco convive
  com formatos mistos e a trilha 52 está com `n_alternativas=0` (livre).
  O proibido continua sendo o oposto: cortar, acrescentar ou remanejar
  alternativa para a questão "caber" no formato — isso falsifica a prova.
  Descartar questão real comprovada por causa da contagem de alternativas é
  perda pura e **não é o comportamento desejado**.

### Bloqueio técnico — não tente contornar
A tabela tem a constraint `chk_valida_exige_comprovacao`: qualquer INSERT com
`situacao='valida'` faltando banca, órgão, concurso_prova, cargo, ano_prova,
prova, numero_questao, url_prova, gabarito_oficial, `origem_verificada=true`
ou `classificacao_auditoria='VERIFICADA_REAL'` é **rejeitado pelo Postgres**
(erro 23514). Se bater nesse erro, é porque falta comprovação: vá buscar o
dado que falta ou não cadastre a questão. **Nunca** preencha um campo com
valor inventado/aproximado só para o INSERT passar.

## Fidelidade obrigatória

Transcreva **exatamente** como está na prova: enunciado, texto-base,
alternativas e a ordem delas, itens C/E, números, unidades, nomes, observações
da banca. **Não corrija o português da banca, não simplifique, não modernize,
não reordene.** Só normalização técnica (encoding, espaço duplo) é permitida.

- Questão **anulada** no gabarito definitivo (marcada `X`): não cadastre como
  válida — pule e registre no relatório.
- Questão que depende de imagem/tabela/gráfico que você não consegue
  reproduzir: pule e registre. Não descreva a imagem com palavras suas.
- Antes de inserir, cheque duplicata:
  `SELECT id FROM questoes WHERE enunciado = '<texto>';`

## O que NÃO fazer

- Não altere, reative ou apague as questões em quarentena — elas ficam como
  registro histórico.
- Não mexa em dados de outras trilhas ao trabalhar em uma.
- Não use o campo legado `banca_estilo` como se fosse a banca real.
- Não preencha `explicacao` com justificativa inventada; deixe NULL se a banca
  não publicou padrão de resposta.

## Validação antes de reportar

```sql
SELECT c.id, c.nome, c.n_alternativas,
       count(*) FILTER (WHERE q.situacao='valida') AS validas,
       count(*) FILTER (WHERE q.situacao='valida' AND q.tipo='mcq'
         AND c.n_alternativas > 0
         AND jsonb_array_length(q.alternativas) <> c.n_alternativas) AS fora_do_formato_alvo,
       count(*) FILTER (WHERE q.situacao='valida' AND q.tipo='mcq'
         AND (q.gabarito::int < 0 OR q.gabarito::int >= jsonb_array_length(q.alternativas))) AS gabarito_fora
FROM questoes q
JOIN blocos b ON b.id=q.bloco_id
JOIN concursos c ON c.id=b.concurso_id
GROUP BY c.id, c.nome, c.n_alternativas ORDER BY c.id;

SELECT count(*) FROM questoes_verificadas;
```
`gabarito_fora` deve ser 0 — é erro real (gabarito apontando para alternativa
inexistente). Já `fora_do_formato_alvo` é apenas **informativo**: mostra
quantas questões reais vieram em formato diferente do da banca-alvo, para você
saber onde ainda vale procurar mais provas daquela banca. **Não é erro e não
deve ser "corrigido"** — nunca apague nem altere questão real por causa dele.

## Relatório final (obrigatório)

1. Por trilha: quantas questões reais foram cadastradas e de quais provas.
2. Lista das provas usadas (banca, órgão, cargo, ano, caderno, URL da prova,
   URL do gabarito).
3. Tabela: trilha | tópico | nº da questão | banca | prova | gabarito oficial.
4. Tópicos onde **não** foi localizada questão real → marque
   `SEM_QUESTAO_REAL_LOCALIZADA` e explique o que você tentou.
5. Itens pulados (anulados, dependentes de imagem, duplicados) com o motivo.
6. Confirmação explícita: "não formulei, adaptei nem parafraseei nenhuma
   questão; todas são transcrições de provas aplicadas".

---
name: tutor-concurso
description: Gera blocos de estudo diários para a plataforma concurso-tutor a partir do edital (com pesquisa real, sem invenção) e corrige questões discursivas. Use quando Eduardo pedir para criar conteúdo/exercícios para os alunos de concurso, ou para corrigir discursivas pendentes.
---

# Tutor de Concurso (skill do Hermes)

Esta skill conecta o Hermes à plataforma `concurso-tutor` (FastAPI + SQLite + web).
O Hermes é o "professor": gera o bloco do dia (mini-aula + 10 questões mistas) com
base no edital real e corrige as discursivas que a plataforma não consegue sozinha.

## Princípio central
CONTEÚDO NUNCA INVENTADO. Tudo vem do edital ou de pesquisa (web/PDF). O Hermes faz
a curadoria e a formulação das questões, mas a matéria é ancorada na fonte.

## Fluxo: gerar bloco diário
1. Identificar concurso (PF Agente Admin → concurso_id X; Téc. Enfermagem → Y).
   - Listar concursos: `GET /api/admin/concurso` (ou consultar DB).
2. Pegar tópicos pendentes do plano:
   - `GET /api/plano` (como admin) → próximos tópicos por aluno.
   OU usar a lógica do `planner.py`: prioriza não-estudados (cobertura 100%) e
   vencidos para revisão espaçada; tópicos fracos têm prioridade.
3. Buscar fonte do edital:
   - Se houver `edital_url`/`edital_text` no concurso, usar como base.
   - Senão, pesquisar na web os tópicos (ex.: "Direito Administrativo princípios
     Cebraspe agente administrativo PF"). Usar web_search / navegação real.
4. Montar o bloco JSON no formato abaixo e enviar:
   - `POST /api/bloco/gerar` (header `Authorization: Bearer <token_admin>`)
   - Body: `{"concurso_id": ID, "bloco": {...}}`

### Formato BlocoSchema
```json
{
  "concurso_id": 1,
  "bloco": {
    "titulo": "Português + Raciocínio Lógico (dia 3)",
    "introducao": "Mini-aula de 1h. 10 questões: 7 MCQ + 3 discursivas.",
    "duracao_min": 60,
    "topicos_ids": [11, 12],
    "questoes": [
      {"topico_id": 11, "tipo": "mcq", "enunciado": "...",
       "alternativas": ["A) ...", "B) ..."], "gabarito": "1", "dificuldade": 2},
      {"topico_id": 12, "tipo": "discursiva", "enunciado": "...",
       "resposta_modelo": "Resposta correta resumida...",
       "rubric": "Critérios: citar X, Y, Z", "dificuldade": 3}
    ]
  }
}
```
- 10 questões por bloco (padrão: 7 mcq + 3 discursiva), ajustável.
- `gabarito` = índice 0-based da alternativa correta (string "0","1",...).
- `resposta_modelo` + `rubric` dão à plataforma o padrão de correção da discursiva.

## Fluxo: corrigir discursivas pendentes
A plataforma marca `corrigido_por=null` para discursivas. O Hermes:
1. `GET /api/respostas/pendentes` (endpoint a criar) → lista de respostas.
2. Para cada uma, comparar com `resposta_modelo`+`rubric` da questão.
3. `POST /api/bloco/responder/corrigir` com `{resposta_id, nota (0..1), feedback, correta}`.
4. A plataforma atualiza o progresso (dominância) do aluno.

## Nudge diário (cron)
Criar cron no Hermes para, todo dia às 07:00, gerar o bloco de cada aluno e enviar
um lembrete no Telegram (assíncrono). Exemplo de prompt do cron:
"Gere o bloco de hoje para o aluno PF (concurso_id=1) via skill tutor-concurso
e avise o Eduardo no Telegram que está pronto."

## Usuários demo
- admin / admin123 (role admin — gera conteúdo)
- aluno_pf / 123456, aluno_enf / 123456 (role aluno)

## Credenciais de API
- Token admin obtido via `POST /api/login` (admin/admin123).
- Guardar o token em memória ou passar inline nos comandos curl.

## Pitfalls
- NÃO inventar fatos jurídicos/médicos: ancore no edital/pesquisa real.
- `gabarito` é índice numérico string, não a letra.
- Sempre marcar `topicos_ids` para a cobertura de 100% do edital ser contabilizada.
- Bloco sem `topicos_ids` não conta como "estudado" no heatmap de cobertura.

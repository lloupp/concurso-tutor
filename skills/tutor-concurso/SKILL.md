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
Executado pelo cron (todo dia) OU manualmente pelo Eduardo.

1. Login admin para obter token:
   - `POST /api/login` → `{"username":"admin","password":"admin123"}` → guarda `token`.
2. Descobrir alunos e concursos:
   - `GET /api/admin/alunos` → lista `[{id, username, full_name, concurso_id}]`.
   Para cada aluno, repita 3-6.
3. Selecionar tópicos a gerar (baseado em cobertura + domínio):
   - `GET /api/admin/topicos-selecao?concurso_id=ID&n=2` →
     `[{id, nome, razao}]`. A lógica prioriza: (0) tópico não estudado →
     cobertura 100%; (1) revisão espaçada vencida; (2) baixa dominância média.
4. Buscar fonte do edital:
   - Se o concurso tiver `edital_url`/`edital_text`, usar como base. Senão, pesquisar
     na web os tópicos (ex.: "Direito Administrativo princípios Cebraspe agente
     administrativo PF"). Usar web_search / navegação real. NÃO inventar fatos.
5. Montar o bloco JSON (formato abaixo) com 10 questões (padrão 7 MCQ + 3 discursiva)
   ancoradas na fonte, e enviar:
   - `POST /api/bloco/gerar` (header `Authorization: Bearer <token_admin>`)
   - Body: `{"concurso_id": ID, "bloco": {...}}`
6. Confirmar e avisar o Eduardo no Telegram que o bloco do aluno X está pronto.

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

## Nudge diário (cron do Hermes)
Crie um cron no Hermes para, todo dia (ex.: 07:00), gerar o bloco de cada aluno e
avisar no Telegram. Exemplo de `prompt` do cron (auto-contido):

```
Use a skill 'tutor-concurso'. Para cada aluno listado em GET /api/admin/alunos
(plataforma concurso-tutor rodando em http://127.0.0.1:8000), gere o bloco do dia:
1) login admin (admin/admin123) p/ pegar token; 2) GET /api/admin/topicos-selecao
para o concurso do aluno (n=2); 3) pesquise o edital/tópicos na web (sem inventar);
4) POST /api/bloco/gerar com 10 questões (7 MCQ + 3 discursiva) ancoradas na fonte;
5) ao fim, envie UMA mensagem no Telegram para o Eduardo listando os blocos gerados
por aluno e os tópicos escolhidos. Se a plataforma não responder, reporte o erro.
```

O cron roda autônomo; o Hermes usa web_search para o conteúdo e a API para gravar.

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

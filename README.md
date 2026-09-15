# Concurso Tutor

Plataforma web (Python + FastAPI + SQLite + front vanilla) que funciona como um
**professor de concurso autônomo assistido por IA (Hermes)**.

## Regra fundamental sobre questões

O Concurso Tutor **não cria questões**.

Toda questão apresentada ao aluno deve ser uma **questão real já aplicada em prova de concurso público**, reproduzida fielmente e com origem verificável.

É proibido usar IA para inventar, adaptar, reescrever, parafrasear ou produzir questões apenas "no estilo" de uma banca. A IA pode localizar, classificar e explicar questões reais, mas não alterar o conteúdo original.

A especificação obrigatória está em [`MANUAL_QUESTOES_REAIS.md`](MANUAL_QUESTOES_REAIS.md).

## Conceito (definido com o Eduardo)
- **2 alunos**, concursos diferentes:
  - PF — Agente Administrativo (banca Cebraspe)
  - Técnico em Enfermagem
- O **Hermes** (IA) monta, **todos os dias**, um bloco de estudo com base no **edital real + pesquisa**, selecionando **questões reais de provas anteriores** do banco validado.
- Exercícios podem incluir múltipla escolha, certo/errado e outros formatos existentes nas provas de origem. A correção e a explicação pedagógica podem ser assistidas por IA, sem alterar a questão original.
- A plataforma mede **progresso e dominância por tópico** (mapa de calor) e aplica
  **revisão espaçada**, mas **estuda tudo** (cobertura 100% do edital).
- Fluxo **assíncrono**: Hermes monta o bloco e avisa no Telegram; o aluno resolve
  na plataforma no próprio ritmo.
- Código **portátil** (GitHub, roda em qualquer lugar via Docker ou Termux).

## Stack
- Backend: FastAPI + SQLAlchemy + SQLite local ou PostgreSQL Supabase
- Front: HTML/CSS/JS puro (SPA, sem build)
- IA: Hermes Agent (skill `tutor-concurso`) seleciona/organiza conteúdo e pode corrigir discursivas ou gerar explicações pedagógicas

## Como rodar (Docker — qualquer lugar)
```bash
git clone https://github.com/lloupp/concurso-tutor.git
cd concurso-tutor
cp .env.example .env
docker compose up --build
# abra http://localhost:8000
```

## Como rodar (Termux / Python direto)
```bash
cd concurso-tutor/backend
pip install -r ../requirements.txt
python -m backend.seed          # popula dados demo
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

## Usuários demo
| usuário | senha | papel |
|---|---|---|
| admin | admin123 | administra conteúdo |
| aluno_pf | 123456 | PF Agente Administrativo |
| aluno_enf | 123456 | Técnico em Enfermagem |

## Endpoints principais
| Método | Rota | Função |
|---|---|---|
| POST | `/api/login` | autenticação |
| GET | `/api/bloco/hoje` | bloco do dia do aluno |
| POST | `/api/bloco/responder` | envia respostas |
| GET | `/api/progresso` | dominância + cobertura |
| GET | `/api/plano` | próximos tópicos (revisão espaçada) |
| POST | `/api/bloco/gerar` | admin/Hermes monta bloco usando questões reais validadas |
| POST | `/api/admin/*` | admin cria concurso/tópico/aluno |

## Integração com o Hermes / Pi

Hermes pode pesquisar o edital, localizar provas, classificar questões reais, montar blocos e produzir explicações pedagógicas. **Não pode criar questões inéditas.**

Qualquer processo de população em massa deve seguir [`MANUAL_QUESTOES_REAIS.md`](MANUAL_QUESTOES_REAIS.md): cada questão precisa ter origem rastreável e ser conferida com a prova/gabarito correspondente antes de entrar no banco.

## Simulado estático (GitHub Pages)
Além da plataforma completa (backend), há um **simulado estático** em `docs/`.
As questões desse simulado também devem ser **questões reais de provas**, nunca perguntas criadas apenas para imitar concursos.

Publicado em: **https://lloupp.github.io/concurso-tutor/**

**Ativar o Pages (uma vez, nas configurações do repositório):**
Settings → Pages → Build and deployment → Source: `Deploy from a branch` →
Branch: `main` / pasta `/docs` → Save.

**Testar localmente:**
```bash
cd docs
python3 -m http.server 8080
# abra http://localhost:8080
```

Para adicionar questões, veja [`docs/CONTRIBUINDO.md`](docs/CONTRIBUINDO.md) e, obrigatoriamente, [`MANUAL_QUESTOES_REAIS.md`](MANUAL_QUESTOES_REAIS.md).

## Modelo de dados
`Concurso → Topico (árvore) → Bloco → Questao → Resposta → Progresso (dominância)`
Usuários têm papel `aluno` (1 concurso) ou `admin`.

O modelo de `Questao` deve evoluir para manter proveniência suficiente para auditoria, incluindo banca, órgão/concurso, cargo, ano, número da questão, fonte da prova e fonte do gabarito.

## Roadmap
- [ ] Banco auditável de questões reais com metadados de proveniência
- [ ] Importação de provas e gabaritos oficiais
- [ ] Validação automática/manual contra a fonte antes de publicar
- [ ] Upload de PDF de edital + extração automática de tópicos
- [ ] Endpoint de correção discursiva pelo Hermes (webhook)
- [ ] Cron real de montagem diária + notificação Telegram
- [ ] Multi-dispositivo (deploy VPS/túnel)
- [ ] Estatísticas por banca e simulados completos

# Concurso Tutor

Plataforma web (Python + FastAPI + SQLite + front vanilla) que funciona como um
**professor de concurso autônomo assistido por IA (Hermes)**.

## Conceito (definido com o Eduardo)
- **2 alunos**, concursos diferentes:
  - PF — Agente Administrativo (banca Cebraspe)
  - Técnico em Enfermagem
- O **Hermes** (IA) gera, **todos os dias**, um bloco de estudo com base no **edital
  real + pesquisa** (sem invenção): mini-aula + **10 questões** (1h de estudo).
- Exercícios **mistos**: múltipla escolha (correção automática) + discursiva/cálculo
  (correção por IA/Hermes com rubrica).
- A plataforma mede **progresso e dominância por tópico** (mapa de calor) e aplica
  **revisão espaçada**, mas **estuda tudo** (cobertura 100% do edital).
- Fluxo **assíncrono**: Hermes monta o bloco e avisa no Telegram; o aluno resolve
  na plataforma no próprio ritmo.
- Código **portátil** (GitHub, roda em qualquer lugar via Docker ou Termux).

## Stack
- Backend: FastAPI + SQLAlchemy + SQLite
- Front: HTML/CSS/JS puro (SPA, sem build)
- IA: Hermes Agent (skill `tutor-concurso`) gera conteúdo e corrige discursivas

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
| admin | admin123 | gera conteúdo (Hermes) |
| aluno_pf | 123456 | PF Agente Administrativo |
| aluno_enf | 123456 | Técnico em Enfermagem |

## Endpoints principais
| Método | Rota | Função |
|---|---|---|
| POST | `/api/login` | autenticação |
| GET | `/api/bloco/hoje` | bloco do dia do aluno |
| POST | `/api/bloco/responder` | envia respostas (corrige MCQ) |
| GET | `/api/progresso` | dominância + cobertura |
| GET | `/api/plano` | próximos tópicos (revisão espaçada) |
| POST | `/api/bloco/gerar` | admin/Hermes cria bloco (JSON) |
| POST | `/api/admin/*` | admin cria concurso/tópico/aluno |

## Integração com o Hermes / Pi (geração de conteúdo)
A geração de blocos é feita por um "professor" IA que pesquisa o edital real e
chama a API. Dois caminhos:

- **Hermes (cron diário 07:00):** usa a skill `tutor-concurso` (em
  `skills/tutor-concurso/SKILL.md`) para gerar o bloco de cada aluno e avisar no
  Telegram. Job já criado e testado.
- **Pi orquestrado (população em massa):** para encher a plataforma de uma vez,
  orquestramos N instâncias do Pi (`~/.pi/agent`) — uma por concurso — via `tmux`,
  cada uma guiada pela skill `tutor-concurso` (web research + `curl` na API local).
  Exemplo usado: 2 sessões (`pipf`, `pienf`) geraram PF (7 blocos/42 questões,
  cobertura 100%) e Enfermagem (3 blocos/30 questões). Ver skills
  `pi-coding-agent-orchestrator`.
- **Grok CLI:** há `grok_populate_prompt.md` com o prompt equivalente, mas o CLI
  `grok` neste ambiente não está autenticado (XAI_API_KEY=dummy, sessão vazia);
  o backend (shim→OpenRouter) funciona. Falta `grok login --device-code`.

Conteúdo NUNCA é inventado: sempre ancorado em fontes (Estratégia, Gran, Direção,
Cofen, Planalto/CF88, editais UFMG/UFES).

## Modelo de dados
`Concurso → Topico (árvore) → Bloco → Questao → Resposta → Progresso (dominância)`
Usuários têm papel `aluno` (1 concurso) ou `admin`.

## Roadmap
- [ ] Upload de PDF de edital + extração automática de tópicos
- [ ] Endpoint de correção discursiva pelo Hermes (webhook)
- [ ] Cron real de geração diária + notificação Telegram
- [ ] Multi-dispositivo (deploy VPS/túnel)
- [ ] Estatísticas por banca e simulados completos

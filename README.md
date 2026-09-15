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

## Integração com o Hermes (busca de questões reais)

> **Atualizado em 2026-09-15 pela auditoria de questões reais** — ver
> [`AUDITORIA_QUESTOES_REAIS.md`](AUDITORIA_QUESTOES_REAIS.md). O fluxo
> anterior descrito aqui ("Hermes/Pi/Grok geram blocos") fazia uma IA
> **formular** questões ancoradas em fontes gerais (editais, sites de
> concurso, leis) — isso **não é** prova de origem de uma questão real e foi
> desativado. Todas as questões cadastradas por esse processo (Supabase de
> produção e bancos locais) foram colocadas em quarentena
> (`situacao='quarentena'`) e não são mais servidas ao aluno.
>
> O fluxo atual é o oposto: o Hermes **busca e recupera** questões
> efetivamente aplicadas em provas reais (com banca, órgão, concurso,
> cargo, ano, número da questão, URL da prova e gabarito oficial
> comprovados) — nunca formula, adapta ou parafraseia. Ver o passo a passo
> em [`skills/tutor-concurso/SKILL.md`](skills/tutor-concurso/SKILL.md). O
> banco tem uma constraint (`chk_valida_exige_comprovacao`) que rejeita
> qualquer questão marcada "válida" sem essa comprovação completa.

## Simulado estático (GitHub Pages)
Além da plataforma completa (backend), há um **simulado estático** em `docs/`
(Português, Matemática/Raciocínio Lógico, Informática, Direito Constitucional,
Direito Administrativo, Atualidades) — roda 100% no navegador, sem backend.
Publicado em: **https://lloupp.github.io/concurso-tutor/**

Desde a auditoria de 2026-09-15, os arquivos em `docs/data/` estão vazios:
as questões anteriores não tinham comprovação de origem numa prova real
aplicada e foram removidas (não substituídas por questões inventadas). Ver
[`docs/CONTRIBUINDO.md`](docs/CONTRIBUINDO.md) para as regras de como
adicionar questões reais.

**Ativar o Pages (uma vez, nas configurações do repositório):**
Settings → Pages → Build and deployment → Source: `Deploy from a branch` →
Branch: `main` / pasta `/docs` → Save. O site fica disponível em
`https://<usuário>.github.io/concurso-tutor/`.

**Testar localmente:**
```bash
cd docs
python3 -m http.server 8080
# abra http://localhost:8080
```

## Modelo de dados
`Concurso → Topico (árvore) → Bloco → Questao → Resposta → Progresso (dominância)`
Usuários têm papel `aluno` (1 concurso) ou `admin`.

## Roadmap
- [ ] Upload de PDF de edital + extração automática de tópicos
- [ ] Endpoint de correção discursiva pelo Hermes (webhook)
- [ ] Cron real de geração diária + notificação Telegram
- [ ] Multi-dispositivo (deploy VPS/túnel)
- [ ] Estatísticas por banca e simulados completos

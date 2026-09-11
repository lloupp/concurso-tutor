# Arquitetura Mobile/Android — concurso-tutor (Fase 1: análise)

Documento de análise da estrutura atual e proposta de evolução para app Android
(Capacitor) com suporte offline e sincronização incremental. Escrito antes de
qualquer alteração de código, conforme pedido.

## 1. O que já existe (será preservado)

**Backend** (`backend/app/`): FastAPI + SQLAlchemy + SQLite, API REST em `/api`.
- Modelos (`models.py`): `User`, `Sessao` (token Bearer), `Concurso`, `Topico`
  (árvore), `Bloco`, `Questao`, `Resposta`, `Progresso` (dominância + revisão
  espaçada).
- Auth simples por token opaco em tabela `Sessao` (sem JWT), `Authorization: Bearer <token>`.
- Lógica de progresso/plano de estudo em `planner.py` (EMA de domínio, revisão
  espaçada, seleção de próximos tópicos) — já é o "motor" certo para basear a
  função "Atualizar meus estudos".
- CORS já liberado (`allow_origins=["*"]`) — não precisa mudar para aceitar
  requisições de um WebView/app.

**Frontend** (`frontend/`): HTML/CSS/JS puro, sem build, SPA com 3 abas (Bloco do
dia, Boletim, Plano de estudo). Chama a API com `const API = "/api"` (caminho
relativo) — funciona hoje porque o próprio FastAPI serve o frontend via
`StaticFiles` no mesmo host/porta.

**Deploy**: Docker (`Dockerfile` + `docker-compose.yml`, uvicorn) ou execução
direta (Termux/Python). Banco SQLite em arquivo (`DB_PATH`), portátil.

## 2. O que impede empacotar como APK hoje

1. **`API = "/api"` é relativo** (`frontend/app.js:1`). Num APK/Capacitor o
   WebView carrega os arquivos locais (origem `capacitor://localhost` ou
   similar), então `fetch("/api/...")` tentaria bater no próprio dispositivo,
   não no servidor real. Precisa virar uma URL absoluta e configurável.
2. **Sem armazenamento offline**: hoje só o token e o `concurso_id` ativo vão
   pro `localStorage`. Matérias, tópicos, blocos, questões e respostas não têm
   cache local nem fila de pendências.
3. **Sem sincronização incremental**: não existem `updated_at`/`version` nas
   tabelas nem endpoint que devolva "o que mudou desde X".
4. **Sem endpoint para o aluno pedir conteúdo novo**: hoje só admin/Hermes
   chama `POST /api/bloco/gerar`; o aluno não tem como disparar isso.
5. **Layout**: o CSS atual não foi desenhado mobile-first (a confirmar em
   teste real de tela pequena na Fase 2).

## 3. Arquitetura proposta

### Backend (mudanças aditivas, nada quebra o que existe)
- Adicionar `updated_at` (DateTime) e opcionalmente `version` (Integer) em
  `Topico`, `Bloco`, `Questao`, `Progresso`, `Resposta` — SQLite aceita
  `ALTER TABLE ADD COLUMN`, sem migração destrutiva.
- Novos endpoints (nomes ajustáveis):
  - `GET /api/sync/status?concurso_id=` → carimbo de tempo do último dado
    disponível + contagens (para o app decidir se vale a pena sincronizar).
  - `GET /api/sync?since=<ISO timestamp>&concurso_id=` → só os registros com
    `updated_at > since`, agrupados por tabela (`topicos`, `blocos`,
    `questoes`, `progresso`).
  - `POST /api/sync/respostas` → upload em lote de respostas registradas
    offline (idempotente: aceita um `client_id` opcional por resposta para
    evitar duplicar se reenviado).
  - `POST /api/conteudo/solicitar` → aluno autenticado pede geração de bloco
    novo. Reaproveita `planner.proximos_topicos_admin` para decidir o quê
    gerar; a geração em si (pesquisa + redação de questões) continua sendo
    trabalho do Hermes/admin no servidor (nunca no celular) — o endpoint só
    registra o pedido como pendente para o próximo ciclo, igual ao fluxo atual
    descrito em `skills/tutor-concurso/SKILL.md`.
- Endpoints existentes continuam exatamente como estão.

### Frontend (continua HTML/CSS/JS puro, sem framework novo)
- `API_BASE` configurável (tela de Configurações, guardado em storage local;
  default = mesmo host em dev, URL completa em produção).
- Camada de armazenamento local (IndexedDB, via wrapper leve) para cache de
  matérias/tópicos/blocos/questões e fila de respostas pendentes com
  `sync_status` (`pendente` | `sincronizado`).
- Navegação em 5 abas mobile: Início / Estudar / Revisões / Progresso /
  Configurações — reaproveitando as telas e chamadas de API já existentes.

### Empacotamento
- **Capacitor** (`@capacitor/android`) com `webDir` apontando para
  `frontend/`. Gera uma pasta `android/` (projeto Gradle nativo) que builda
  o APK. Reaproveita 100% do HTML/CSS/JS — não é reescrita.
- Plugins nativos usados apenas onde fizer diferença real: `Preferences`
  (token fora de `localStorage` puro) e `Network` (detectar online/offline).

## 4. Por que Capacitor e não outra coisa

Reaproveita o frontend existente sem reescrever em React Native/Flutter/Kotlin;
suporta plugins nativos (storage seguro, detecção de rede) chamáveis do
mesmo JS; e o projeto Android gerado é buildável com as ferramentas padrão
(Gradle). Custo: WebView tem overhead de nativo puro, mas é aceitável para
um app de poucas telas como este.

## 5. Ambiente de build verificado nesta sessão

- Node 22, npm 10, Java 21 (OpenJDK), Gradle 8.14 e Maven já instalados.
- **Android SDK não está instalado.** Gerar o projeto `android/` via Capacitor
  não depende do SDK, mas **compilar o APK** exige `sdkmanager`/`ANDROID_HOME`
  com as *build-tools* e *platform* corretas — isso normalmente é feito
  localmente (Android Studio) ou baixando o SDK command-line tools, o que pode
  ser lento/instável atrás do proxy deste ambiente. Vou tentar instalar o SDK
  mínimo necessário quando chegarmos na Fase 3, mas se não for viável aqui, o
  projeto `android/` fica pronto e documentado para você buildar localmente ou
  em CI.

## 6. Pontos que preciso confirmar antes de codificar

1. **Banco**: mantemos SQLite (adequado a 1 servidor pequeno/uso pessoal) ou
   já planejamos Postgres pensando em múltiplos dispositivos/usuários
   simultâneos? (Não muda a Fase 1-7, mas influencia se vale a pena já trocar
   agora ou deixar para depois.)
2. **Geração sob demanda**: o botão "Atualizar meus estudos" deve efetivamente
   disparar pesquisa web/LLM em tempo real no servidor (tem custo de API), ou
   apenas registrar um pedido que o Hermes processa no próximo ciclo
   (assíncrono, como já funciona hoje)?
3. Sigo direto para a Fase 2 (mobile-first CSS + `API_BASE` configurável —
   baixo risco, não muda contrato de API) e só then aviso antes de mexer em
   Capacitor (Fase 3), ou prefere revisar este documento primeiro?

---
Próximo passo sugerido: Fase 2 (responsividade + configuração de API), que não
altera nenhum endpoint nem modelo existente.

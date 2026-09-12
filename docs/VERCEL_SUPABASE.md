# Preparação Vercel + Supabase

FastAPI é compatível com o runtime Python da Vercel por meio de api/index.py.
SQLAlchemy permanece e seleciona o banco por DATABASE_URL. Sem ela, o projeto continua usando SQLite local.

Para funções serverless, use o pooler Supabase em modo transaction, porta 6543, com NullPool. A chave service_role nunca vai para frontend ou APK.

Foram adaptados: vercel.json; backend/app/db.py com psycopg e NullPool; Docker sem seed automático; migrations/001_initial_postgres.sql com chaves, checks, JSONB, timestamps e índices; scripts/export_data.py.

Geração por IA, pesquisa web, correção em lote, importação e backups não devem rodar como trabalho permanente ou bloqueante em uma request. Use worker ou serviço externo, ou cron que apenas dispare tarefa idempotente e responda rapidamente.

Vercel Cron usa UTC; no plano Hobby a frequência mínima é diária, o minuto exato não é garantido e falhas não são automaticamente repetidas. Consulte https://vercel.com/docs/cron-jobs e https://vercel.com/docs/functions/limitations.

Nesta fase permanece a autenticação própria, pois ela já cobre o fluxo atual. Supabase Auth pode ser adotado depois para OAuth, recuperação de senha, RLS ou identidade compartilhada, após definir a migração de sessões.

Não há credenciais nem projeto Vercel/Supabase conectados nesta sessão. Compatibilidade foi preparada e validada localmente, mas URL pública, conexão real com Supabase e deploy não foram executados.

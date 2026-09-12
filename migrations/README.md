# Migração SQLite para Supabase PostgreSQL

1. Crie o projeto Supabase e use a URL do pooler compartilhado em modo
   transaction (porta 6543) em DATABASE_URL.
2. Execute 001_initial_postgres.sql no SQL Editor.
3. Exporte o SQLite com python scripts/export_data.py --db data/concurso.db.
4. Faça a carga em ambiente controlado, preservando IDs e validando contagens.
5. Execute python -m pytest -q.

DATABASE_URL e SUPABASE_SERVICE_ROLE_KEY ficam exclusivamente no backend.

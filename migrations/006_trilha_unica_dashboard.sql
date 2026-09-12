alter table public.users
  add column if not exists tempo_diario integer not null default 60;

alter table public.users
  add constraint users_tempo_diario_check
  check (tempo_diario in (20, 30, 45, 60, 90));

create index if not exists ix_users_concurso_id on public.users(concurso_id);
create index if not exists ix_progresso_user_topico on public.progresso(user_id, topico_id);
create index if not exists ix_respostas_user_created on public.respostas(user_id, created_at);

alter table public.questoes
  add column if not exists explicacao text,
  add column if not exists fonte_id integer references public.fontes(id) on delete set null;

create index if not exists ix_questoes_fonte on public.questoes(fonte_id);

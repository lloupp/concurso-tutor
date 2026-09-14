-- Índices para as junções e filtros executados pelos fluxos autenticados.
create index if not exists ix_questoes_topico on public.questoes(topico_id);
create index if not exists ix_respostas_questao on public.respostas(questao_id);
create index if not exists ix_progresso_topico on public.progresso(topico_id);
create index if not exists ix_sessoes_user on public.sessoes(user_id);
create index if not exists ix_topicos_pai on public.topicos(pai_id);
create index if not exists ix_topicos_fontes_fonte on public.topicos_fontes(fonte_id);

-- 006 recriou um índice idêntico ao da migration inicial.
drop index if exists public.ix_respostas_user_created;

-- Impede resolução de objetos por schemas injetados no search_path da sessão.
alter function public.normalizar_gabarito_certo_errado()
  set search_path = public, pg_temp;

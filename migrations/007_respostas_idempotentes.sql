create unique index if not exists uq_respostas_user_questao
  on public.respostas(user_id, questao_id);

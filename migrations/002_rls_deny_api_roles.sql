-- O app usa autenticacao propria e acessa o Postgres pela conexao privada.
-- As roles da Data API nao devem ler nem alterar as tabelas internas.
do $$
declare
  tabela text;
begin
  foreach tabela in array array[
    'concursos', 'users', 'sessoes', 'topicos', 'blocos',
    'questoes', 'respostas', 'progresso', 'fontes', 'topicos_fontes'
  ] loop
    execute format('drop policy if exists "deny_api_roles" on public.%I', tabela);
    execute format(
      'create policy "deny_api_roles" on public.%I for all to anon, authenticated using (false) with check (false)',
      tabela
    );
    execute format('revoke all on table public.%I from anon, authenticated', tabela);
  end loop;
end $$;

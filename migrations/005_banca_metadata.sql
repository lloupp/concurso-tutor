alter table public.concursos
  add column if not exists ano integer,
  add column if not exists tipo_prova varchar(80),
  add column if not exists n_alternativas integer,
  add column if not exists usa_certo_errado boolean not null default false,
  add column if not exists tem_texto_base boolean not null default false,
  add column if not exists estilo_enunciado text,
  add column if not exists dificuldade_tipica varchar(80),
  add column if not exists distribuicao_materias jsonb;

alter table public.questoes
  add column if not exists banca_estilo varchar(40),
  add column if not exists materia varchar(120),
  add column if not exists trilha varchar(120),
  add column if not exists texto_base text;

create index if not exists ix_questoes_filtro_estilo
  on public.questoes(banca_estilo, materia, trilha, dificuldade);

update public.questoes q
set materia = coalesce(nullif(split_part(t.nome, ' — ', 1), ''), t.nome),
    trilha = case when t.concurso_id = 51 then 'Concursos de Nível Médio — Administrativo'
                  when t.concurso_id = 52 then 'Técnico em Enfermagem' end,
    banca_estilo = case when t.concurso_id = 51 then 'Cebraspe'
                        when t.concurso_id = 52 then 'FUNDATEC' end
from public.topicos t
where t.id = q.topico_id;

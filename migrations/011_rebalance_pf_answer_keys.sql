-- Redistribui gabaritos do banco PF sem alterar questões já respondidas.
with candidatas as (
  select q.id,row_number() over(order by q.id) rn
  from public.questoes q join public.blocos b on b.id=q.bloco_id
  where b.concurso_id=51 and q.tipo='mcq' and q.gabarito='0'
    and jsonb_array_length(q.alternativas::jsonb)=4
    and not exists(select 1 from public.respostas r where r.questao_id=q.id)
  order by q.id limit 240
), destinos as (
  select id,((rn-1)%3)+1 destino from candidatas
)
update public.questoes q
set alternativas=case d.destino
      when 1 then jsonb_build_array(q.alternativas::jsonb->1,q.alternativas::jsonb->0,q.alternativas::jsonb->2,q.alternativas::jsonb->3)
      when 2 then jsonb_build_array(q.alternativas::jsonb->1,q.alternativas::jsonb->2,q.alternativas::jsonb->0,q.alternativas::jsonb->3)
      else jsonb_build_array(q.alternativas::jsonb->1,q.alternativas::jsonb->2,q.alternativas::jsonb->3,q.alternativas::jsonb->0)
    end,
    gabarito=d.destino::text
from destinos d where q.id=d.id;

-- Dois itens apontados na auditoria mantêm a resposta correta na mesma posição;
-- o texto e os distratores passam a exigir distinção conceitual real.
update public.questoes set
 enunciado='Um agente público identifica uma providência eficiente, mas sem autorização legal. À luz da legalidade administrativa, deve:',
 alternativas='["abster-se até existir fundamento jurídico competente","praticar o ato porque o resultado é útil","agir e buscar autorização retroativa","substituir a lei por decisão interna"]'::jsonb,
 explicacao='Na administração pública, eficiência não substitui competência legal: o agente somente pode atuar dentro das autorizações e limites do ordenamento.',
 dificuldade=2
where id=16 and gabarito='0';

update public.questoes set
 enunciado='Na arquitetura da Web, a sigla HTTP identifica o protocolo de aplicação denominado:',
 alternativas='["HyperText Transfer Protocol","Host Transmission Processing","Hyperlink Transport Port","HyperText Terminal Procedure"]'::jsonb,
 explicacao='HTTP significa HyperText Transfer Protocol e define a troca de mensagens entre clientes e servidores na Web; as demais expansões não correspondem ao protocolo.',
 dificuldade=2
where id=18 and gabarito='0';

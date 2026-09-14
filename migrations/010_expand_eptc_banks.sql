-- Expansão idempotente das trilhas EPTC: mínimo de cinco itens válidos por tópico.
-- Somente INSERTs: respostas e questões já utilizadas permanecem imutáveis.

insert into public.blocos (concurso_id, data, titulo, introducao, duracao_min, criado_por, status)
select c.id, current_date, 'Banco editorial EPTC — expansão 2026',
       'Questões de cobertura do edital, revisadas por tópico e vinculadas a fontes oficiais.',
       60, 'revisao-editorial', 'banco'
from public.concursos c
where c.id in (53, 54)
  and not exists (
    select 1 from public.blocos b
    where b.concurso_id=c.id and b.titulo='Banco editorial EPTC — expansão 2026'
  );

-- Reaproveitamento controlado de itens já revisados dos bancos PF/Enfermagem.
with mapa (topico_id, questao_id, ordem) as (values
  (59,84,1),(59,181,2),(59,276,3),
  (68,104,1),(68,275,2),(68,154,3),
  (61,312,1),(61,345,2),(61,63,3),
  (67,342,1),(67,465,2),(67,505,3),
  (57,510,1),(57,637,2),(57,998,3),
  (58,233,1),(58,272,2),(58,311,3),(58,380,4),
  (64,65,1),(64,173,2),(64,151,3),
  (55,138,1),(55,142,2),(55,144,3),(55,158,4),
  (63,92,1),(63,140,2),(63,141,3)
 ,(62,89,1),(62,90,2)
), contagens as (
  select topico_id,count(*) qtd from public.questoes group by topico_id
), candidatos as (
  select m.*,row_number() over(partition by m.topico_id order by m.ordem) rn,
         greatest(0,5-coalesce(ct.qtd,0)) faltam
  from mapa m left join contagens ct on ct.topico_id=m.topico_id
), bloco as (
  select concurso_id,id from public.blocos
  where titulo='Banco editorial EPTC — expansão 2026'
)
insert into public.questoes
  (bloco_id,topico_id,tipo,enunciado,alternativas,gabarito,resposta_modelo,rubric,
   explicacao,fonte_id,tolerancia,unidade,banca_estilo,materia,trilha,texto_base,dificuldade)
select b.id,c.topico_id,q.tipo,q.enunciado,q.alternativas,q.gabarito,q.resposta_modelo,q.rubric,
       q.explicacao,q.fonte_id,q.tolerancia,q.unidade,'FUNDATEC',t.nome,'EPTC Nível Médio',q.texto_base,q.dificuldade
from candidatos c join public.questoes q on q.id=c.questao_id join public.topicos t on t.id=c.topico_id
join bloco b on b.concurso_id=t.concurso_id
where c.rn<=c.faltam
  and not exists (select 1 from public.questoes x join public.blocos xb on xb.id=x.bloco_id
                  where xb.concurso_id=t.concurso_id and lower(trim(x.enunciado))=lower(trim(q.enunciado)));

-- Itens autorais baseados nas fontes oficiais cadastradas.
with dados(topico_id,enunciado,alternativas,gabarito,explicacao,fonte_id,dificuldade) as (values
 (54,'Na frase “A cidade acordou apressada”, a atribuição de comportamento humano à cidade constitui:',
  '["eufemismo","metáfora","personificação","antítese"]'::jsonb,'2','O enunciado atribui à cidade a ação humana de acordar e o estado de pressa; trata-se de personificação ou prosopopeia.',25,2),
 (54,'Em um relatório técnico, a palavra “claro” foi empregada com o sentido de “compreensível”. Essa relação de sentido é de:',
  '["sinonímia contextual","antonímia absoluta","homonímia perfeita","onomatopeia"]'::jsonb,'0','No contexto, “claro” pode ser substituído por “compreensível” sem alteração relevante do sentido, configurando sinonímia contextual.',25,2),
 (54,'O uso de uma variedade linguística informal é mais adequado em:',
  '["sentença judicial","norma técnica","conversa espontânea entre amigos","edital de concurso"]'::jsonb,'2','A adequação linguística depende da situação comunicativa; a conversa espontânea admite registro informal, ao contrário dos documentos formais.',25,1),
 (57,'Um terreno retangular mede 12 m de comprimento e 8 m de largura. Qual é a sua área?',
  '["20 m²","40 m²","96 m²","192 m²"]'::jsonb,'2','A área do retângulo é o produto entre comprimento e largura: 12 × 8 = 96 m².',25,1),
 (57,'Em um triângulo retângulo, os catetos medem 6 cm e 8 cm. Quanto mede a hipotenusa?',
  '["7 cm","10 cm","12 cm","14 cm"]'::jsonb,'1','Pelo teorema de Pitágoras, h² = 6² + 8² = 100; portanto, h = 10 cm.',25,2),

 (51,'Segundo o Estatuto da Igualdade Racial, as políticas públicas devem buscar principalmente:',
  '["igualdade de oportunidades e defesa de direitos","separação de serviços por raça","restrição de participação social","tratamento desigual sem justificativa"]'::jsonb,'0','O Estatuto orienta a garantia de igualdade de oportunidades e a defesa dos direitos étnicos individuais, coletivos e difusos.',31,2),
 (51,'A discriminação racial ou étnico-racial caracteriza-se por distinção, exclusão, restrição ou preferência que tenha por efeito:',
  '["ampliar a burocracia","anular ou restringir direitos em igualdade de condições","criar política universal","organizar dados estatísticos"]'::jsonb,'1','A definição legal alcança práticas cujo objetivo ou efeito seja anular ou restringir o reconhecimento ou exercício de direitos em igualdade.',31,2),
 (51,'Na Lei Brasileira de Inclusão, adaptação razoável significa:',
  '["favor sem relação com direitos","mudança ilimitada em qualquer hipótese","ajuste necessário que não imponha ônus desproporcional","substituição automática da pessoa por representante"]'::jsonb,'2','Adaptações razoáveis são modificações necessárias e adequadas, sem ônus desproporcional ou indevido, para assegurar direitos.',32,2),
 (51,'A acessibilidade prevista na Lei Brasileira de Inclusão busca permitir à pessoa com deficiência:',
  '["uso apenas assistido de espaços","acesso com segurança e autonomia","acesso restrito a serviços públicos","dispensa de comunicação acessível"]'::jsonb,'1','A acessibilidade assegura alcance e utilização, com segurança e autonomia, de espaços, transportes, informação, comunicação e serviços.',32,1),
 (51,'Para a Lei Brasileira de Inclusão, a avaliação da deficiência, quando necessária, deve ser:',
  '["exclusivamente econômica","apenas documental","realizada por qualquer pessoa","biopsicossocial por equipe multiprofissional e interdisciplinar"]'::jsonb,'3','A lei adota avaliação biopsicossocial, considerando impedimentos, fatores socioambientais, limitações de atividades e restrições de participação.',32,3),

 (60,'Na Lei de Acesso à Informação, a regra geral para informações de interesse público é:',
  '["sigilo permanente","publicidade, sendo o sigilo exceção","acesso apenas a servidores","destruição após o pedido"]'::jsonb,'1','A LAI adota a publicidade como preceito geral e o sigilo como exceção, além de incentivar transparência ativa.',34,1),
 (60,'Segundo a LGPD, o princípio da finalidade exige que o tratamento de dados ocorra para:',
  '["propósitos legítimos, específicos e informados","qualquer uso futuro não informado","divulgação irrestrita","armazenamento sem necessidade"]'::jsonb,'0','Finalidade exige propósitos legítimos, específicos, explícitos e informados ao titular, sem tratamento posterior incompatível.',35,2),
 (60,'Qual alternativa contém apenas dados pessoais sensíveis segundo a LGPD?',
  '["nome e CEP","placa e telefone","dado de saúde e biometria vinculados a pessoa","cargo e matrícula funcional"]'::jsonb,'2','Dados referentes à saúde e dados biométricos vinculados a pessoa natural integram as categorias sensíveis definidas pela LGPD.',35,2),
 (60,'Após a reforma da Lei de Improbidade Administrativa, a configuração dos atos tipificados exige, como regra:',
  '["mera irregularidade","culpa leve","resultado administrativo desfavorável","conduta dolosa tipificada"]'::jsonb,'3','A Lei nº 8.429/1992, com a redação vigente, exige dolo para os atos de improbidade tipificados; ilegalidade isolada não basta.',33,3),

 (66,'A Lei nº 13.303/2016 aplica-se ao estatuto jurídico de:',
  '["autarquias apenas","empresas públicas e sociedades de economia mista e suas subsidiárias","cartórios extrajudiciais","partidos políticos"]'::jsonb,'1','A Lei das Estatais disciplina empresas públicas, sociedades de economia mista e subsidiárias nas diferentes esferas federativas.',27,1),
 (66,'Nas empresas estatais, as regras de governança previstas na Lei nº 13.303/2016 incluem mecanismos de:',
  '["sigilo absoluto","nomeação sem requisitos","transparência, gestão de riscos e controles internos","dispensa de fiscalização"]'::jsonb,'2','A lei estabelece práticas de transparência, estruturas de controle, gestão de riscos e requisitos para administradores.',27,2),
 (66,'Nas licitações regidas pela Lei nº 13.303/2016, o julgamento deve observar:',
  '["critérios definidos no instrumento convocatório","preferência pessoal do gestor","critério secreto posterior","sorteio obrigatório em todos os casos"]'::jsonb,'0','A seleção deve seguir critérios objetivos previamente definidos no instrumento convocatório, preservando isonomia e competitividade.',27,2),
 (66,'O dever de fiscalização dos contratos celebrados por empresa estatal:',
  '["termina na assinatura","cabe somente ao contratado","é facultativo","permanece durante a execução contratual"]'::jsonb,'3','A contratação não elimina o dever da estatal de acompanhar e fiscalizar a execução, registrando ocorrências e exigindo correções.',27,2),

 (53,'A Lei Orgânica municipal funciona, no âmbito local, como:',
  '["norma fundamental de organização do Município","decreto federal temporário","contrato privado","regulamento interno de uma empresa"]'::jsonb,'0','A Lei Orgânica estrutura o Município, suas competências e seus Poderes, subordinada às Constituições Federal e Estadual.',29,1),
 (53,'A autonomia municipal compreende capacidade de auto-organização, autogoverno, autoadministração e:',
  '["soberania internacional","competência normativa nos assuntos locais","poder judiciário próprio","emissão de moeda"]'::jsonb,'1','A Constituição e a Lei Orgânica reconhecem autonomia política, administrativa, financeira e normativa dentro das competências municipais.',29,2),
 (53,'A atuação da administração municipal deve observar, entre outros, o princípio da:',
  '["promoção pessoal","publicidade apenas opcional","legalidade","decisão secreta como regra"]'::jsonb,'2','A administração pública municipal se submete aos princípios constitucionais, inclusive legalidade, impessoalidade, moralidade, publicidade e eficiência.',29,1),
 (53,'A fiscalização contábil, financeira e orçamentária do Município envolve:',
  '["somente empresas privadas","apenas o Poder Executivo","nenhum controle externo","controle externo do Legislativo e sistemas de controle interno"]'::jsonb,'3','O modelo constitucional reproduzido no âmbito municipal combina controle externo exercido pelo Legislativo e controle interno de cada Poder.',29,2),
 (53,'Assuntos de interesse predominantemente local podem ser disciplinados pelo Município mediante:',
  '["legislação municipal dentro de sua competência","tratado internacional próprio","decisão de outro Município","ato sem publicidade"]'::jsonb,'0','Compete ao Município legislar sobre assuntos de interesse local e suplementar a legislação federal e estadual quando cabível.',29,2),

 (56,'A Lei Municipal nº 8.133/1998 trata do sistema de:',
  '["saúde suplementar","transporte e circulação de Porto Alegre","educação superior federal","arrecadação aduaneira"]'::jsonb,'1','A ementa oficial da Lei nº 8.133/1998 disciplina o Sistema de Transporte e Circulação no Município de Porto Alegre.',28,1),
 (56,'A EPTC é organizada como:',
  '["secretaria estadual","autarquia federal","empresa pública municipal","associação privada sem vínculo público"]'::jsonb,'2','A legislação e o Estatuto Social identificam a EPTC como Empresa Pública de Transporte e Circulação vinculada ao Município.',30,1),
 (56,'Entre as finalidades institucionais da EPTC está:',
  '["operar e fiscalizar trânsito e transporte no âmbito municipal","editar leis federais","julgar crimes de trânsito","emitir moeda"]'::jsonb,'0','A EPTC atua no planejamento, operação e fiscalização da circulação e dos transportes de competência municipal.',30,2),
 (56,'Os empregados públicos da EPTC submetem-se, em regra, ao regime:',
  '["militar","diplomático","estatutário federal","celetista"]'::jsonb,'3','Por ser empresa pública, a EPTC adota regime de emprego público regido pela CLT, sem afastar as exigências constitucionais.',30,2),
 (56,'A prestação de serviços de transporte no Município deve observar:',
  '["apenas conveniência do operador","regulamentação, controle e fiscalização do poder público competente","ausência de padrões de segurança","sigilo de itinerários"]'::jsonb,'1','A Lei nº 8.133/1998 atribui ao poder público municipal funções de regulamentação, controle e fiscalização dos serviços.',28,2),

 (65,'Para o Código de Trânsito Brasileiro, o trânsito em condições seguras é:',
  '["direito de todos e dever dos órgãos do Sistema Nacional de Trânsito","benefício apenas de condutores habilitados","responsabilidade exclusiva dos pedestres","faculdade sem dever estatal"]'::jsonb,'0','O art. 1º do CTB define o trânsito seguro como direito de todos e dever dos órgãos e entidades do Sistema Nacional de Trânsito.',26,1),
 (65,'Compete aos órgãos executivos municipais de trânsito, dentro de sua circunscrição:',
  '["julgar crimes","expedir leis federais","operar, fiscalizar e aplicar medidas previstas no CTB","licenciar aeronaves"]'::jsonb,'2','O CTB atribui aos órgãos municipais competências de engenharia, operação, fiscalização e aplicação das medidas administrativas e penalidades cabíveis.',26,2),
 (65,'Ao se aproximar de faixa de pedestres sem semáforo, o condutor deve:',
  '["acelerar para liberar a via","reduzir a velocidade e dar preferência ao pedestre nas hipóteses legais","buzinar continuamente","parar apenas se houver agente"]'::jsonb,'1','O CTB protege a travessia de pedestres e exige condução prudente, com redução de velocidade e preferência nas situações previstas.',26,2),
 (65,'A sinalização de trânsito tem por finalidade principal:',
  '["decorar a via","substituir todas as normas","orientar somente turistas","regulamentar, advertir e indicar condições de uso da via"]'::jsonb,'3','Os sinais comunicam regulamentação, advertência e indicação para ordenar a circulação e promover segurança.',26,1),

 (52,'O Manual Brasileiro de Fiscalização de Trânsito tem como função:',
  '["padronizar procedimentos de fiscalização e enquadramento de infrações","substituir o CTB","criar tributos municipais","regular apenas transporte aéreo"]'::jsonb,'0','O manual uniformiza procedimentos e critérios operacionais usados pelos órgãos de trânsito, em conformidade com o CTB e normas do CONTRAN.',37,2),
 (52,'Na lavratura do auto de infração, o agente deve registrar:',
  '["opiniões pessoais sem relação com o fato","dados exigidos pela norma e elementos que caracterizem a infração","somente a placa, sempre","informações inventadas para completar campos"]'::jsonb,'1','A consistência do auto depende dos dados obrigatórios e da caracterização objetiva da conduta observada.',37,2),
 (52,'Quando a abordagem do veículo não for possível, a autuação:',
  '["é sempre proibida","vira advertência automaticamente","pode ocorrer nas hipóteses admitidas, com registro adequado da constatação","dispensa enquadramento legal"]'::jsonb,'2','A fiscalização pode constatar determinadas infrações sem abordagem, desde que observe a norma aplicável e registre corretamente os elementos do fato.',37,2),
 (52,'O enquadramento de uma infração deve corresponder:',
  '["ao veículo de maior valor","à preferência do agente","ao código usado no dia anterior","à conduta efetivamente constatada e ao dispositivo aplicável"]'::jsonb,'3','Tipificação correta exige correspondência entre fato observado, código de enquadramento e dispositivo legal vigente.',37,2),
 (52,'A padronização nacional dos procedimentos de fiscalização favorece:',
  '["segurança jurídica e tratamento uniforme","decisões secretas","dispensa de motivação","alteração local do CTB"]'::jsonb,'0','Procedimentos uniformes reduzem divergências de enquadramento e aumentam previsibilidade, controle e segurança jurídica.',37,1)
), bloco as (
 select b.id,b.concurso_id from public.blocos b
 where b.titulo='Banco editorial EPTC — expansão 2026' and b.concurso_id=53
)
insert into public.questoes
 (bloco_id,topico_id,tipo,enunciado,alternativas,gabarito,explicacao,fonte_id,banca_estilo,materia,trilha,dificuldade)
select b.id,d.topico_id,'mcq',d.enunciado,d.alternativas,d.gabarito,d.explicacao,d.fonte_id,
       'FUNDATEC',t.nome,'EPTC Nível Médio',d.dificuldade
from dados d join public.topicos t on t.id=d.topico_id cross join bloco b
where not exists (select 1 from public.questoes q join public.blocos qb on qb.id=q.bloco_id
                  where qb.concurso_id=53 and lower(trim(q.enunciado))=lower(trim(d.enunciado)));

-- Conteúdo comum do edital: replica para a trilha de Enfermagem uma amostra
-- equilibrada do banco EPTC Médio já completado acima.
with plano(destino,origem,limite,prioridade) as (values
 (81,59,5,1),(76,68,3,1),(76,54,2,2),
 (89,57,3,1),(89,67,2,2),(86,58,3,1),(86,64,2,2),
 (77,55,5,1),(88,63,5,1),
 (91,62,2,1),(91,51,3,2),(82,66,5,1),
 (83,53,2,1),(83,56,2,2),(83,65,1,3)
), escolhidas as (
 select p.destino,q.*,row_number() over(partition by p.destino order by p.prioridade,q.id) geral,
        row_number() over(partition by p.destino,p.origem order by q.id) na_origem,p.limite
 from plano p join public.questoes q on q.topico_id=p.origem
), bloco as (
 select id from public.blocos where concurso_id=54 and titulo='Banco editorial EPTC — expansão 2026'
)
insert into public.questoes
 (bloco_id,topico_id,tipo,enunciado,alternativas,gabarito,resposta_modelo,rubric,
  explicacao,fonte_id,tolerancia,unidade,banca_estilo,materia,trilha,texto_base,dificuldade)
select b.id,e.destino,e.tipo,e.enunciado,e.alternativas,e.gabarito,e.resposta_modelo,e.rubric,
       e.explicacao,e.fonte_id,e.tolerancia,e.unidade,'FUNDATEC',t.nome,
       'EPTC Enfermagem do Trabalho',e.texto_base,e.dificuldade
from escolhidas e join public.topicos t on t.id=e.destino cross join bloco b
where e.na_origem<=e.limite
  and not exists (select 1 from public.questoes x join public.blocos xb on xb.id=x.bloco_id
                  where xb.concurso_id=54 and lower(trim(x.enunciado))=lower(trim(e.enunciado)));

-- Conteúdo técnico já consolidado, selecionado por aderência ao tópico e
-- qualidade da justificativa.
with mapa(topico_id,questao_id,ordem) as (values
 (69,1145,1),(69,1125,2),(69,1152,3),(69,1126,4),(69,1151,5),
 (80,1121,1),(80,1130,2),(80,1129,3),(80,1131,4),(80,1122,5),
 (72,1123,1),(72,1124,2),(72,648,3),(72,408,4),(72,292,5),
 (79,1135,1),(79,1136,2),(79,332,3),(79,294,4),(79,208,5),
 (87,253,1),(87,1139,2),(87,1140,3),(87,121,4),(87,1010,5),
 (75,1117,1),(75,401,2),(75,1118,3),(75,1119,4),(75,529,5),
 (84,324,1),(84,881,2),
 (71,1154,1),(71,1137,2),(71,1142,3),(71,1141,4),(71,96,5)
), contagens as (
 select topico_id,count(*) qtd from public.questoes group by topico_id
), candidatos as (
 select m.*,row_number() over(partition by m.topico_id order by m.ordem) rn,
        greatest(0,5-coalesce(ct.qtd,0)) faltam
 from mapa m left join contagens ct on ct.topico_id=m.topico_id
), bloco as (
 select id from public.blocos where concurso_id=54 and titulo='Banco editorial EPTC — expansão 2026'
)
insert into public.questoes
 (bloco_id,topico_id,tipo,enunciado,alternativas,gabarito,resposta_modelo,rubric,
  explicacao,fonte_id,tolerancia,unidade,banca_estilo,materia,trilha,texto_base,dificuldade)
select b.id,c.topico_id,q.tipo,q.enunciado,q.alternativas,q.gabarito,q.resposta_modelo,q.rubric,
       q.explicacao,q.fonte_id,q.tolerancia,q.unidade,'FUNDATEC',t.nome,
       'EPTC Enfermagem do Trabalho',q.texto_base,q.dificuldade
from candidatos c join public.questoes q on q.id=c.questao_id join public.topicos t on t.id=c.topico_id cross join bloco b
where c.rn<=c.faltam
  and not exists (select 1 from public.questoes x join public.blocos xb on xb.id=x.bloco_id
                  where xb.concurso_id=54 and lower(trim(x.enunciado))=lower(trim(q.enunciado)));

with dados(topico_id,enunciado,alternativas,gabarito,explicacao,fonte_id,dificuldade) as (values
 (84,'Em uma passagem de plantão segura, a comunicação deve ser:',
  '["vaga e baseada em suposições","restrita aos eventos antigos","estruturada, objetiva e centrada nas informações relevantes","substituída apenas por mensagens informais"]'::jsonb,'2','A comunicação estruturada reduz omissões, favorece continuidade do cuidado e permite confirmar informações críticas entre profissionais.',16,1),
 (84,'Diante de divergência técnica entre membros da equipe, a conduta profissional é:',
  '["discutir o caso com respeito, evidências e foco na segurança","expor o colega diante do paciente","ocultar a divergência mesmo com risco","interromper toda comunicação"]'::jsonb,'0','O diálogo respeitoso, baseado em evidências e pelos canais adequados, protege o paciente e mantém colaboração efetiva.',16,2),
 (84,'A técnica de comunicação em alça fechada exige que o receptor:',
  '["ignore a mensagem após ouvi-la","confirme a informação recebida e permita sua verificação","responda somente ao fim do turno","transfira a decisão sem comunicar"]'::jsonb,'1','Repetir ou confirmar a mensagem permite ao emissor verificar seu entendimento, reduzindo falhas em situações críticas.',16,2),
 (78,'Segundo a RDC nº 222/2018, a segregação dos resíduos de serviços de saúde deve ocorrer:',
  '["no momento e local de sua geração","apenas no abrigo externo","depois do transporte","somente no destino final"]'::jsonb,'0','Segregar no momento e local da geração evita misturas, reduz riscos ocupacionais e permite o manejo adequado de cada grupo.',41,1),
 (78,'Resíduos perfurocortantes devem ser acondicionados em recipiente:',
  '["de papel aberto","rígido, resistente à punctura, ruptura e vazamento","de tecido reutilizável","sem identificação"]'::jsonb,'1','O recipiente para perfurocortantes deve resistir à punctura, ruptura e vazamento, possuir tampa e identificação apropriada.',41,1),
 (78,'O Plano de Gerenciamento de Resíduos de Serviços de Saúde deve descrever:',
  '["somente custos","apenas a coleta externa","as ações relativas ao manejo desde a geração até a destinação","dados clínicos dos pacientes"]'::jsonb,'2','O PGRSS documenta segregação, acondicionamento, identificação, coleta, armazenamento, transporte, tratamento e disposição final.',41,2),
 (78,'Ao atingir o limite indicado no coletor de perfurocortantes, deve-se:',
  '["comprimir o conteúdo","transferir as agulhas","reabrir o recipiente","fechar e substituir o coletor conforme o procedimento"]'::jsonb,'3','Ultrapassar ou comprimir o conteúdo aumenta o risco de acidentes; o coletor deve ser fechado e substituído no limite indicado.',41,1),
 (78,'A identificação dos recipientes de resíduos permite:',
  '["reconhecer o grupo e os riscos para orientar o manejo seguro","misturar resíduos incompatíveis","dispensar capacitação","eliminar a segregação"]'::jsonb,'0','Símbolos, cores e inscrições possibilitam reconhecer o conteúdo e os riscos durante todas as etapas do gerenciamento.',41,1),
 (74,'A finalidade principal do SESMT, conforme a NR-04, é:',
  '["promover a saúde e proteger a integridade do trabalhador","substituir a CIPA em toda organização","realizar apenas exames admissionais","administrar a folha de pagamento"]'::jsonb,'0','O SESMT reúne competências de segurança e medicina do trabalho para promover saúde e proteger a integridade dos trabalhadores.',38,1),
 (74,'O dimensionamento do SESMT considera principalmente:',
  '["preferência dos empregados","número de empregados e grau de risco da atividade","faturamento mensal apenas","quantidade de clientes"]'::jsonb,'1','A NR-04 dimensiona o serviço segundo o número de trabalhadores e a natureza ou grau de risco da atividade econômica.',38,2),
 (74,'Entre os profissionais que podem compor o SESMT está o:',
  '["auditor fiscal municipal","contador do trabalho","enfermeiro do trabalho","corretor de seguros"]'::jsonb,'2','A composição prevista na NR-04 inclui médico, engenheiro e enfermeiro do trabalho, além de técnicos de segurança e de enfermagem do trabalho.',38,1),
 (74,'No ambulatório ocupacional, um atendimento de urgência deve ser:',
  '["omitido do prontuário","tratado sem identificação","adiado até o exame periódico","registrado e encaminhado segundo a gravidade e o fluxo definido"]'::jsonb,'3','Registro, avaliação inicial e encaminhamento conforme gravidade preservam continuidade assistencial, rastreabilidade e segurança.',38,2),
 (74,'A articulação entre SESMT, CIPA e PCMSO busca:',
  '["integrar prevenção, vigilância e resposta aos riscos ocupacionais","duplicar documentos sem análise","restringir comunicação de riscos","eliminar a participação dos trabalhadores"]'::jsonb,'0','A integração permite que riscos identificados orientem prevenção, acompanhamento da saúde e participação dos trabalhadores.',38,2),

 (85,'O objetivo do PCMSO previsto na NR-07 é:',
  '["selecionar candidatos por condição de saúde","proteger e preservar a saúde dos empregados em relação aos riscos ocupacionais","substituir o PGR","registrar somente acidentes graves"]'::jsonb,'1','O PCMSO deve proteger e preservar a saúde dos empregados, considerando os riscos ocupacionais identificados e classificados pelo PGR.',38,1),
 (85,'Qual exame ocupacional está expressamente previsto na NR-07?',
  '["vestibular","tributário","admissional","patrimonial"]'::jsonb,'2','A NR-07 prevê exames admissionais, periódicos, de retorno ao trabalho, de mudança de riscos ocupacionais e demissionais.',38,1),
 (85,'O Atestado de Saúde Ocupacional deve ser emitido:',
  '["somente quando houver doença","apenas no desligamento","sem identificação do empregado","para cada exame clínico ocupacional, com as informações exigidas"]'::jsonb,'3','A NR-07 exige a emissão do ASO para cada exame clínico ocupacional, com identificação, riscos, procedimentos e conclusão de aptidão.',38,2),
 (85,'Os achados dos exames ocupacionais devem contribuir para:',
  '["vigilância da saúde e aperfeiçoamento das medidas de prevenção","divulgação pública do diagnóstico","dispensa do inventário de riscos","substituição da avaliação clínica"]'::jsonb,'0','O acompanhamento coletivo e individual deve retroalimentar as ações preventivas, preservado o sigilo das informações de saúde.',38,2),
 (85,'O prontuário médico individual do PCMSO deve preservar:',
  '["acesso irrestrito","confidencialidade e guarda conforme a NR-07","eliminação imediata","uso para finalidade comercial"]'::jsonb,'1','Dados clínicos ocupacionais exigem confidencialidade, responsabilidade médica e conservação pelo período definido na norma.',38,2),

 (90,'O Programa de Gerenciamento de Riscos materializa-se no PGR, que deve conter ao menos:',
  '["balanço financeiro e organograma","folha de ponto e contrato social","inventário de riscos e plano de ação","apenas lista de EPIs"]'::jsonb,'2','Segundo a NR-01, o PGR contempla, no mínimo, o inventário de riscos ocupacionais e o plano de ação.',38,1),
 (90,'Na hierarquia de medidas de prevenção, deve-se priorizar:',
  '["EPI antes de qualquer análise","advertência ao empregado","pagamento de adicional","eliminação ou redução do risco por medidas coletivas e organizacionais"]'::jsonb,'3','A prevenção prioriza eliminar perigos e adotar proteção coletiva e organização do trabalho antes de depender exclusivamente de EPI.',38,2),
 (90,'O inventário de riscos ocupacionais deve registrar:',
  '["perigos, avaliações dos riscos e medidas de prevenção","somente acidentes já ocorridos","apenas nomes dos gestores","informações comerciais sem relação com SST"]'::jsonb,'0','O inventário consolida processos, perigos, possíveis lesões, grupos expostos, avaliação dos riscos e controles existentes.',38,2),
 (90,'Cabe à organização fornecer EPI ao empregado:',
  '["mediante cobrança integral","adequado ao risco, gratuitamente e em condições de uso","somente após acidente","sem orientação de uso"]'::jsonb,'1','A NR-06 atribui à organização o fornecimento gratuito de EPI adequado, aprovado e conservado, acompanhado de orientação e treinamento.',38,1),
 (90,'A participação dos trabalhadores no gerenciamento de riscos inclui:',
  '["ocultar perigos observados","dispensar treinamentos","comunicar riscos percebidos e colaborar com medidas preventivas","alterar registros sem autorização"]'::jsonb,'2','Comunicação de perigos e participação nas ações preventivas fortalecem o GRO e o funcionamento efetivo da CIPA.',38,2),

 (70,'A Lei nº 8.213/1991 define acidente do trabalho como o ocorrido pelo exercício do trabalho que provoque:',
  '["somente dano material","apenas atraso","qualquer desconforto passageiro","lesão ou perturbação funcional com morte ou perda ou redução da capacidade"]'::jsonb,'3','O art. 19 relaciona o acidente a lesão corporal ou perturbação funcional que cause morte ou redução, permanente ou temporária, da capacidade.',40,2),
 (70,'A empresa deve comunicar o acidente do trabalho à Previdência Social:',
  '["até o primeiro dia útil seguinte e, em caso de morte, imediatamente","apenas no fechamento anual","somente se houver afastamento superior a 30 dias","quando o empregado solicitar judicialmente"]'::jsonb,'0','O art. 22 da Lei nº 8.213/1991 fixa comunicação até o primeiro dia útil seguinte; em caso de morte, a comunicação é imediata.',40,2),
 (70,'Se a empresa não emitir a CAT, a comunicação pode ser feita, entre outros, pelo:',
  '["cliente da empresa apenas","próprio acidentado, dependentes, sindicato, médico ou autoridade pública","fornecedor estrangeiro apenas","ninguém além da empresa"]'::jsonb,'1','A omissão empresarial não impede a CAT: a lei legitima o acidentado, dependentes, sindicato, médico assistente e autoridade pública.',40,2),
 (70,'A doença profissional é aquela:',
  '["sem relação possível com trabalho","causada apenas fora da empresa","produzida ou desencadeada pelo exercício de trabalho peculiar a determinada atividade","decorrente exclusivamente da idade"]'::jsonb,'2','A Lei nº 8.213/1991 distingue doença profissional, ligada ao trabalho peculiar da atividade, e doença do trabalho, ligada às condições especiais.',40,2),
 (70,'O acidente ocorrido no trajeto entre residência e local de trabalho pode:',
  '["ser sempre ignorado","ser equiparado a acidente do trabalho nas condições legais","dispensar investigação","eliminar o dever de registro"]'::jsonb,'1','A legislação previdenciária prevê hipóteses de equiparação, incluindo o percurso residência-trabalho e vice-versa, observadas as circunstâncias legais.',40,2),

 (73,'O Capítulo V da CLT disciplina matérias relativas a:',
  '["segurança e medicina do trabalho","direito eleitoral","tributação internacional","processo penal"]'::jsonb,'0','Os arts. 154 e seguintes da CLT fundamentam as obrigações de segurança e saúde e a edição das Normas Regulamentadoras.',39,1),
 (73,'As Normas Regulamentadoras de segurança e saúde no trabalho:',
  '["são recomendações sem efeito","complementam as obrigações previstas na CLT","aplicam-se apenas a servidores estatutários","substituem todo acordo coletivo"]'::jsonb,'1','As NRs complementam o Capítulo V da CLT e estabelecem obrigações técnicas e administrativas de prevenção.',38,1),
 (73,'O empregado deve colaborar com a aplicação das normas de segurança e:',
  '["remover proteções de máquinas","recusar todo treinamento","usar corretamente o EPI fornecido","ocultar acidentes"]'::jsonb,'2','A prevenção é dever compartilhado: o trabalhador deve observar instruções, participar dos treinamentos e utilizar corretamente os equipamentos fornecidos.',38,1),
 (73,'A capacitação em segurança e saúde deve ocorrer:',
  '["sem conteúdo relacionado aos riscos","somente depois de acidente fatal","apenas para gestores","nos momentos e condições previstos nas NRs, com conteúdo adequado aos riscos"]'::jsonb,'3','Treinamentos iniciais, periódicos ou eventuais devem atender à NR aplicável e preparar o trabalhador para os riscos reais da atividade.',38,2),
 (73,'Diante de risco ocupacional grave e iminente, a conduta preventiva exige:',
  '["interromper a exposição e adotar medidas de controle conforme o procedimento aplicável","manter a tarefa sem avaliação","apagar o registro do risco","aguardar o exame demissional"]'::jsonb,'0','Risco grave e iminente demanda ação imediata para impedir exposição, comunicação e implementação de controles eficazes.',38,2)
), bloco as (
 select id from public.blocos where concurso_id=54 and titulo='Banco editorial EPTC — expansão 2026'
)
insert into public.questoes
 (bloco_id,topico_id,tipo,enunciado,alternativas,gabarito,explicacao,fonte_id,banca_estilo,materia,trilha,dificuldade)
select b.id,d.topico_id,'mcq',d.enunciado,d.alternativas,d.gabarito,d.explicacao,d.fonte_id,
       'FUNDATEC',t.nome,'EPTC Enfermagem do Trabalho',d.dificuldade
from dados d join public.topicos t on t.id=d.topico_id cross join bloco b
where not exists (select 1 from public.questoes q join public.blocos qb on qb.id=q.bloco_id
                  where qb.concurso_id=54 and lower(trim(q.enunciado))=lower(trim(d.enunciado)));

update public.questoes q set explicacao=case q.enunciado
 when 'A área de quadrado de lado 6 é:' then 'A área do quadrado é lado × lado: 6 × 6 = 36 unidades quadradas.'
 when 'A área de retângulo de 5 por 4 é:' then 'A área do retângulo é base × altura: 5 × 4 = 20 unidades quadradas.'
 when 'A média de 12, 15 e 18 é:' then 'A média aritmética é a soma dos valores dividida pela quantidade: (12 + 15 + 18) ÷ 3 = 15.'
 when 'A razão 3:5 equivale a:' then 'A razão 3:5 corresponde à fração 3/5, que resulta em 0,6 ou 60%.'
 when 'A razão entre 12 e 4 é:' then 'A razão entre 12 e 4 é calculada por 12 ÷ 4, resultando em 3.'
 else q.explicacao end
from public.blocos b
where b.id=q.bloco_id and b.titulo='Banco editorial EPTC — expansão 2026'
  and not exists(select 1 from public.respostas r where r.questao_id=q.id);

-- Corrige o viés posicional herdado sem tocar em itens já respondidos.
with escolhidas as (
 select q.id from public.questoes q join public.blocos b on b.id=q.bloco_id
 where b.concurso_id=53 and b.titulo='Banco editorial EPTC — expansão 2026'
   and b.criado_por='revisao-editorial'
   and q.tipo='mcq' and q.gabarito='0'
   and not exists(select 1 from public.respostas r where r.questao_id=q.id)
 order by q.id limit 12
)
update public.questoes q
set alternativas=(q.alternativas::jsonb - 0) || jsonb_build_array(q.alternativas::jsonb -> 0),
    gabarito=(jsonb_array_length(q.alternativas::jsonb)-1)::text
from escolhidas e where q.id=e.id;

update public.blocos set criado_por='revisao-editorial-balanceado'
where concurso_id in (53,54) and titulo='Banco editorial EPTC — expansão 2026'
  and criado_por='revisao-editorial';

do $$
begin
  if exists (
    select 1 from public.topicos t
    left join public.questoes q on q.topico_id=t.id
    where t.concurso_id in (53,54)
    group by t.id having count(q.id)<5
  ) then
    raise exception 'expansão EPTC incompleta: há tópico com menos de cinco questões';
  end if;
end $$;

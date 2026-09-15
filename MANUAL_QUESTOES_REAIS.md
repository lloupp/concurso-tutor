# Manual obrigatório — Questões reais de provas

## Regra principal

O Concurso Tutor **NÃO É um gerador de questões**.

Toda questão apresentada ao aluno deve ser uma **questão real, já aplicada em uma prova de concurso público**, reproduzida fielmente a partir de uma fonte verificável.

> **É proibido criar, inventar, adaptar, reescrever, parafrasear ou produzir questões apenas "no estilo" de uma banca.**

Se não houver uma questão real e verificável disponível para o tópico solicitado, o sistema deve informar que não encontrou uma questão adequada. **Nunca deve preencher a lacuna criando uma nova questão.**

## O que significa "igual à prova"

Para ser aceita no banco, a questão deve preservar o conteúdo da prova original:

- enunciado;
- textos de apoio;
- comandos;
- alternativas ou itens de julgamento;
- ordem das alternativas, quando aplicável;
- imagens, tabelas ou referências necessárias para resolver a questão;
- gabarito oficial;
- condição especial, quando existir, como questão anulada ou gabarito alterado.

São permitidas apenas normalizações técnicas que **não alterem o conteúdo**, como correção de encoding, espaços duplicados ou formatação para exibição. Correções de OCR só podem ser feitas após comparação com a prova original.

## É proibido

- criar uma questão inédita com IA;
- pedir a uma IA para escrever questões "no estilo Cebraspe", "no estilo FGV", "no estilo FCC" etc.;
- transformar uma questão existente em outra;
- trocar nomes, números, contexto ou alternativas para gerar uma variação;
- resumir ou parafrasear o enunciado;
- combinar partes de questões diferentes;
- inventar alternativas;
- inferir ou inventar um gabarito sem confirmação;
- publicar uma questão sem conseguir identificar sua origem;
- usar uma fonte secundária como se fosse prova original quando a fonte oficial estiver disponível.

## Fonte e rastreabilidade obrigatórias

Toda questão deve possuir metadados suficientes para permitir auditoria. Sempre que disponíveis, registrar:

- banca;
- órgão ou instituição;
- concurso;
- cargo;
- ano e data da prova;
- disciplina;
- número da questão na prova;
- tipo/caderno da prova, quando houver;
- URL ou identificação do arquivo da prova de origem;
- URL ou identificação do gabarito oficial;
- gabarito oficial;
- situação da questão: válida, anulada ou com gabarito alterado.

A fonte preferencial é sempre a **prova e o gabarito publicados pela própria banca ou pelo órgão responsável**. Outras fontes podem auxiliar na localização, mas a questão deve ser confrontada com uma origem confiável antes de ser publicada.

## Regra de falha segura

Na dúvida, **não publicar**.

Uma questão deve ser rejeitada quando:

1. não for possível confirmar que ela realmente foi aplicada;
2. o texto estiver incompleto ou ilegível;
3. houver divergência entre transcrições sem acesso à prova original;
4. o gabarito não puder ser confirmado;
5. faltar parte indispensável, como imagem, tabela ou texto-base;
6. a origem da questão não puder ser rastreada.

A ausência de questões para determinado tópico **não autoriza geração por IA**.

## Papel permitido para a IA

A IA pode trabalhar **sobre uma questão real já armazenada**, sem modificar seu conteúdo original, para:

- explicar o gabarito;
- produzir comentário pedagógico;
- identificar disciplina e assunto;
- associar a questão a tópicos do edital;
- estimar dificuldade;
- explicar por que alternativas estão certas ou erradas;
- sugerir revisão teórica;
- auxiliar na extração/OCR, desde que o resultado seja validado contra a fonte;
- localizar provas e questões candidatas para posterior validação.

A explicação da IA deve ficar em campo separado. **Nunca deve substituir nem modificar o texto original da questão.**

## Comportamento da plataforma

### Banco de questões

O banco deve funcionar como um repositório de questões reais, não como um gerador de perguntas.

### Seleção de questões

Quando o aluno pedir novas questões, o sistema deve:

1. pesquisar o banco de questões reais;
2. filtrar por concurso, banca, disciplina, tópico, nível ou outros critérios;
3. evitar repetição quando possível;
4. entregar outra questão real já validada.

Se não houver questão compatível, deve retornar algo equivalente a:

> Não há outra questão real validada disponível para este filtro.

### Interface

Evitar expressões que sugiram geração artificial, como **"Gerar mais questões"**. Preferir, conforme o contexto:

- "Carregar mais questões";
- "Buscar outras questões";
- "Próxima questão";
- "Mais questões de provas".

Sempre que possível, a interface deve exibir a identificação da origem, por exemplo:

> Cebraspe · INSS · Técnico do Seguro Social · 2022

## Estrutura mínima recomendada

Exemplo conceitual de registro:

```json
{
  "enunciado": "Texto exatamente conforme a prova...",
  "alternativas": ["...", "...", "...", "..."],
  "gabarito": "B",
  "banca": "...",
  "orgao": "...",
  "concurso": "...",
  "cargo": "...",
  "ano": 2025,
  "disciplina": "...",
  "numero_questao": 12,
  "prova_fonte": "...",
  "gabarito_fonte": "...",
  "status": "valida",
  "explicacao_ia": "Comentário pedagógico separado do texto original."
}
```

O schema definitivo pode variar, mas **proveniência e fidelidade ao original são obrigatórias**.

## Critério de aceite para qualquer nova questão

Antes de entrar em produção, todas as respostas abaixo devem ser **SIM**:

1. Esta questão realmente apareceu em uma prova?
2. A prova de origem pode ser identificada?
3. O texto foi conferido com a fonte?
4. As alternativas/itens são os mesmos da prova?
5. O gabarito foi conferido em fonte confiável, preferencialmente oficial?
6. Os metadados permitem localizar novamente a prova?
7. Nenhuma parte da questão foi criada, adaptada ou completada por IA?

Se qualquer resposta for **NÃO**, a questão **não deve ser publicada**.

## Regra para agentes, automações e contribuidores

Qualquer agente de IA, script, importador, colaborador ou automação que trabalhe neste repositório deve obedecer a este manual.

Quando houver conflito entre este documento e instruções antigas que autorizem "criar", "gerar", "adaptar" ou produzir questões "no estilo" de uma banca, **este manual prevalece**.

**Resumo obrigatório:** o Concurso Tutor usa questões reais de provas. A IA pode localizar, organizar, classificar e explicar essas questões, mas **não pode criar questões**.
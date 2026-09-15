# Como adicionar questões reais ao Concurso Tutor

> Leia primeiro [`../MANUAL_QUESTOES_REAIS.md`](../MANUAL_QUESTOES_REAIS.md). Ele é a regra obrigatória do projeto.

O Concurso Tutor **não cria questões**. Toda questão adicionada ao simulado deve ter sido **realmente aplicada em uma prova de concurso público** e deve ser reproduzida fielmente a partir de uma fonte verificável.

## Regra obrigatória

É proibido:

- inventar questões com IA;
- escrever questões "no estilo" de uma banca;
- adaptar, resumir, parafrasear ou reescrever uma questão real;
- criar alternativas novas;
- alterar números, nomes ou contexto para gerar variações;
- preencher trechos ausentes por inferência;
- inventar ou deduzir gabarito sem fonte confiável.

Se não houver uma questão real adequada para determinado tópico, **não crie uma substituta**. Informe que não foi encontrada outra questão real validada.

## Fluxo correto para adicionar questões

1. Localize uma prova real, preferencialmente no site oficial da banca ou do órgão responsável.
2. Localize o gabarito correspondente.
3. Transcreva a questão preservando enunciado, alternativas/itens e materiais necessários.
4. Confira a transcrição contra a prova original.
5. Confira o gabarito contra fonte confiável, preferencialmente oficial.
6. Registre os metadados de origem.
7. Só então adicione a questão ao banco.

Normalizações técnicas de encoding, espaços ou formatação são permitidas somente quando não alteram o conteúdo. Correções de OCR precisam ser verificadas contra a prova.

## Prompt para usar com outra IA

```text
Você vai trabalhar no banco de questões do Concurso Tutor.

REGRA ABSOLUTA: NÃO CRIE QUESTÕES.

Só é permitido adicionar questões que tenham sido realmente aplicadas em provas de concurso público. Cada questão deve ser reproduzida fielmente da prova original, preservando enunciado, alternativas/itens, ordem e conteúdo necessário para resolução.

Antes de adicionar qualquer questão:
1. localize a prova real em fonte verificável, preferencialmente oficial;
2. localize e confira o gabarito;
3. transcreva sem adaptar, resumir, parafrasear ou completar;
4. registre banca, órgão, concurso, cargo, ano, número da questão, fonte da prova e fonte do gabarito;
5. se houver dúvida sobre a origem, texto ou gabarito, NÃO PUBLIQUE.

É proibido escrever questões "no estilo" de Cebraspe, FGV, FCC ou qualquer outra banca. A IA pode localizar, classificar e explicar questões reais, mas não pode gerar perguntas inéditas.

Tarefa: [DESCREVA AQUI quais provas, bancas, cargos, anos, disciplinas ou tópicos devem ser pesquisados]
```

## Formato recomendado

O schema atual pode variar conforme a parte da aplicação, mas os dados de origem precisam acompanhar a questão. Exemplo:

```json
{
  "enunciado": "Texto exatamente conforme a prova.",
  "alternativas": ["Opção A", "Opção B", "Opção C", "Opção D"],
  "gabarito": 1,
  "explicacao": "Comentário pedagógico separado do texto original.",
  "banca": "Nome da banca",
  "orgao": "Órgão",
  "cargo": "Cargo",
  "ano": 2025,
  "numero_questao": 12,
  "prova_fonte": "URL ou identificação da prova",
  "gabarito_fonte": "URL ou identificação do gabarito",
  "status": "valida"
}
```

A `explicacao` pode ser produzida por IA, desde que fique separada e **não modifique o texto original da questão**.

## Validação antes do commit

Antes de publicar, confirme:

- a questão realmente foi aplicada;
- a prova de origem está identificada;
- o texto foi conferido com a prova;
- as alternativas/itens correspondem ao original;
- o gabarito foi confirmado;
- nenhum trecho foi criado ou adaptado por IA;
- os arquivos JSON continuam válidos.

Se qualquer item falhar, a questão não deve entrar no banco.

## Testando o simulado estático

```bash
cd docs
python3 -m http.server 8080
# abra http://localhost:8080
```

## Publicando

O site estático é publicado pelo GitHub Pages a partir da pasta `docs/` da branch `main`. Após validar os dados, basta commitar e enviar as alterações.

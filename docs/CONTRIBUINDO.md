# Como adicionar mais questões ao Simulado Ensino Médio

Este site é 100% estático: cada matéria é um arquivo JSON em `docs/data/`,
carregado direto pelo navegador (sem backend).

**Em 2026-09-15, todas as questões anteriores foram removidas** (colocadas
em quarentena e retiradas do JSON) porque nenhuma tinha comprovação de
origem numa prova real aplicada — eram formuladas/parafraseadas com base em
leis, editais ou fatos institucionais gerais, o que não é prova de origem
de uma questão. Ver `AUDITORIA_QUESTOES_REAIS.md` na raiz do repositório.

## REGRA ABSOLUTA

**Proibido gerar, formular, adaptar, parafrasear ou escrever questões "no
estilo" de concurso/Enem.** Uma questão só pode ser adicionada aqui se for
a transcrição fiel de uma questão **efetivamente aplicada** numa prova real
(concurso público ou Enem), com:

- banca/instituição aplicadora, órgão, concurso/edição, ano;
- nome/número do caderno de prova e número da questão;
- URL da prova original (idealmente com a página);
- gabarito oficial definitivo.

Uma lei, edital, manual ou site de estudos **não é prova de origem** — só
mostra que o assunto cai em prova, não que aquela questão específica existe
numa prova aplicada. Se você não encontrar a prova original com gabarito
oficial, **não adicione a questão** — deixe a matéria com menos itens.

## Formato de cada arquivo `docs/data/<materia>.json`

```json
{
  "materia": "Nome de exibição da matéria",
  "questoes": [
    {
      "enunciado": "Texto EXATO da prova aplicada.",
      "alternativas": ["Opção A", "Opção B", "Opção C", "Opção D"],
      "gabarito": 1,
      "explicacao": "Opcional: por que a alternativa correta está certa (pode citar a lei/conceito).",
      "fonte": {
        "banca": "Nome da banca/instituição",
        "orgao": "Órgão/instituição do concurso",
        "concurso": "Nome do concurso/edição",
        "ano": 2023,
        "prova": "Nome ou código do caderno",
        "numero_questao": "23",
        "url_prova": "https://.../prova.pdf",
        "gabarito_oficial": "B"
      }
    }
  ]
}
```

- `alternativas`: array com exatamente 4 strings, na ordem original da
  prova (sem prefixo "A)", "B)" — o site adiciona a letra automaticamente).
  Se a prova original tiver mais/menos alternativas ou for certo/errado,
  preserve o formato original em vez de forçar 4 opções.
- `gabarito`: índice 0-based da alternativa correta, conforme o gabarito
  oficial (não resolva a questão você mesmo).
- `fonte`: **obrigatório** para toda questão nova — sem ele a questão não
  deve ser adicionada.

## Registrando uma matéria nova

Depois de criar o JSON, adicione uma linha no array `MATERIAS` no topo de
`docs/app.js`:

```js
{ id: "legislacao_especifica", nome: "Legislação Específica", arquivo: "data/legislacao_especifica.json" },
```

O `id` deve ser único, em minúsculas, sem espaços ou acentos.

## Testando localmente

```bash
cd docs
python3 -m http.server 8080
# abra http://localhost:8080
```

## Publicando

O site é publicado via GitHub Pages a partir da pasta `docs/` na branch
`main`. Basta commitar e dar push nas mudanças em `docs/` — o Pages
atualiza automaticamente.

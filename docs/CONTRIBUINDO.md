# Como adicionar mais questões ao Simulado Ensino Médio

Este documento é um manual para você (ou outra IA) usar como prompt/roteiro ao
pedir para popular o simulado com mais questões. O site é 100% estático: cada
matéria é um arquivo JSON em `docs/data/`, carregado direto pelo navegador
(sem backend).

## Prompt pronto para colar em outra IA

```
Você vai adicionar questões ao simulado estático em docs/ do repositório
concurso-tutor. É um quiz de múltipla escolha no estilo de concursos
públicos de nível médio (cargos como Assistente/Auxiliar Administrativo,
Técnico) — atualmente cobre Português, Matemática/Raciocínio Lógico,
Informática, Direito Constitucional (noções), Direito Administrativo
(noções) e Atualidades/Conhecimentos Gerais — sem backend: cada matéria é
um arquivo JSON em docs/data/.

Regras:
1. NÃO invente fatos incertos (datas, artigos de lei, números). Use apenas
   conteúdo consagrado de concursos de nível médio (CF/88, princípios da
   Administração Pública, informática básica, etc.), ancorado em fontes
   reais. Se tiver dúvida sobre um fato, pesquise antes de escrever a
   questão. Em "Atualidades", prefira fatos institucionais estáveis
   (ONU, Mercosul, SUS, IBGE etc.) em vez de notícias recentes que ficam
   desatualizadas rápido.
2. Sempre 4 alternativas por questão, só uma correta.
3. "gabarito" é o índice da alternativa correta, começando em 0
   (0 = primeira alternativa, 1 = segunda, etc.).
4. Toda questão deve ter "explicacao": 1-2 frases justificando a resposta
   correta.
5. Para adicionar questões a uma matéria já existente: edite o arquivo
   docs/data/<materia>.json e acrescente objetos ao array "questoes",
   seguindo exatamente o formato abaixo.
6. Para criar uma matéria nova: crie docs/data/<nome>.json no mesmo formato
   e adicione uma linha em MATERIAS no início de docs/app.js:
   { id: "<nome>", nome: "<Nome de exibição>", arquivo: "data/<nome>.json" }
7. Não altere a lógica do quiz (docs/app.js) além dessa linha do MATERIAS,
   nem o layout (docs/styles.css), a menos que peçam explicitamente.
8. Depois de editar, valide que todo JSON é válido (sem vírgula sobrando,
   aspas corretas) antes de commitar.

Tarefa: [DESCREVA AQUI quantas questões, quais matérias/tópicos você quer]
```

## Formato de cada arquivo `docs/data/<materia>.json`

```json
{
  "materia": "Nome de exibição da matéria",
  "questoes": [
    {
      "enunciado": "Texto da pergunta.",
      "alternativas": ["Opção A", "Opção B", "Opção C", "Opção D"],
      "gabarito": 1,
      "explicacao": "Por que a alternativa correta está certa."
    }
  ]
}
```

- `alternativas`: sempre um array com exatamente 4 strings (sem prefixo
  "A)", "B)" — o site adiciona a letra automaticamente).
- `gabarito`: número inteiro (índice 0-based) da alternativa correta.
- `explicacao`: opcional, mas recomendado — aparece na correção.

## Registrando uma matéria nova

Se for criar uma matéria que ainda não existe (ex.: Inglês, Atualidades,
Redação/Interpretação), depois de criar o JSON adicione uma linha no array
`MATERIAS` no topo de `docs/app.js`:

```js
{ id: "legislacao_especifica", nome: "Legislação Específica", arquivo: "data/legislacao_especifica.json" },
```

O `id` deve ser único, em minúsculas, sem espaços ou acentos.

## Testando localmente

Como é um site estático, basta servir a pasta `docs/` com qualquer servidor
HTTP simples (abrir o `index.html` direto com `file://` pode falhar por causa
do `fetch` dos JSONs):

```bash
cd docs
python3 -m http.server 8080
# abra http://localhost:8080
```

## Publicando

O site é publicado via GitHub Pages a partir da pasta `docs/` na branch
`main` (ver instruções no README principal do repositório). Basta commitar e
dar push nas mudanças em `docs/` — o Pages atualiza automaticamente.

// Simulado Ensino Médio — quiz estático, sem backend (roda 100% no navegador via GitHub Pages)

// Manifesto das matérias disponíveis. Para adicionar uma nova, crie o JSON em
// docs/data/ (ver docs/CONTRIBUINDO.md) e inclua uma linha aqui.
const MATERIAS = [
  { id: "portugues", nome: "Português", arquivo: "data/portugues.json" },
  { id: "matematica", nome: "Matemática/RLM", arquivo: "data/matematica.json" },
  { id: "informatica", nome: "Informática", arquivo: "data/informatica.json" },
  { id: "direito_constitucional", nome: "Direito Constitucional", arquivo: "data/direito_constitucional.json" },
  { id: "direito_administrativo", nome: "Direito Administrativo", arquivo: "data/direito_administrativo.json" },
  { id: "atualidades", nome: "Atualidades", arquivo: "data/atualidades.json" },
];

let BANCO = {};      // { materiaId: { materia, questoes: [...] } }
let QUESTOES = [];    // questões selecionadas para a rodada atual, com id único

function embaralhar(arr) {
  const a = arr.slice();
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

async function carregarBanco() {
  const box = document.getElementById("materiasBox");
  try {
    const resultados = await Promise.all(
      MATERIAS.map(m => fetch(m.arquivo).then(r => {
        if (!r.ok) throw new Error(`falha ao carregar ${m.arquivo}`);
        return r.json();
      }))
    );
    MATERIAS.forEach((m, i) => { BANCO[m.id] = resultados[i]; });
  } catch (e) {
    box.innerHTML = "<p class='errbox'>Não foi possível carregar as questões: " + e.message + "</p>";
    return;
  }
  box.innerHTML = "";
  MATERIAS.forEach(m => {
    const total = BANCO[m.id].questoes.length;
    const label = document.createElement("label");
    label.className = "materia-check";
    label.innerHTML = `<input type="checkbox" value="${m.id}" checked />
      <span>${m.nome}</span>
      <span class="count">${total} questões</span>`;
    box.appendChild(label);
  });
}

function materiasSelecionadas() {
  return Array.from(document.querySelectorAll("#materiasBox input:checked")).map(i => i.value);
}

function montarQuestoes(ids) {
  const todas = [];
  ids.forEach(id => {
    BANCO[id].questoes.forEach((q, i) => {
      todas.push({ ...q, uid: `${id}-${i}`, materia: BANCO[id].materia });
    });
  });
  return embaralhar(todas);
}

function iniciarSimulado() {
  const err = document.getElementById("configErr");
  const ids = materiasSelecionadas();
  if (!ids.length) {
    err.textContent = "Selecione ao menos uma matéria.";
    return;
  }
  err.textContent = "";
  QUESTOES = montarQuestoes(ids);

  document.getElementById("config").hidden = true;
  document.getElementById("resultado").hidden = true;
  const quiz = document.getElementById("quiz");
  quiz.hidden = false;

  document.getElementById("quizInfo").innerHTML = `
    <div class="protocolo">
      <p class="eyebrow">Simulado</p>
      <h2>${ids.map(id => BANCO[id].materia).join(" · ")}</h2>
      <div class="protocolo-meta">
        <div><span>Questões</span><b>${QUESTOES.length}</b></div>
        <div><span>Tipo</span><b>Múltipla escolha</b></div>
        <div><span>Correção</span><b>Automática</b></div>
      </div>
    </div>`;

  const form = document.getElementById("formQuiz");
  form.innerHTML = "";
  QUESTOES.forEach((q, i) => {
    const div = document.createElement("div");
    div.className = "q";
    div.dataset.uid = q.uid;
    let inner = `
      <div class="q-head">
        <span class="q-num">Q${i + 1}</span>
        <span class="q-type">${q.materia}</span>
      </div>
      <p class="q-body">${q.enunciado}</p>
      <div class="bubbles">`;
    q.alternativas.forEach((a, ai) => {
      const letra = String.fromCharCode(65 + ai);
      inner += `<label class="bubble-option">
        <input type="radio" name="${q.uid}" value="${ai}" hidden />
        <span class="bubble">${letra}</span>
        <span class="opt-text">${a}</span>
      </label>`;
    });
    inner += `</div>`;
    div.innerHTML = inner;
    form.appendChild(div);
  });

  window.scrollTo({ top: 0, behavior: "smooth" });
}

function corrigirSimulado() {
  let acertos = 0;
  const linhas = [];

  QUESTOES.forEach((q, i) => {
    const div = document.querySelector(`.q[data-uid="${q.uid}"]`);
    const marcado = div.querySelector("input[type=radio]:checked");
    const valor = marcado ? parseInt(marcado.value, 10) : null;
    const correta = valor === q.gabarito;
    if (correta) acertos++;

    // marca visualmente as opções na própria pergunta
    div.querySelectorAll(".bubble-option").forEach((opt, ai) => {
      if (ai === q.gabarito) opt.classList.add("opt-correct");
      else if (ai === valor) opt.classList.add("opt-wrong");
      opt.querySelector("input").disabled = true;
    });
    if (q.explicacao) {
      const exp = document.createElement("p");
      exp.className = "q-explicacao";
      exp.textContent = q.explicacao;
      div.appendChild(exp);
    }

    linhas.push({ i: i + 1, materia: q.materia, correta });
  });

  document.getElementById("btnEnviar").hidden = true;

  const pct = Math.round((acertos / QUESTOES.length) * 100);
  const box = document.getElementById("resultado");
  box.hidden = false;
  let html = `
    <div class="resultado-score">
      <p class="eyebrow">Resultado</p>
      <div class="valor">${acertos}<span>/${QUESTOES.length}</span></div>
      <p class="legenda">${pct}% de acerto</p>
    </div>`;
  linhas.forEach(r => {
    html += `<div class="stamp-row">
      <span class="stamp ${r.correta ? "stamp-ok" : "stamp-bad"}">${r.correta ? "Correto" : "Errado"}</span>
      <span>Q${r.i} · ${r.materia}</span>
    </div>`;
  });
  html += `<button id="btnRefazer" class="btn-ghost">Fazer novo simulado</button>`;
  box.innerHTML = html;
  document.getElementById("btnRefazer").onclick = voltarConfig;

  box.scrollIntoView({ behavior: "smooth" });
}

function voltarConfig() {
  document.getElementById("quiz").hidden = true;
  document.getElementById("resultado").hidden = true;
  document.getElementById("btnEnviar").hidden = false;
  document.getElementById("config").hidden = false;
  window.scrollTo({ top: 0, behavior: "smooth" });
}

document.getElementById("btnIniciar").onclick = iniciarSimulado;
document.getElementById("btnEnviar").onclick = corrigirSimulado;

carregarBanco();

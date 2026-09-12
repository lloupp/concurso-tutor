const API = "/api";
let TOKEN = localStorage.getItem("ct_token") || null;
let ME = null;
let CONCURSOS = [];              // trilhas disponíveis apenas para cadastro
let CONCURSO = null;             // trilha fixa do aluno

// carrega trilhas somente para o cadastro
async function carregarPerfis() {
  try {
    const data = await fetch(API + "/concursos").then(r => { if (!r.ok) throw new Error("erro"); return r.json(); });
    CONCURSOS = data.concursos;
  } catch (e) { console.error("perfis", e); return; }
  if (CONCURSOS.length) {
    document.getElementById("cadTrilha").innerHTML =
      CONCURSOS.filter(c => c.id === 51 || c.id === 52).map(c => `<option value="${c.id}">${c.nome}</option>`).join("");
  }
}

// define o perfil ativo e sincroniza o select do topo
function setPerfil(id) {
  CONCURSO = id;
  localStorage.setItem("ct_concurso", id);
}

function novoTomarPerfil() {
  localStorage.removeItem("ct_concurso");
}

async function api(path, opts = {}) {
  opts.headers = opts.headers || {};
  if (TOKEN) opts.headers["Authorization"] = "Bearer " + TOKEN;
  if (opts.body) opts.headers["Content-Type"] = "application/json";
  const r = await fetch(API + path, opts);
  if (!r.ok) {
    const t = await r.text();
    throw new Error(t || r.status);
  }
  return r.json();
}

function domLevel(d) {
  if (d >= 0.85) return "ok";
  if (d >= 0.6) return "warn";
  return "bad";
}

async function login(u, p) {
  try {
    const data = await api("/login", { method: "POST", body: JSON.stringify({ username: u, password: p }) });
    TOKEN = data.token; ME = data.user;
    localStorage.setItem("ct_token", TOKEN);
    setPerfil(ME.concurso_id);
    showApp();
  } catch (e) {
    document.getElementById("loginErr").textContent = "Falha: " + e.message;
  }
}

async function cadastro() {
  const msg = document.getElementById("cadastroMsg");
  try {
    await api("/cadastro", { method: "POST", body: JSON.stringify({
      full_name: document.getElementById("cadNome").value,
      username: document.getElementById("cadUsuario").value,
      password: document.getElementById("cadSenha").value,
      concurso_id: parseInt(document.getElementById("cadTrilha").value, 10),
      tempo_diario: parseInt(document.getElementById("cadTempo").value, 10),
    }) });
    msg.textContent = "Perfil criado. Agora entre com seu usuário e senha.";
  } catch (e) { msg.textContent = "Não foi possível criar: " + e.message; }
}

function logout() {
  TOKEN = null; ME = null; localStorage.removeItem("ct_token"); novoTomarPerfil();
  document.getElementById("app").hidden = true;
  document.getElementById("login").hidden = false;
  document.getElementById("topbar").hidden = true;
}

async function showApp() {
  document.getElementById("login").hidden = true;
  document.getElementById("app").hidden = false;
  document.getElementById("topbar").hidden = false;
  document.getElementById("userinfo").textContent = `${ME.full_name} (${ME.role})`;
  await carregarBloco();
  await carregarBlocos();
  await carregarProgresso();
  await carregarPlano();
}

// renderiza o bloco (do dia ou escolhido) no form; aceita bloco_id opcional
async function carregarBloco(blocoId = null) {
  const box = document.getElementById("blocoInfo");
  const form = document.getElementById("formBloco");
  document.getElementById("resultado").innerHTML = "";
  try {
    const path = blocoId ? `/bloco/${blocoId}` : "/bloco/hoje";
    const { bloco } = await api(path);
    if (!bloco) {
      box.innerHTML = "<p class='warn-box'>Nenhum bloco para hoje. Peça ao Hermes para gerar.</p>";
      form.innerHTML = "";
      return;
    }
    box.innerHTML = `
      <div class="protocolo">
        <p class="eyebrow">Bloco de estudo</p>
        <h2>${bloco.titulo}</h2>
        <p class="intro">${bloco.introducao}</p>
        <div class="protocolo-meta">
          <div><span>Data</span><b>${bloco.data}</b></div>
          <div><span>Duração</span><b>${bloco.duracao_min} min</b></div>
          <div><span>Questões</span><b>${bloco.questoes.length}</b></div>
        </div>
      </div>`;
    form.innerHTML = "";
    bloco.questoes.forEach((q, i) => {
      const div = document.createElement("div");
      div.className = "q";
      let inner = `
        <div class="q-head">
          <span class="q-num">Q${i + 1}</span>
          <span class="q-type">${q.tipo === "mcq" ? "Objetiva" : q.tipo === "verdadeiro_falso" ? "Certo ou errado" : q.tipo === "numerica" ? "Resposta numérica" : "Legada"}</span>
        </div>
        ${q.texto_base ? `<div class="texto-base">${q.texto_base}</div>` : ""}
        <p class="q-body">${q.enunciado}</p>`;
      const anterior = q.resposta_anterior;
      if (q.tipo === "mcq") {
        inner += `<div class="bubbles">`;
        q.alternativas.forEach((a, ai) => {
          const letra = String.fromCharCode(65 + ai);
          const texto = a.replace(/^[A-Za-z]\)\s*/, "");
          inner += `<label class="bubble-option">
            <input type="radio" name="q${q.id}" value="${ai}" ${anterior && anterior.resposta === String(ai) ? "checked" : ""} hidden />
            <span class="bubble">${letra}</span>
            <span class="opt-text">${texto}</span>
          </label>`;
        });
        inner += `</div>`;
      } else if (q.tipo === "verdadeiro_falso") {
        inner += `<div class="bubbles">
          <label class="bubble-option"><input type="radio" name="q${q.id}" value="true" ${anterior && anterior.resposta === "true" ? "checked" : ""} hidden /><span class="bubble">C</span><span class="opt-text">Certo</span></label>
          <label class="bubble-option"><input type="radio" name="q${q.id}" value="false" ${anterior && anterior.resposta === "false" ? "checked" : ""} hidden /><span class="bubble">E</span><span class="opt-text">Errado</span></label>
        </div>`;
      } else if (q.tipo === "numerica") {
        inner += `<input class="numeric-answer" type="text" inputmode="decimal" name="q${q.id}" value="${anterior ? anterior.resposta : ""}" placeholder="Sua resposta${q.unidade ? ` (${q.unidade})` : ""}" />`;
      } else {
        inner += `<textarea class="ruled" name="q${q.id}" placeholder="Sua resposta discursiva..."></textarea>`;
      }
      if (anterior) {
        const estado = anterior.correta ? "Correto" : "A revisar";
        const detalhe = anterior.feedback || "Resposta registrada.";
        const explicacao = q.explicacao && !detalhe.includes(q.explicacao) ? ` ${q.explicacao}` : "";
        inner += `<div class="answer-history"><b>${estado}</b> · ${detalhe}${explicacao}</div>`;
      }
      div.innerHTML = inner;
      form.appendChild(div);
    });
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "btn-stamp";
    btn.textContent = "Enviar respostas";
    btn.onclick = enviarRespostas;
    form.appendChild(btn);
  } catch (e) { box.innerHTML = "<p class='errbox'>" + e.message + "</p>"; }
}

// lista os blocos do perfil no seletor (conteúdo completo)
async function carregarBlocos() {
  const sel = document.getElementById("seletorBloco");
  try {
    const { blocos } = await api("/blocos");
    sel.innerHTML = `<option value="">— hoje —</option>` +
      blocos.map(b => `<option value="${b.id}">${b.data} · ${b.titulo}</option>`).join("");
  } catch (e) { sel.innerHTML = "<option value=''>—</option>"; }
}

async function abrirBlocoSelecionado() {
  const sel = document.getElementById("seletorBloco");
  if (!sel.value) { await carregarBloco(); return; }
  await carregarBloco(sel.value);
}

async function enviarRespostas() {
  const form = document.getElementById("formBloco");
  const respostas = [];
  form.querySelectorAll(".q").forEach(qdiv => {
    const radio = qdiv.querySelector('input[type=radio]:checked');
    const anyRadio = qdiv.querySelector("input[type=radio]");
      const ta = qdiv.querySelector("textarea");
    const numeric = qdiv.querySelector(".numeric-answer");
    const ref = radio || anyRadio || ta || numeric;
    if (!ref) return;
    if (anyRadio && !radio) return;
    if (numeric && !numeric.value.trim()) return;
    if (ta && !ta.value.trim()) return;
    const id = parseInt(ref.name.replace("q", ""));
    const val = radio ? radio.value : (numeric ? numeric.value : (ta ? ta.value : ""));
    respostas.push({ questao_id: id, resposta: val });
  });
  try {
    const out = await api("/bloco/responder", { method: "POST", body: JSON.stringify({ respostas }) });
    let html = `<div class="correcao"><p class="eyebrow">Gabarito</p>`;
    out.resultados.forEach(r => {
      const cls = r.correta === true ? "stamp-ok" : (r.correta === false ? "stamp-bad" : "stamp-pending");
      const label = r.correta === true ? "Correto" : (r.correta === false ? "A revisar" : "Legada");
      const detalhe = r.feedback || "";
      const explicacao = r.explicacao && !detalhe.includes(r.explicacao) ? " " + r.explicacao : "";
      html += `<div class="stamp-row"><span class="stamp ${cls}">${label}</span><span class="stamp-detail">Q${r.questao_id}${detalhe ? " · " + detalhe : ""}${explicacao}</span></div>`;
    });
    html += "</div>";
    document.getElementById("resultado").innerHTML = html;
    await carregarProgresso();
  } catch (e) {
    document.getElementById("resultado").innerHTML = "<p class='errbox'>" + e.message + "</p>";
  }
}

async function carregarProgresso() {
  const box = document.getElementById("heatmap");
  const cov = document.getElementById("cobertura");
  try {
    const { dominancia, cobertura, dashboard } = await api("/progresso");
    cov.innerHTML = `<p class="cobertura-valor">${cobertura.pct}%<span>cobertura do edital · ${cobertura.estudados}/${cobertura.total} tópicos</span></p>`;
    document.getElementById("dashboardCards").innerHTML = [
      ["Domínio médio", `${dashboard.dominio_medio}%`], ["Respondidas", dashboard.questoes_respondidas],
      ["Acertos", dashboard.acertos], ["Taxa de acerto", `${dashboard.taxa_acerto}%`],
      ["Revisões pendentes", dashboard.revisoes_pendentes], ["Matérias iniciadas", `${dashboard.materias_iniciadas}/${dashboard.materias_total}`],
    ].map(([label, value]) => `<div class="dashboard-card"><span>${label}</span><b>${value}</b></div>`).join("");
    box.innerHTML = "";
    dominancia.forEach(d => {
      const level = domLevel(d.dominio);
      const pct = Math.round(d.dominio * 100);
      const row = document.createElement("div");
      row.className = "boletim-row";
      row.innerHTML = `
        <span class="boletim-nome">${d.nome}</span>
        <span class="boletim-bar"><span class="boletim-fill ${level}" style="width:${pct}%"></span></span>
        <span class="boletim-pct ${level}">${pct}%</span>
        <span class="boletim-tent">${d.tentativas} tent.</span>`;
      box.appendChild(row);
    });
  } catch (e) { box.innerHTML = "<p class='errbox'>" + e.message + "</p>"; }
}

async function carregarPlano() {
  const box = document.getElementById("planoLista");
  try {
    const { proximos_topicos } = await api("/plano");
    box.innerHTML = proximos_topicos.length
      ? proximos_topicos.map((t, i) => `<div class="agenda-item"><span class="agenda-num">${String(i + 1).padStart(2, "0")}</span><span>${t.nome}</span></div>`).join("")
      : "<p class='agenda-empty'>Tudo coberto e em dia ✓</p>";
  } catch (e) { box.innerHTML = "<p class='errbox'>" + e.message + "</p>"; }
}

// Eventos
document.getElementById("btnLogin").onclick = () => {
  login(document.getElementById("username").value, document.getElementById("password").value);
};
document.getElementById("btnCadastro").onclick = cadastro;
document.getElementById("logout").onclick = logout;
document.querySelectorAll(".tabs button").forEach(b => {
  b.onclick = () => {
    document.querySelectorAll(".tabs button").forEach(x => x.classList.remove("active"));
    b.classList.add("active");
    document.querySelectorAll(".tabpanel").forEach(p => p.hidden = true);
    document.getElementById("tab-" + b.dataset.tab).hidden = false;
  };
});

// boot: carrega trilhas e restaura sessão
(async function boot() {
  await carregarPerfis();
  const salvo = parseInt(localStorage.getItem("ct_concurso"), 10);
  if (CONCURSOS.length) {
    if (CONCURSOS.some(c => c.id === salvo)) setPerfil(salvo);
  }
  if (TOKEN) {
    api("/me").then(u => { ME = u; showApp(); }).catch(() => logout());
  }
})();

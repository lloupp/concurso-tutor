const API = "/api";
let TOKEN = localStorage.getItem("ct_token") || null;
let ME = null;
let CONCURSOS = [];              // perfis disponíveis
let CONCURSO = null;             // perfil ativo (id)

// carrega perfis no início (tela de login) e popula os dois selects
async function carregarPerfis() {
  try {
    const data = await fetch(API + "/concursos").then(r => { if (!r.ok) throw new Error("erro"); return r.json(); });
    CONCURSOS = data.concursos;
  } catch (e) { console.error("perfis", e); return; }
  if (CONCURSOS.length) {
    document.getElementById("perfilLogin").innerHTML =
      CONCURSOS.map(c => `<option value="${c.id}">${c.cargo} · ${c.nome}</option>`).join("");
    document.getElementById("perfilTopo").innerHTML =
      CONCURSOS.map(c => `<option value="${c.id}">${c.cargo}</option>`).join("");
  }
}

// define o perfil ativo e sincroniza o select do topo
function setPerfil(id) {
  CONCURSO = id;
  localStorage.setItem("ct_concurso", id);
  const sel = document.getElementById("perfilTopo");
  if (sel.options.length) sel.value = id;
}

function novoTomarPerfil() {
  localStorage.removeItem("ct_concurso");
}

async function api(path, opts = {}) {
  opts.headers = opts.headers || {};
  if (TOKEN) opts.headers["Authorization"] = "Bearer " + TOKEN;
  if (opts.body) opts.headers["Content-Type"] = "application/json";
  // injeta o perfil ativo apenas nas rotas de conteúdo
  const isConteudo = /^\/(bloco|blocos|progresso|plano)/.test(path);
  const sep = path.includes("?") ? "&" : "?";
  const pathC = (CONCURSO && isConteudo) ? path + sep + "concurso_id=" + CONCURSO : path;
  const r = await fetch(API + pathC, opts);
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
    // perfil ativo: escolhido no login > concurso do usuário > primeiro disponível
    const sel = document.getElementById("perfilLogin");
    let id = parseInt(sel.value, 10);
    if (!CONCURSOS.some(c => c.id === id)) id = ME.concurso_id ?? CONCURSOS[0].id;
    setPerfil(id);
    showApp();
  } catch (e) {
    document.getElementById("loginErr").textContent = "Falha: " + e.message;
  }
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
  document.getElementById("perfilTopo").value = CONCURSO;
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
          <span class="q-type">${q.tipo === "mcq" ? "Objetiva" : "Discursiva"}</span>
        </div>
        <p class="q-body">${q.enunciado}</p>`;
      if (q.tipo === "mcq") {
        inner += `<div class="bubbles">`;
        q.alternativas.forEach((a, ai) => {
          const letra = String.fromCharCode(65 + ai);
          const texto = a.replace(/^[A-Za-z]\)\s*/, "");
          inner += `<label class="bubble-option">
            <input type="radio" name="q${q.id}" value="${ai}" hidden />
            <span class="bubble">${letra}</span>
            <span class="opt-text">${texto}</span>
          </label>`;
        });
        inner += `</div>`;
      } else {
        inner += `<textarea class="ruled" name="q${q.id}" placeholder="Sua resposta discursiva..."></textarea>`;
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
    const ref = radio || anyRadio || ta;
    if (!ref) return;
    const id = parseInt(ref.name.replace("q", ""));
    const val = radio ? radio.value : (ta ? ta.value : "");
    respostas.push({ questao_id: id, resposta: val });
  });
  try {
    const out = await api("/bloco/responder", { method: "POST", body: JSON.stringify({ respostas }) });
    let html = `<div class="correcao"><p class="eyebrow">Gabarito</p>`;
    out.resultados.forEach(r => {
      const cls = r.correta === true ? "stamp-ok" : (r.correta === false ? "stamp-bad" : "stamp-pending");
      const label = r.correta === true ? "Correto" : (r.correta === false ? "A revisar" : "Aguardando correção");
      html += `<div class="stamp-row"><span class="stamp ${cls}">${label}</span><span class="stamp-detail">Q${r.questao_id}${r.feedback ? " · " + r.feedback : ""}</span></div>`;
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
    const { dominancia, cobertura } = await api("/progresso");
    cov.innerHTML = `<p class="cobertura-valor">${cobertura.pct}%<span>cobertura do edital · ${cobertura.estudados}/${cobertura.total} tópicos</span></p>`;
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
  const sel = document.getElementById("perfilLogin");
  if (sel.value) setPerfil(parseInt(sel.value, 10));
  login(document.getElementById("username").value, document.getElementById("password").value);
};
document.getElementById("logout").onclick = logout;
document.getElementById("perfilTopo").onchange = async (e) => {
  setPerfil(parseInt(e.target.value, 10));
  // mostra a aba "Bloco do dia" e recarrega todo o conteúdo do novo perfil
  document.querySelectorAll(".tabs button").forEach(x => x.classList.remove("active"));
  document.querySelector(".tabs button[data-tab='hoje']").classList.add("active");
  document.querySelectorAll(".tabpanel").forEach(p => p.hidden = true);
  document.getElementById("tab-hoje").hidden = false;
  await carregarBloco();
  await carregarBlocos();
  await carregarProgresso();
  await carregarPlano();
};
document.querySelectorAll(".tabs button").forEach(b => {
  b.onclick = () => {
    document.querySelectorAll(".tabs button").forEach(x => x.classList.remove("active"));
    b.classList.add("active");
    document.querySelectorAll(".tabpanel").forEach(p => p.hidden = true);
    document.getElementById("tab-" + b.dataset.tab).hidden = false;
  };
});

// boot: carrega perfis e restaura perfil ativo (login ou sessão)
(async function boot() {
  await carregarPerfis();
  const salvo = parseInt(localStorage.getItem("ct_concurso"), 10);
  if (CONCURSOS.length) {
    const id = CONCURSOS.some(c => c.id === salvo) ? salvo : CONCURSOS[0].id;
    setPerfil(id);
    document.getElementById("perfilLogin").value = id;
  }
  if (TOKEN) {
    api("/me").then(u => { ME = u; showApp(); }).catch(() => logout());
  }
})();

const API = "/api";
let TOKEN = localStorage.getItem("ct_token") || null;
let ME = null;

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
    showApp();
  } catch (e) {
    document.getElementById("loginErr").textContent = "Falha: " + e.message;
  }
}

function logout() {
  TOKEN = null; ME = null; localStorage.removeItem("ct_token");
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
  await carregarProgresso();
  await carregarPlano();
}

async function carregarBloco() {
  const box = document.getElementById("blocoInfo");
  const form = document.getElementById("formBloco");
  document.getElementById("resultado").innerHTML = "";
  try {
    const { bloco } = await api("/bloco/hoje");
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
document.getElementById("btnLogin").onclick = () =>
  login(document.getElementById("username").value, document.getElementById("password").value);
document.getElementById("logout").onclick = logout;
document.querySelectorAll(".tabs button").forEach(b => {
  b.onclick = () => {
    document.querySelectorAll(".tabs button").forEach(x => x.classList.remove("active"));
    b.classList.add("active");
    document.querySelectorAll(".tabpanel").forEach(p => p.hidden = true);
    document.getElementById("tab-" + b.dataset.tab).hidden = false;
  };
});

if (TOKEN) { api("/me").then(u => { ME = u; showApp(); }).catch(() => logout()); }

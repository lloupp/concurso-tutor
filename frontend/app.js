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

function domColor(d) {
  if (d >= 0.85) return "#3fb950";
  if (d >= 0.6) return "#d29922";
  return "#f85149";
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
  try {
    const { bloco } = await api("/bloco/hoje");
    if (!bloco) { box.innerHTML = "<p class='warn'>Nenhum bloco hoje. Peça ao Hermes gerar.</p>"; form.innerHTML = ""; return; }
    box.innerHTML = `<h2>${bloco.titulo}</h2><p>${bloco.introducao}</p>
      <p class='hint'>${bloco.questoes.length} questões · ${bloco.duracao_min} min · ${bloco.data}</p>`;
    form.innerHTML = "";
    bloco.questoes.forEach((q, i) => {
      const div = document.createElement("div");
      div.className = "q";
      let inner = `<h4>${i + 1}. [${q.tipo}] ${q.enunciado}</h4>`;
      if (q.tipo === "mcq") {
        inner += `<div class="alts">`;
        q.alternativas.forEach((a, ai) => {
          inner += `<label><input type="radio" name="q${q.id}" value="${ai}" /> ${String.fromCharCode(65 + ai)}) ${a}</label>`;
        });
        inner += `</div>`;
      } else {
        inner += `<textarea name="q${q.id}" placeholder="Sua resposta discursiva..."></textarea>`;
      }
      div.innerHTML = inner;
      form.appendChild(div);
    });
    const btn = document.createElement("button");
    btn.textContent = "Enviar respostas";
    btn.onclick = enviarRespostas;
    form.appendChild(btn);
  } catch (e) { box.innerHTML = "<p class='err'>" + e.message + "</p>"; }
}

async function enviarRespostas() {
  const form = document.getElementById("formBloco");
  const respostas = [];
  form.querySelectorAll(".q").forEach(qdiv => {
    const radio = qdiv.querySelector('input[type=radio]:checked');
    const ta = qdiv.querySelector("textarea");
    const name = (radio && radio.name) || (ta && ta.name);
    const id = parseInt(name.replace("q", ""));
    let val = radio ? radio.value : (ta ? ta.value : "");
    respostas.push({ questao_id: id, resposta: val });
  });
  try {
    const out = await api("/bloco/responder", { method: "POST", body: JSON.stringify({ respostas }) });
    let html = "<h3>Correção</h3>";
    out.resultados.forEach(r => {
      const ok = r.correta === true ? "<span class='ok'>✓</span>" : (r.correta === false ? "<span class='bad'>✗</span>" : "<span class='warn'>⏳ discursiva</span>");
      html += `<p>${ok} Q${r.questao_id}: ${r.feedback || ""}</p>`;
    });
    document.getElementById("resultado").innerHTML = html;
    await carregarProgresso();
  } catch (e) {
    document.getElementById("resultado").innerHTML = "<p class='err'>" + e.message + "</p>";
  }
}

async function carregarProgresso() {
  const box = document.getElementById("heatmap");
  const cov = document.getElementById("cobertura");
  try {
    const { dominancia, cobertura } = await api("/progresso");
    cov.innerHTML = `Cobertura do edital: <b>${cobertura.pct}%</b> (${cobertura.estudados}/${cobertura.total} tópicos)`;
    box.innerHTML = "";
    dominancia.forEach(d => {
      const c = domColor(d.dominio);
      const el = document.createElement("div");
      el.className = "hcell";
      el.style.background = c;
      el.innerHTML = `${d.nome}<small>domínio ${(d.dominio * 100).toFixed(0)}% · ${d.tentativas} tent.</small>`;
      box.appendChild(el);
    });
  } catch (e) { box.innerHTML = "<p class='err'>" + e.message + "</p>"; }
}

async function carregarPlano() {
  const box = document.getElementById("planoLista");
  try {
    const { proximos_topicos } = await api("/plano");
    box.innerHTML = proximos_topicos.length
      ? proximos_topicos.map(t => `<p>▶ ${t.nome}</p>`).join("")
      : "<p>Tudo coberto e em dia.</p>";
  } catch (e) { box.innerHTML = "<p class='err'>" + e.message + "</p>"; }
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

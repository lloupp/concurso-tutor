const API = "/api";
let TOKEN = localStorage.getItem("ct_token") || null;
let ME = null;
let CONCURSOS = [];
let CONCURSO = null;
let SESSION_VERSION = 0;
let BLOCK_VERSION = 0;
let BLOCK_CONTROLLER = null;
let CURRENT_BLOCK_IDS = [];
let BANK_STATS = null;
const PERF_METRICS = [];
window.__ctPerf = PERF_METRICS;

function htmlSeguro(valor) {
  return String(valor ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

const PERFIS_PUBLICOS = new Set([51, 52, 53, 54]);
const ANO_POR_TRILHA = { 51: 2025, 52: 2021, 53: 2026, 54: 2026 };
const FONTES = {
  1: "Lei nº 8.080/1990 — Lei Orgânica da Saúde",
  2: "Lei nº 8.142/1990 — participação da comunidade e transferências",
  3: "Caderno oficial de prova PF — Cebraspe 2021",
  4: "Edital Porto Alegre 77/2021 — Anexo III",
  5: "Edital nº 1/2025 — PF Administrativo",
  15: "RDC Anvisa nº 15/2012 — Processamento de Produtos para Saúde",
  16: "Resolução Cofen nº 564/2017 — Código de Ética dos Profissionais de Enfermagem",
  17: "Lei nº 7.498/1986 — Exercício da Enfermagem",
  18: "Protocolo de Segurança na Prescrição, Uso e Administração de Medicamentos",
  19: "Calendário Técnico Nacional de Vacinação — 2026",
  20: "Resolução Cofen nº 713/2022 — atendimento pré-hospitalar móvel",
  21: "Anvisa — Segurança do Paciente: Higienização das Mãos",
  22: "Protocolo de Identificação do Paciente",
  23: "Ministério da Saúde / SAMU 192 — Protocolos de Suporte Básico de Vida",
  24: "Ministério da Saúde — Exposição a Materiais Biológicos",
  25: "Edital nº 01/2026 — Concurso Público EPTC Porto Alegre",
  26: "Lei nº 9.503/1997 — Código de Trânsito Brasileiro (CTB)",
  27: "Lei nº 13.303/2016 — Estatuto Jurídico das Empresas Estatais",
  28: "Lei Municipal nº 8.133/1998 — Sistema de Transporte e Circulação de Porto Alegre",
  29: "Lei Orgânica do Município de Porto Alegre",
  30: "Estatuto Social da EPTC",
  31: "Lei nº 12.288/2010 — Estatuto da Igualdade Racial",
  32: "Lei nº 13.146/2015 — Estatuto da Pessoa com Deficiência",
  33: "Lei nº 8.429/1992 — Improbidade Administrativa",
  34: "Lei nº 12.527/2011 — Lei de Acesso à Informação",
  35: "Lei nº 13.709/2018 — LGPD",
  36: "Constituição da República Federativa do Brasil de 1988",
  37: "Portaria SENATRAN nº 354/2022 — Auto de Infração de Trânsito",
  38: "MTE — Normas Regulamentadoras NR-01, NR-04, NR-05, NR-06, NR-07 e NR-32",
  39: "CLT — Capítulo V: Segurança e Medicina do Trabalho",
  40: "Lei nº 8.213/1991 — Benefícios da Previdência Social",
  41: "RDC Anvisa nº 222/2018 — Resíduos de Serviços de Saúde"
};

function mensagemErro(raw, fallback = "Não foi possível concluir a operação.") {
  if (!raw) return fallback;
  try {
    const obj = JSON.parse(raw);
    return obj.detail || obj.message || fallback;
  } catch (_) {
    return raw.length < 180 ? raw : fallback;
  }
}

function registrarPerf(metrica) {
  PERF_METRICS.push({ ...metrica, at: new Date().toISOString() });
  if (PERF_METRICS.length > 100) PERF_METRICS.shift();
  console.info("[ct-perf]", JSON.stringify(PERF_METRICS.at(-1)));
}

async function api(path, opts = {}) {
  const inicio = performance.now();
  const skipAuth = Boolean(opts.skipAuth);
  delete opts.skipAuth;
  opts.headers = { ...(opts.headers || {}) };
  if (TOKEN && !skipAuth) opts.headers.Authorization = "Bearer " + TOKEN;
  if (opts.body) opts.headers["Content-Type"] = "application/json";
  try {
    const r = await fetch(API + path, opts);
    registrarPerf({ tipo: "api", path, status: r.status,
      rede_ms: Math.round(performance.now() - inicio),
      servidor: r.headers.get("server-timing") || null });
    if (!r.ok) {
      const t = await r.text();
      const err = new Error(mensagemErro(t));
      err.status = r.status;
      throw err;
    }
    return r.json();
  } catch (erro) {
    if (!erro.status) registrarPerf({ tipo: "api", path, status: 0,
      rede_ms: Math.round(performance.now() - inicio), erro: erro.name || "Erro" });
    throw erro;
  }
}

function limparTelaEstudo() {
  BLOCK_VERSION += 1;
  CURRENT_BLOCK_IDS = [];
  BANK_STATS = null;
  if (BLOCK_CONTROLLER) {
    BLOCK_CONTROLLER.abort();
    BLOCK_CONTROLLER = null;
  }
  ["blocoInfo", "formBloco", "resultado", "cobertura", "dashboardCards", "heatmap", "planoLista"].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.innerHTML = "";
  });
  const aviso = document.getElementById("bankNotice");
  if (aviso) { aviso.hidden = true; aviso.textContent = ""; }
}

async function carregarPerfis() {
  try {
    const data = await fetch(API + "/concursos").then(async r => {
      if (!r.ok) throw new Error(mensagemErro(await r.text(), "Erro ao carregar perfis"));
      return r.json();
    });
    CONCURSOS = data.concursos || [];
  } catch (e) {
    console.error("perfis", e);
    return;
  }
  const select = document.getElementById("cadTrilha");
  if (select) {
    select.innerHTML = CONCURSOS.filter(c => PERFIS_PUBLICOS.has(c.id))
      .map(c => `<option value="${Number(c.id)}">${htmlSeguro(c.nome)}</option>`).join("");
  }
}

function setPerfil(id) {
  CONCURSO = id == null ? null : Number(id);
  if (CONCURSO == null || Number.isNaN(CONCURSO)) localStorage.removeItem("ct_concurso");
  else localStorage.setItem("ct_concurso", String(CONCURSO));
}

function perfilAtual() {
  return CONCURSOS.find(c => c.id === CONCURSO) || {};
}

function domLevel(d) {
  if (d >= 0.85) return "ok";
  if (d >= 0.6) return "warn";
  return "bad";
}

async function login(u, p) {
  const versao = ++SESSION_VERSION;
  limparTelaEstudo();
  document.getElementById("loginErr").textContent = "";
  try {
    const data = await api("/login", {
      method: "POST",
      skipAuth: true,
      body: JSON.stringify({ username: u, password: p })
    });
    if (versao !== SESSION_VERSION) return;
    TOKEN = data.token;
    ME = data.user;
    localStorage.setItem("ct_token", TOKEN);
    setPerfil(ME.concurso_id);
    await showApp();
  } catch (e) {
    if (versao !== SESSION_VERSION) return;
    document.getElementById("loginErr").textContent = "Não foi possível entrar: " + e.message;
  }
}

async function cadastro() {
  const msg = document.getElementById("cadastroMsg");
  try {
    await api("/cadastro", {
      method: "POST",
      skipAuth: true,
      body: JSON.stringify({
        full_name: document.getElementById("cadNome").value,
        username: document.getElementById("cadUsuario").value,
        password: document.getElementById("cadSenha").value,
        concurso_id: parseInt(document.getElementById("cadTrilha").value, 10),
        tempo_diario: parseInt(document.getElementById("cadTempo").value, 10)
      })
    });
    msg.textContent = "Perfil criado. Agora entre com seu usuário e senha.";
    ["cadNome", "cadUsuario", "cadSenha"].forEach(id => {
      document.getElementById(id).value = "";
    });
    document.getElementById("cadTrilha").selectedIndex = 0;
    document.getElementById("cadTempo").value = "60";
  } catch (e) {
    msg.textContent = "Não foi possível criar: " + e.message;
  }
}

function logout() {
  SESSION_VERSION += 1;
  limparTelaEstudo();
  TOKEN = null;
  ME = null;
  setPerfil(null);
  localStorage.removeItem("ct_token");
  document.getElementById("app").hidden = true;
  document.getElementById("login").hidden = false;
  document.getElementById("topbar").hidden = true;
  const tabs = document.querySelector(".tabs");
  if (tabs) tabs.hidden = false;
}

async function showApp() {
  const sessao = SESSION_VERSION;
  limparTelaEstudo();
  document.getElementById("login").hidden = true;
  document.getElementById("app").hidden = false;
  document.getElementById("topbar").hidden = false;
  document.getElementById("userinfo").textContent = `${ME.full_name} (${ME.role})`;
  const tabs = document.querySelector(".tabs");

  if (ME.role === "admin") {
    if (tabs) tabs.hidden = true;
    document.getElementById("blocoInfo").innerHTML =
      "<div class='warn-box'><b>Área administrativa não disponível nesta interface.</b><br>Este acesso não possui uma trilha de aluno. Use as ferramentas administrativas do projeto para gerenciar conteúdo; nenhuma trilha anterior será exibida aqui.</div>";
    return;
  }

  if (tabs) tabs.hidden = false;
  if (!CONCURSO) {
    document.getElementById("blocoInfo").innerHTML = "<p class='errbox'>Seu usuário não possui uma trilha de estudo configurada.</p>";
    return;
  }

  await Promise.all([carregarBloco(), carregarProgresso(), carregarPlano()]);
  if (sessao !== SESSION_VERSION) return;
}

function referenciaQuestao(q) {
  const perfil = perfilAtual();
  const partes = [q.banca_estilo || perfil.banca, perfil.nome, ANO_POR_TRILHA[CONCURSO], FONTES[q.fonte_id]]
    .filter(Boolean);
  return partes.length ? `Referência: ${partes.join(" · ")}` : "Referência não cadastrada";
}

function atualizarBotaoMais() {
  const botao = document.getElementById("btnMaisQuestoes");
  if (!botao || !BANK_STATS) return;
  const ineditas = Math.max(0, Number(BANK_STATS.ineditas || 0));
  if (ineditas === 0) {
    botao.textContent = "Revisar 10 questões";
    botao.title = "Não há questões inéditas; será montado um bloco de revisão.";
  } else if (ineditas < 10) {
    botao.textContent = `Fazer mais ${ineditas} inéditas`;
    botao.title = `Há ${ineditas} questões inéditas disponíveis nesta trilha.`;
  } else {
    botao.textContent = "Fazer mais 10 questões";
    botao.removeAttribute("title");
  }
}

async function carregarBloco(blocoId = null, adaptativo = false) {
  const inicioRender = performance.now();
  const box = document.getElementById("blocoInfo");
  const form = document.getElementById("formBloco");
  const resultado = document.getElementById("resultado");
  const sessao = SESSION_VERSION;
  const perfil = CONCURSO;
  const versao = ++BLOCK_VERSION;

  if (BLOCK_CONTROLLER) BLOCK_CONTROLLER.abort();
  const controller = new AbortController();
  BLOCK_CONTROLLER = controller;
  const signal = controller.signal;
  let expirou = false;
  const limite = setTimeout(() => {
    expirou = true;
    controller.abort();
  }, 15000);

  resultado.innerHTML = "";
  box.innerHTML = "<p class='hint'>Carregando questões...</p>";
  form.innerHTML = "";

  try {
    const path = blocoId ? "/bloco/" + blocoId : (adaptativo ? "/bloco/proximo" : "/bloco/hoje");
    const { bloco } = await api(path, { signal });
    if (signal.aborted || versao !== BLOCK_VERSION || sessao !== SESSION_VERSION || perfil !== CONCURSO) return;

    if (!bloco) {
      CURRENT_BLOCK_IDS = [];
      box.innerHTML = "<p class='warn-box'>Ainda não há questões disponíveis para esta trilha. Em breve teremos mais questões.</p>";
      return;
    }

    CURRENT_BLOCK_IDS = bloco.questoes.map(q => q.id);
    box.innerHTML = `
      <div class="protocolo">
        <p class="eyebrow">Bloco de estudo</p>
        <h2>${htmlSeguro(bloco.titulo)}</h2>
        <p class="intro">${htmlSeguro(bloco.introducao)}</p>
        <div class="protocolo-meta">
          <div><span>Data</span><b>${htmlSeguro(bloco.data)}</b></div>
          <div><span>Duração</span><b>${Number(bloco.duracao_min)} min</b></div>
          <div><span>Questões</span><b>${Number(bloco.questoes.length)}</b></div>
        </div>
        <button type="button" class="btn secondary" id="btnMaisQuestoes">Fazer mais 10 questões</button>
      </div>`;
    document.getElementById("btnMaisQuestoes").onclick = () => carregarBloco(null, true);
    atualizarBotaoMais();

    bloco.questoes.forEach((q, i) => {
      const div = document.createElement("div");
      div.className = "q";
      const tituloId = `q-titulo-${Number(q.id)}`;
      div.setAttribute("role", "group");
      div.setAttribute("aria-labelledby", tituloId);
      let inner = `
        <div class="q-head">
          <span class="q-num">Q${i + 1}</span>
          <span class="q-type">${q.tipo === "mcq" ? "Objetiva" : q.tipo === "verdadeiro_falso" ? "Certo ou errado" : q.tipo === "numerica" ? "Resposta numérica" : "Legada"}</span>
          <span class="q-type q-source-meta">${htmlSeguro(referenciaQuestao(q))}</span>
        </div>
        ${q.texto_base ? `<div class="texto-base">${htmlSeguro(q.texto_base)}</div>` : ""}
        <p class="q-body" id="${tituloId}">${htmlSeguro(q.enunciado)}</p>`;
      const anterior = q.resposta_anterior;
      if (q.tipo === "mcq") {
        inner += `<div class="bubbles">`;
        (q.alternativas || []).forEach((a, ai) => {
          const letra = String.fromCharCode(65 + ai);
          const texto = String(a).replace(/^[A-Za-z][\)\.]\s*/, "");
          inner += `<label class="bubble-option">
            <input class="sr-radio" type="radio" name="q${Number(q.id)}" value="${ai}" ${anterior && anterior.resposta === String(ai) ? "checked" : ""} />
            <span class="bubble">${letra}</span><span class="opt-text">${htmlSeguro(texto)}</span>
          </label>`;
        });
        inner += `</div>`;
      } else if (q.tipo === "verdadeiro_falso") {
        inner += `<div class="bubbles">
          <label class="bubble-option"><input class="sr-radio" type="radio" name="q${Number(q.id)}" value="true" ${anterior && anterior.resposta === "true" ? "checked" : ""} /><span class="bubble">C</span><span class="opt-text">Certo</span></label>
          <label class="bubble-option"><input class="sr-radio" type="radio" name="q${Number(q.id)}" value="false" ${anterior && anterior.resposta === "false" ? "checked" : ""} /><span class="bubble">E</span><span class="opt-text">Errado</span></label>
        </div>`;
      } else if (q.tipo === "numerica") {
        inner += `<input class="numeric-answer" type="text" inputmode="decimal" name="q${Number(q.id)}" aria-label="Resposta da questão ${i + 1}" value="${htmlSeguro(anterior ? anterior.resposta : "")}" placeholder="Sua resposta${q.unidade ? ` (${htmlSeguro(q.unidade)})` : ""}" />`;
      }
      if (anterior) {
        const estado = anterior.correta ? "Correto" : "A revisar";
        const detalhe = anterior.feedback || "Resposta registrada.";
        inner += `<div class="answer-history"><b>${htmlSeguro(estado)}</b> · ${htmlSeguro(detalhe)}</div>`;
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
    registrarPerf({ tipo: "ui", evento: "bloco_renderizado", adaptativo,
      questoes: bloco.questoes.length,
      total_ms: Math.round(performance.now() - inicioRender) });
  } catch (e) {
    if (versao !== BLOCK_VERSION || sessao !== SESSION_VERSION || perfil !== CONCURSO) return;
    if (expirou) {
      box.innerHTML = "<p class='errbox'>O servidor demorou mais que o esperado para preparar as questões. Tente novamente em alguns instantes.</p>";
      return;
    }
    if (e.name === "AbortError" || signal.aborted) return;
    box.innerHTML = `<p class='errbox'>Não foi possível carregar este bloco: ${htmlSeguro(e.message)}</p>`;
  } finally {
    clearTimeout(limite);
  }
}

async function enviarRespostas() {
  const form = document.getElementById("formBloco");
  const resultado = document.getElementById("resultado");
  const sessao = SESSION_VERSION;
  const perfil = CONCURSO;
  const idsNaTela = [...CURRENT_BLOCK_IDS];
  const respostas = [];

  form.querySelectorAll(".q").forEach(qdiv => {
    const radio = qdiv.querySelector('input[type="radio"]:checked');
    const anyRadio = qdiv.querySelector('input[type="radio"]');
    const numeric = qdiv.querySelector(".numeric-answer");
    const ref = radio || anyRadio || numeric;
    if (!ref || (anyRadio && !radio) || (numeric && !numeric.value.trim())) return;
    const id = parseInt(ref.name.replace("q", ""), 10);
    if (!idsNaTela.includes(id)) return;
    respostas.push({ questao_id: id, resposta: radio ? radio.value : numeric.value });
  });

  if (!respostas.length) {
    resultado.innerHTML = "<p class='warn-box'>Selecione pelo menos uma resposta antes de enviar.</p>";
    return;
  }

  const submit = form.querySelector(".btn-stamp");
  if (submit) { submit.disabled = true; submit.textContent = "Enviando..."; }
  try {
    const out = await api("/bloco/responder", { method: "POST", body: JSON.stringify({ respostas }) });
    if (sessao !== SESSION_VERSION || perfil !== CONCURSO || idsNaTela.join(",") !== CURRENT_BLOCK_IDS.join(",")) return;
    let html = `<div class="correcao"><p class="eyebrow">Resultado</p>`;
    out.resultados.forEach(r => {
      const cls = r.correta === true ? "stamp-ok" : (r.correta === false ? "stamp-bad" : "stamp-pending");
      const label = r.correta === true ? "Correto" : (r.correta === false ? "A revisar" : "Pendente");
      const detalhe = r.feedback || "";
      html += `<div class="stamp-row"><span class="stamp ${cls}">${label}</span><span class="stamp-detail">Q${Number(r.questao_id)}${detalhe ? " · " + htmlSeguro(detalhe) : ""}</span></div>`;
    });
    html += "</div>";
    resultado.innerHTML = html;
    await carregarProgresso();
  } catch (e) {
    if (sessao !== SESSION_VERSION) return;
    const msg = e.status === 403
      ? "Este bloco ficou desatualizado para a sua trilha. Clique em “Fazer mais 10 questões” para carregar um bloco válido."
      : e.message;
    resultado.innerHTML = `<p class='errbox'>Não foi possível enviar as respostas: ${htmlSeguro(msg)}</p>`;
  } finally {
    if (submit && sessao === SESSION_VERSION) { submit.disabled = false; submit.textContent = "Enviar respostas"; }
  }
}

async function carregarProgresso() {
  if (!ME || ME.role === "admin") return;
  const sessao = SESSION_VERSION;
  const perfil = CONCURSO;
  const box = document.getElementById("heatmap");
  const cov = document.getElementById("cobertura");
  try {
    const { dominancia, cobertura, dashboard } = await api("/progresso");
    if (sessao !== SESSION_VERSION || perfil !== CONCURSO) return;
    cov.innerHTML = `<p class="cobertura-valor">${cobertura.pct}%<span>cobertura do edital · ${cobertura.estudados}/${cobertura.total} tópicos</span></p>`;
    document.getElementById("dashboardCards").innerHTML = [
      ["Domínio médio", `${dashboard.dominio_medio}%`], ["Respondidas", dashboard.questoes_respondidas],
      ["Acertos", dashboard.acertos], ["Taxa de acerto", `${dashboard.taxa_acerto}%`],
      ["Revisões pendentes", dashboard.revisoes_pendentes], ["Matérias iniciadas", `${dashboard.materias_iniciadas}/${dashboard.materias_total}`]
    ].map(([label, value]) => `<div class="dashboard-card"><span>${label}</span><b>${value}</b></div>`).join("");
    box.innerHTML = "";
    dominancia.forEach(d => {
      const level = domLevel(d.dominio);
      const pct = Math.round(d.dominio * 100);
      const row = document.createElement("div");
      row.className = "boletim-row";
      row.innerHTML = `<span class="boletim-nome">${htmlSeguro(d.nome)}</span><span class="boletim-bar"><span class="boletim-fill ${level}" style="width:${pct}%"></span></span><span class="boletim-pct ${level}">${pct}%</span><span class="boletim-tent">${Number(d.tentativas)} tent.</span>`;
      box.appendChild(row);
    });
    const aviso = document.getElementById("bankNotice");
    const total = Number(dashboard.questoes_banco || 0);
    const ineditas = Number(dashboard.ineditas_restantes || 0);
    BANK_STATS = { total, ineditas };
    atualizarBotaoMais();
    if (aviso) {
      if (total > 0 && total < 50) {
        aviso.hidden = false;
        aviso.className = "warn-box";
        aviso.textContent = `Este banco ainda está em expansão. Há ${total} questões disponíveis no momento, sendo ${ineditas} inéditas para você. Em breve teremos mais questões.`;
      } else {
        aviso.hidden = true;
        aviso.textContent = "";
      }
    }
  } catch (e) {
    if (sessao !== SESSION_VERSION) return;
    box.innerHTML = `<p class='errbox'>Não foi possível carregar seu boletim: ${htmlSeguro(e.message)}</p>`;
  }
}

async function carregarPlano() {
  if (!ME || ME.role === "admin") return;
  const sessao = SESSION_VERSION;
  const perfil = CONCURSO;
  const box = document.getElementById("planoLista");
  try {
    const { proximos_topicos } = await api("/plano");
    if (sessao !== SESSION_VERSION || perfil !== CONCURSO) return;
    box.innerHTML = proximos_topicos.length
      ? proximos_topicos.map((t, i) => `<div class="agenda-item"><span class="agenda-num">${String(i + 1).padStart(2, "0")}</span><span>${htmlSeguro(t.nome)}</span></div>`).join("")
      : "<p class='agenda-empty'>Tudo coberto e em dia ✓</p>";
  } catch (e) {
    if (sessao !== SESSION_VERSION) return;
    box.innerHTML = `<p class='errbox'>Não foi possível carregar o plano de estudo: ${htmlSeguro(e.message)}</p>`;
  }
}

document.getElementById("btnLogin").onclick = () => login(document.getElementById("username").value, document.getElementById("password").value);
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

window.addEventListener("storage", event => {
  if (event.key === "ct_token" && event.newValue !== TOKEN) logout();
});

(async function boot() {
  await carregarPerfis();
  if (TOKEN) {
    try {
      const u = await api("/me");
      ME = u;
      setPerfil(u.concurso_id);
      await showApp();
    } catch (_) {
      logout();
    }
  }
})();

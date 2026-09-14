(() => {
  if (typeof FONTES !== "undefined") {
    Object.assign(FONTES, {
      42: "PROFAE — Anatomia e Fisiologia (Ministério da Saúde / Fiocruz)",
      43: "PROFAE — Fundamentos de Enfermagem (Ministério da Saúde / Fiocruz)",
      44: "Protocolo de Prevenção de Quedas — MS / Anvisa / Fiocruz",
      45: "Protocolo de Prevenção de Lesão por Pressão — MS / Anvisa / Fiocruz"
    });
  }

  function escaparHtml(valor) {
    return String(valor ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  enviarRespostas = async function () {
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
    if (submit) {
      submit.disabled = true;
      submit.textContent = "Enviando...";
    }

    try {
      const out = await api("/bloco/responder", {
        method: "POST",
        body: JSON.stringify({ respostas })
      });
      if (sessao !== SESSION_VERSION || perfil !== CONCURSO || idsNaTela.join(",") !== CURRENT_BLOCK_IDS.join(",")) return;

      let corretas = 0;
      let corrigidas = 0;
      out.resultados.forEach(r => {
        const campo = form.querySelector(`[name="q${r.questao_id}"]`);
        const questao = campo && campo.closest(".q");
        if (!questao) return;

        const anterior = questao.querySelector(".submitted-feedback");
        if (anterior) anterior.remove();

        const estado = r.correta === true ? "Correto" : (r.correta === false ? "A revisar" : "Pendente");
        if (r.correta !== null && r.correta !== undefined) corrigidas += 1;
        if (r.correta === true) corretas += 1;

        let detalhe = r.feedback || "Resposta registrada.";
        if (r.correta === true) detalhe = detalhe.replace(/^Correto\.\s*/i, "");
        if (r.explicacao && !detalhe.includes(r.explicacao)) detalhe += `${detalhe ? " " : ""}${r.explicacao}`;
        if (!detalhe) detalhe = "Resposta correta.";
        const feedback = document.createElement("div");
        feedback.className = "answer-history submitted-feedback";
        feedback.innerHTML = `<b>${escaparHtml(estado)}</b> · ${escaparHtml(detalhe)}`;
        questao.appendChild(feedback);
      });

      resultado.innerHTML = corrigidas
        ? `<p class="hint"><b>${corretas}/${corrigidas}</b> corretas. O feedback está logo abaixo de cada questão respondida.</p>`
        : "<p class='hint'>Respostas registradas. O feedback está logo abaixo de cada questão.</p>";
      await carregarProgresso();
    } catch (e) {
      if (sessao !== SESSION_VERSION) return;
      const msg = e.status === 403
        ? "Este bloco ficou desatualizado para a sua trilha. Clique em “Fazer mais 10 questões” para carregar um bloco válido."
        : e.message;
      resultado.innerHTML = `<p class='errbox'>Não foi possível enviar as respostas: ${escaparHtml(msg)}</p>`;
    } finally {
      if (submit && sessao === SESSION_VERSION) {
        submit.disabled = false;
        submit.textContent = "Enviar respostas";
      }
    }
  };
})();

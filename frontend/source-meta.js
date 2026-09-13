(() => {
  const ANO_POR_TRILHA = { 51: 2025, 52: 2021 };
  const FONTES = {
    1: 'Lei nº 8.080/1990 — Lei Orgânica da Saúde',
    2: 'Lei nº 8.142/1990 — participação da comunidade e transferências',
    3: 'Caderno oficial de prova PF — Cebraspe 2021',
    4: 'Edital Porto Alegre 77/2021 — Anexo III',
    5: 'Edital nº 1/2025 — PF Administrativo',
    15: 'RDC Anvisa nº 15/2012 — Processamento de Produtos para Saúde',
    16: 'Resolução Cofen nº 564/2017 — Código de Ética dos Profissionais de Enfermagem',
    17: 'Lei nº 7.498/1986 — Exercício da Enfermagem',
    18: 'Protocolo de Segurança na Prescrição, Uso e Administração de Medicamentos',
    19: 'Calendário Técnico Nacional de Vacinação — 2026',
    20: 'Resolução Cofen nº 713/2022 — atendimento pré-hospitalar móvel',
    21: 'Anvisa — Segurança do Paciente: Higienização das Mãos',
    22: 'Protocolo de Identificação do Paciente',
    23: 'Ministério da Saúde / SAMU 192 — Protocolos de Suporte Básico de Vida',
    24: 'Ministério da Saúde — Exposição a Materiais Biológicos'
  };

  function perfilAtual() {
    try {
      return (CONCURSOS || []).find(c => c.id === CONCURSO) || {};
    } catch (_) {
      return {};
    }
  }

  function idDaQuestao(el) {
    const campo = el.querySelector('input[name^="q"], textarea[name^="q"]');
    return campo ? Number(campo.name.slice(1)) : null;
  }

  function nomeFonte(q) {
    if (!q.fonte_id) return 'fonte específica não cadastrada';
    if (CONCURSO === 52 && q.fonte_id === 3) return 'referência inconsistente — revisão pendente';
    return FONTES[q.fonte_id] || `Fonte cadastrada #${q.fonte_id}`;
  }

  function renderizarReferencias(bloco) {
    if (!bloco || !Array.isArray(bloco.questoes)) return;
    const porId = new Map(bloco.questoes.map(q => [q.id, q]));
    const perfil = perfilAtual();
    document.querySelectorAll('#formBloco .q').forEach(el => {
      const id = idDaQuestao(el);
      const q = porId.get(id);
      const head = el.querySelector('.q-head');
      if (!q || !head) return;
      let tag = head.querySelector('.q-source-meta');
      if (!tag) {
        tag = document.createElement('span');
        tag.className = 'q-type q-source-meta';
        head.appendChild(tag);
      }
      const banca = q.banca_estilo || perfil.banca || 'não informada';
      const concurso = perfil.nome || q.trilha || 'não informado';
      const ano = ANO_POR_TRILHA[CONCURSO] || 'não informado';
      tag.textContent = `Referência: ${banca} · ${concurso} · ${ano} · ${nomeFonte(q)}`;
    });
  }

  async function carregarMetadados(blocoId = null, adaptativo = false) {
    try {
      const path = blocoId ? '/bloco/' + blocoId : (adaptativo ? '/bloco/proximo' : '/bloco/hoje');
      const out = await api(path);
      renderizarReferencias(out.bloco);
    } catch (_) {
      // A informação de origem é complementar; nunca bloqueia a resolução da prova.
    }
  }

  const carregarOriginal = carregarBloco;
  carregarBloco = async function(blocoId = null, adaptativo = false) {
    await carregarOriginal(blocoId, adaptativo);
    await carregarMetadados(blocoId, adaptativo);
  };

  if (document.querySelector('#formBloco .q')) carregarMetadados();
})();

(() => {
  const ANO_POR_TRILHA = { 51: 2025, 52: 2021, 53: 2026, 54: 2026 };
  const PERFIS_PUBLICOS = new Set([51, 52, 53, 54]);
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
    24: 'Ministério da Saúde — Exposição a Materiais Biológicos',
    25: 'Edital nº 01/2026 — Concurso Público EPTC Porto Alegre',
    26: 'Lei nº 9.503/1997 — Código de Trânsito Brasileiro (CTB)',
    27: 'Lei nº 13.303/2016 — Estatuto Jurídico das Empresas Estatais',
    28: 'Lei Municipal nº 8.133/1998 — Sistema de Transporte e Circulação de Porto Alegre',
    29: 'Lei Orgânica do Município de Porto Alegre',
    30: 'Estatuto Social da EPTC',
    31: 'Lei nº 12.288/2010 — Estatuto da Igualdade Racial',
    32: 'Lei nº 13.146/2015 — Estatuto da Pessoa com Deficiência',
    33: 'Lei nº 8.429/1992 — Improbidade Administrativa',
    34: 'Lei nº 12.527/2011 — Lei de Acesso à Informação',
    35: 'Lei nº 13.709/2018 — LGPD',
    36: 'Constituição da República Federativa do Brasil de 1988',
    37: 'Portaria SENATRAN nº 354/2022 — Auto de Infração de Trânsito',
    38: 'MTE — Normas Regulamentadoras NR-01, NR-04, NR-05, NR-06, NR-07 e NR-32',
    39: 'CLT — Capítulo V: Segurança e Medicina do Trabalho',
    40: 'Lei nº 8.213/1991 — Benefícios da Previdência Social',
    41: 'RDC Anvisa nº 222/2018 — Resíduos de Serviços de Saúde'
  };

  async function habilitarPerfisPublicos() {
    try {
      let perfis = Array.isArray(CONCURSOS) ? CONCURSOS : [];
      if (!perfis.length) {
        const r = await fetch('/api/concursos');
        if (!r.ok) return;
        perfis = (await r.json()).concursos || [];
        CONCURSOS = perfis;
      }
      const select = document.getElementById('cadTrilha');
      if (!select) return;
      select.innerHTML = perfis
        .filter(c => PERFIS_PUBLICOS.has(c.id))
        .map(c => `<option value="${c.id}">${c.nome}</option>`)
        .join('');
    } catch (_) {
      // A lista original continua disponível se esta melhoria falhar.
    }
  }

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

  habilitarPerfisPublicos();
  setTimeout(habilitarPerfisPublicos, 750);
  if (document.querySelector('#formBloco .q')) carregarMetadados();
})();

(() => {
  if (typeof PERFIS_PUBLICOS !== "undefined") {
    PERFIS_PUBLICOS.add(55);
    PERFIS_PUBLICOS.add(56);
  }
  if (typeof ANO_POR_TRILHA !== "undefined") {
    ANO_POR_TRILHA[55] = 2026;
    ANO_POR_TRILHA[56] = 2026;
  }
  if (typeof FONTES !== "undefined") {
    Object.assign(FONTES, {
      47: "Edital nº 01/2026 — Município de Alvorada/RS — Instituto Legalle",
      48: "Lei Complementar nº 101/2000 — Lei de Responsabilidade Fiscal",
      49: "Lei nº 9.784/1999 — Processo Administrativo Federal",
      50: "Decreto nº 8.373/2014 — eSocial",
      51: "Manual de Redação da Presidência da República — 3ª edição",
      52: "CONARQ — Publicações Técnicas e Glossário Arquivístico",
      53: "Microsoft Support — Windows 11",
      54: "Microsoft Support — Word 365",
      55: "Google Chrome Help",
      56: "Decreto nº 7.508/2011 — Regulamentação da Lei nº 8.080/1990",
      57: "Portaria nº 2.436/2017 — Política Nacional de Atenção Básica",
      58: "Lei Municipal nº 3.670/2022 — Regime Jurídico dos Servidores de Alvorada",
      59: "Lei Orgânica do Município de Alvorada/RS — texto compilado",
      60: "ENAP — Análise e Melhoria de Processos: PDCA, MASP e ferramentas da qualidade",
      61: "ENAP — Gestão de Materiais",
      62: "eSocial — Documentação Técnica e Manual de Orientação S-1.3"
    });
  }

  if (typeof carregarPerfis === "function") {
    carregarPerfis();
  }
})();

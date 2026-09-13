(() => {
  async function atualizarAvisoBanco() {
    const aviso = document.getElementById('bankNotice');
    if (!aviso) return;
    try {
      const out = await api('/progresso');
      const dashboard = out.dashboard || {};
      const total = Number(dashboard.questoes_banco || 0);
      const ineditas = Number(dashboard.ineditas_restantes || 0);
      if (total > 0 && total < 50) {
        aviso.hidden = false;
        aviso.className = 'warn-box';
        aviso.textContent = `Este banco ainda está em expansão. Há ${total} questões disponíveis no momento, sendo ${ineditas} inéditas para você. Em breve teremos mais questões.`;
      } else {
        aviso.hidden = true;
        aviso.textContent = '';
      }
    } catch (_) {
      aviso.hidden = true;
    }
  }

  const anterior = carregarBloco;
  carregarBloco = async function(blocoId = null, adaptativo = false) {
    await anterior(blocoId, adaptativo);
    const botao = document.querySelector('#blocoInfo .protocolo button');
    if (botao) botao.textContent = 'Fazer mais 10 questões';
    const seletor = document.getElementById('seletorBloco');
    if (seletor) seletor.hidden = true;
    await atualizarAvisoBanco();
  };
})();
(() => {
  const anterior = carregarBloco;
  carregarBloco = async function(blocoId = null, adaptativo = false) {
    await anterior(blocoId, adaptativo);
    const botao = document.querySelector('#blocoInfo .protocolo button');
    if (botao) botao.textContent = 'Fazer mais 10 questões';
    const seletor = document.getElementById('seletorBloco');
    if (seletor) seletor.hidden = true;
  };
})();
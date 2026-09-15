> **DEPRECADO em 2026-09-15** pela auditoria de questões reais
> (ver `AUDITORIA_QUESTOES_REAIS.md`). O fluxo abaixo instruía uma IA a
> **formular/criar** questões "ancoradas" em fontes gerais (editais, sites de
> concurso). Isso é proibido: uma questão só pode entrar na plataforma se
> for a transcrição fiel de uma questão efetivamente aplicada em uma prova
> real, com banca, órgão, concurso, cargo, ano, caderno, número da questão,
> URL da prova e gabarito oficial comprovados. Este arquivo é mantido apenas
> como registro histórico do que NÃO fazer mais. Use o fluxo descrito em
> `skills/tutor-concurso/SKILL.md` (seção "Buscar/recuperar questões reais").

---

# (histórico — não usar) Prompt original de povoamento via IA generativa

Este prompt pedia a um agente para pesquisar o conteúdo programático dos
editais e **formular** 40 questões (mistas, mcq/discursiva) "ancoradas" nessa
pesquisa, sem exigir que cada questão fosse a transcrição de uma questão
real de uma prova aplicada. O resultado é conteúdo AUTORAL_INVENTADA ou, na
melhor hipótese, NAO_COMPROVADA — nunca VERIFICADA_REAL — mesmo quando os
fatos citados (leis, artigos, protocolos) estavam corretos. Fatos corretos
não tornam uma questão real; só a correspondência textual com uma prova
aplicada comprovadamente torna.

Todas as questões geradas a partir deste prompt foram colocadas em
quarentena (`situacao='quarentena'`) na auditoria de 2026-09-15. Não gere
novas questões com este método.

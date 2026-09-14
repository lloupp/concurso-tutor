"""Barreiras editoriais para lotes enviados ao banco."""
from scripts.validate_batch import validar


def _questao(indice, gabarito="0"):
    temas = [
        "coesão textual", "concordância nominal", "regência verbal", "crase",
        "porcentagem", "probabilidade", "geometria plana", "sequências lógicas",
        "segurança de redes", "planilhas eletrônicas", "direitos fundamentais",
        "acesso à informação", "proteção de dados", "empresas estatais",
        "sinalização viária", "administração de medicamentos", "biossegurança",
        "primeiros socorros", "saúde ocupacional", "ética profissional",
    ]
    return {
        "tipo": "mcq", "enunciado": f"Situação específica sobre {temas[indice]} com dados próprios",
        "alternativas": ["opção um", "opção dois", "opção três", "opção quatro"],
        "gabarito": gabarito, "explicacao": "Explicação verificável.",
        "topico_id": 1, "dificuldade": 2, "banca_estilo": "Instituto Objetiva",
        "fonte_id": 25, "materia": "Conhecimentos gerais",
    }


def test_validador_rejeita_comando_discursivo_e_alternativa_truncada():
    questoes = [_questao(i, str(i % 4)) for i in range(20)]
    questoes[0]["enunciado"] = "Explique o princípio da eficiência."
    questoes[1]["alternativas"][0] = "A"
    erros = validar({"bloco": {"topicos_ids": [1], "questoes": questoes}})
    assert any("comando discursivo" in erro for erro in erros)
    assert any("truncada" in erro for erro in erros)


def test_validador_rejeita_gabarito_concentrado():
    questoes = [_questao(i, "0") for i in range(20)]
    erros = validar({"bloco": {"topicos_ids": [1], "questoes": questoes}})
    assert any("concentrados" in erro for erro in erros)


def test_validador_aceita_lote_balanceado():
    questoes = [_questao(i, str(i % 4)) for i in range(20)]
    assert validar({"bloco": {"topicos_ids": [1], "questoes": questoes}}) == []

"""Valida lotes de questões antes da inserção no Supabase.

Uso: python scripts/validate_batch.py lote.json
O arquivo deve conter {"concurso_id": ..., "bloco": {"topicos_ids": [...], "questoes": [...]}}.
"""
import argparse
import json
import re
import sys
import unicodedata
from difflib import SequenceMatcher


def normalizar(texto):
    texto = unicodedata.normalize("NFKD", str(texto or ""))
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return re.sub(r"\W+", " ", texto.lower()).strip()


def validar(dados, minimo=20, maximo=50):
    bloco = dados.get("bloco", dados)
    questoes = bloco.get("questoes", [])
    erros = []
    if not minimo <= len(questoes) <= maximo:
        erros.append(f"lote deve ter entre {minimo} e {maximo} questões (tem {len(questoes)})")
    topicos = set(bloco.get("topicos_ids", []))
    enunciados = []
    distribuicao = {}
    for i, q in enumerate(questoes, 1):
        prefixo = f"questão {i}"
        tipo = q.get("tipo", "mcq")
        if tipo not in {"mcq", "verdadeiro_falso", "numerica"}:
            erros.append(f"{prefixo}: tipo não corrigível: {tipo}")
        if not str(q.get("enunciado", "")).strip():
            erros.append(f"{prefixo}: enunciado vazio")
        if not str(q.get("explicacao", "")).strip():
            erros.append(f"{prefixo}: explicação obrigatória ausente")
        if q.get("topico_id") is None:
            erros.append(f"{prefixo}: topico_id ausente")
        elif topicos and q["topico_id"] not in topicos:
            erros.append(f"{prefixo}: tópico fora de topicos_ids")
        if q.get("dificuldade") not in {1, 2, 3}:
            erros.append(f"{prefixo}: dificuldade deve ser 1, 2 ou 3")
        if not q.get("banca_estilo"):
            erros.append(f"{prefixo}: banca_estilo ausente")
        if q.get("fonte_id") is None:
            erros.append(f"{prefixo}: fonte_id ausente")
        if not str(q.get("materia", "")).strip():
            erros.append(f"{prefixo}: matéria ausente")
        if tipo == "mcq" and re.match(r"^\s*(explique|discorra|justifique)\b",
                                      str(q.get("enunciado", "")), re.I):
            erros.append(f"{prefixo}: comando discursivo incompatível com MCQ")
        if tipo == "mcq":
            alternativas = q.get("alternativas") or []
            if len(alternativas) not in {4, 5}:
                erros.append(f"{prefixo}: MCQ deve ter 4 ou 5 alternativas")
            if str(q.get("gabarito")) not in {str(x) for x in range(len(alternativas))}:
                erros.append(f"{prefixo}: gabarito MCQ fora do intervalo")
            else:
                chave = str(q.get("gabarito"))
                distribuicao[chave] = distribuicao.get(chave, 0) + 1
            normalizadas = [normalizar(a) for a in alternativas]
            if len(set(normalizadas)) != len(normalizadas):
                erros.append(f"{prefixo}: alternativas duplicadas")
            if any(re.fullmatch(r"[a-z]", a or "") for a in normalizadas):
                erros.append(f"{prefixo}: alternativa aparentemente truncada")
        elif tipo == "verdadeiro_falso":
            if str(q.get("gabarito")).lower() not in {"true", "false", "certo", "errado", "verdadeiro", "falso"}:
                erros.append(f"{prefixo}: gabarito C/E inválido")
        elif tipo == "numerica":
            try:
                float(str(q.get("gabarito")).replace(",", "."))
            except (TypeError, ValueError):
                erros.append(f"{prefixo}: gabarito numérico inválido")
        enunciado = normalizar(q.get("enunciado"))
        if enunciado in enunciados:
            erros.append(f"{prefixo}: enunciado duplicado no lote")
        elif any(SequenceMatcher(None, enunciado, anterior).ratio() >= 0.92 for anterior in enunciados):
            erros.append(f"{prefixo}: enunciado quase duplicado no lote")
        enunciados.append(enunciado)
    if len(questoes) >= 20 and distribuicao:
        contagens = [distribuicao.get(str(i), 0) for i in range(4)]
        if max(contagens) > len(questoes) * 0.45:
            erros.append(f"lote: gabaritos excessivamente concentrados {contagens}")
    return erros


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("arquivo")
    parser.add_argument("--min", type=int, default=20)
    parser.add_argument("--max", type=int, default=50)
    args = parser.parse_args()
    with open(args.arquivo, encoding="utf-8") as f:
        dados = json.load(f)
    erros = validar(dados, args.min, args.max)
    if erros:
        print("LOTE REPROVADO")
        print("\n".join(f"- {e}" for e in erros))
        return 1
    print(f"LOTE APROVADO: {len(dados.get('bloco', dados).get('questoes', []))} questões")
    return 0


if __name__ == "__main__":
    sys.exit(main())

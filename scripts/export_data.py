"""Exporta as tabelas do SQLite para JSON antes da migração."""
import argparse
import json
import os
import sqlite3
from datetime import date, datetime

TABLES = ("concursos", "users", "sessoes", "topicos", "blocos", "questoes",
          "respostas", "progresso", "fontes", "topicos_fontes")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=os.environ.get("DB_PATH", "data/concurso.db"))
    parser.add_argument("--out", default="backup-concurso-tutor.json")
    args = parser.parse_args()
    con = sqlite3.connect(args.db)
    con.row_factory = sqlite3.Row
    payload = {"schema": 1, "tables": {}}
    for table in TABLES:
        exists = con.execute(
            "select 1 from sqlite_master where type='table' and name=?",
            (table,),
        ).fetchone()
        rows = con.execute("select * from " + table).fetchall() if exists else []
        payload["tables"][table] = [dict(row) for row in rows]
    with open(args.out, "w", encoding="utf-8") as out:
        json.dump(payload, out, ensure_ascii=False, indent=2, default=str)
    print("Exportadas", sum(map(len, payload["tables"].values())), "linhas para", args.out)


if __name__ == "__main__":
    main()

# Auditoria Hermes — concurso-tutor

Gerado em: `2026-09-06 12:01:29`

## Escopo

- **Não alterei código-fonte nem arquivos de configuração.**
- Arquivo criado/atualizado por pedido do Eduardo: `HERMES_AUDIT.md`.
- Testes executados apenas quando havia comando/estrutura detectável, com timeout curto e sem instalar dependências do projeto.

## Resumo

- Tipo detectado: **Python app/lib**
- Arquivos analisados: **38**
- Tamanho aproximado analisado: **0.31 MB**

## Linguagens / tipos de arquivo

- Python: 13
- JSON: 10
- Outro: 6
- Markdown: 4
- INI: 1
- YAML: 1
- JavaScript: 1
- HTML: 1
- CSS: 1

## Arquivos principais vistos

- `.coverage`
- `.env.example`
- `.gitignore`
- `.pi/plans/plano.md`
- `Dockerfile`
- `README.md`
- `backend/app/__init__.py`
- `backend/app/auth.py`
- `backend/app/db.py`
- `backend/app/main.py`
- `backend/app/models.py`
- `backend/app/planner.py`
- `backend/app/schemas.py`
- `backend/data/concurso.db`
- `backend/seed.py`
- `backend/tests/__init__.py`
- `backend/tests/conftest.py`
- `backend/tests/test_auth.py`
- `backend/tests/test_main.py`
- `backend/tests/test_planner.py`
- `bloco1_enf.json`
- `bloco1_pericia.json`
- `bloco1_pf.json`
- `bloco2_enf.json`
- `bloco2_pericia.json`
- `bloco2_pf.json`
- `bloco3_enf.json`
- `bloco3_pericia.json`
- `bloco4_enf.json`
- `bloco4_pf.json`
- `docker-compose.yml`
- `frontend/app.js`
- `frontend/index.html`
- `frontend/styles.css`
- `grok_populate_prompt.md`
- `pytest.ini`
- `requirements.txt`
- `skills/tutor-concurso/SKILL.md`

## Estado Git

- Comando: `git status --short --branch`
- Exit code: `0`

```text
## main...origin/main
```

## Resultado dos testes / validações

### ✅ OK
- Comando: `python3 -m pytest -q`
- Exit code: `0`
- Tempo: `19.47s`

```text
........................................................................ [ 93%]
.....                                                                    [100%]
77 passed in 15.76s
```

### ✅ OK
- Comando: `python3 -m compileall -q /home/eduardodlima/projetos/concurso-tutor/backend/seed.py /home/eduardodlima/projetos/concurso-tutor/backend/tests/test_planner.py /home/eduardodlima/projetos/concurso-tutor/backend/tests/test_main.py /home/eduardodlima/projetos/concurso-tutor/backend/tests/conftest.py /home/eduardodlima/projetos/concurso-tutor/backend/tests/__init__.py /home/eduardodlima/projetos/concurso-tutor/backend/tests/test_auth.py /home/eduardodlima/projetos/concurso-tutor/backend/app/auth.py /home/eduardodlima/projetos/concurso-tutor/backend/app/schemas.py /home/eduardodlima/projetos/concurso-tutor/backend/app/main.py /home/eduardodlima/projetos/concurso-tutor/backend/app/planner.py /home/eduardodlima/projetos/concurso-tutor/backend/app/models.py /home/eduardodlima/projetos/concurso-tutor/backend/app/__init__.py /home/eduardodlima/projetos/concurso-tutor/backend/app/db.py`
- Exit code: `0`
- Tempo: `0.74s`

```text
(sem saída)
```

### ✅ OK
- Comando: `node /tmp/check_html_inline_scripts.js /home/eduardodlima/projetos/concurso-tutor`
- Exit code: `0`
- Tempo: `0.33s`

```text
/home/eduardodlima/projetos/concurso-tutor/frontend/index.html sem script inline para checar
```


## Propostas gerais de melhoria

1. Criar suíte mínima de testes em `tests/`.

## Próximo passo sugerido

Priorizar pequenas melhorias incrementais com teste antes/depois, porque o estado atual validou sem falhas nos checks executados.

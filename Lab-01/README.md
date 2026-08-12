# Lab01 — Características de repositórios populares + Setup do Kanban

Ver enunciado completo em [`Enunciado_Lab-01.md`](Enunciado_Lab-01.md).

## Estrutura

```
Lab-01/
├── data/
│   ├── raw/            # CSV dos repositórios coletados (scripts em scripts/)
│   └── snapshots/       # CSVs de fechamento de sprint do GitHub Projects (Parte 2, item 6)
├── reports/
│   └── figures/          # gráficos gerados para o relatório (Lab01S03)
├── scripts/              # runners que orquestram config + src.queries + src.github_client + src.metrics
├── src/
│   ├── analysis/          # estatísticas e gráficos (Lab01S03) - pendente
│   ├── export/            # escrita de CSV/JSON
│   ├── github_client/     # cliente GraphQL genérico (auth, request, retry)
│   ├── metrics/            # um extract_rqXX por RQ: "o que fazer com a resposta"
│   └── queries/             # strings de query GraphQL: "o que perguntar", uma por RQ
├── tests/                 # pendente
├── config.py               # token e URL da API, lidos do .env
├── requirements.txt
└── pyproject.toml          # deixa `config` e `src.*` importáveis (pip install -e .)
```

Cada runner em `scripts/` é o "validador" de uma RQ: busca uma amostra, valida os
campos e imprime/persiste o resultado. O script único do grupo
(`scripts/script_unico_grupo.py`) junta os campos já integrados numa única consulta
para os 100 repositórios pedidos pela S01.

## Setup

```
cd Lab-01
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install -e .          # instala `config` e `src.*` em modo editável
copy .env.example .env    # editar e colar um GitHub token seu (sem escopos, só leitura pública)
```

## Rodar

```
python scripts\rq01_idade.py
python scripts\rq02_prs_aceitas.py
python scripts\rq03_releases.py
python scripts\rq04_atualizacao.py
python scripts\script_unico_grupo.py
```

Notas de validação de cada RQ (amostra, checklist, observações) ficam em
`scripts/README_<pessoa>.md`.

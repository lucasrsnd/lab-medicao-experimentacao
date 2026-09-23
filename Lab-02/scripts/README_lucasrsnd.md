# Scripts de Lucas

Issues [S01] a cargo do Lucas (Milestone `Lab02S01` no GitHub Projects):

- [x] **#48 Script de coleta de métricas estáticas (Radon + jscpd)**, em `../src/metrics/static_metrics.py`
- [x] **#49 Setup do GitHub Projects para o Lab02**, em `../src/project/snapshot.py` (reaproveita `Lab-01/scripts/snapshot_project.py`, com milestone por sprint a mais)
- [x] **Revisão conjunta do desenho do experimento** (compartilhado com Gustavo e Davi)

Issues [S03] / Relatório Final a cargo do Lucas:

- [x] **#72 RQ3 — Complexidade ciclomática e duplicação**, em `../src/analysis/rq3_estrutura.py` (resultados em `../docs/resultados-rq3.md`)
- [x] **#77 Discussão final + ameaças à validade**, seções 4 e 5 de `../reports/relatorio_final.md`
- [x] **#78 Print do board + link do repositório/Projects**, seção 6 de `../reports/relatorio_final.md` (print em `../reports/figures/board_github_projects.png`)

> Nota: este arquivo estava, por engano, com uma cópia do conteúdo de
> `README_DaviSantos23.md`, corrigido para refletir as issues de fato
> atribuídas ao Lucas.

## Como rodar

Métricas estáticas de um trial (Radon cc/raw/mi + jscpd), acrescenta uma linha em `data/raw/trials_metricas.csv`:

```bash
python -m src.metrics.static_metrics \
    --kata k1 --participante lucasrsnd --tratamento sem_ia \
    --path katas/k1/sem_ia/lucasrsnd
```

Snapshot de fechamento de sprint do GitHub Projects, salva em `data/snapshots/snapshot_Lab02S01.csv`:

```bash
python -m src.project.snapshot --sprint Lab02S01
```

Análise da RQ3 (lê `data/raw/trials_metricas.csv`, grava `reports/analysis/rq3_estrutura.{md,json}`):

```bash
python -m src.analysis.rq3_estrutura
```

Testes: `python -m pytest tests/test_static_metrics.py tests/test_snapshot.py tests/test_rq3_estrutura.py`.

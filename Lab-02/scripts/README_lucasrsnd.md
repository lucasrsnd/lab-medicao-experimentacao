# Scripts de Lucas

Issues [S01] a cargo do Lucas (Milestone `Lab02S01` no GitHub Projects):

- [x] **#48 Script de coleta de métricas estáticas (Radon + jscpd)**, em `../src/metrics/static_metrics.py`
- [x] **#49 Setup do GitHub Projects para o Lab02**, em `../src/project/snapshot.py` (reaproveita `Lab-01/scripts/snapshot_project.py`, com milestone por sprint a mais)
- [x] **Revisão conjunta do desenho do experimento** (compartilhado com Gustavo e Davi)

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

Testes: `python -m pytest tests/test_static_metrics.py tests/test_snapshot.py`.

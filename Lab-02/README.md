# Lab02 — Assistentes de IA vs. Codificação Manual

Experimento controlado (crossover within-subject) comparando trials de
programação com e sem assistente de IA, em 6 katas resolvidos pelos 3
integrantes do grupo. Enunciado completo em `Laboratório 02.pdf`. Issues e
Milestones (`Lab02S01`, `Lab02S02`, `Lab02S03`, `Lab02-RelatorioFinal`) vivem
no GitHub Projects do grupo — fonte de verdade para a correção, não replicadas aqui.

**Repositório / GitHub Projects:** https://github.com/lucasrsnd/lab-medicao-experimentacao
(projeto "Laboratório - Medição e Experimentação", mesmo board do Lab01).

## Estrutura

```
Lab-02/
├── docs/                    # desenho do experimento, ambiente de execução
├── katas/kXX/               # 6 katas; cada um com com_ia/ e sem_ia/ por integrante
├── src/
│   ├── timing/              # cronometragem / time-to-green (Gustavo)
│   ├── metrics/             # Radon + jscpd + LOC (Lucas)
│   ├── project/             # setup/snapshot do GitHub Projects (Lucas)
│   └── analysis/            # RQ1-RQ3 + dashboard (Milestone S03)
├── scripts/                 # READMEs individuais + entrypoints CLI
├── data/{raw,processed,snapshots}/
├── reports/figures/         # gráficos do dashboard e do relatório final
├── tests/                   # testes unitários dos módulos de src/
└── config.py, .env.example  # assistente de IA, time-box, credenciais do Projects
```

Convenção herdada do Lab01: `src/` tem a lógica reutilizável, `scripts/` são
entrypoints finos que a chamam, `data/`/`reports/` guardam saída gerada
(nunca lógica).

## Setup

```bash
python -m venv .venv
.venv/Scripts/activate   # Windows
pip install -r requirements.txt
cp .env.example .env     # preencher AI_ASSISTANT_NAME etc.
```

`jscpd` (duplicação de código, RQ3) roda via Node/npm — ver nota em
`requirements.txt`.

## Sprints

| Sprint | Entregável | Pontos |
|---|---|---|
| Lab02S01 | Desenho do experimento + preparação | 5 |
| Lab02S02 | Execução do experimento + coleta de dados | 5 |
| Lab02S03 | Análise de resultados (RQ1-RQ3) + Dashboard | 5 |
| Relatório Final | Documento final | 5 |

Divisão de responsabilidades por sprint: ver as Issues da Milestone correspondente
no GitHub Projects e os `scripts/README_<usuário>.md` de cada integrante.

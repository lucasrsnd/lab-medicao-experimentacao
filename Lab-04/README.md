# Lab 04 — Pearson × Spearman por simulação

Par **P5**: tamanho do módulo (LOC) × número de defeitos. Plano, arquitetura e
contratos entre módulos em [`docs/plano-lab04.md`](docs/plano-lab04.md).

- GitHub Projects: <https://github.com/users/lucasrsnd/projects/2>
- Dashboard: *link adicionado na publicação (FINAL-02)*

## Instalação

No diretório `Lab-04`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

## Testes

```powershell
python -m pytest
```

## Contratos compartilhados

| Módulo | Conteúdo |
|---|---|
| `lab04.config` | semente (`SEED = 42`), α, repetições, tamanhos de efeito e caminhos de `data/` e `outputs/` |
| `lab04.contracts` | `MarginalParams`, `Scenario`, `TestResult` e colunas dos arquivos trocados entre módulos |
| `lab04.style` | cor e rótulo de cada teste e `apply_layout` (título, eixos e legenda) |

Os comandos de reprodução e do dashboard serão adicionados nas issues seguintes.

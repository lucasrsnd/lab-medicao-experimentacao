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

## Dashboard

No diretório `Lab-04`, com o ambiente ativado:

```powershell
streamlit run src/lab04/dashboard/app.py
```

O dashboard só lê os artefatos versionados em `data/real/`, `outputs/` e
`docs/dashboard/`. Os textos de cada seção ficam em `docs/dashboard/NN-*.md`, e
cada autor edita só o seu. Seções cujos artefatos ainda não existem mostram um
aviso em vez de quebrar a página.

| Seção | Conteúdo | Situação |
|---|---|---|
| 1. Cenário | pergunta, H₀/H₁, origem dos dados | S01 |
| 2. Os dados | G1 — real × simulado | S01 |
| 3. Como os testes funcionam | G2 — t sob H₀, região de rejeição, p-valor do exemplo | S01 |
| 4. Erro tipo I | G3 | S02 |
| 5. Poder | G4 | S02 |
| 6. Dados reais | tabela dos dois testes | entrega final |
| 7. Conclusão | expectativa × resultado, recomendação | entrega final |

## Contratos compartilhados

| Módulo | Conteúdo |
|---|---|
| `lab04.config` | semente (`SEED = 42`), α, repetições, tamanhos de efeito e caminhos de `data/` e `outputs/` |
| `lab04.contracts` | `MarginalParams`, `Scenario`, `TestResult` e colunas dos arquivos trocados entre módulos |
| `lab04.style` | cor e rótulo de cada teste e `apply_layout` (título, eixos e legenda) |

O comando único de reprodução será adicionado na integração final (FINAL-01).

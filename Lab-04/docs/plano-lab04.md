# Lab04 — Plano do projeto

Par escolhido: **P5 — Pearson × Spearman**. Cenário: tamanho do módulo (LOC) × número de defeitos, com amostra real de um dataset público (NASA MDP / PROMISE). Dashboard em **Streamlit**.

O backlog completo (critérios de aceite de cada issue) está em [`../tools/create_lab04_backlog.sh`](../tools/create_lab04_backlog.sh). Use `--table` para ver o resumo e `--dry-run` para ver os corpos.

## Princípios

1. **Um módulo, um dono.** Cada integrante só edita os arquivos da sua issue. Ninguém altera o módulo do outro durante a sprint.
2. **Integração por contrato.** Os módulos se comunicam por funções com assinatura fixa (abaixo) e por arquivos em `outputs/` com formato fixo. Quem precisa de algo que ainda não existe usa uma *fixture* sintética nos testes.
3. **Funções puras.** Gráficos recebem `DataFrame` e devolvem `plotly.graph_objects.Figure`. Simulação recebe `numpy.random.Generator`. Nada lê ou escreve arquivo dentro da lógica; I/O fica na CLI.
4. **Reprodutível.** Semente única em `config.SEED = 42`, um comando para rodar tudo e outro para abrir o dashboard.
5. **Commits com `#issue`.** Sem o número da issue, o commit não conta para a correção.

## Estrutura

```text
Lab-04/
├── README.md                     # instalação + os dois comandos
├── pyproject.toml
├── data/real/                    # dataset bruto + amostra.csv + README com fonte/licença  (Lucas)
├── docs/
│   ├── cenario.md                # item c: pergunta, H0/H1, distribuições, expectativa  (Lucas)
│   └── dashboard/NN-*.md         # textos curtos de cada seção (2 a 4 frases)          (autor da seção)
├── scripts/                      # exemplo_simulado.py (Davi), simular.py (Davi)
├── outputs/                      # gerados por código e versionados (o dashboard só lê)
│   ├── real_params.json          # (Lucas)
│   ├── exemplo_simulado.json     # (Davi)
│   └── simulacoes.csv            # (Davi)
├── src/lab04/
│   ├── config.py  contracts.py  style.py          # compartilhados          (Gustavo, S01-01)
│   ├── cli.py  __main__.py                         # comando único           (Gustavo, final)
│   ├── real_data.py                                # carga, amostra, ajuste  (Lucas)
│   ├── stats_tests.py                              # Pearson e Spearman      (Davi)
│   ├── simulation/
│   │   ├── generator.py                            # cópula gaussiana        (Davi)
│   │   ├── scenarios.py                            # registro de cenários    (Davi)
│   │   ├── montecarlo.py  sample_size.py           # Q1/Q2, poder × n        (Davi)
│   │   └── violations.py                           # cenários da Q3          (Lucas)
│   ├── plots/
│   │   ├── g1_dados.py  g3_erro_tipo1.py           #                         (Lucas)
│   │   └── g2_nula.py   g4_poder.py                #                         (Gustavo)
│   └── dashboard/app.py  interativo.py             #                         (Gustavo)
└── tests/                        # um arquivo de teste por módulo, mesmo dono
```

## Contratos

Valem desde o primeiro dia. Quem começar antes do merge da S01-01 copia estas assinaturas e ajusta o import depois.

### `config.py`

```python
SEED = 42
ALPHA = 0.05
N_SIMS = 10_000
EFFECTS = (0.0, 0.1, 0.2, 0.3, 0.4, 0.5)   # correlação latente ρ (≥ 5 valores, começando em 0)
N_REAL = 30
TESTS = ("pearson", "spearman")
```

### `contracts.py`

```python
@dataclass(frozen=True)
class MarginalParams:
    loc_mu: float              # log da mediana de LOC (lognormal)
    loc_sigma: float
    defects_mean: float        # binomial negativa: variância = m + m²/k
    defects_dispersion: float  # k

@dataclass(frozen=True)
class Scenario:
    name: str                  # id estável, ex.: "realista", "outliers"
    label: str                 # texto para gráficos
    n: int
    params: MarginalParams
    postprocess: Callable[[np.ndarray, np.ndarray, np.random.Generator],
                          tuple[np.ndarray, np.ndarray]] | None = None   # ex.: injeção de outliers

@dataclass(frozen=True)
class TestResult:
    test: str                  # "pearson" | "spearman"
    statistic: float           # t com n-2 g.l. (os dois testes)
    p_value: float             # bicaudal
    effect: float              # r ou ρ amostral
    ci_low: float
    ci_high: float
    n: int
```

### Funções

| Módulo | Assinatura | Dono |
|---|---|---|
| `simulation.generator` | `generate(params, n, rho, rng) -> DataFrame[loc, defects]` | Davi |
| `simulation.generator` | `generate_batch(scenario, rho, n_sims, rng) -> (X, Y)` com forma `(n_sims, n)` | Davi |
| `simulation.scenarios` | `register(s: Scenario)`, `get(name)`, `all_scenarios() -> list[Scenario]` | Davi |
| `stats_tests` | `pearson(x, y) -> TestResult`, `spearman(x, y) -> TestResult` | Davi |
| `stats_tests` | `pvalues(test, X, Y) -> ndarray` (vetorizado por linha) | Davi |
| `simulation.montecarlo` | `rejection_rates(scenarios, effects, n_sims, alpha, seed) -> DataFrame` | Davi |
| `real_data` | `load_sample() -> DataFrame[module_id, loc, defects]`, `fit_params(df) -> MarginalParams` | Lucas |
| `simulation.violations` | `register_violations() -> list[Scenario]` | Lucas |
| `plots.g1_dados` | `figure(real: DataFrame, simulated: DataFrame) -> Figure` | Lucas |
| `plots.g2_nula` | `figure(test, n, observed_statistic, alpha=ALPHA) -> Figure` | Gustavo |
| `plots.g3_erro_tipo1` | `figure(results: DataFrame) -> Figure` | Lucas |
| `plots.g4_poder` | `figure(results: DataFrame) -> Figure` | Gustavo |
| `style` | `TEST_COLORS`, `TEST_LABELS`, `apply_layout(fig, title, x_title, y_title)` | Gustavo |

### Arquivos em `outputs/`

| Arquivo | Formato | Produzido por | Lido por |
|---|---|---|---|
| `data/real/amostra.csv` | `module_id, loc, defects` | Lucas | G1, seção 6 |
| `real_params.json` | `{"fonte", "n", "params": MarginalParams, "observado": {"pearson_r", "spearman_rho", "assimetria_loc", "assimetria_defects", "prop_zeros"}}` | Lucas | gerador, seções 1–2 |
| `exemplo_simulado.json` | `{"seed", "rho", "n", "resultados": [TestResult, TestResult]}` | Davi | G2, seção 3 |
| `simulacoes.csv` | `scenario, label, n, effect, test, rejections, n_sims, rate, ci_low, ci_high, alpha` | Davi | G3, G4 |

## Divisão

Papéis: **A = Davi** (@DaviSantos23), **B = Gustavo** (@gustavoprehl), **C = Lucas** (@lucasrsnd). Cada pessoa tem código em cada sprint.

| Sprint | Davi — simulação e testes | Lucas — dados reais e violações | Gustavo — base, dashboard e integração |
|---|---|---|---|
| **S01** | S01-03 Gerador (cópula gaussiana)<br>S01-04 Testes + aplicação a um conjunto simulado | S01-05 Amostra real + ajuste de parâmetros<br>S01-06 Cenário (item c) + G1 | S01-01 Pacote, contratos e config<br>S01-02 Dashboard (seções 1–3) + G2 |
| **S02** | S02-01 Motor Monte Carlo (Q1, Q2)<br>S02-02 Poder × tamanho da amostra | S02-03 Cenários de violação (Q3)<br>S02-04 G3 erro tipo I | S02-05 G4 + seções 4–5<br>S02-06 Bônus: simulador interativo |
| **Final** | — | — | FINAL-01 Merge e comando único<br>FINAL-02 Seções 6–7 e publicação<br>FINAL-03 Roteiro das 15 perguntas |

Dependências reais são poucas: cada issue pode ser desenvolvida e testada com fixtures. Só o **merge** (FINAL-01, e o merge de fim de cada sprint) junta tudo.

## Fluxo de trabalho

- Uma branch por integrante (`dev_<Nome>`), PR para `main` ao concluir cada issue.
- Gustavo faz o merge de fim de sprint para o dashboard exibir G1/G2 (S01) e G3/G4 (S02), como pede o enunciado.
- No board: no máximo uma issue em *Doing* por pessoa; mover cartões semanalmente; milestones `Lab04S01`, `Lab04S02`, `Lab04-EntregaFinal` criados e atribuídos pelo script.
- Done = critérios marcados, testes passando, commit com `#N`, revisão de outro integrante.

"""Seção 6: os dois testes aplicados aos dados reais e o poder no tamanho real.

Lógica pura (recebe e devolve dados); o I/O fica em ``main``, chamada pela etapa
``python -m lab04 dados-reais``. Grava:

- ``outputs/dados_reais.json``: estatística, p-valor (aproximação t e permutação),
  correlação com IC 95% e a conversão do efeito observado para a escala da simulação;
- ``outputs/poder_por_n.csv``: poder dos dois testes por tamanho de amostra para o
  efeito observado e para um efeito conservador (limite inferior do IC do Spearman).

A simulação controla a correlação **latente** ρ da cópula; o ρ de Spearman medido
em amostras de 30 classes com muitos empates é menor. ``calibrate_latent_rho``
encontra o ρ latente cuja média do ρ de Spearman amostral iguala o observado.
"""

from __future__ import annotations

import json
from dataclasses import replace

import numpy as np
import pandas as pd
from scipy import stats

from lab04.config import ALPHA, OUTPUTS_DIR, SEED, TESTS
from lab04.contracts import SIMULATION_COLUMNS, Scenario
from lab04.permutation import permutation_null, permutation_pvalue
from lab04.simulation.generator import generate_batch
from lab04.simulation.sample_size import minimum_sample_sizes, power_by_n
from lab04.stats_tests import pearson, spearman

REAL_RESULTS_PATH = OUTPUTS_DIR / "dados_reais.json"
POWER_BY_N_PATH = OUTPUTS_DIR / "poder_por_n.csv"
N_PERMUTATIONS = 20_000
CALIBRATION_GRID = np.round(np.arange(0.0, 0.96, 0.05), 2)
CALIBRATION_SIMS = 2_000
POWER_NS = [10, 15, 20, 25, 30, 40, 50, 60, 80, 100, 125, 150, 200]
POWER_SIMS = 2_000
TARGET_POWER = 0.8
REFERENCES = {"observado": "efeito observado", "conservador": "efeito conservador (limite inferior do IC)"}


def real_tests(sample: pd.DataFrame, n_perm: int = N_PERMUTATIONS, seed: int = SEED) -> list[dict]:
    """Os dois testes nos dados reais, com p-valor pela t(n−2) e por permutação."""
    x, y = sample["loc"].to_numpy(dtype=float), sample["defects"].to_numpy(dtype=float)
    rows = []
    for test, run in (("pearson", pearson), ("spearman", spearman)):
        result = run(x, y)
        null = permutation_null(test, x, y, n_perm=n_perm, rng=np.random.default_rng(seed))
        rows.append({**result.to_dict(), "p_permutation": permutation_pvalue(null, result.statistic)})
    return rows


def _row_spearman(X: np.ndarray, Y: np.ndarray) -> np.ndarray:
    rx, ry = stats.rankdata(X, axis=1), stats.rankdata(Y, axis=1)
    rx -= rx.mean(axis=1, keepdims=True)
    ry -= ry.mean(axis=1, keepdims=True)
    den = np.sqrt(np.einsum("ij,ij->i", rx, rx) * np.einsum("ij,ij->i", ry, ry))
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.einsum("ij,ij->i", rx, ry) / den


def spearman_by_latent_rho(scenario: Scenario, n_sims: int = CALIBRATION_SIMS, seed: int = SEED) -> pd.Series:
    """ρ de Spearman amostral médio (no ``n`` do cenário) para cada ρ latente da grade."""
    rng = np.random.default_rng(seed)
    means = {}
    for rho in CALIBRATION_GRID:
        X, Y = generate_batch(scenario, float(rho), n_sims, rng)
        means[float(rho)] = float(np.nanmean(_row_spearman(X.astype(float), Y.astype(float))))
    return pd.Series(means)


def calibrate_latent_rho(observed_spearman: float, curve: pd.Series) -> float:
    """Interpola a curva (monótona) para achar o ρ latente equivalente ao observado."""
    if not curve.is_monotonic_increasing:
        curve = curve.cummax()
    return float(np.interp(observed_spearman, curve.to_numpy(), curve.index.to_numpy()))


def power_curves(scenario: Scenario, effects: dict[str, float], n_sims: int = POWER_SIMS) -> pd.DataFrame:
    """Poder × n para cada efeito de referência (coluna ``reference``)."""
    frames = []
    for reference, effect in effects.items():
        frame = power_by_n(scenario, round(effect, 3), POWER_NS, n_sims=n_sims, seed=SEED)
        frames.append(frame.assign(reference=reference))
    return pd.concat(frames, ignore_index=True)[["reference", *SIMULATION_COLUMNS]]


def required_n(curves: pd.DataFrame, target: float = TARGET_POWER) -> dict[str, dict[str, int | None]]:
    """Menor n da grade com poder ≥ ``target``, por efeito de referência e teste."""
    out = {}
    for reference, frame in curves.groupby("reference", sort=False):
        table = minimum_sample_sizes(frame[list(SIMULATION_COLUMNS)], target)
        out[reference] = {row.test: (None if pd.isna(row.n_min) else int(row.n_min)) for row in table.itertuples()}
    return out


def build(sample: pd.DataFrame, scenario: Scenario) -> tuple[dict, pd.DataFrame]:
    tests = real_tests(sample)
    spearman_row = next(r for r in tests if r["test"] == "spearman")
    curve = spearman_by_latent_rho(scenario)
    effects = {
        "observado": calibrate_latent_rho(spearman_row["effect"], curve),
        "conservador": calibrate_latent_rho(spearman_row["ci_low"], curve),
    }
    curves = power_curves(scenario, effects)
    at_real_n = curves[curves["n"] == scenario.n]
    content = {
        "n": int(len(sample)),
        "alpha": ALPHA,
        "seed": SEED,
        "n_permutations": N_PERMUTATIONS,
        "resultados": tests,
        "efeito_latente": {k: round(v, 3) for k, v in effects.items()},
        "efeito_referencia": {"observado": spearman_row["effect"], "conservador": spearman_row["ci_low"]},
        "poder_no_n_real": {
            ref: {t: float(at_real_n[(at_real_n["reference"] == ref) & (at_real_n["test"] == t)]["rate"].iloc[0])
                  for t in TESTS}
            for ref in effects
        },
        "n_para_80": required_n(curves),
        "power_sims": POWER_SIMS,
    }
    return content, curves


def main() -> None:
    from lab04.config import SAMPLE_PATH
    from lab04.simulation.scenarios import get

    sample = pd.read_csv(SAMPLE_PATH)
    content, curves = build(sample, get("realista"))
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    REAL_RESULTS_PATH.write_text(json.dumps(content, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    curves.to_csv(POWER_BY_N_PATH, index=False)
    print(f"Resultados nos dados reais -> {REAL_RESULTS_PATH}")
    print(f"Poder por tamanho de amostra -> {POWER_BY_N_PATH}")
    print(json.dumps({k: content[k] for k in ("efeito_latente", "poder_no_n_real", "n_para_80")}, indent=2))


if __name__ == "__main__":
    main()

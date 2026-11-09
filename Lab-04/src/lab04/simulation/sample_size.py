"""Estimativas de poder estatístico para diferentes tamanhos amostrais."""

from __future__ import annotations

from dataclasses import replace

import pandas as pd

from lab04.config import ALPHA, N_SIMS, SEED, TESTS
from lab04.contracts import SIMULATION_COLUMNS, Scenario
from lab04.simulation.montecarlo import rejection_rates


def power_by_n(
    scenario: Scenario,
    effect: float,
    ns: list[int],
    *,
    n_sims: int = N_SIMS,
    seed: int = SEED,
) -> pd.DataFrame:
    """Calcula o poder dos dois testes para cada tamanho amostral em ``ns``.

    O resultado segue as mesmas colunas de ``simulacoes.csv`` e pode ser
    gravado por um chamador sem introduzir I/O nesta função.
    """
    if not ns:
        raise ValueError("É necessário fornecer ao menos um tamanho amostral.")
    if any(not isinstance(n, int) or isinstance(n, bool) or n < 4 for n in ns):
        raise ValueError("Cada tamanho amostral deve ser um inteiro >= 4.")
    if len(set(ns)) != len(ns):
        raise ValueError("Os tamanhos amostrais não podem se repetir.")

    rows = [
        rejection_rates(
            [replace(scenario, n=n)],
            (effect,),
            n_sims,
            ALPHA,
            seed,
        )
        for n in sorted(ns)
    ]
    return pd.concat(rows, ignore_index=True).loc[:, SIMULATION_COLUMNS]


def power_at_observed_n(
    scenario: Scenario,
    observed_effect: float,
    *,
    n_sims: int = N_SIMS,
    seed: int = SEED,
) -> pd.DataFrame:
    """Estima o poder no ``n`` do cenário usando o efeito observado informado.

    O valor observado é fornecido pelo chamador (por exemplo, lido de
    ``real_params.json``); a função permanece pura e não acessa arquivos.
    """
    return power_by_n(
        scenario,
        observed_effect,
        [scenario.n],
        n_sims=n_sims,
        seed=seed,
    )


def minimum_sample_sizes(
    power_results: pd.DataFrame,
    target_power: float = 0.8,
) -> pd.DataFrame:
    """Retorna o menor ``n`` que atinge o poder-alvo em cada teste.

    ``n_min`` é ``None`` para testes que não atingem o alvo nos tamanhos
    disponíveis.
    """
    missing = set(SIMULATION_COLUMNS) - set(power_results.columns)
    if missing:
        raise ValueError(f"power_results sem as colunas {sorted(missing)}.")
    if not 0.0 < target_power <= 1.0:
        raise ValueError("target_power deve estar em (0, 1].")
    unknown = set(power_results["test"]) - set(TESTS)
    if unknown:
        raise ValueError(f"Testes desconhecidos em power_results: {sorted(unknown)}.")

    rows: list[dict[str, object]] = []
    for test in TESTS:
        eligible = power_results[
            (power_results["test"] == test)
            & (power_results["rate"] >= target_power)
        ]
        n_min = int(eligible["n"].min()) if not eligible.empty else None
        rows.append({"test": test, "n_min": n_min, "target_power": target_power})
    return pd.DataFrame(rows, columns=["test", "n_min", "target_power"])

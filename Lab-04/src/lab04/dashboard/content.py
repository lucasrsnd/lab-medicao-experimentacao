"""Leitura dos artefatos exibidos no dashboard, sem dependência do Streamlit.

Cada função devolve ``None`` quando o artefato ainda não existe, para que a
seção correspondente mostre um aviso em vez de quebrar a página.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from lab04.config import (
    DASHBOARD_TEXTS_DIR, EXAMPLE_PATH, REAL_PARAMS_PATH, SAMPLE_PATH, SEED, TESTS,
)
from lab04.contracts import MarginalParams, TestResult
from lab04.simulation.generator import generate

# Tamanho do conjunto simulado do G1: grande o bastante para mostrar a forma da marginal.
G1_SIMULATED_N = 10_000


@dataclass(frozen=True)
class RealParams:
    source: str
    n: int
    params: MarginalParams
    observed: dict[str, float]


@dataclass(frozen=True)
class Example:
    seed: int
    rho: float
    n: int
    results: dict[str, TestResult]


def section_text(name: str, base: Path = DASHBOARD_TEXTS_DIR) -> str | None:
    """Texto de ``docs/dashboard/<name>.md`` (ex.: ``01-cenario``)."""
    path = base / f"{name}.md"
    return path.read_text(encoding="utf-8").strip() if path.exists() else None


def real_sample(path: Path = SAMPLE_PATH) -> pd.DataFrame | None:
    return pd.read_csv(path) if path.exists() else None


def real_params(path: Path = REAL_PARAMS_PATH) -> RealParams | None:
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return RealParams(
        source=data["fonte"],
        n=int(data["n"]),
        params=MarginalParams.from_dict(data["params"]),
        observed={k: float(v) for k, v in data["observado"].items()},
    )


def example(path: Path = EXAMPLE_PATH) -> Example | None:
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    results = {r["test"]: TestResult.from_dict(r) for r in data["resultados"]}
    if set(results) != set(TESTS):
        raise ValueError(f"exemplo_simulado.json deve ter os testes {TESTS}.")
    return Example(seed=int(data["seed"]), rho=float(data["rho"]), n=int(data["n"]), results=results)


def example_sample(ex: Example, params: MarginalParams) -> pd.DataFrame:
    """Recria o conjunto do exemplo (mesma receita de scripts/exemplo_simulado.py)."""
    return generate(params, n=ex.n, rho=ex.rho, rng=np.random.default_rng(ex.seed))


def g1_simulated(params: MarginalParams, n: int = G1_SIMULATED_N, seed: int = SEED) -> pd.DataFrame:
    """Conjunto simulado para o G1; ρ = 0 porque o G1 compara só as marginais."""
    return generate(params, n=n, rho=0.0, rng=np.random.default_rng(seed))

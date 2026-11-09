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
    DASHBOARD_TEXTS_DIR, EXAMPLE_PATH, REAL_PARAMS_PATH, SAMPLE_PATH, SEED, SIMULATIONS_PATH, TESTS,
)
from lab04.contracts import SIMULATION_COLUMNS, MarginalParams, TestResult
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


def section_parts(name: str, base: Path = DASHBOARD_TEXTS_DIR) -> dict[str, str] | None:
    """Blocos de ``docs/dashboard/<name>.md``, indexados pelo cabeçalho ``## ...``.

    Ex.: ``{"O que observar": "...", "Conclusão": "..."}``. Texto antes do
    primeiro cabeçalho fica na chave ``""``. A ordem do arquivo é preservada.
    """
    path = base / f"{name}.md"
    if not path.exists():
        return None
    parts: dict[str, list[str]] = {"": []}
    current = ""
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            current = line[3:].strip()
            parts[current] = []
        else:
            parts[current].append(line)
    blocks = {key: "\n".join(lines).strip() for key, lines in parts.items()}
    return {key: body for key, body in blocks.items() if body}


def real_sample(path: Path = SAMPLE_PATH) -> pd.DataFrame | None:
    return pd.read_csv(path) if path.exists() else None


def simulations(path: Path = SIMULATIONS_PATH) -> pd.DataFrame | None:
    """``outputs/simulacoes.csv`` (Q1–Q3), validado contra o contrato de colunas."""
    if not path.exists():
        return None
    data = pd.read_csv(path)
    missing = set(SIMULATION_COLUMNS) - set(data.columns)
    if missing:
        raise ValueError(f"simulacoes.csv sem as colunas {sorted(missing)}.")
    return data


def real_results(path: Path | None = None) -> dict | None:
    """``outputs/dados_reais.json`` (seção 6)."""
    from lab04.real_results import REAL_RESULTS_PATH

    path = path or REAL_RESULTS_PATH
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def power_by_n_curves(path: Path | None = None) -> pd.DataFrame | None:
    """``outputs/poder_por_n.csv`` (seção 6)."""
    from lab04.real_results import POWER_BY_N_PATH

    path = path or POWER_BY_N_PATH
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

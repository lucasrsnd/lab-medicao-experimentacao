"""Dados sintéticos no formato longo, usados até a coleta piloto real (#184) chegar."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from analise.config import SEED


def generate(
    n_unidades: int = 20,
    repeticoes: int = 5,
    tratamentos: tuple[str, str] = ("A", "B"),
    razao_mediana: float = 0.85,
    seed: int = SEED,
) -> pd.DataFrame:
    """Gera duas métricas fictícias: ``tempo_ms`` (lognormal) e ``tamanho_kb`` (normal).

    Cada unidade (ex.: consulta, página, tarefa) é medida em todos os tratamentos, então os
    dados servem para os desenhos pareado e independente. ``razao_mediana`` é o efeito
    simulado do segundo tratamento sobre o tempo.
    """
    rng = np.random.default_rng(seed)
    base = rng.lognormal(mean=np.log(200.0), sigma=0.5, size=n_unidades)
    size = rng.normal(800.0, 150.0, size=n_unidades)
    rows = []
    for t_index, treatment in enumerate(tratamentos):
        factor = razao_mediana**t_index
        for unit in range(n_unidades):
            for rep in range(1, repeticoes + 1):
                rows.append((treatment, f"u{unit:03d}", rep, "tempo_ms",
                             base[unit] * factor * rng.lognormal(0.0, 0.15)))
                rows.append((treatment, f"u{unit:03d}", rep, "tamanho_kb",
                             size[unit] + rng.normal(0.0, 5.0)))
    return pd.DataFrame(rows, columns=["tratamento", "unidade", "repeticao", "metrica", "valor"])


def main() -> None:
    parser = argparse.ArgumentParser(description="Gera um piloto sintético no formato longo.")
    parser.add_argument("saida", type=Path, help="Caminho do CSV de saída.")
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args()
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    generate(seed=args.seed).to_csv(args.saida, index=False)
    print(f"Gerado: {args.saida}")


if __name__ == "__main__":
    main()

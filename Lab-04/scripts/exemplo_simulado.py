"""Gera e salva um exemplo reproduzível dos testes Pearson e Spearman."""

from __future__ import annotations

import json

import numpy as np

from lab04.config import EXAMPLE_PATH, SEED
from lab04.simulation.generator import generate
from lab04.simulation.scenarios import get
from lab04.stats_tests import pearson, spearman


def build_example() -> dict:
    """Monta o exemplo n=30, rho=0,5, sem realizar operações de arquivo."""
    scenario = get("realista")
    rho = 0.5
    sample = generate(
        scenario.params,
        n=30,
        rho=rho,
        rng=np.random.default_rng(SEED),
    )
    results = [
        pearson(sample["loc"].to_numpy(), sample["defects"].to_numpy()).to_dict(),
        spearman(sample["loc"].to_numpy(), sample["defects"].to_numpy()).to_dict(),
    ]
    return {"seed": SEED, "rho": rho, "n": 30, "resultados": results}


def main() -> None:
    content = build_example()
    EXAMPLE_PATH.parent.mkdir(parents=True, exist_ok=True)
    EXAMPLE_PATH.write_text(
        json.dumps(content, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Exemplo salvo em {EXAMPLE_PATH}")


if __name__ == "__main__":
    main()

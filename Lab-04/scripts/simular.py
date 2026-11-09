"""Executa o motor Monte Carlo e salva outputs/simulacoes.csv."""

from __future__ import annotations

from lab04.config import ALPHA, EFFECTS, N_SIMS, SEED, SIMULATIONS_PATH
from lab04.simulation.montecarlo import rejection_rates
from lab04.simulation.scenarios import all_scenarios


def main() -> None:
    """Gera as simulações configuradas e salva o CSV de resultados."""
    results = rejection_rates(all_scenarios(), EFFECTS, N_SIMS, ALPHA, SEED)
    SIMULATIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(SIMULATIONS_PATH, index=False)
    print(f"Simulações salvas em {SIMULATIONS_PATH}")


if __name__ == "__main__":
    main()

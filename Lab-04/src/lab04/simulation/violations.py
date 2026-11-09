"""Cenários que violam pressupostos dos testes de correlação (Q3).

Todos partem dos parâmetros estimados nos dados reais (``real_params.json``) e
usam apenas ``Scenario.postprocess`` e os parâmetros marginais: o gerador não
muda. Com ρ = 0 a hipótese nula continua verdadeira em todos eles, então a taxa
de rejeição medida é erro tipo I; com ρ > 0 ela mede o poder sob a violação.

Violações:

* ``outliers``: parte das observações de LOC e de defeitos é contaminada por
  valores extremos, escolhidos de forma independente em X e em Y.
* ``assimetria_extrema``: marginais bem mais assimétricas que as reais
  (LOC com σ maior, defeitos com dispersão k muito pequena).
* ``amostra_pequena``: n = 10, onde a aproximação por t(n−2) é menos confiável.
"""

from __future__ import annotations

from dataclasses import replace

import numpy as np

from lab04.config import N_REAL
from lab04.contracts import MarginalParams, Scenario
from lab04.simulation import scenarios

# Fração de cada variável contaminada por outliers (X e Y sorteados em separado).
OUTLIER_FRACTION = 0.05
# Um outlier de LOC é a classe multiplicada por este fator (classe 10× maior).
LOC_OUTLIER_FACTOR = 10
# Um outlier de defeitos soma este número de defeitos (age mesmo sobre zeros).
DEFECTS_OUTLIER_SHIFT = 20

# Assimetria extrema: σ de LOC e dispersão de defeitos em relação ao real.
SKEW_LOC_SIGMA = 2.5
SKEW_DEFECTS_DISPERSION = 0.05
SMALL_SAMPLE_N = 10


def inject_outliers(
    loc: np.ndarray, defects: np.ndarray, rng: np.random.Generator
) -> tuple[np.ndarray, np.ndarray]:
    """Contamina ``OUTLIER_FRACTION`` de X e de Y, cada um com sua própria máscara.

    A máscara de X é sorteada sem olhar para Y (e vice-versa), e o valor
    contaminado depende só da própria variável. Assim, se X e Y eram
    independentes (ρ = 0), continuam independentes e H₀ segue verdadeira.
    """
    loc, defects = np.asarray(loc), np.asarray(defects)
    loc_mask = rng.random(loc.shape) < OUTLIER_FRACTION
    defects_mask = rng.random(defects.shape) < OUTLIER_FRACTION
    return (
        np.where(loc_mask, loc * LOC_OUTLIER_FACTOR, loc),
        np.where(defects_mask, defects + DEFECTS_OUTLIER_SHIFT, defects),
    )


def build_violations(base: MarginalParams) -> list[Scenario]:
    """Monta os cenários de violação a partir das marginais reais ``base``."""
    return [
        Scenario(
            name="outliers",
            label="Outliers (5% de cada variável)",
            n=N_REAL,
            params=base,
            postprocess=inject_outliers,
        ),
        Scenario(
            name="assimetria_extrema",
            label="Assimetria extrema",
            n=N_REAL,
            params=replace(
                base,
                loc_sigma=max(base.loc_sigma, SKEW_LOC_SIGMA),
                defects_dispersion=min(base.defects_dispersion, SKEW_DEFECTS_DISPERSION),
            ),
        ),
        Scenario(
            name="amostra_pequena",
            label=f"Amostra pequena (n = {SMALL_SAMPLE_N})",
            n=SMALL_SAMPLE_N,
            params=base,
        ),
    ]


def register_violations() -> list[Scenario]:
    """Registra os cenários de violação (idempotente) e devolve-os.

    Usa as marginais do cenário ``realista`` já registrado, de modo que os
    parâmetros reais ficam em um só lugar.
    """
    base = scenarios.get("realista").params
    registered = []
    for scenario in build_violations(base):
        try:
            registered.append(scenarios.get(scenario.name))
        except KeyError:
            scenarios.register(scenario)
            registered.append(scenario)
    return registered

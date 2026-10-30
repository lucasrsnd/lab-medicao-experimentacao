"""Contratos compartilhados entre os módulos (ver docs/plano-lab04.md).

Alterações aqui afetam todos os integrantes: combine antes de mudar campos.
"""

from collections.abc import Callable
from dataclasses import asdict, dataclass
import math

import numpy as np

from lab04.config import TESTS

# Colunas de data/real/amostra.csv.
SAMPLE_COLUMNS = ("module_id", "loc", "defects")
# Colunas de DataFrames simulados (gerador → G1).
SIMULATED_COLUMNS = ("loc", "defects")
# Colunas de outputs/simulacoes.csv (motor Monte Carlo → G3, G4).
SIMULATION_COLUMNS = (
    "scenario", "label", "n", "effect", "test",
    "rejections", "n_sims", "rate", "ci_low", "ci_high", "alpha",
)

Postprocess = Callable[
    [np.ndarray, np.ndarray, np.random.Generator], tuple[np.ndarray, np.ndarray]
]


def _require_positive(value: float, field: str) -> None:
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{field} deve ser finito e positivo.")


@dataclass(frozen=True)
class MarginalParams:
    """Marginais da simulação: LOC lognormal e defeitos binomial negativa."""

    loc_mu: float              # log da mediana de LOC
    loc_sigma: float
    defects_mean: float        # variância = m + m²/k
    defects_dispersion: float  # k

    def __post_init__(self) -> None:
        if not math.isfinite(self.loc_mu):
            raise ValueError("loc_mu deve ser finito.")
        _require_positive(self.loc_sigma, "loc_sigma")
        _require_positive(self.defects_mean, "defects_mean")
        _require_positive(self.defects_dispersion, "defects_dispersion")

    def to_dict(self) -> dict[str, float]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "MarginalParams":
        return cls(**{key: float(data[key]) for key in cls.__dataclass_fields__})


@dataclass(frozen=True)
class Scenario:
    """Situação simulada; ``postprocess`` altera (X, Y) já gerados, ex.: outliers."""

    name: str
    label: str
    n: int
    params: MarginalParams
    postprocess: Postprocess | None = None

    def __post_init__(self) -> None:
        if not self.name or not self.name.isidentifier():
            raise ValueError("name deve ser um identificador estável, ex.: 'outliers'.")
        if self.n < 4:
            raise ValueError("n deve ser >= 4 para os testes de correlação.")


@dataclass(frozen=True)
class TestResult:
    """Resultado de um teste bicaudal de correlação."""

    __test__ = False  # impede o pytest de tratar a classe como teste

    test: str
    statistic: float           # t com n-2 g.l. (os dois testes)
    p_value: float
    effect: float              # r ou ρ amostral
    ci_low: float
    ci_high: float
    n: int

    def __post_init__(self) -> None:
        if self.test not in TESTS:
            raise ValueError(f"test deve ser um de {TESTS}.")
        if not 0.0 <= self.p_value <= 1.0:
            raise ValueError("p_value deve estar em [0, 1].")
        if not -1.0 <= self.ci_low <= self.effect <= self.ci_high <= 1.0:
            raise ValueError("Exige -1 <= ci_low <= effect <= ci_high <= 1.")
        if self.n < 4:
            raise ValueError("n deve ser >= 4.")

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "TestResult":
        return cls(**{key: data[key] for key in cls.__dataclass_fields__})

"""Registro de cenários disponíveis para as simulações."""

from __future__ import annotations

import json

from lab04.config import N_REAL, REAL_PARAMS_PATH
from lab04.contracts import MarginalParams, Scenario

_SCENARIOS: dict[str, Scenario] = {}


def register(scenario: Scenario) -> None:
    """Registra um cenário, rejeitando nomes já utilizados."""
    if scenario.name in _SCENARIOS:
        raise ValueError(f"O cenário {scenario.name!r} já está registrado.")
    _SCENARIOS[scenario.name] = scenario


def get(name: str) -> Scenario:
    """Retorna o cenário registrado com ``name``."""
    try:
        return _SCENARIOS[name]
    except KeyError as exc:
        raise KeyError(f"Cenário não registrado: {name!r}.") from exc


def all_scenarios() -> list[Scenario]:
    """Devolve uma lista dos cenários registrados, na ordem de registro."""
    return list(_SCENARIOS.values())


# Reserva quando outputs/real_params.json ainda não existe (valores da amostra de Ant 1.7).
FALLBACK_PARAMS = MarginalParams(
    loc_mu=4.922853178784091,
    loc_sigma=1.4809567864815052,
    defects_mean=0.7333333333333333,
    defects_dispersion=0.22734045999352126,
)


def _real_params() -> MarginalParams:
    """Parâmetros estimados dos dados reais, para a simulação acompanhar a amostra."""
    if not REAL_PARAMS_PATH.exists():
        return FALLBACK_PARAMS
    data = json.loads(REAL_PARAMS_PATH.read_text(encoding="utf-8"))
    return MarginalParams.from_dict(data["params"])


def _register_default() -> None:
    register(Scenario(name="realista", label="Realista", n=N_REAL, params=_real_params()))


_register_default()

import json

import pytest

from lab04 import cli
from lab04.config import LAB_ROOT, REAL_PARAMS_PATH
from lab04.contracts import MarginalParams
from lab04.simulation import scenarios


@pytest.fixture
def recorded(monkeypatch):
    calls = []
    fake = {name: (desc, (lambda n=name: calls.append(n))) for name, (desc, _) in cli.STEPS.items()}
    monkeypatch.setattr(cli, "STEPS", fake)
    return calls


def test_default_runs_every_step_in_pipeline_order(recorded):
    cli.main([])
    assert recorded == ["amostra", "exemplo", "simular", "dados-reais"]


def test_single_step(recorded):
    cli.main(["simular"])
    assert recorded == ["simular"]


def test_unknown_step_is_rejected():
    with pytest.raises(SystemExit):
        cli.main(["inexistente"])


def test_scripts_called_by_cli_exist():
    for name in ("exemplo_simulado.py", "simular.py"):
        assert (LAB_ROOT / "scripts" / name).exists()


def test_realistic_scenario_uses_committed_real_params():
    saved = json.loads(REAL_PARAMS_PATH.read_text(encoding="utf-8"))["params"]
    assert scenarios.get("realista").params == MarginalParams.from_dict(saved)

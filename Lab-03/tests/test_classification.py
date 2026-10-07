import math

import pytest

from lab03.metrics import classify_dora


@pytest.mark.parametrize(("frequency", "points"), [
    (7, 4),
    (1, 3),
    (12 / 52, 2),
    (12 / 52 - 1e-9, 1),
])
def test_limites_de_classificacao_da_frequencia(frequency, points):
    result = classify_dora(
        deployment_frequency_per_week=frequency,
        lead_time_hours=None,
        change_failure_rate=None,
        recovery_time_hours=None,
        denominators={"deployment_frequency_per_week": 1},
    )
    assert result["metrics"]["deployment_frequency_per_week"]["points"] == points


@pytest.mark.parametrize(("hours", "points"), [
    (0, 4), (24 - 1e-9, 4), (24, 3), (168 - 1e-9, 3),
    (168, 2), (720 - 1e-9, 2), (720, 1),
])
def test_limites_de_classificacao_de_lead_time(hours, points):
    result = classify_dora(
        deployment_frequency_per_week=None,
        lead_time_hours=hours,
        change_failure_rate=None,
        recovery_time_hours=None,
        denominators={"lead_time_hours": 1},
    )
    assert result["metrics"]["lead_time_hours"]["points"] == points


@pytest.mark.parametrize(("cfr", "points"), [
    (0, 4), (0.15, 4), (0.150001, 3), (0.30, 3),
    (0.300001, 2), (0.45, 2), (0.450001, 1), (1, 1),
])
def test_limites_de_classificacao_de_cfr(cfr, points):
    result = classify_dora(
        deployment_frequency_per_week=None,
        lead_time_hours=None,
        change_failure_rate=cfr,
        recovery_time_hours=None,
        denominators={"change_failure_rate": 1},
    )
    assert result["metrics"]["change_failure_rate"]["points"] == points


@pytest.mark.parametrize(("hours", "points"), [
    (0, 4), (1 - 1e-9, 4), (1, 3), (24 - 1e-9, 3),
    (24, 2), (168 - 1e-9, 2), (168, 1),
])
def test_limites_de_classificacao_de_recuperacao(hours, points):
    result = classify_dora(
        deployment_frequency_per_week=None,
        lead_time_hours=None,
        change_failure_rate=None,
        recovery_time_hours=hours,
        denominators={"recovery_time_hours": 1},
    )
    assert result["metrics"]["recovery_time_hours"]["points"] == points


def test_classificacao_geral_usa_mediana_arredondada_para_baixo():
    result = classify_dora(
        deployment_frequency_per_week=7,
        lead_time_hours=24,
        change_failure_rate=0.30,
        recovery_time_hours=168,
        denominators={
            "deployment_frequency_per_week": 52,
            "lead_time_hours": 5,
            "change_failure_rate": 50,
            "recovery_time_hours": 3,
        },
    )
    assert [metric["points"] for metric in result["metrics"].values()] == [4, 3, 3, 1]
    assert result["overall"] == {
        "points": 3,
        "category": "High",
        "status": "classified",
        "missing_metrics": [],
    }


def test_dados_ausentes_nao_recebem_categoria_nem_pontos():
    result = classify_dora(
        deployment_frequency_per_week=0,
        lead_time_hours=None,
        change_failure_rate=None,
        recovery_time_hours=None,
        denominators={"deployment_frequency_per_week": 52.0},
        numerators={"deployment_frequency_per_week": 0},
        missing_reasons={
            "change_failure_rate": "not_collected",
            "recovery_time_hours": "not_collected",
        },
    )
    assert result["metrics"]["deployment_frequency_per_week"]["category"] == "Low"
    assert result["metrics"]["deployment_frequency_per_week"]["denominator"] == 52.0
    assert result["metrics"]["lead_time_hours"]["category"] is None
    assert result["metrics"]["change_failure_rate"]["category"] is None
    assert result["overall"]["points"] is None
    assert result["overall"]["category"] is None
    assert result["overall"]["status"] == "incomplete"
    assert result["policy"]["incomplete_metrics"] == "not_classified"


def test_valor_sem_denominador_nao_e_classificado():
    result = classify_dora(
        deployment_frequency_per_week=7,
        lead_time_hours=None,
        change_failure_rate=None,
        recovery_time_hours=None,
    )
    metric = result["metrics"]["deployment_frequency_per_week"]
    assert metric["value"] is None
    assert metric["category"] is None
    assert metric["missing_reason"] == "missing_denominator"
    assert result["overall"]["status"] == "incomplete"


@pytest.mark.parametrize(("name", "value"), [
    ("lead_time_hours", -1),
    ("deployment_frequency_per_week", -0.1),
    ("change_failure_rate", 1.1),
    ("recovery_time_hours", -1),
    ("lead_time_hours", math.inf),
])
def test_metricas_invalidas_sao_rejeitadas(name, value):
    values = {
        "deployment_frequency_per_week": None,
        "lead_time_hours": None,
        "change_failure_rate": None,
        "recovery_time_hours": None,
    }
    values[name] = value
    with pytest.raises(ValueError):
        classify_dora(**values, denominators={name: 1})

"""Classificação DORA da disciplina, com ausência de dados explícita."""

import math
from statistics import median

CATEGORIES = {
    4: "Elite",
    3: "High",
    2: "Medium",
    1: "Low",
}

FREQUENCY_MONTHLY_THRESHOLD_PER_WEEK = 12 / 52


def _numeric_value(name: str, value: float | int | None) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} deve ser número ou None.")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} deve ser finito.")
    return result


def _classify(name: str, value: float | None) -> int | None:
    if value is None:
        return None
    if name == "deployment_frequency_per_week":
        if value < 0:
            raise ValueError("Frequência não pode ser negativa.")
        if value >= 7:
            return 4
        if value >= 1:
            return 3
        if value >= FREQUENCY_MONTHLY_THRESHOLD_PER_WEEK:
            return 2
        return 1
    if name == "lead_time_hours":
        if value < 0:
            raise ValueError("Lead time não pode ser negativo.")
        if value < 24:
            return 4
        if value < 168:
            return 3
        if value < 720:
            return 2
        return 1
    if name == "change_failure_rate":
        if not 0 <= value <= 1:
            raise ValueError("CFR deve estar no intervalo [0, 1].")
        if value <= 0.15:
            return 4
        if value <= 0.30:
            return 3
        if value <= 0.45:
            return 2
        return 1
    if name == "recovery_time_hours":
        if value < 0:
            raise ValueError("Tempo de recuperação não pode ser negativo.")
        if value < 1:
            return 4
        if value < 24:
            return 3
        if value < 168:
            return 2
        return 1
    raise ValueError(f"Métrica DORA desconhecida: {name}")


def classify_dora(
    *,
    deployment_frequency_per_week: float | int | None,
    lead_time_hours: float | int | None,
    change_failure_rate: float | int | None,
    recovery_time_hours: float | int | None,
    denominators: dict[str, float | int | None] | None = None,
    denominator_units: dict[str, str] | None = None,
    numerators: dict[str, float | int | None] | None = None,
    missing_reasons: dict[str, str] | None = None,
) -> dict:
    """Classifica as quatro métricas e só calcula a geral com dados completos."""
    raw_values = {
        "deployment_frequency_per_week": deployment_frequency_per_week,
        "lead_time_hours": lead_time_hours,
        "change_failure_rate": change_failure_rate,
        "recovery_time_hours": recovery_time_hours,
    }
    units = {
        "deployment_frequency_per_week": "releases_per_week",
        "lead_time_hours": "hours",
        "change_failure_rate": "proportion",
        "recovery_time_hours": "hours",
    }
    denominators = denominators or {}
    denominator_units = denominator_units or {}
    numerators = numerators or {}
    missing_reasons = missing_reasons or {}
    metrics = {}
    scores = []
    missing = []

    for name, raw_value in raw_values.items():
        value = _numeric_value(name, raw_value)
        denominator = denominators.get(name)
        if denominator is not None:
            denominator = _numeric_value(f"{name} denominator", denominator)
            if denominator < 0:
                raise ValueError(f"{name} denominator não pode ser negativo.")
            if denominator == 0:
                value = None
        elif value is not None:
            value = None
        points = _classify(name, value)
        reason = missing_reasons.get(name)
        if value is None:
            reason = reason or (
                "zero_denominator" if denominator == 0
                else "missing_denominator" if denominator is None and raw_value is not None
                else "missing_required_data"
            )
            missing.append(name)
        metrics[name] = {
            "value": value,
            "unit": units[name],
            "numerator": numerators.get(name),
            "denominator": denominator,
            "denominator_unit": denominator_units.get(name),
            "points": points,
            "category": CATEGORIES[points] if points is not None else None,
            "status": "classified" if points is not None else "incomplete",
            "missing_reason": reason if points is None else None,
        }
        if points is not None:
            scores.append(points)

    complete = not missing
    overall_score = math.floor(median(scores)) if complete else None
    return {
        "metrics": metrics,
        "overall": {
            "points": overall_score,
            "category": CATEGORIES[overall_score] if overall_score is not None else None,
            "status": "classified" if complete else "incomplete",
            "missing_metrics": missing,
        },
        "policy": {
            "incomplete_metrics": "not_classified",
            "overall_requires_all_four_metrics": True,
            "monthly_frequency_conversion": "1 release per month = 12/52 releases per week",
            "frequency_monthly_threshold_per_week": FREQUENCY_MONTHLY_THRESHOLD_PER_WEEK,
        },
    }

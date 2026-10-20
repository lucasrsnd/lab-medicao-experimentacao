"""Funções estatísticas e de formatação comuns às análises da S03."""

import statistics


def median_iqr(values: list[float]) -> dict:
    if not values:
        return {"median": None, "q1": None, "q3": None, "iqr": None}
    if len(values) == 1:
        q1 = q3 = values[0]
    else:
        q1, _, q3 = statistics.quantiles(values, n=4, method="inclusive")
    return {"median": statistics.median(values), "q1": q1, "q3": q3, "iqr": q3 - q1}


def holm(p_values: list[float | None]) -> list[float | None]:
    """Holm-Bonferroni sobre os p-valores definidos; indefinidos ficam None."""
    defined = sorted((p, i) for i, p in enumerate(p_values) if p is not None)
    adjusted: list[float | None] = [None] * len(p_values)
    running, m = 0.0, len(defined)
    for rank, (p, index) in enumerate(defined):
        running = max(running, min(1.0, (m - rank) * p))
        adjusted[index] = running
    return adjusted


def fmt(value, digits=3):
    return "—" if value is None else f"{value:.{digits}f}"


def fmt_p(value):
    return "—" if value is None else f"{value:.2e}" if value < 0.001 else f"{value:.4f}"

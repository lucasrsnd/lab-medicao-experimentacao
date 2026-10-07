"""Frequência de releases por semana na janela observada."""

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from lab03.domain import Window

SECONDS_PER_WEEK = 7 * 24 * 60 * 60


@dataclass(frozen=True)
class DeploymentFrequencyResult:
    releases_in_window: int
    window_seconds: float
    window_weeks: float
    releases_per_week: float


def calculate_deployment_frequency(
    published_at: Iterable[datetime], window: Window,
) -> DeploymentFrequencyResult:
    """Conta publicações em [start, end) e divide pela duração exata em semanas."""
    if not isinstance(window, Window):
        raise TypeError("window deve ser um Window.")
    if window.start.utcoffset() is None or window.end.utcoffset() is None:
        raise ValueError("A janela deve conter timestamps com fuso horário.")

    publications = tuple(published_at)
    if any(not isinstance(value, datetime) for value in publications):
        raise TypeError("Cada data de publicação deve ser datetime.")
    if any(value.utcoffset() is None for value in publications):
        raise ValueError("Cada data de publicação deve conter fuso horário.")

    seconds = (window.end - window.start).total_seconds()
    weeks = seconds / SECONDS_PER_WEEK
    count = sum(window.contains(value) for value in publications)
    return DeploymentFrequencyResult(
        releases_in_window=count,
        window_seconds=seconds,
        window_weeks=weeks,
        releases_per_week=count / weeks,
    )

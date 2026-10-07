"""Change failure rate (a), proxy de CI, segundo RQ03(a)."""

from collections import Counter
from dataclasses import dataclass
from typing import Iterable

from lab03.domain import WorkflowRun

SUCCESS_CONCLUSIONS = frozenset({"success"})
FAILURE_CONCLUSIONS = frozenset({"failure", "timed_out", "startup_failure"})


@dataclass(frozen=True)
class CiFailureRateResult:
    """`rate` é None quando não há run válido: ausência de dado, não 0%."""
    rate: float | None
    failures: int
    successes: int
    runs_evaluated: int
    ignored: dict[str, int]


def calculate_ci_failure_rate(runs: Iterable[WorkflowRun]) -> CiFailureRateResult:
    """falhas / (falhas + sucessos) sobre todos os workflows do repositório.

    Conclusões fora da tabela da seção 3 (cancelled, skipped, neutral,
    action_required, stale ou vazia) são ignoradas e contadas em `ignored`.
    Filtros de branch, evento e janela pertencem ao coletor.
    """
    failures = successes = 0
    ignored: Counter[str] = Counter()
    for run in runs:
        if run.conclusion in SUCCESS_CONCLUSIONS:
            successes += 1
        elif run.conclusion in FAILURE_CONCLUSIONS:
            failures += 1
        else:
            ignored[run.conclusion or "in_progress_or_empty"] += 1
    evaluated = failures + successes
    return CiFailureRateResult(
        rate=failures / evaluated if evaluated else None,
        failures=failures,
        successes=successes,
        runs_evaluated=evaluated,
        ignored=dict(sorted(ignored.items())),
    )

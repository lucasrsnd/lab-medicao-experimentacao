"""Episódios de falha de CI e tempo de recuperação, segundo RQ04."""

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from statistics import median
from typing import Iterable

from lab03.domain import WorkflowRun
from lab03.metrics.change_failure_rate import FAILURE_CONCLUSIONS, SUCCESS_CONCLUSIONS


@dataclass(frozen=True)
class RecoveryEpisode:
    workflow_id: int
    started_at: datetime
    ended_at: datetime | None
    failed_runs: int
    recovery_hours: float | None

    @property
    def censored(self) -> bool:
        return self.ended_at is None


@dataclass(frozen=True)
class RecoveryResult:
    """`median_hours` considera só episódios recuperados; os censurados são
    contados à parte (e não descartados) em `censored_episodes`."""
    median_hours: float | None
    episodes_total: int
    episodes_recovered: int
    censored_episodes: int
    censored_proportion: float | None
    leading_failures_without_prior_success: int
    exclusions: dict[str, int]
    episodes: tuple[RecoveryEpisode, ...]


def calculate_recovery(runs: Iterable[WorkflowRun]) -> RecoveryResult:
    """Cada workflow é percorrido em ordem cronológica, de forma independente.

    Episódio: começa na primeira falha após um sucesso e termina no próximo
    sucesso do mesmo workflow. Tempo = `updated_at` do sucesso − `run_started_at`
    da primeira falha (ou `created_at` se aquele não existir). Falha que nunca
    é seguida de sucesso na janela é censurada. Falhas iniciais sem sucesso
    anterior na janela não abrem episódio (o enunciado exige "após um
    sucesso"); são contadas em `leading_failures_without_prior_success`.
    Conclusões fora de sucesso/falha (ex.: cancelled) não alteram o estado.
    """
    by_workflow: dict[int, list[WorkflowRun]] = defaultdict(list)
    for run in runs:
        if run.conclusion in SUCCESS_CONCLUSIONS or run.conclusion in FAILURE_CONCLUSIONS:
            by_workflow[run.workflow_id].append(run)

    episodes: list[RecoveryEpisode] = []
    exclusions: Counter[str] = Counter()
    leading = 0
    for workflow_id in sorted(by_workflow):
        ordered = sorted(by_workflow[workflow_id], key=lambda r: (r.created_at, r.id))
        seen_success = False
        first_failure: WorkflowRun | None = None
        failed_runs = 0
        for run in ordered:
            if run.conclusion in FAILURE_CONCLUSIONS:
                if first_failure is not None:
                    failed_runs += 1
                elif seen_success:
                    first_failure, failed_runs = run, 1
                else:
                    leading += 1
                continue
            seen_success = True
            if first_failure is None:
                continue
            started = first_failure.run_started_at or first_failure.created_at
            ended = run.updated_at
            if ended is None or ended < started:
                exclusions["invalid_recovery_timestamps"] += 1
            else:
                episodes.append(RecoveryEpisode(
                    workflow_id, started, ended, failed_runs,
                    (ended - started).total_seconds() / 3600,
                ))
            first_failure, failed_runs = None, 0
        if first_failure is not None:
            episodes.append(RecoveryEpisode(
                workflow_id, first_failure.run_started_at or first_failure.created_at,
                None, failed_runs, None,
            ))

    recovered = [e.recovery_hours for e in episodes if not e.censored]
    censored = len(episodes) - len(recovered)
    return RecoveryResult(
        median_hours=median(recovered) if recovered else None,
        episodes_total=len(episodes),
        episodes_recovered=len(recovered),
        censored_episodes=censored,
        censored_proportion=censored / len(episodes) if episodes else None,
        leading_failures_without_prior_success=leading,
        exclusions=dict(exclusions),
        episodes=tuple(episodes),
    )

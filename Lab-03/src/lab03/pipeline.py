"""Orquestração dos coletores, métricas e análise do repositório."""

from dataclasses import asdict

from lab03.collectors.releases import collect_releases
from lab03.collectors.commits import collect_changes
from lab03.domain import Window, WorkflowRun
from lab03.github import GitHubClient
from lab03.metrics import (
    calculate_ci_failure_rate,
    calculate_deployment_frequency,
    calculate_lead_time,
    calculate_recovery,
    classify_dora,
)
from lab03.analysis.report import repository_report


def run(
    client: GitHubClient,
    repository: str,
    window: Window,
    workflow_runs: tuple[WorkflowRun, ...] | None = None,
) -> dict:
    """Com `workflow_runs=None` (ex.: modo amostra), CFR e recuperação ficam
    explicitamente ausentes e a classificação geral permanece incompleta."""
    catalog = collect_releases(client, repository, window)
    changes = collect_changes(client, repository, catalog, window)
    lead_time = calculate_lead_time(changes)
    frequency = calculate_deployment_frequency(
        (release.published_at for release in catalog.releases),
        window,
    )
    ci_failure_rate = recovery = None
    numerators = {"deployment_frequency_per_week": frequency.releases_in_window}
    denominators = {
        "deployment_frequency_per_week": frequency.window_weeks,
        "lead_time_hours": lead_time.releases_used,
    }
    missing_reasons = {
        "lead_time_hours": "no_valid_release_observations",
        "change_failure_rate": "workflow_runs_not_collected",
        "recovery_time_hours": "workflow_runs_not_collected",
    }
    if workflow_runs is not None:
        ci_failure_rate = calculate_ci_failure_rate(workflow_runs)
        recovery = calculate_recovery(workflow_runs, window)
        numerators["change_failure_rate"] = ci_failure_rate.failures
        denominators["change_failure_rate"] = ci_failure_rate.runs_evaluated
        denominators["recovery_time_hours"] = recovery.episodes_recovered
        missing_reasons["change_failure_rate"] = "no_valid_ci_runs"
        missing_reasons["recovery_time_hours"] = (
            "all_failure_episodes_censored" if recovery.episodes_total
            else "invalid_recovery_timestamps" if recovery.exclusions
            else "no_failure_episodes"
        )
    classification = classify_dora(
        deployment_frequency_per_week=frequency.releases_per_week,
        lead_time_hours=lead_time.by_release_hours,
        change_failure_rate=ci_failure_rate.rate if ci_failure_rate else None,
        recovery_time_hours=recovery.median_hours if recovery else None,
        numerators=numerators,
        denominators=denominators,
        denominator_units={
            "deployment_frequency_per_week": "weeks",
            "lead_time_hours": "releases",
            "change_failure_rate": "valid_ci_runs",
            "recovery_time_hours": "recovered_episodes",
        },
        missing_reasons=missing_reasons,
    )
    result = repository_report(repository, window, catalog, changes, lead_time)
    result["deployment_frequency"] = asdict(frequency)
    result["ci_failure_rate"] = asdict(ci_failure_rate) if ci_failure_rate else None
    result["recovery"] = asdict(recovery) if recovery else None
    result["dora_classification"] = classification
    return result

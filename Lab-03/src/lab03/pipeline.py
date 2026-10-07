"""Orquestração dos coletores, métricas e análise do repositório."""

from dataclasses import asdict

from lab03.collectors.releases import collect_releases
from lab03.collectors.commits import collect_changes
from lab03.domain import Window
from lab03.github import GitHubClient
from lab03.metrics import calculate_deployment_frequency, calculate_lead_time, classify_dora
from lab03.analysis.report import repository_report


def run(client: GitHubClient, repository: str, window: Window) -> dict:
    catalog = collect_releases(client, repository, window)
    changes = collect_changes(client, repository, catalog, window)
    lead_time = calculate_lead_time(changes)
    frequency = calculate_deployment_frequency(
        (release.published_at for release in catalog.releases),
        window,
    )
    classification = classify_dora(
        deployment_frequency_per_week=frequency.releases_per_week,
        lead_time_hours=lead_time.by_release_hours,
        change_failure_rate=None,
        recovery_time_hours=None,
        numerators={
            "deployment_frequency_per_week": frequency.releases_in_window,
        },
        denominators={
            "deployment_frequency_per_week": frequency.window_weeks,
            "lead_time_hours": lead_time.releases_used,
        },
        denominator_units={
            "deployment_frequency_per_week": "weeks",
            "lead_time_hours": "releases",
            "change_failure_rate": "valid_ci_runs",
            "recovery_time_hours": "recovery_episodes",
        },
        missing_reasons={
            "lead_time_hours": "no_valid_release_observations",
            "change_failure_rate": "not_collected_by_current_pipeline",
            "recovery_time_hours": "not_collected_by_current_pipeline",
        },
    )
    result = repository_report(repository, window, catalog, changes, lead_time)
    result["deployment_frequency"] = asdict(frequency)
    result["dora_classification"] = classification
    return result

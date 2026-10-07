"""Orquestração dos coletores, métricas e análise do repositório."""

from lab03.collectors.releases import collect_releases
from lab03.collectors.commits import collect_changes
from lab03.domain import Window
from lab03.github import GitHubClient
from lab03.metrics import calculate_lead_time
from lab03.analysis.report import repository_report


def run(client: GitHubClient, repository: str, window: Window) -> dict:
    catalog = collect_releases(client, repository, window)
    changes = collect_changes(client, repository, catalog, window)
    lead_time = calculate_lead_time(changes)
    return repository_report(repository, window, catalog, changes, lead_time)

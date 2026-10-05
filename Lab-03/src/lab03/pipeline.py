"""Orquestração do recorte de Gustavo: releases -> commits -> lead time."""

from dataclasses import asdict
from datetime import datetime, timezone
from lab03 import __version__
from lab03.collectors.releases import collect_releases
from lab03.collectors.commits import collect_changes
from lab03.domain import Window
from lab03.github import GitHubClient
from lab03.metrics import calculate_lead_time


def run(client: GitHubClient, repository: str, window: Window) -> dict:
    catalog = collect_releases(client, repository, window)
    main = collect_changes(client, repository, catalog, window)
    return {
        "schema_version": 1,
        "pipeline_version": __version__,
        "repository": repository,
        "generated_at": datetime.now(timezone.utc),
        "window": asdict(window),
        "catalog": asdict(catalog),
        "changes": [asdict(change) for change in main],
        "lead_time": asdict(calculate_lead_time(main)),
    }


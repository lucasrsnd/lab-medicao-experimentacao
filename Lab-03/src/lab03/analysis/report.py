"""Projeção dos objetos de domínio para o contrato JSON de saída."""

from dataclasses import asdict
from datetime import datetime, timezone

from lab03 import __version__
from lab03.domain import ReleaseCatalog, ReleaseChanges, Window
from lab03.metrics import LeadTimeResult


def repository_report(
    repository: str,
    window: Window,
    catalog: ReleaseCatalog,
    changes: tuple[ReleaseChanges, ...],
    lead_time: LeadTimeResult,
) -> dict:
    return {
        "schema_version": 1,
        "pipeline_version": __version__,
        "repository": repository,
        "generated_at": datetime.now(timezone.utc),
        "window": asdict(window),
        "catalog": asdict(catalog),
        "changes": [asdict(change) for change in changes],
        "lead_time": asdict(lead_time),
    }

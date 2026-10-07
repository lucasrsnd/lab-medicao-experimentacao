"""Integra seleção, elegibilidade, métricas e registros de workflow runs."""

from dataclasses import asdict

from lab03 import __version__
from lab03.collectors.candidates import select_candidates
from lab03.collectors.workflow_runs import collect_workflow_runs
from lab03.domain import Window
from lab03.github import DataError, GitHubClient
from lab03.pipeline import run


def run_pilot(
    client: GitHubClient,
    *,
    window: Window,
    target_size: int,
    stars_min_exclusive: int,
    minimum_releases: int,
    minimum_valid_runs: int,
    valid_conclusions: tuple[str, ...],
) -> dict:
    candidate_limit = target_size
    selection = None
    while True:
        selection = select_candidates(
            client,
            window.start,
            window.end,
            stars_min_exclusive=stars_min_exclusive,
            sample_size=candidate_limit,
            minimum_releases=minimum_releases,
            minimum_valid_runs=minimum_valid_runs,
            valid_conclusions=valid_conclusions,
        )
        eligible = selection["eligible_repositories"]
        selected_count = selection["funnel"]["search"]["selected"]
        available_count = selection["funnel"]["search"]["matching_candidates"]
        if len(eligible) >= target_size:
            break
        if selected_count >= available_count:
            raise DataError(
                f"Piloto incompleto: encontrados {len(eligible)} de "
                f"{target_size} repositórios elegíveis após avaliar "
                f"{selected_count} candidatos."
            )
        candidate_limit = min(max(candidate_limit * 2, candidate_limit + 1), available_count)

    selected = eligible[:target_size]
    selection["pilot_sample"] = {
        "target": target_size,
        "selected": len(selected),
        "eligible_not_selected": len(eligible) - len(selected),
    }
    results = []
    for metadata in selected:
        repository = metadata["full_name"]
        collection = {}
        workflow_runs = collect_workflow_runs(
            client,
            repository,
            window,
            metadata["default_branch"],
            valid_conclusions,
            stats=collection,
        )
        if len(workflow_runs) < minimum_valid_runs:
            raise DataError(
                f"{repository}: contagem de workflow runs mudou após a elegibilidade "
                f"({len(workflow_runs)} < {minimum_valid_runs})."
            )
        report = run(client, repository, window, workflow_runs)
        if len(report["catalog"]["releases"]) < minimum_releases:
            raise DataError(
                f"{repository}: releases do default branch abaixo do mínimo após integração."
            )
        results.append({
            "metadata": metadata,
            "report": report,
            "workflow_run_collection": collection,
            "workflow_runs": [asdict(workflow_run) for workflow_run in workflow_runs],
        })

    return {
        "schema_version": 1,
        "issue": 106,
        "pipeline_version": __version__,
        "collected_at": selection["collected_at"],
        "window": selection["window"],
        "criteria": selection["criteria"],
        "funnel": selection["funnel"],
        "pilot_sample": selection["pilot_sample"],
        "eligible_repositories": selected,
        "repositories": results,
    }

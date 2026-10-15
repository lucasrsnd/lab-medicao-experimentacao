"""Integra seleção, elegibilidade, métricas e registros de workflow runs."""

from dataclasses import asdict
from typing import Callable

from lab03 import __version__
from lab03.collectors.candidates import parallel_map, parallel_stream, select_candidates
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
    collect_tags: bool = True,
    top_only: bool = False,
    workers: int = 1,
    maximum_runs: int | None = None,
    maximum_releases: int | None = None,
    on_start=None,
    on_result=None,
    include_workflow_runs: bool = True,
    selection: dict | None = None,
    slice_range: tuple[int, int] | None = None,
    notify: Callable[[str], None] | None = None,
    required_repositories: tuple[str, ...] = (),
) -> dict:
    """Com `selection` (saída de uma seleção anterior, ex.: `config/selecao-amostra.json`)
    a busca e o funil não são refeitos: só a coleta, opcionalmente de uma fatia
    `slice_range=(início, fim)` da lista de elegíveis, para dividir o trabalho
    (e a cota de API) entre pessoas.

    Com `on_result`, cada repositório coletado é entregue (e descartado) assim
    que fica pronto, `on_start(cabeçalho)` é chamado antes do primeiro, e o
    retorno não traz `repositories`: a memória não cresce com a amostra."""
    notify = notify or (lambda message: None)
    if selection is None:
        # A integração detalhada pode descartar elegíveis que mudaram desde a triagem.
        # A reserva permite substituí-los sem deixar a amostra completa incompleta.
        candidate_limit = target_size * 8 if top_only else target_size
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
                top_only=top_only,
                workers=workers,
                maximum_runs=maximum_runs,
                maximum_releases=maximum_releases,
                ranked_search=True,
                notify=notify,
                required_repositories=required_repositories,
            )
            eligible = selection["eligible_repositories"]
            eligible_names = {r["full_name"].lower() for r in eligible}
            missing_required = [
                r for r in required_repositories if r.lower() not in eligible_names
            ]
            if missing_required:
                raise DataError(f"Repositórios obrigatórios não elegíveis: {missing_required}")
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
            # Seleção rápida: passos pequenos param assim que o alvo é atingido (o
            # que já foi avaliado vem do cache). Fora dela, o lote dobra.
            grown = candidate_limit + max(50, target_size // 2) if top_only else candidate_limit * 2
            candidate_limit = min(max(grown, candidate_limit + 1), available_count)

    else:
        eligible = selection["eligible_repositories"]
        if len(eligible) < target_size:
            raise DataError(
                f"A seleção informada tem {len(eligible)} repositórios; esperados {target_size}."
            )

    selected = eligible[:target_size]
    refill_candidates = top_only and on_result is not None and slice_range is None
    selection["pilot_sample"] = {
        "target": target_size,
        "selected": len(selected),
        "eligible_not_selected": len(eligible) - len(selected),
    }
    if slice_range is not None:
        start, end = slice_range
        if not 0 <= start < end <= len(selected):
            raise DataError(f"Fatia {start}:{end} fora da seleção de {len(selected)} repositórios.")
        selected = selected[start:end]
        selection["pilot_sample"]["slice"] = [start, end]
    collection_candidates = eligible if refill_candidates else selected

    def collect_repository(metadata):
        repository = metadata["full_name"]
        notify(f"Coleta completa: {repository}")
        collection = {}
        workflow_runs = collect_workflow_runs(
            client,
            repository,
            window,
            metadata["default_branch"],
            valid_conclusions,
            stats=collection,
            tolerate_drift=top_only,
        )
        if len(workflow_runs) < minimum_valid_runs:
            if top_only:
                return {
                    "collection_exclusion": {
                        "repository": repository,
                        "reason": "minimum_valid_workflow_runs_not_met_after_collection",
                    },
                    "metadata": metadata,
                }
            raise DataError(
                f"{repository}: contagem de workflow runs mudou após a elegibilidade "
                f"({len(workflow_runs)} < {minimum_valid_runs})."
            )
        report = run(client, repository, window, workflow_runs, collect_tags=collect_tags)
        if len(report["catalog"]["releases"]) < minimum_releases:
            if top_only:
                return {
                    "collection_exclusion": {
                        "repository": repository,
                        "reason": "minimum_releases_not_met_after_collection",
                    },
                    "metadata": metadata,
                }
            raise DataError(
                f"{repository}: releases do default branch abaixo do mínimo após integração."
            )
        return {
            "metadata": metadata,
            "report": report,
            "workflow_run_collection": collection,
            "workflow_run_count": len(workflow_runs),
            "workflow_runs": (
                [asdict(workflow_run) for workflow_run in workflow_runs]
                if include_workflow_runs else []
            ),
        }

    header = {
        "schema_version": 1,
        "issue": 106,
        "pipeline_version": __version__,
        "collected_at": selection["collected_at"],
        "window": selection["window"],
        "criteria": selection["criteria"],
        "funnel": selection["funnel"],
        "pilot_sample": selection["pilot_sample"],
        "tags_collected": collect_tags,
        "eligible_repositories": selected,
    }
    if on_result is None:
        header["repositories"] = parallel_map(collect_repository, selected, workers)
        return header
    if on_start is not None:
        on_start(header)
    if not refill_candidates:
        parallel_stream(collect_repository, selected, on_result, workers)
    else:
        exclusions = []
        replacements = []
        initial_names = {item["full_name"] for item in selected}
        collected = 0

        def consume(item):
            nonlocal collected
            exclusion = item.get("collection_exclusion")
            if exclusion is not None:
                exclusions.append(exclusion)
                return
            if collected >= target_size:
                return
            on_result(item)
            collected += 1
            repository = item["metadata"]["full_name"]
            if repository not in initial_names:
                replacements.append(repository)

        batch_size = max(1, workers * 2)
        for start in range(0, len(collection_candidates), batch_size):
            batch = collection_candidates[start:start + batch_size]
            parallel_stream(collect_repository, batch, consume, workers)
            if collected >= target_size:
                break
        if collected < target_size:
            raise DataError(
                f"Coleta incompleta: {collected} de {target_size} repositórios "
                f"atenderam aos critérios após integração."
            )
        header["collection_exclusions"] = exclusions
        header["collection_replacements"] = replacements
    return header

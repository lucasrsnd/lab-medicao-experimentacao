"""Coleta workflow runs válidos do branch padrão dentro da janela."""

from lab03.domain import WorkflowRun, Window
from lab03.github import DataError, GitHubClient
from lab03.normalization import normalize_workflow_run
from lab03.collectors.releases import repo_path


def collect_workflow_runs(
    client: GitHubClient,
    repository: str,
    window: Window,
    default_branch: str,
    valid_conclusions: tuple[str, ...],
) -> tuple[WorkflowRun, ...]:
    root = repo_path(repository)
    query = f"{window.start.isoformat()}..{window.end.isoformat()}"
    runs = {}
    expected_total = None
    observed = 0
    for page in client.pages(f"{root}/actions/runs", {
        "branch": default_branch,
        "event": "push",
        "created": query,
        "per_page": 100,
    }):
        if not isinstance(page, dict) or not isinstance(page.get("workflow_runs"), list):
            raise DataError("Resposta inválida ao listar workflow runs.")
        page_total = page.get("total_count")
        if (not isinstance(page_total, int) or isinstance(page_total, bool)
                or page_total < 0):
            raise DataError("Resposta de workflow runs sem total_count válido.")
        if expected_total is not None and expected_total != page_total:
            raise DataError("Total de workflow runs mudou durante a paginação.")
        expected_total = page_total
        for raw in page["workflow_runs"]:
            if not isinstance(raw, dict):
                raise DataError("Workflow run inválido.")
            identifier = raw.get("id")
            if not isinstance(identifier, int) or isinstance(identifier, bool):
                raise DataError("Workflow run sem ID numérico.")
            if identifier in runs:
                continue
            observed += 1
            run = normalize_workflow_run(raw)
            if (run.branch == default_branch and run.event == "push"
                    and run.conclusion in valid_conclusions
                    and window.contains(run.created_at)):
                runs[identifier] = run
    if expected_total is not None and observed < expected_total:
        raise DataError("Paginação de workflow runs incompleta.")
    return tuple(sorted(runs.values(), key=lambda run: (run.created_at, run.id)))

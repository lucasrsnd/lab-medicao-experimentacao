"""Coleta workflow runs válidos do branch padrão dentro da janela, sem truncamento.

A API limita cada consulta filtrada a 1.000 resultados e informa o
`total_count` real. Por isso a janela é fatiada em meses e qualquer fatia cujo
total chegue ao teto é bisseccionada até caber; se nem a menor fatia couber, a
coleta falha em vez de devolver dados truncados.
"""

from collections import Counter
from datetime import datetime, timedelta, timezone

from lab03.domain import WorkflowRun, Window
from lab03.github import DataError, GitHubClient
from lab03.normalization import normalize_workflow_run
from lab03.collectors.releases import repo_path

SEARCH_RESULT_CAP = 1000
def month_slices(window: Window) -> list[Window]:
    """Fatias mensais consecutivas, em UTC, cobrindo exatamente [start, end)."""
    start = window.start.astimezone(timezone.utc)
    end = window.end.astimezone(timezone.utc)
    slices = []
    cursor = start
    while cursor < end:
        month = cursor.month % 12 + 1
        year = cursor.year + (cursor.month == 12)
        following = datetime(year, month, 1, tzinfo=timezone.utc)
        slices.append(Window(cursor, min(following, end)))
        cursor = following
    return slices


def _format(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _fetch_slice(
    client: GitHubClient,
    root: str,
    default_branch: str,
    piece: Window,
    runs: dict[int, dict],
    stats: dict,
) -> None:
    # Arredondar o último instante para cima antes de subtrair 1s evita
    # perder runs no último segundo de janelas com limites fracionários.
    upper = piece.end.replace(microsecond=0)
    if piece.end.microsecond:
        upper += timedelta(seconds=1)
    last = upper - timedelta(seconds=1)
    query = f"{_format(piece.start)}..{_format(max(last, piece.start))}"
    pages = client.pages(f"{root}/actions/runs", {
        "branch": default_branch,
        "event": "push",
        "created": query,
        "per_page": 100,
    })
    fetched: dict[int, dict] = {}
    expected_total = None
    for page in pages:
        if not isinstance(page, dict) or not isinstance(page.get("workflow_runs"), list):
            raise DataError("Resposta inválida ao listar workflow runs.")
        page_total = page.get("total_count")
        if (not isinstance(page_total, int) or isinstance(page_total, bool)
                or page_total < 0):
            raise DataError("Resposta de workflow runs sem total_count válido.")
        if expected_total is not None and expected_total != page_total:
            raise DataError("Total de workflow runs mudou durante a paginação.")
        expected_total = page_total
        stats["requests"] += 1
        if page_total > SEARCH_RESULT_CAP:
            # Teto atingido: o conteúdo seria truncado. Não paginar; bisseccionar.
            break
        for raw in page["workflow_runs"]:
            if not isinstance(raw, dict):
                raise DataError("Workflow run inválido.")
            identifier = raw.get("id")
            if not isinstance(identifier, int) or isinstance(identifier, bool):
                raise DataError("Workflow run sem ID numérico.")
            fetched[identifier] = raw

    if expected_total is not None and expected_total > SEARCH_RESULT_CAP:
        middle = (piece.start + (piece.end - piece.start) / 2).replace(microsecond=0)
        if not piece.start < middle < piece.end:
            raise DataError(
                f"Mais de {SEARCH_RESULT_CAP} workflow runs em {query}; "
                "a janela não pode ser subdividida o suficiente."
            )
        stats["bisections"] += 1
        for half in (Window(piece.start, middle), Window(middle, piece.end)):
            _fetch_slice(client, root, default_branch, half, runs, stats)
        return
    if expected_total is not None and len(fetched) < expected_total:
        raise DataError("Paginação de workflow runs incompleta.")
    runs.update(fetched)


def collect_workflow_runs(
    client: GitHubClient,
    repository: str,
    window: Window,
    default_branch: str,
    valid_conclusions: tuple[str, ...],
    *,
    stats: dict | None = None,
) -> tuple[WorkflowRun, ...]:
    root = repo_path(repository)
    raw_runs: dict[int, dict] = {}
    stats = stats if stats is not None else {}
    stats.update({"slices": 0, "bisections": 0, "requests": 0})
    for piece in month_slices(window):
        stats["slices"] += 1
        _fetch_slice(client, root, default_branch, piece, raw_runs, stats)

    runs = {}
    ignored = Counter()
    exclusions = Counter()
    for identifier, raw in raw_runs.items():
        # Cancelled/em andamento não exigem datas de término/início válidas.
        if raw.get("head_branch") != default_branch or raw.get("event") != "push":
            ignored["branch_or_event"] += 1
            continue
        if raw.get("conclusion") not in valid_conclusions:
            ignored[raw.get("conclusion") or "in_progress_or_empty"] += 1
            continue
        try:
            run = normalize_workflow_run(raw)
        except DataError:
            exclusions["invalid_workflow_run"] += 1
            continue
        if not window.contains(run.created_at):
            ignored["outside_window"] += 1
            continue
        runs[identifier] = run
    stats.update({
        "observed": len(raw_runs), "valid": len(runs),
        "ignored": dict(ignored), "exclusions": dict(exclusions),
    })
    return tuple(sorted(runs.values(), key=lambda run: (run.created_at, run.id)))

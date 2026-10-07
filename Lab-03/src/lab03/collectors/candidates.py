"""Seleção da amostra e funil de elegibilidade de repositórios."""

from datetime import date, datetime, timedelta, timezone
from lab03.domain import timestamp
from lab03.github import ApiError, DataError, GitHubClient
from lab03.collectors.releases import repo_path

SEARCH_START = date(2008, 1, 1)
SEARCH_RESULT_LIMIT = 1000
SEARCH_PAGE_SIZE = 100
MAX_STARS = 2_147_483_647


def _current_search_end() -> date:
    return datetime.now(timezone.utc).date()


def _search_query(
    stars_min_exclusive: int, start: date, end: date,
    star_range: tuple[int, int] | None = None,
) -> str:
    stars = (
        f"stars:{star_range[0]}..{star_range[1]}"
        if star_range else f"stars:>{stars_min_exclusive}"
    )
    return f"is:public {stars} created:{start.isoformat()}..{end.isoformat()}"


def _search_count(client: GitHubClient, query: str) -> int:
    response = client.get("/search/repositories", {"q": query, "per_page": 1})
    if not isinstance(response, dict) or response.get("incomplete_results") is True:
        raise DataError("Busca de repositórios incompleta.")
    count = response.get("total_count")
    if not isinstance(count, int) or count < 0:
        raise DataError("Resposta inválida ao contar repositórios candidatos.")
    return count


def _search_slice(
    client: GitHubClient, query: str, start: date, end: date, stars_min_exclusive: int,
    star_range: tuple[int, int] | None = None,
) -> tuple[list[dict], list[dict]]:
    count = _search_count(client, query)
    if count >= SEARCH_RESULT_LIMIT:
        if start < end:
            midpoint = start + (end - start) // 2
            next_day = midpoint + timedelta(days=1)
            left_query = _search_query(stars_min_exclusive, start, midpoint, star_range)
            right_query = _search_query(stars_min_exclusive, next_day, end, star_range)
            left_items, left_queries = _search_slice(
                client, left_query, start, midpoint, stars_min_exclusive, star_range,
            )
            right_items, right_queries = _search_slice(
                client, right_query, next_day, end, stars_min_exclusive, star_range,
            )
        elif star_range is None:
            lower = stars_min_exclusive + 1
            midpoint = (lower + MAX_STARS) // 2
            ranges = ((lower, midpoint), (midpoint + 1, MAX_STARS))
            split_results = []
            for low, high in ranges:
                bounds = (low, high)
                split_query = _search_query(stars_min_exclusive, start, end, bounds)
                split_results.append(_search_slice(
                    client, split_query, start, end, stars_min_exclusive, bounds,
                ))
            left_items, left_queries = split_results[0]
            right_items, right_queries = split_results[1]
        elif star_range[0] < star_range[1]:
            low, high = star_range
            midpoint = (low + high) // 2
            ranges = ((low, midpoint), (midpoint + 1, high))
            split_results = []
            for bounds in ranges:
                split_query = _search_query(stars_min_exclusive, start, end, bounds)
                split_results.append(_search_slice(
                    client, split_query, start, end, stars_min_exclusive, bounds,
                ))
            left_items, left_queries = split_results[0]
            right_items, right_queries = split_results[1]
        else:
            raise DataError(
                f"Busca excedeu o limite de {SEARCH_RESULT_LIMIT} repositórios "
                f"com {star_range[0]} estrelas em {start.isoformat()}; "
                "não foi possível subdividir sem omitir candidatos."
            )
        return left_items + right_items, [
            {"query": query, "total_count": count, "pages": 0},
            *left_queries,
            *right_queries,
        ]

    items = []
    page_count = 0
    for page in client.pages(
        "/search/repositories",
        {"q": query, "per_page": SEARCH_PAGE_SIZE},
    ):
        page_count += 1
        if (not isinstance(page, dict) or not isinstance(page.get("items"), list)
                or page.get("incomplete_results") is True):
            raise DataError("Resposta inválida ao listar repositórios candidatos.")
        items.extend(page["items"])
    if len(items) < count:
        raise DataError("Busca de repositórios incompleta: paginação retornou menos itens que o total.")
    return items, [{"query": query, "total_count": count, "pages": page_count}]


def search_popular_repositories(
    client: GitHubClient, stars_min_exclusive: int,
) -> tuple[list[dict], dict]:
    """Busca repositórios públicos sem aceitar buscas truncadas pelo limite da API."""
    end = _current_search_end()
    query = _search_query(stars_min_exclusive, SEARCH_START, end)
    records, queries = _search_slice(client, query, SEARCH_START, end, stars_min_exclusive)
    unique: dict[int, dict] = {}
    duplicates = 0
    for record in records:
        if not isinstance(record, dict):
            raise DataError("Resposta inválida ao listar repositórios candidatos.")
        identifier = record.get("id")
        if not isinstance(identifier, int):
            raise DataError("Repositório candidato sem ID numérico.")
        if identifier in unique:
            duplicates += 1
        else:
            unique[identifier] = record
    return list(unique.values()), {
        "query": query,
        "queries": queries,
        "query_count": len(queries),
        "unique_candidates": len(unique),
        "duplicate_ids": duplicates,
    }


def _has_actions(client: GitHubClient, root: str) -> bool:
    try:
        response = client.get(f"{root}/actions/workflows", {"per_page": 1})
    except ApiError as error:
        if error.status == 404:
            return False
        raise
    if (not isinstance(response, dict)
            or not isinstance(response.get("total_count"), int)
            or isinstance(response.get("total_count"), bool)
            or response["total_count"] < 0):
        raise DataError("Resposta inválida ao verificar GitHub Actions.")
    return response["total_count"] > 0


def _contributor_count(client: GitHubClient, root: str) -> int:
    identifiers = set()
    for page in client.pages(f"{root}/contributors", {
        "anon": 1,
        "per_page": SEARCH_PAGE_SIZE,
    }):
        if not isinstance(page, list):
            raise DataError("Resposta inválida ao listar contribuidores.")
        for contributor in page:
            if not isinstance(contributor, dict):
                raise DataError("Resposta inválida ao listar contribuidores.")
            identifier = contributor.get("id")
            if isinstance(identifier, int) and not isinstance(identifier, bool):
                identifiers.add(("user", identifier))
            elif contributor.get("type") == "Anonymous":
                name = contributor.get("name")
                email = contributor.get("email")
                if not isinstance(name, str) or not isinstance(email, str):
                    raise DataError("Contribuidor anônimo sem identidade verificável.")
                identifiers.add(("anonymous", name, email))
            else:
                raise DataError("Contribuidor sem ID numérico.")
    return len(identifiers)


def _metadata(client: GitHubClient, record: dict, root: str, collected_at: datetime) -> dict:
    stars = record.get("stargazers_count")
    full_name = record.get("full_name")
    branch = record.get("default_branch")
    created_value = record.get("created_at")
    language = record.get("language")
    if not isinstance(stars, int) or isinstance(stars, bool) or stars < 0:
        raise ValueError("invalid_stars")
    if not isinstance(full_name, str) or not full_name:
        raise ValueError("missing_full_name")
    if not isinstance(branch, str) or not branch:
        raise ValueError("missing_default_branch")
    if language is not None and not isinstance(language, str):
        raise ValueError("invalid_language")
    try:
        created_at = timestamp(created_value)
    except (ValueError, TypeError, AttributeError):
        raise ValueError("invalid_created_at") from None
    return {
        "id": record["id"],
        "full_name": full_name,
        "stars": stars,
        "primary_language": language,
        "created_at": created_at.isoformat(),
        "age_days_at_collection": (collected_at - created_at).total_seconds() / 86400,
        "default_branch": branch,
        "contributor_count": _contributor_count(client, root),
    }


def _count_releases(client: GitHubClient, root: str, window_start: datetime, window_end: datetime) -> tuple[int, int]:
    count = 0
    invalid_dates = 0
    seen = set()
    for page in client.pages(f"{root}/releases", {"per_page": SEARCH_PAGE_SIZE}):
        if not isinstance(page, list):
            raise DataError("Resposta inválida ao listar releases.")
        for release in page:
            if (not isinstance(release, dict)
                    or not isinstance(release.get("id"), int)
                    or isinstance(release.get("id"), bool)):
                raise DataError("Release sem ID numérico.")
            if release["id"] in seen:
                continue
            seen.add(release["id"])
            if release.get("draft") or release.get("prerelease"):
                continue
            try:
                published_at = timestamp(release.get("published_at"))
            except (ValueError, TypeError, AttributeError):
                invalid_dates += 1
                continue
            if window_start <= published_at < window_end:
                count += 1
    return count, invalid_dates


def _count_valid_runs(
    client: GitHubClient, root: str, branch: str, window_start: datetime,
    window_end: datetime, valid_conclusions: tuple[str, ...],
) -> tuple[int, int]:
    query = f"{window_start.isoformat()}..{window_end.isoformat()}"
    count = 0
    observed = 0
    seen = set()
    expected_total = None
    for page in client.pages(f"{root}/actions/runs", {
        "branch": branch,
        "event": "push",
        "created": query,
        "per_page": SEARCH_PAGE_SIZE,
    }):
        if (not isinstance(page, dict) or not isinstance(page.get("workflow_runs"), list)):
            raise DataError("Resposta inválida ao listar workflow runs.")
        page_total = page.get("total_count")
        if (not isinstance(page_total, int) or isinstance(page_total, bool)
                or page_total < 0):
            raise DataError("Resposta de workflow runs sem total_count válido.")
        if expected_total is not None and page_total != expected_total:
            raise DataError("Total de workflow runs mudou durante a paginação.")
        expected_total = page_total
        for run in page["workflow_runs"]:
            if (not isinstance(run, dict) or not isinstance(run.get("id"), int)
                    or isinstance(run.get("id"), bool)):
                raise DataError("Workflow run sem ID numérico.")
            if run["id"] in seen:
                continue
            seen.add(run["id"])
            observed += 1
            if run.get("event") != "push" or run.get("head_branch") != branch:
                continue
            try:
                created_at = timestamp(run.get("created_at"))
            except (ValueError, TypeError, AttributeError):
                continue
            if window_start <= created_at < window_end and run.get("conclusion") in valid_conclusions:
                count += 1
    if expected_total is not None and observed < expected_total:
        raise DataError("Paginação de workflow runs incompleta.")
    return count, observed


def select_candidates(
    client: GitHubClient,
    window_start: datetime,
    window_end: datetime,
    *,
    stars_min_exclusive: int,
    sample_size: int,
    minimum_releases: int,
    minimum_valid_runs: int,
    valid_conclusions: tuple[str, ...],
) -> dict:
    """Executa as etapas do funil e retorna apenas candidatos elegíveis."""
    if stars_min_exclusive < 0 or sample_size < 1 or minimum_releases < 0 or minimum_valid_runs < 0:
        raise ValueError("Parâmetros do funil não podem ser negativos e a amostra deve ser positiva.")
    if window_start.utcoffset() is None or window_end.utcoffset() is None or window_start >= window_end:
        raise ValueError("A janela do funil deve ser timezone-aware e crescente.")

    records, search = search_popular_repositories(client, stars_min_exclusive)
    collected_at = datetime.now(timezone.utc)
    invalid_star_records = sum(
        not isinstance(record.get("stargazers_count"), int)
        or record["stargazers_count"] <= stars_min_exclusive
        for record in records
    )
    records = [
        record for record in records
        if isinstance(record.get("stargazers_count"), int)
        and record["stargazers_count"] > stars_min_exclusive
    ]
    records.sort(key=lambda item: (-item["stargazers_count"], item["id"]))
    sample = records[:sample_size]
    funnel = {
        "search": {
            **search,
            "matching_candidates": len(records),
            "sample_size": sample_size,
            "selected": len(sample),
            "excluded": {
                "invalid_or_below_star_threshold": invalid_star_records,
                "outside_initial_sample": len(records) - len(sample),
            },
        },
        "actions": {"input": len(sample), "passed": 0, "excluded": {}},
        "metadata": {"input": 0, "passed": 0, "excluded": {}},
        "releases": {"input": 0, "passed": 0, "excluded": {}},
        "workflow_runs": {"input": 0, "passed": 0, "excluded": {}},
    }
    with_actions = []
    for record in sample:
        try:
            root = repo_path(record.get("full_name", ""))
        except ValueError:
            reason = "invalid_repository_name"
            funnel["actions"]["excluded"][reason] = funnel["actions"]["excluded"].get(reason, 0) + 1
            continue
        if _has_actions(client, root):
            with_actions.append((record, root))
        else:
            funnel["actions"]["excluded"]["no_actions"] = (
                funnel["actions"]["excluded"].get("no_actions", 0) + 1
            )
    funnel["actions"]["passed"] = len(with_actions)

    candidates = []
    funnel["metadata"]["input"] = len(with_actions)
    for record, root in with_actions:
        try:
            candidate = _metadata(client, record, root, collected_at)
        except ValueError as error:
            reason = str(error)
            funnel["metadata"]["excluded"][reason] = funnel["metadata"]["excluded"].get(reason, 0) + 1
            continue
        candidates.append((candidate, root))
    funnel["metadata"]["passed"] = len(candidates)

    measured = []
    funnel["releases"]["input"] = len(candidates)
    funnel["workflow_runs"]["input"] = len(candidates)
    for candidate, root in candidates:
        release_count, invalid_release_dates = _count_releases(
            client, root, window_start, window_end,
        )
        run_count, observed_runs = _count_valid_runs(
            client, root, candidate["default_branch"], window_start, window_end,
            valid_conclusions,
        )
        candidate["release_count"] = release_count
        candidate["invalid_release_dates"] = invalid_release_dates
        candidate["valid_workflow_run_count"] = run_count
        candidate["observed_workflow_run_count"] = observed_runs
        measured.append(candidate)

    release_eligible = []
    run_eligible = []
    for candidate in measured:
        if candidate["release_count"] >= minimum_releases:
            release_eligible.append(candidate)
        else:
            reason = "minimum_releases_not_met"
            funnel["releases"]["excluded"][reason] = funnel["releases"]["excluded"].get(reason, 0) + 1
        if candidate["valid_workflow_run_count"] >= minimum_valid_runs:
            run_eligible.append(candidate)
        else:
            reason = "minimum_valid_workflow_runs_not_met"
            funnel["workflow_runs"]["excluded"][reason] = funnel["workflow_runs"]["excluded"].get(reason, 0) + 1
    funnel["releases"]["passed"] = len(release_eligible)
    funnel["workflow_runs"]["passed"] = len(run_eligible)
    run_ids = {candidate["id"] for candidate in run_eligible}
    eligible = [candidate for candidate in release_eligible if candidate["id"] in run_ids]
    final_exclusions = {}
    for candidate in measured:
        reasons = []
        if candidate["release_count"] < minimum_releases:
            reasons.append("minimum_releases_not_met")
        if candidate["valid_workflow_run_count"] < minimum_valid_runs:
            reasons.append("minimum_valid_workflow_runs_not_met")
        if reasons:
            reason = "+".join(reasons)
            final_exclusions[reason] = final_exclusions.get(reason, 0) + 1
    funnel["final_eligibility"] = {
        "input": len(measured),
        "passed": len(eligible),
        "excluded": final_exclusions,
    }
    return {
        "schema_version": 1,
        "issue": 97,
        "collected_at": collected_at.isoformat(),
        "window": {"start": window_start.isoformat(), "end": window_end.isoformat(), "interval": "[start, end)"},
        "criteria": {
            "stars_min_exclusive": stars_min_exclusive,
            "minimum_releases": minimum_releases,
            "minimum_valid_workflow_runs": minimum_valid_runs,
            "valid_workflow_conclusions": list(valid_conclusions),
            "initial_sample_size": sample_size,
        },
        "funnel": funnel,
        "eligible_repositories": eligible,
    }

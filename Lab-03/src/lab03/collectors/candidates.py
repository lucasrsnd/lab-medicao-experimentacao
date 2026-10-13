"""Seleção da amostra e funil de elegibilidade de repositórios."""

import re
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from typing import Callable
from urllib.parse import urlencode, urljoin
from lab03.domain import Window, timestamp
from lab03.github import API_ROOT, ApiError, DataError, GitHubClient, NetworkError
from lab03.collectors.releases import collect_releases, release_pages, repo_path
from lab03.collectors.workflow_runs import collect_workflow_runs

SEARCH_START = date(2008, 1, 1)
SEARCH_RESULT_LIMIT = 1000
SEARCH_PAGE_SIZE = 100
MAX_STARS = 2_147_483_647


def parallel_map(function, items, workers: int = 1) -> list:
    """`map` que preserva a ordem; com `workers > 1` usa threads (E/S de rede).
    A primeira exceção interrompe e é repropagada."""
    items = list(items)
    if workers <= 1 or len(items) <= 1:
        return [function(item) for item in items]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(function, items))


def parallel_stream(function, items, consume, workers: int = 1) -> None:
    """Como `parallel_map`, mas entrega cada resultado a `consume` na ordem de
    entrada assim que fica pronto e não os acumula: memória limitada a uma janela
    de `2 * workers` resultados em voo, em vez de todos."""
    items = list(items)
    if workers <= 1 or len(items) <= 1:
        for item in items:
            consume(function(item))
        return
    pending: deque = deque()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        iterator = iter(items)
        for item in iterator:
            pending.append(pool.submit(function, item))
            if len(pending) >= workers * 2:
                consume(pending.popleft().result())
        while pending:
            consume(pending.popleft().result())


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
    client: GitHubClient, stars_min_exclusive: int, *, limit: int | None = None,
) -> tuple[list[dict], dict]:
    """Busca repositórios públicos sem aceitar buscas truncadas pelo limite da API."""
    end = _current_search_end()
    query = _search_query(stars_min_exclusive, SEARCH_START, end)
    population_count = _search_count(client, query) if limit is not None else None
    if limit is not None and limit < SEARCH_RESULT_LIMIT and population_count > limit:
        # A busca ordenada pode fornecer um prefixo sem enumerar toda a população.
        # Completar o empate na fronteira preserva a ordenação por estrelas e ID.
        records = []
        pages = 0
        for page in client.pages('/search/repositories', {
            'q': query, 'sort': 'stars', 'order': 'desc', 'per_page': SEARCH_PAGE_SIZE,
        }):
            pages += 1
            if (not isinstance(page, dict) or page.get('incomplete_results') is True
                    or not isinstance(page.get('items'), list)):
                raise DataError('Busca ordenada de candidatos incompleta.')
            records.extend(page['items'])
            if len(records) >= limit:
                break
        if len(records) < limit:
            raise DataError('Busca ordenada retornou menos candidatos que o solicitado.')
        if any(not isinstance(r.get('stargazers_count'), int) for r in records):
            raise DataError('Busca ordenada retornou candidato sem estrelas válidas.')
        records.sort(key=lambda r: (-r['stargazers_count'], r['id']))
        boundary = records[limit - 1]['stargazers_count']
        bounds = (boundary, boundary)
        tie_query = _search_query(stars_min_exclusive, SEARCH_START, end, bounds)
        ties, tie_queries = _search_slice(
            client, tie_query, SEARCH_START, end, stars_min_exclusive, bounds,
        )
        records.extend(ties)
        queries = [{'query': query, 'total_count': population_count, 'pages': pages,
                    'sort': 'stars', 'order': 'desc', 'purpose': 'ranked_prefix'}, *tie_queries]
    else:
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
        "population_count": population_count if population_count is not None else len(unique),
    }


def search_top_repositories(
    client: GitHubClient, stars_min_exclusive: int, limit: int,
) -> tuple[list[dict], dict]:
    """Os `limit` repositórios mais estrelados, sem enumerar a população inteira.

    A seleção do funil já avalia candidatos em ordem decrescente de estrelas;
    aqui a própria busca vem ordenada (`sort=stars`) e desce por faixas de
    estrelas quando o teto de 1.000 resultados por consulta é atingido. Empates
    na fronteira entre faixas são deduplicados por ID.
    """
    population = _search_count(client, f"is:public stars:>{stars_min_exclusive}")
    wanted = min(limit, population)
    unique: dict[int, dict] = {}
    queries = []
    upper = MAX_STARS
    while len(unique) < wanted:
        query = f"is:public stars:{stars_min_exclusive + 1}..{upper}"
        count = _search_count(client, query)
        pages = 0
        lowest = None
        for page in client.pages("/search/repositories", {
            "q": query, "sort": "stars", "order": "desc", "per_page": SEARCH_PAGE_SIZE,
        }):
            pages += 1
            if (not isinstance(page, dict) or not isinstance(page.get("items"), list)
                    or page.get("incomplete_results") is True):
                raise DataError("Resposta inválida ao listar repositórios candidatos.")
            for record in page["items"]:
                identifier = record.get("id") if isinstance(record, dict) else None
                stars = record.get("stargazers_count") if isinstance(record, dict) else None
                if not isinstance(identifier, int) or not isinstance(stars, int):
                    raise DataError("Repositório candidato sem ID ou estrelas numéricos.")
                unique.setdefault(identifier, record)
                lowest = stars if lowest is None else min(lowest, stars)
            if len(unique) >= wanted:
                break
        queries.append({"query": query, "total_count": count, "pages": pages})
        if count <= SEARCH_RESULT_LIMIT or len(unique) >= wanted:
            break
        if lowest is None or lowest >= upper:
            raise DataError(
                f"Mais de {SEARCH_RESULT_LIMIT} repositórios com {upper} estrelas; "
                "não foi possível descer a busca sem omitir candidatos."
            )
        upper = lowest
    # Faixas e páginas chegam em ordem decrescente de estrelas; aparar a última página.
    return list(unique.values())[:wanted], {
        "query": f"is:public stars:>{stars_min_exclusive} sort:stars-desc",
        "queries": queries,
        "query_count": len(queries),
        "unique_candidates": min(len(unique), wanted),
        "duplicate_ids": 0,
        "population_total": population,
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


def _contributor_count_fast(client: GitHubClient, root: str) -> int | None:
    """Uma requisição: com `per_page=1`, o número da última página do cabeçalho
    `Link` é o total de contribuidores (dica do enunciado, seção 4)."""
    url = urljoin(API_ROOT, f"{root}/contributors") + "?" + urlencode({"anon": 1, "per_page": 1})
    try:
        response = client.transport.get(url)
    except ApiError as error:
        if error.status == 403:
            return None
        raise
    last = re.search(r'<[^>]*[?&]page=(\d+)[^>]*>\s*;\s*rel="last"', response.headers.get("link", ""))
    if last:
        return int(last[1])
    if not isinstance(response.data, list):
        raise DataError("Resposta inválida ao contar contribuidores.")
    return len(response.data)


def _contributor_count(client: GitHubClient, root: str, fast: bool = False) -> int | None:
    """Modo rápido (S02): None quando o GitHub se recusa a listar (403: lista grande
    demais, caso do kernel do Linux). Ausência explícita, nunca zero. Fora dele, o
    403 propaga e o funil decide (`contributors_too_large` exclui o repositório)."""
    if fast:
        return _contributor_count_fast(client, root)
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


def _metadata(
    client: GitHubClient, record: dict, root: str, collected_at: datetime, fast: bool = False,
) -> dict:
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
        "contributor_count": _contributor_count(client, root, fast),
    }


def _count_releases(
    client: GitHubClient, root: str, window_start: datetime, window_end: datetime,
    stop_above: int | None = None,
) -> tuple[int, int]:
    count = 0
    invalid_dates = 0
    seen = set()
    for page in release_pages(client, root, window_start):
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
        if stop_above is not None and count > stop_above:
            # Já passou do teto: não paginar o resto (há repositórios com ~30 mil
            # releases automáticas, que estouram o limite de paginação da API).
            return count, invalid_dates
    return count, invalid_dates


def _push_runs_total(
    client: GitHubClient, root: str, branch: str, window_start: datetime, window_end: datetime,
) -> int:
    """`total_count` de runs de push do branch na janela (qualquer conclusão).
    Usa a mesma URL de `_count_valid_runs`, então normalmente vem do cache."""
    page = client.get(f"{root}/actions/runs", {
        "branch": branch,
        "event": "push",
        "created": f"{window_start.isoformat()}..{window_end.isoformat()}",
        "per_page": SEARCH_PAGE_SIZE,
    })
    total = page.get("total_count") if isinstance(page, dict) else None
    if not isinstance(total, int) or isinstance(total, bool) or total < 0:
        raise DataError("Resposta de workflow runs sem total_count válido.")
    return total


def _count_valid_runs(
    client: GitHubClient, root: str, branch: str, window_start: datetime,
    window_end: datetime, valid_conclusions: tuple[str, ...],
    stop_at: int | None = None,
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
            if stop_at is None:
                raise DataError("Total de workflow runs mudou durante a paginação.")
            # Seleção rápida: runs reexecutados/apagados durante a leitura não
            # mudam a elegibilidade (só importa passar do mínimo).
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
        if stop_at is not None and count >= stop_at:
            # Elegibilidade já provada: não paginar o resto (pode ter milhares de runs).
            return count, observed
    if stop_at is None and expected_total is not None and observed < expected_total:
        raise DataError("Paginação de workflow runs incompleta.")
    return count, observed


def _count_collected_runs(client, root, branch, window_start, window_end, valid_conclusions):
    """Contagem exaustiva pelo coletor completo (bissecção do teto da busca)."""
    stats = {}
    runs = collect_workflow_runs(
        client, root.removeprefix("/repos/"), Window(window_start, window_end),
        branch, valid_conclusions, stats=stats,
    )
    return len(runs), stats["observed"]


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
    top_only: bool = False,
    workers: int = 1,
    maximum_runs: int | None = None,
    maximum_releases: int | None = None,
    ranked_search: bool = False,
    notify: Callable[[str], None] | None = None,
    required_repositories: tuple[str, ...] = (),
) -> dict:
    """Executa as etapas do funil e retorna apenas candidatos elegíveis.

    `top_only=True` busca só os `sample_size` mais estrelados (rápido); o padrão
    enumera toda a população antes de ordenar."""
    if stars_min_exclusive < 0 or sample_size < 1 or minimum_releases < 0 or minimum_valid_runs < 0:
        raise ValueError("Parâmetros do funil não podem ser negativos e a amostra deve ser positiva.")
    if window_start.utcoffset() is None or window_end.utcoffset() is None or window_start >= window_end:
        raise ValueError("A janela do funil deve ser timezone-aware e crescente.")

    notify = notify or (lambda message: None)
    notify(f"Buscando os {sample_size} candidatos mais populares...")
    if top_only:
        records, search = search_top_repositories(client, stars_min_exclusive, sample_size)
    else:
        records, search = search_popular_repositories(
            client, stars_min_exclusive, limit=sample_size if ranked_search else None,
        )
    population = search.get("population_total", search.get("population_count", len(records)))
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
    required = []
    required_ids = set()
    for name in required_repositories:
        record = client.get(repo_path(name))
        if (record.get("private") is not False
                or not isinstance(record.get("stargazers_count"), int)
                or record["stargazers_count"] <= stars_min_exclusive):
            raise DataError(f"Repositório obrigatório fora da população: {name}")
        if record["id"] not in required_ids:
            required.append(record)
            required_ids.add(record["id"])
    if len(required) > sample_size:
        raise ValueError("Mais repositórios obrigatórios que vagas na amostra.")
    sample = (required + [r for r in records if r["id"] not in required_ids])[:sample_size]
    funnel = {
        "search": {
            **search,
            "matching_candidates": population,
            "sample_size": sample_size,
            "selected": len(sample),
            "excluded": {
                "invalid_or_below_star_threshold": invalid_star_records,
                "outside_initial_sample": population - len(sample),
            },
        },
        "actions": {"input": len(sample), "passed": 0, "excluded": {}},
        "metadata": {"input": 0, "passed": 0, "excluded": {}},
        "releases": {"input": 0, "passed": 0, "excluded": {}},
        "workflow_runs": {"input": 0, "passed": 0, "excluded": {}},
    }
    if required:
        funnel["search"]["required_repositories"] = [r["full_name"] for r in required]
        funnel["search"]["selection_policy"] = "required_then_stars_desc_id_asc"

    def check_actions(record):
        notify(f"Actions: {record.get('full_name')}")
        try:
            root = repo_path(record.get("full_name", ""))
        except ValueError:
            return record, None, "invalid_repository_name"
        if _has_actions(client, root):
            return record, root, None
        return record, root, "no_actions"

    with_actions = []
    for record, root, reason in parallel_map(check_actions, sample, workers):
        if reason is None:
            with_actions.append((record, root))
        else:
            funnel["actions"]["excluded"][reason] = funnel["actions"]["excluded"].get(reason, 0) + 1
    funnel["actions"]["passed"] = len(with_actions)

    def fetch_metadata(item):
        record, root = item
        notify(f"Metadados: {record.get('full_name')}")
        try:
            return _metadata(client, record, root, collected_at, top_only), root, None
        except ApiError as error:
            if error.reason != "contributors_too_large":
                raise
            return None, root, "contributors_unavailable_api_limit"
        except DataError:
            raise  # Falha de paginação não é ausência de metadados.
        except ValueError as error:
            return None, root, str(error)

    candidates = []
    funnel["metadata"]["input"] = len(with_actions)
    for candidate, root, reason in parallel_map(fetch_metadata, with_actions, workers):
        if reason is not None:
            funnel["metadata"]["excluded"][reason] = funnel["metadata"]["excluded"].get(reason, 0) + 1
            continue
        candidates.append((candidate, root))
    funnel["metadata"]["passed"] = len(candidates)

    funnel["releases"]["input"] = len(candidates)
    funnel["workflow_runs"]["input"] = len(candidates)

    def measure(item):
        candidate, root = item
        notify(f"Elegibilidade: {candidate['full_name']}")
        if top_only:
            # Seleção em lote: um repositório que o GitHub não consegue servir
            # (5xx persistente após as retentativas, ex.: releases gigantes) é
            # excluído com motivo, em vez de derrubar a coleta inteira.
            try:
                return _measure_fast(candidate, root)
            except (ApiError, NetworkError) as error:
                status = getattr(error, "status", None)
                reason = f"api_error_{status}" if status else "network_error"
                if isinstance(error, ApiError) and status < 500:
                    raise
                return {"id": candidate["id"], "full_name": candidate["full_name"], "measure_error": reason}
        return _measure_full(candidate, root)

    def _measure_fast(candidate, root):
        release_count, invalid_release_dates = _count_releases(
            client, root, window_start, window_end, stop_above=maximum_releases,
        )
        run_count, observed_runs = _count_valid_runs(
            client, root, candidate["default_branch"], window_start, window_end,
            valid_conclusions, stop_at=minimum_valid_runs,
        )
        candidate["valid_workflow_run_count_capped"] = run_count >= minimum_valid_runs
        candidate["release_count"] = release_count
        candidate["invalid_release_dates"] = invalid_release_dates
        candidate["valid_workflow_run_count"] = run_count
        candidate["observed_workflow_run_count"] = observed_runs
        return _with_activity_total(candidate, root)

    def _measure_full(candidate, root):
        catalog = collect_releases(
            client, candidate["full_name"], Window(window_start, window_end),
            collect_tags=False,
        )
        # Usar o branch observado pelo coletor, não o valor possivelmente
        # desatualizado da busca de repositórios.
        candidate["default_branch"] = catalog.default_branch
        candidate["default_head_sha"] = catalog.default_head
        run_count, observed_runs = _count_collected_runs(
            client, root, candidate["default_branch"], window_start, window_end,
            valid_conclusions,
        )
        candidate["release_count"] = len(catalog.releases)
        candidate["invalid_release_dates"] = sum(
            item.reason == "invalid_published_at" for item in catalog.exclusions
        )
        candidate["release_exclusions"] = [
            {"id": item.identifier, "reason": item.reason} for item in catalog.exclusions
        ]
        candidate["valid_workflow_run_count"] = run_count
        candidate["observed_workflow_run_count"] = observed_runs
        notify(f"  {candidate['release_count']} releases; {run_count} runs validos")
        return _with_activity_total(candidate, root)

    def _with_activity_total(candidate, root):
        if maximum_runs is not None:
            candidate["push_runs_total"] = _push_runs_total(
                client, root, candidate["default_branch"], window_start, window_end,
            )
        return candidate

    measured_all = parallel_map(measure, candidates, workers)
    measure_errors: dict[str, int] = {}
    for item in measured_all:
        if "measure_error" in item:
            measure_errors[item["measure_error"]] = measure_errors.get(item["measure_error"], 0) + 1
    funnel["measure_errors"] = measure_errors
    measured = [item for item in measured_all if "measure_error" not in item]

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
    def within_activity_cap(candidate):
        return maximum_runs is None or candidate["push_runs_total"] <= maximum_runs

    def within_release_cap(candidate):
        return maximum_releases is None or candidate["release_count"] <= maximum_releases

    eligible = [
        candidate for candidate in release_eligible
        if candidate["id"] in run_ids and within_activity_cap(candidate)
        and within_release_cap(candidate)
    ]
    final_exclusions = {}
    for candidate in measured:
        reasons = []
        if candidate["release_count"] < minimum_releases:
            reasons.append("minimum_releases_not_met")
        if candidate["valid_workflow_run_count"] < minimum_valid_runs:
            reasons.append("minimum_valid_workflow_runs_not_met")
        if not within_activity_cap(candidate):
            reasons.append("above_activity_cap")
        if not within_release_cap(candidate):
            reasons.append("above_release_cap")
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
            "maximum_push_runs_in_window": maximum_runs,
            "maximum_releases_in_window": maximum_releases,
        },
        "funnel": funnel,
        "eligible_repositories": eligible,
    }

"""Tags do default branch como unidade de entrega (variante C3, RQ07).

Resolver cada tag com `commits/{sha}` e um `compare` de pertencimento custa
duas requisições por tag, e há repositórios com milhares delas. Aqui a data e
o pertencimento saem da listagem de commits do default branch:

1. `GET /tags` (todas as páginas): nome -> SHA do commit apontado;
2. `GET /commits?sha=<head>&since=<início>`: ancestrais do head com data
   recente; uma tag cujo SHA aparece aí está no default branch e recebe
   `commit.author.date` do próprio commit;
3. antecessora: `GET /commits?sha=<head>&until=<início>`, parando no primeiro
   commit marcado por tag (a listagem é cronológica reversa). A busca tem
   limite de páginas; se ele for atingido, não há antecessora presumida.

Várias tags no mesmo commit (ex.: `v1.2.0` e `latest`) formam uma única
entrega: o código entregue é o mesmo. Tags fora do default branch ou com
commit anterior à janela não são distinguidas sem resolução individual e são
contadas juntas em `tags_unmatched`.
"""

from dataclasses import dataclass
from datetime import datetime
from urllib.parse import quote

from lab03.collectors.releases import repo_path
from lab03.domain import Release, ReleaseCatalog, Window, timestamp
from lab03.github import DataError, GitHubClient

PREDECESSOR_MAX_PAGES = 50


@dataclass(frozen=True)
class TaggedCommit:
    sha: str
    names: tuple[str, ...]
    authored_at: datetime


@dataclass(frozen=True)
class TagHistory:
    """`deliveries` inclui a antecessora fora da janela, se encontrada."""
    deliveries: tuple[TaggedCommit, ...]
    predecessor_status: str
    tags_total: int
    tags_in_window: int
    tagged_commits_in_window: int
    tags_unmatched: int
    invalid_author_dates: int


def _iso(value: datetime) -> str:
    return value.strftime("%Y-%m-%dT%H:%M:%SZ")


def collect_tag_history(
    client: GitHubClient, repository: str, window: Window, head: str,
    *, predecessor_max_pages: int = PREDECESSOR_MAX_PAGES,
) -> TagHistory:
    root = repo_path(repository)
    names_by_sha: dict[str, set[str]] = {}
    seen_names = set()
    for page in client.pages(f"{root}/tags", {"per_page": 100}):
        for raw in page:
            if raw["name"] in seen_names:
                continue
            seen_names.add(raw["name"])
            names_by_sha.setdefault(raw["commit"]["sha"], set()).add(raw["name"])

    found: dict[str, datetime] = {}
    invalid = 0

    def visit(raw: dict) -> datetime | None:
        nonlocal invalid
        sha = raw["sha"]
        if sha not in names_by_sha or sha in found:
            return None
        try:
            authored = timestamp(raw["commit"]["author"]["date"])
        except (KeyError, TypeError, ValueError, AttributeError):
            invalid += 1
            names_by_sha.pop(sha)  # sem data não há data presumida
            return None
        found[sha] = authored
        return authored

    if names_by_sha:
        params = {"sha": head, "since": _iso(window.start), "per_page": 100}
        for page in client.pages(f"{root}/commits", params):
            for raw in page:
                visit(raw)

    predecessor_status = "not_needed"
    in_window = [sha for sha, date in found.items() if window.contains(date)]
    before = [sha for sha, date in found.items() if date < window.start]
    if in_window:
        unmatched = set(names_by_sha) - set(found)
        if before:
            predecessor_status = "found"
        elif not unmatched:
            predecessor_status = "no_earlier_tag"
        else:
            predecessor_status = "search_limit_reached"
            params = {"sha": head, "until": _iso(window.start), "per_page": 100}
            pages = 0
            for page in client.pages(f"{root}/commits", params):
                pages += 1
                for raw in page:
                    authored = visit(raw)
                    if authored is not None and authored < window.start:
                        before.append(raw["sha"])
                if before:
                    predecessor_status = "found"
                    break
                if pages >= predecessor_max_pages:
                    break
            else:
                if not before:
                    predecessor_status = "no_earlier_tag"
            in_window = [sha for sha, date in found.items() if window.contains(date)]

    chosen = list(in_window)
    if before:
        chosen.append(max(before, key=lambda sha: (found[sha], sha)))
    deliveries = sorted(
        (TaggedCommit(sha, tuple(sorted(names_by_sha[sha])), found[sha]) for sha in chosen),
        key=lambda item: (item.authored_at, item.names),
    )
    return TagHistory(
        deliveries=tuple(deliveries),
        predecessor_status=predecessor_status,
        tags_total=len(seen_names),
        tags_in_window=sum(len(names_by_sha[sha]) for sha in in_window),
        tagged_commits_in_window=len(in_window),
        tags_unmatched=sum(
            len(names) for sha, names in names_by_sha.items() if sha not in found
        ),
        invalid_author_dates=invalid,
    )


def tag_catalog(
    repository: str, history: TagHistory, window: Window, default_branch: str, head: str,
) -> ReleaseCatalog:
    """Representa cada commit marcado como uma "release" para reutilizar o
    `collect_changes` e o cálculo de lead time sem duplicar regras."""
    releases = tuple(
        Release(
            id=index, tag=item.names[0], sha=item.sha, published_at=item.authored_at,
            prerelease=False, notes="",
            url=f"https://github.com/{repository}/tree/{quote(item.names[0], safe='')}",
        )
        for index, item in enumerate(history.deliveries)
    )
    if len({release.sha for release in releases}) != len(releases):
        raise DataError("Commit marcado repetido no histórico de tags.")
    return ReleaseCatalog(
        default_branch, head, releases,
        tuple(r for r in releases if window.contains(r.published_at)), (), (), (),
    )

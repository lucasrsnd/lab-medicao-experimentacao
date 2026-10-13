"""#98: releases/tags com histórico e vínculo verificável ao default branch."""

import re
from urllib.parse import quote

from lab03.domain import Exclusion, Release, ReleaseCatalog, Tag, Window, timestamp
from lab03.github import ApiError, GitHubClient
from lab03.normalization import normalize_release


def repo_path(repository: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ValueError("Repositório deve ter formato owner/repo.")
    return f"/repos/{repository}"


def release_pages(client: GitHubClient, root: str, window_start):
    """Páginas de releases, da mais nova para a mais antiga (ordem da API).

    Para ao fim da primeira página em que todas as releases publicadas são
    anteriores ao início da janela: ela já contém a antecessora imediata e o
    resto do histórico nunca entra em métrica. Repositórios com milhares de
    releases (nightlies) deixam de custar dezenas de requisições.
    """
    for page in client.pages(f"{root}/releases", {"per_page": 100}):
        yield page
        dated = []
        for raw in page if isinstance(page, list) else ():
            if isinstance(raw, dict) and not raw.get("draft"):
                try:
                    dated.append(timestamp(raw.get("published_at")))
                except (ValueError, TypeError, AttributeError):
                    pass
        if dated and all(published < window_start for published in dated):
            return


def collect_releases(
    client: GitHubClient, repository: str, window: Window, *, collect_tags: bool = True,
) -> ReleaseCatalog:
    """`collect_tags=False` pula a variante de tags (C3, RQ07): resolver cada tag
    custa duas requisições e o repositório pode ter milhares."""
    root = repo_path(repository)
    branch = client.get(root)["default_branch"]
    head = client.get(f"{root}/commits/{quote(branch, safe='')}")["sha"]
    exclusions: list[Exclusion] = []
    # Cache restrito à chamada; persistência/retomada pertence ao Transport (#96).
    commit_refs: dict[str, dict] = {}
    membership: dict[str, bool] = {}

    def resolve(ref: str) -> dict:
        if ref not in commit_refs:
            commit_refs[ref] = client.get(f"{root}/commits/{quote(ref, safe='')}")
        return commit_refs[ref]

    def on_default_branch(sha: str) -> bool:
        if sha not in membership:
            comparison = client.get(
                f"{root}/compare/{quote(sha, safe='')}...{quote(head, safe='')}",
                {"per_page": 1},
            )
            membership[sha] = comparison["status"] in ("ahead", "identical")
        return membership[sha]

    raw_releases = []
    seen = set()
    for page in release_pages(client, root, window.start):
        for raw in page:
            identifier = str(raw["id"])
            if raw["id"] in seen:
                continue
            seen.add(raw["id"])
            if raw["draft"]:
                exclusions.append(Exclusion("release", identifier, "draft"))
                continue
            try:
                published = timestamp(raw["published_at"])
            except (ValueError, TypeError, AttributeError):
                exclusions.append(Exclusion("release", identifier, "invalid_published_at"))
                continue
            if published >= window.end:
                continue
            raw_releases.append((published, raw))
    raw_releases.sort(key=lambda item: (item[0], item[1]["id"]))
    # Só resolvemos SHA/ramo das releases da janela e da antecessora imediata de
    # cada cadeia (só publicadas; publicadas + pré-releases). Releases mais
    # antigas nunca entram em compare nem em métrica.
    needed = {
        raw["id"] for published, raw in raw_releases if window.contains(published)
    }
    before = [(p, raw) for p, raw in raw_releases if p < window.start]
    if before:
        needed.add(before[-1][1]["id"])
        stable = [raw for _, raw in before if not raw["prerelease"]]
        if stable:
            needed.add(stable[-1]["id"])
    history = []
    for published, raw in raw_releases:
        if raw["id"] not in needed:
            continue
        identifier = str(raw["id"])
        try:
            sha = resolve(raw["tag_name"])["sha"]
            if not on_default_branch(sha):
                exclusions.append(Exclusion("release", identifier, "outside_default_branch"))
                continue
        except ApiError as error:
            if error.status != 404:
                raise
            exclusions.append(Exclusion("release", identifier, "unresolved_ref_404"))
            # Preservar posição temporal: não saltar uma antecessora apagada.
            sha = None
        history.append(normalize_release(raw, sha, published))
    history.sort(key=lambda release: (release.published_at, release.id))
    # Não confiar na ordem da API nem em target_commitish (pode estar desatualizado).
    tags = []
    seen_tags = set()
    for page in (client.pages(f"{root}/tags", {"per_page": 100}) if collect_tags else ()):
        for raw in page:
            if raw["name"] in seen_tags:
                continue
            seen_tags.add(raw["name"])
            try:
                commit = resolve(raw["commit"]["sha"])
                authored = timestamp(commit["commit"]["author"]["date"])
                if window.contains(authored):
                    if on_default_branch(commit["sha"]):
                        tags.append(Tag(raw["name"], commit["sha"], authored))
                    else:
                        exclusions.append(Exclusion("tag", raw["name"], "outside_default_branch"))
            except ApiError as error:
                if error.status != 404:
                    raise
                exclusions.append(Exclusion("tag", raw["name"], "unresolved_ref_404"))
            except (ValueError, TypeError, AttributeError):
                exclusions.append(Exclusion("tag", raw["name"], "invalid_author_date"))
    tags.sort(key=lambda tag: (tag.authored_at, tag.name))
    return ReleaseCatalog(
        branch, head, tuple(history),
        tuple(r for r in history if r.sha and not r.prerelease and window.contains(r.published_at)),
        tuple(r for r in history if r.sha and r.prerelease and window.contains(r.published_at)),
        tuple(tags), tuple(exclusions),
    )

"""#99: comparação paginada, preservando exclusões e antecessora fora da janela."""

from urllib.parse import quote

from lab03.domain import Commit, ReleaseCatalog, ReleaseChanges, Window, timestamp
from lab03.github import ApiError, DataError, GitHubClient
from lab03.collectors.releases import repo_path


def collect_changes(
    client: GitHubClient, repository: str, catalog: ReleaseCatalog,
    window: Window, *, include_prereleases: bool = False,
) -> tuple[ReleaseChanges, ...]:
    root = repo_path(repository)
    history = sorted(
        (r for r in catalog.history if include_prereleases or not r.prerelease),
        key=lambda r: (r.published_at, r.id),
    )
    result = []
    previous = None
    for release in history:
        if not window.contains(release.published_at):
            previous = release
            continue
        if release.sha is None:
            result.append(ReleaseChanges(release, previous, exclusion="unresolved_release_ref"))
        elif previous is None:
            result.append(ReleaseChanges(release, None, exclusion="no_previous_release"))
        elif previous.sha is None:
            result.append(ReleaseChanges(release, previous, exclusion="unresolved_previous_ref"))
        else:
            path = f"{root}/compare/{quote(previous.sha, safe='')}...{quote(release.sha, safe='')}"
            commits: dict[str, Commit] = {}
            expected = None
            reason = None
            try:
                for page in client.pages(path, {"per_page": 100}):
                    if page["status"] not in ("ahead", "identical"):
                        reason = "non_linear_history"
                        break
                    if expected is None:
                        expected = page["total_commits"]
                    elif expected != page["total_commits"]:
                        raise DataError("Comparação mudou durante a paginação.")
                    for raw in page["commits"]:
                        try:
                            authored = timestamp(raw["commit"]["author"]["date"])
                        except (ValueError, TypeError, AttributeError):
                            authored = None
                        commits[raw["sha"]] = Commit(
                            raw["sha"], authored, raw["commit"]["message"],
                        )
            except ApiError as error:
                if error.status != 404:
                    raise
                reason = "compare_not_found"
            if reason is None and expected != len(commits):
                raise DataError(f"Compare incompleto: esperado={expected}, obtido={len(commits)}.")
            # Nunca aproveitar silenciosamente só as primeiras páginas.
            result.append(ReleaseChanges(
                release, previous, tuple(commits.values()) if reason is None else (), reason,
            ))
        previous = release
    return tuple(result)

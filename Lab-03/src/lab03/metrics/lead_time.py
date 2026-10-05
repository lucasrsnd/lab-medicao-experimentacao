"""#100: lead time por release e por commit, em horas, segundo RQ02."""

from collections import Counter
from dataclasses import dataclass
from statistics import median
from typing import Iterable

from lab03.domain import ReleaseChanges


@dataclass(frozen=True)
class LeadTimeResult:
    by_release_hours: float | None
    by_commit_hours: float | None
    releases_total: int
    releases_used: int
    commits_used: int
    exclusions: dict[str, int]


def calculate_lead_time(changes: Iterable[ReleaseChanges]) -> LeadTimeResult:
    release_values = []
    commit_values = []
    exclusions: Counter[str] = Counter()
    total = 0
    for change in changes:
        total += 1
        reason = change.exclusion
        if reason is None and change.previous is None:
            reason = "no_previous_release"
        if reason is None and not change.commits:
            reason = "no_new_commits"
        published = change.release.published_at
        if reason is None and (
            published.utcoffset() is None or any(
                commit.authored_at is None or commit.authored_at.utcoffset() is None
                for commit in change.commits
            )
        ):
            reason = "invalid_timestamp"
        if reason is not None:
            exclusions[reason] += 1
            continue
        hours = [
            (published - commit.authored_at).total_seconds() / 3600
            for commit in change.commits
        ]
        if any(value < 0 for value in hours):
            # Excluir toda a release evita comparar variantes sobre commits diferentes.
            exclusions["negative_lead_time"] += 1
            continue
        release_values.append(max(hours))
        commit_values.extend(hours)
    return LeadTimeResult(
        float(median(release_values)) if release_values else None,
        float(median(commit_values)) if commit_values else None,
        total, len(release_values), len(commit_values), dict(exclusions),
    )


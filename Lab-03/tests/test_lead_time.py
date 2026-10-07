from dataclasses import replace
from datetime import datetime
import pytest

from lab03.domain import Commit, Release, ReleaseChanges, timestamp
from lab03.metrics import calculate_lead_time


def release(id=1, date="2025-03-15T00:00:00Z"):
    return Release(id, f"v{id}", f"sha{id}", timestamp(date), False, "", "")


def change(days=(2, 10, 14)):
    commits = tuple(
        Commit(str(day), timestamp(f"2025-03-{day:02d}T00:00:00Z"), "fix: fixture")
        for day in days
    )
    return ReleaseChanges(release(), release(0, "2025-02-20T00:00:00Z"), commits)


def test_exemplo_enunciado():
    result = calculate_lead_time([change()])
    assert result.by_release_hours == 13 * 24
    assert result.by_commit_hours == 5 * 24
    assert result.commits_used == 3
    assert result.releases_used == 1
    assert result.exclusions == {}


def test_mediana_global_por_commit_nao_mediana_das_medianas():
    second = ReleaseChanges(
        release(2, "2025-03-20T00:00:00Z"), release(),
        (Commit("new", timestamp("2025-03-18T00:00:00Z"), "feature"),),
    )
    result = calculate_lead_time([change(), second])
    assert result.by_release_hours == 180
    assert result.by_commit_hours == 84
    assert result.releases_total == 2
    assert result.commits_used == 4


@pytest.mark.parametrize(("item", "reason"), [
    (ReleaseChanges(release(), None), "no_previous_release"),
    (change(()), "no_new_commits"),
    (replace(change(), exclusion="compare_not_found"), "compare_not_found"),
    (replace(change(), commits=(Commit("x", None, ""),)), "invalid_timestamp"),
    (change((2, 16)), "negative_lead_time"),
])
def test_exclusoes_auditaveis_sem_zero_falso(item, reason):
    result = calculate_lead_time([item])
    assert result.by_release_hours is None
    assert result.by_commit_hours is None
    assert result.releases_used == result.commits_used == 0
    assert result.exclusions == {reason: 1}


def test_contratos_rejeitam_timestamp_sem_timezone():
    with pytest.raises(ValueError, match="UTC"):
        Commit("x", datetime(2025, 3, 1), "")
    with pytest.raises(ValueError, match="UTC"):
        Release(1, "v1", "sha", datetime(2025, 3, 15), False, "", "")


def test_entrada_vazia():
    result = calculate_lead_time([])
    assert result.releases_total == 0
    assert result.by_release_hours is result.by_commit_hours is None


def test_zero_real_e_valido():
    result = calculate_lead_time([change((15,))])
    assert result.by_release_hours == result.by_commit_hours == 0
    assert result.releases_used == 1


def test_offsets_equivalentes_e_horas_fracionarias():
    item = replace(change(), commits=(Commit("x", timestamp("2025-03-14T20:30:00-03:00"), ""),))
    assert calculate_lead_time([item]).by_commit_hours == 0.5


def test_exclusao_nao_contamina_release_valida():
    result = calculate_lead_time([change(), change(())])
    assert result.releases_total == 2
    assert result.releases_used == 1
    assert result.by_release_hours == 312
    assert result.exclusions == {"no_new_commits": 1}

from copy import deepcopy

import pytest

from lab03.github import DataError, GitHubClient
from lab03.replacements import reconcile, complete
from lab03.configuration import PipelineConfig
from lab03.domain import Window, timestamp
from test_ineligible_collection import RejectedReleaseTransport, collect
from test_pilot import PilotTransport


def inputs():
    part = {
        "window": {}, "criteria": {}, "pilot_sample": {"slice": [2, 4]},
        "repositories": [{"metadata": {"full_name": "r/keep"}}],
        "collection_validation": {"excluded": [{"repository": "r/reject"}]},
    }
    selection = {"window": {}, "criteria": {}, "eligible_repositories": [
        {"full_name": n} for n in ("r/previous1", "r/previous2", "r/reject", "r/keep")
    ]}
    return part, selection


def test_revision_preserves_other_slice_and_original_file_data():
    part, selection = inputs()
    original = deepcopy(selection)
    revised, records = reconcile(part, selection, [{"metadata": {"full_name": "r/new"}}])
    assert selection == original
    assert revised["eligible_repositories"][:2] == original["eligible_repositories"][:2]
    assert [x["metadata"]["full_name"] for x in records] == ["r/new", "r/keep"]
    assert revised["collection_revision"]["replacements"] == [
        {"index": 2, "previous": "r/reject", "replacement": "r/new"},
    ]


@pytest.mark.parametrize("name", ["r/previous1", "R/PREVIOUS2", "r/keep", "r/reject"])
def test_replacement_cannot_duplicate_either_original_slice(name):
    part, selection = inputs()
    with pytest.raises(ValueError, match="seleção original"):
        reconcile(part, selection, [{"metadata": {"full_name": name}}])


def test_missing_repository_must_have_an_exclusion():
    part, selection = inputs()
    part["collection_validation"]["excluded"] = []
    with pytest.raises(ValueError, match="posições"):
        reconcile(part, selection, [])


def test_replacement_is_fully_collected_and_cap_checked(monkeypatch):
    part = collect(RejectedReleaseTransport(2), continue_on_ineligible=True)
    part["pilot_sample"]["slice"] = [0, 2]
    source = PilotTransport(3)
    selection = {k: part[k] for k in ("window", "criteria", "eligible_repositories", "collected_at", "funnel")}
    record = {**source.repositories[2], "private": False}
    monkeypatch.setattr("lab03.replacements.candidates", lambda *args: iter([record]))
    monkeypatch.setattr("lab03.replacements._push_runs_total", lambda *args: 50)
    cfg = PipelineConfig("study", None, Window(timestamp("2025-03-01T00:00:00Z"),
                         timestamp("2026-03-01T00:00:00Z")), None, True,
                         maximum_push_runs_in_window=1000, maximum_releases_in_window=500)
    revised, records, attempts = complete(GitHubClient(source), part, selection, cfg, notify=lambda _: None)
    assert len(records) == 2
    assert records[0]["metadata"]["full_name"] == record["full_name"]
    assert len(records[0]["report"]["catalog"]["releases"]) == 5
    assert attempts[-1]["result"] == "accepted"
    monkeypatch.setattr("lab03.replacements._push_runs_total", lambda *args: 1001)
    with pytest.raises(DataError, match="Reposição incompleta"):
        complete(GitHubClient(source), part, selection, cfg, notify=lambda _: None)

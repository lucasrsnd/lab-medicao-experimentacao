import pytest

from lab03.domain import Window, timestamp
from lab03.github import DataError, GitHubClient, Response
from lab03.merge import merge_parts
from lab03.pilot import RepositoryIneligible, run_pilot
from test_pilot import PilotTransport


class RejectedReleaseTransport(PilotTransport):
    def get(self, url):
        assert "/search/" not in url, "Não refazer seleção fornecida"
        if "/project-001/compare/" in url and "...head" in url:
            return Response({"status": "diverged"}, {})
        return super().get(url)


def collect(transport, **kwargs):
    window = Window(timestamp("2025-03-01T00:00:00Z"), timestamp("2026-03-01T00:00:00Z"))
    selection = {
        "window": {"start": window.start.isoformat(), "end": window.end.isoformat()},
        "collected_at": "2026-03-02T00:00:00Z", "criteria": {}, "funnel": {},
        "eligible_repositories": transport.repositories,
    }
    return run_pilot(
        GitHubClient(transport), window=window, target_size=2,
        stars_min_exclusive=1000, minimum_releases=5, minimum_valid_runs=50,
        valid_conclusions=("success", "failure", "timed_out", "startup_failure"),
        collect_tags=False, selection=selection, **kwargs,
    )


@pytest.mark.parametrize("workers", [1, 2])
def test_skip_records_rejection_and_collects_next_repository(workers):
    result = collect(RejectedReleaseTransport(2), continue_on_ineligible=True, workers=workers)
    assert [r["metadata"]["full_name"] for r in result["repositories"]] == ["pilot/project-002"]
    assert result["collection_validation"] == {
        "status": "partial", "requested": 2, "accepted": 1,
        "excluded": [{"repository": "pilot/project-001", "reason": "minimum_default_branch_releases_not_met",
                      "observed": 0, "minimum": 5}],
    }
    with pytest.raises(ValueError, match="reposi"):
        merge_parts([result])


def test_default_still_stops_on_ineligible():
    with pytest.raises(RepositoryIneligible):
        collect(RejectedReleaseTransport(2))


def test_stream_only_receives_accepted_results():
    streamed = []
    result = collect(RejectedReleaseTransport(2), continue_on_ineligible=True, on_result=streamed.append)
    assert len(streamed) == 1
    assert result["collection_validation"]["accepted"] == 1


def test_partial_mode_does_not_hide_pagination_failure():
    class Broken(PilotTransport):
        def get(self, url):
            if "/releases" in url:
                raise DataError("paginação incompleta")
            return super().get(url)
    with pytest.raises(DataError, match="paginação"):
        collect(Broken(2), continue_on_ineligible=True)


def test_workflow_minimum_is_also_audited():
    transport = PilotTransport(2)
    transport.runs = transport.runs[:1]
    result = collect(transport, continue_on_ineligible=True)
    assert not result["repositories"]
    assert len(result["collection_validation"]["excluded"]) == 2
    assert all(x["reason"] == "minimum_valid_workflow_runs_not_met"
               for x in result["collection_validation"]["excluded"])

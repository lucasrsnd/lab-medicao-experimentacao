import json
from dataclasses import fields
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from lab03.domain import Commit, Release, Repository, WorkflowRun, timestamp
from lab03.normalization import (
    normalize_commit,
    normalize_release,
    normalize_repository,
    normalize_workflow_run,
)


FIXTURE = Path(__file__).parent / "fixtures" / "contracts.json"


def test_shared_contract_fixture_covers_repository_release_commit_and_run():
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert set(fixture) == {"repository", "release", "commit", "workflow_run"}
    assert {"id", "full_name", "default_branch", "created_at"} <= {
        field.name for field in fields(Repository)
    }
    assert {"id", "published_at"} <= {field.name for field in fields(Release)}
    assert {"sha", "authored_at"} <= {field.name for field in fields(Commit)}
    assert {"id", "workflow_id", "created_at", "run_started_at", "updated_at"} <= {
        field.name for field in fields(WorkflowRun)
    }
    for item in fixture.values():
        for name, value in item.items():
            if name.endswith("_at") and value is not None:
                assert timestamp(value).utcoffset() == timedelta(0)


def test_normalizers_criam_contratos_com_ids_e_timestamps_utc():
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    repo_data = fixture["repository"]
    repository = normalize_repository({
        "id": repo_data["id"],
        "full_name": repo_data["full_name"],
        "default_branch": repo_data["default_branch"],
        "stargazers_count": repo_data["stars"],
        "language": repo_data["primary_language"],
        "created_at": repo_data["created_at"],
    }, repo_data["default_head_sha"])
    release_data = fixture["release"]
    release = normalize_release({
        "id": release_data["id"],
        "tag_name": release_data["tag"],
        "prerelease": release_data["prerelease"],
        "body": release_data["notes"],
        "html_url": release_data["url"],
    }, release_data["sha"], timestamp(release_data["published_at"]))
    commit_data = fixture["commit"]
    commit = normalize_commit({
        "sha": commit_data["sha"],
        "commit": {
            "author": {"date": commit_data["authored_at"]},
            "message": commit_data["message"],
        },
    })
    run_data = fixture["workflow_run"]
    workflow_run = normalize_workflow_run({
        "id": run_data["id"],
        "workflow_id": run_data["workflow_id"],
        "name": run_data["workflow_name"],
        "head_branch": run_data["branch"],
        "event": run_data["event"],
        "status": run_data["status"],
        "conclusion": run_data["conclusion"],
        "head_sha": run_data["head_sha"],
        "created_at": run_data["created_at"],
        "run_started_at": run_data["run_started_at"],
        "updated_at": run_data["updated_at"],
    })
    assert repository.id == repo_data["id"]
    assert release.id == release_data["id"]
    assert commit.sha == commit_data["sha"]
    assert workflow_run.id == run_data["id"]
    assert all(
        value.utcoffset() == timedelta(0)
        for value in (
            repository.created_at,
            release.published_at,
            commit.authored_at,
            workflow_run.created_at,
            workflow_run.run_started_at,
            workflow_run.updated_at,
        )
    )


@pytest.mark.parametrize("contract", [Repository, Release, Commit, WorkflowRun])
def test_contracts_rejeitam_timestamp_nao_utc(contract):
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    values = fixture[{
        Repository: "repository",
        Release: "release",
        Commit: "commit",
        WorkflowRun: "workflow_run",
    }[contract]]
    parsed = dict(values)
    datetime_fields = {
        Repository: ("created_at",),
        Release: ("published_at",),
        Commit: ("authored_at",),
        WorkflowRun: ("created_at", "run_started_at", "updated_at"),
    }[contract]
    for name in datetime_fields:
        parsed[name] = timestamp(parsed[name])
    target = datetime_fields[0]
    parsed[target] = parsed[target].astimezone(timezone(timedelta(hours=-3)))
    with pytest.raises(ValueError, match="UTC"):
        contract(**parsed)

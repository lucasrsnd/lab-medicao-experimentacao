"""Conversão explícita de payloads REST para contratos do domínio."""

from datetime import datetime
from typing import Any

from lab03.domain import Commit, Release, Repository, WorkflowRun, timestamp
from lab03.github import DataError


def _optional_timestamp(value: str | None, field: str) -> datetime | None:
    if value is None:
        return None
    try:
        return timestamp(value)
    except (AttributeError, TypeError, ValueError) as error:
        raise DataError(f"Timestamp inválido em {field}.") from error


def normalize_repository(raw: dict[str, Any], default_head_sha: str) -> Repository:
    try:
        return Repository(
            id=raw["id"],
            full_name=raw["full_name"],
            default_branch=raw["default_branch"],
            default_head_sha=default_head_sha,
            stars=raw["stargazers_count"],
            primary_language=raw["language"],
            created_at=_optional_timestamp(raw.get("created_at"), "repository.created_at"),
        )
    except (AttributeError, KeyError, TypeError, ValueError) as error:
        if isinstance(error, DataError):
            raise
        raise DataError("Metadados do repositório inválidos.") from error


def normalize_release(raw: dict[str, Any], sha: str | None, published_at: datetime) -> Release:
    try:
        return Release(
            id=raw["id"],
            tag=raw["tag_name"],
            sha=sha,
            published_at=published_at,
            prerelease=raw["prerelease"],
            notes=raw.get("body") or "",
            url=raw["html_url"],
        )
    except (AttributeError, KeyError, TypeError, ValueError) as error:
        raise DataError("Payload de release inválido.") from error


def normalize_commit(raw: dict[str, Any]) -> Commit:
    try:
        details = raw["commit"]
        author = details.get("author") or {}
        try:
            authored_at = _optional_timestamp(author.get("date"), "commit.author.date")
        except DataError:
            authored_at = None
        return Commit(
            sha=raw["sha"],
            authored_at=authored_at,
            message=details["message"],
        )
    except (AttributeError, KeyError, TypeError, ValueError) as error:
        if isinstance(error, DataError):
            raise
        raise DataError("Payload de commit inválido.") from error


def normalize_workflow_run(raw: dict[str, Any]) -> WorkflowRun:
    try:
        return WorkflowRun(
            id=raw["id"],
            workflow_id=raw["workflow_id"],
            workflow_name=raw["name"],
            branch=raw["head_branch"],
            event=raw["event"],
            status=raw["status"],
            conclusion=raw["conclusion"],
            head_sha=raw["head_sha"],
            created_at=timestamp(raw["created_at"]),
            run_started_at=_optional_timestamp(raw.get("run_started_at"), "run.run_started_at"),
            updated_at=_optional_timestamp(raw.get("updated_at"), "run.updated_at"),
        )
    except (KeyError, TypeError, ValueError) as error:
        if isinstance(error, DataError):
            raise
        raise DataError("Payload de workflow run inválido.") from error

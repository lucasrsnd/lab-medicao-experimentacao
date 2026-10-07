"""Contratos compartilhados, independentes de HTTP e de persistência."""

from dataclasses import dataclass
from datetime import datetime, timezone


def _require_utc(value: datetime | None, field: str, *, optional: bool = False) -> None:
    if value is None and optional:
        return
    if value is None or value.utcoffset() != timezone.utc.utcoffset(value):
        raise ValueError(f"{field} deve estar normalizado para UTC.")


def timestamp(value: str) -> datetime:
    """Exige timezone explícito e normaliza timestamps ISO 8601 para UTC."""
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.utcoffset() is None:
        raise ValueError("Timestamp deve incluir timezone.")
    return result.astimezone(timezone.utc)


@dataclass(frozen=True)
class Repository:
    id: int
    full_name: str
    default_branch: str
    default_head_sha: str
    stars: int
    primary_language: str | None
    created_at: datetime | None

    def __post_init__(self):
        _require_utc(self.created_at, "created_at", optional=True)


@dataclass(frozen=True)
class Window:
    """Intervalo [start, end): end é exclusivo, inclusive nas variantes."""
    start: datetime
    end: datetime

    def __post_init__(self):
        if self.start.utcoffset() is None or self.end.utcoffset() is None:
            raise ValueError("Janela deve incluir timezone.")
        if self.start >= self.end:
            raise ValueError("Início deve preceder o fim da janela.")

    def contains(self, value: datetime) -> bool:
        return self.start <= value < self.end


@dataclass(frozen=True)
class Release:
    id: int
    tag: str
    sha: str | None
    published_at: datetime
    prerelease: bool
    notes: str
    url: str

    def __post_init__(self):
        _require_utc(self.published_at, "published_at")


@dataclass(frozen=True)
class Tag:
    name: str
    sha: str
    authored_at: datetime

    def __post_init__(self):
        _require_utc(self.authored_at, "authored_at")


@dataclass(frozen=True)
class Commit:
    sha: str
    authored_at: datetime | None
    message: str

    def __post_init__(self):
        _require_utc(self.authored_at, "authored_at", optional=True)


@dataclass(frozen=True)
class WorkflowRun:
    id: int
    workflow_id: int
    workflow_name: str
    branch: str
    event: str
    status: str
    conclusion: str | None
    head_sha: str
    created_at: datetime
    run_started_at: datetime | None
    updated_at: datetime | None

    def __post_init__(self):
        _require_utc(self.created_at, "created_at")
        _require_utc(self.run_started_at, "run_started_at", optional=True)
        _require_utc(self.updated_at, "updated_at", optional=True)


@dataclass(frozen=True)
class ReleaseChanges:
    release: Release
    previous: Release | None
    commits: tuple[Commit, ...] = ()
    exclusion: str | None = None


@dataclass(frozen=True)
class Exclusion:
    entity: str
    identifier: str
    reason: str


@dataclass(frozen=True)
class ReleaseCatalog:
    """history inclui antecessores; releases/prereleases/tags contêm só a janela."""
    default_branch: str
    default_head: str
    history: tuple[Release, ...]
    releases: tuple[Release, ...]
    prereleases: tuple[Release, ...]
    tags: tuple[Tag, ...]
    exclusions: tuple[Exclusion, ...]

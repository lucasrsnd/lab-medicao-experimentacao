"""Contratos compartilhados, independentes de HTTP e de persistência."""

from dataclasses import dataclass
from datetime import datetime, timezone


def timestamp(value: str) -> datetime:
    """Exige timezone explícito e normaliza timestamps ISO 8601 para UTC."""
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.utcoffset() is None:
        raise ValueError("Timestamp deve incluir timezone.")
    return result.astimezone(timezone.utc)


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


@dataclass(frozen=True)
class Tag:
    name: str
    sha: str
    authored_at: datetime


@dataclass(frozen=True)
class Commit:
    sha: str
    authored_at: datetime | None
    message: str


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

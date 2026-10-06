import json
from pathlib import Path
import pytest

from lab03.domain import Window, timestamp
from lab03.github import GitHubClient, SnapshotTransport

BASE = "https://api.github.com/repos/demo/project"


@pytest.fixture
def snapshot():
    path = Path(__file__).parents[1] / "examples" / "demo-api.json"
    return json.loads(path.read_text(encoding="utf-8"))["responses"]


@pytest.fixture
def client(snapshot):
    return GitHubClient(SnapshotTransport(snapshot))


@pytest.fixture
def window():
    return Window(timestamp("2025-03-01T00:00:00Z"), timestamp("2026-03-01T00:00:00Z"))


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def deny(*args, **kwargs):
        pytest.fail("Teste tentou acessar a rede.")
    monkeypatch.setattr("lab03.github.urlopen", deny)


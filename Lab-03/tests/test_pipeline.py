import json
from pathlib import Path
import pytest

from lab03.cli import main
from lab03.domain import Window, timestamp
from lab03.pipeline import run

DEMO = Path(__file__).parents[1] / "examples" / "demo-api.json"


def arguments(output):
    return ["--repo", "demo/project", "--start", "2025-03-01T00:00:00Z",
            "--end", "2026-03-01T00:00:00Z", "--output", str(output)]


def test_pipeline_deterministico_nos_resultados(client, window):
    result = run(client, "demo/project", window)
    assert result["lead_time"]["by_release_hours"] == 180
    assert result["lead_time"]["by_commit_hours"] == 84
    assert result["catalog"]["default_branch"] == "main"
    assert len(result["changes"]) == 2


def test_cli_offline_sem_token(tmp_path, monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    output = tmp_path / "nested" / "result.json"
    assert main(arguments(output) + ["--snapshot", str(DEMO)]) == 0
    result = json.loads(output.read_text(encoding="utf-8"))
    assert result["source"] == "snapshot"
    assert result["lead_time"]["by_commit_hours"] == 84
    assert result["changes"][0]["release"]["notes"].startswith("Release sintética")
    assert not output.with_suffix(".json.tmp").exists()


def test_cli_sem_token_falha_antes_de_rede(tmp_path, monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    with pytest.raises(SystemExit) as error:
        main(arguments(tmp_path / "out.json"))
    assert error.value.code == 2


def test_snapshot_incompleto_nao_grava_parcial(tmp_path):
    snapshot = tmp_path / "bad.json"
    snapshot.write_text('{"responses": {}}', encoding="utf-8")
    output = tmp_path / "out.json"
    with pytest.raises(SystemExit) as error:
        main(arguments(output) + ["--snapshot", str(snapshot)])
    assert error.value.code == 1
    assert not output.exists()


@pytest.mark.parametrize(("start", "end"), [
    ("2025-01-01T00:00:00Z", "2025-01-01T00:00:00Z"),
    ("2026-01-01T00:00:00Z", "2025-01-01T00:00:00Z"),
])
def test_janela_invalida(start, end):
    with pytest.raises(ValueError):
        Window(timestamp(start), timestamp(end))


def test_timestamp_sem_timezone_rejeitado():
    with pytest.raises(ValueError):
        timestamp("2025-01-01T00:00:00")


def test_janela_inicio_inclusivo_fim_exclusivo(window):
    assert window.contains(window.start)
    assert not window.contains(window.end)


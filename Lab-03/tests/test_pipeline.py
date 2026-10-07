import json
from pathlib import Path
import pytest

from lab03.cli import main
from lab03.configuration import load_config
from lab03.domain import Window, timestamp
from lab03.pipeline import run

LAB03 = Path(__file__).parents[1]
DEMO_CONFIG = LAB03 / "config" / "amostra.json"
STUDY_CONFIG = LAB03 / "config" / "estudo.json"


def arguments(output, config=DEMO_CONFIG):
    return ["--config", str(config), "--output", str(output)]


def test_pipeline_deterministico_nos_resultados(client, window):
    result = run(client, "demo/project", window)
    assert result["lead_time"]["by_release_hours"] == 180
    assert result["lead_time"]["by_commit_hours"] == 84
    assert result["catalog"]["default_branch"] == "main"
    assert len(result["changes"]) == 2
    assert result["deployment_frequency"]["releases_in_window"] == 2
    assert result["deployment_frequency"]["window_weeks"] == 365 / 7
    assert result["deployment_frequency"]["releases_per_week"] == 2 / (365 / 7)
    assert result["dora_classification"]["metrics"]["lead_time_hours"]["points"] == 2
    assert result["dora_classification"]["metrics"]["change_failure_rate"]["category"] is None
    assert result["dora_classification"]["overall"]["status"] == "incomplete"


def test_cli_offline_sem_token(tmp_path, monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    output = tmp_path / "nested" / "result.json"
    assert main(arguments(output)) == 0
    result = json.loads(output.read_text(encoding="utf-8"))
    assert result["source"] == "snapshot"
    assert result["lead_time"]["by_commit_hours"] == 84
    assert result["changes"][0]["release"]["notes"].startswith("Release sintética")
    assert not output.with_suffix(".json.tmp").exists()


def test_config_estudo_bloqueia_coleta_e_nao_acessa_rede(tmp_path, monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "token-de-teste")
    blocked = json.loads(STUDY_CONFIG.read_text(encoding="utf-8"))
    blocked["collection_allowed"] = False
    blocked["status"] = "blocked_pending_professor_window"
    blocked_path = tmp_path / "blocked.json"
    blocked_path.write_text(json.dumps(blocked), encoding="utf-8")
    assert main(["--config", str(blocked_path), "--validate-config"]) == 0
    with pytest.raises(SystemExit) as error:
        main(["--config", str(blocked_path), "--repo", "demo/project",
              "--output", str(tmp_path / "out.json")])
    assert error.value.code == 2
    assert not (tmp_path / "out.json").exists()


def test_cli_sem_token_falha_antes_de_rede(tmp_path, monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    config = json.loads(STUDY_CONFIG.read_text(encoding="utf-8"))
    config["status"] = "ready"
    config["collection_allowed"] = True
    config["window"]["start"] = "2025-03-01T00:00:00Z"
    config["window"]["end"] = "2026-03-01T00:00:00Z"
    study_path = tmp_path / "study.json"
    study_path.write_text(json.dumps(config), encoding="utf-8")
    with pytest.raises(SystemExit) as error:
        main(["--config", str(study_path), "--repo", "demo/project",
              "--output", str(tmp_path / "out.json")])
    assert error.value.code == 2


def test_snapshot_incompleto_nao_grava_parcial(tmp_path):
    snapshot = tmp_path / "bad.json"
    snapshot.write_text('{"responses": {}}', encoding="utf-8")
    config = json.loads(DEMO_CONFIG.read_text(encoding="utf-8"))
    config["snapshot"] = str(snapshot)
    config_path = tmp_path / "sample.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    output = tmp_path / "out.json"
    with pytest.raises(SystemExit) as error:
        main(arguments(output, config_path))
    assert error.value.code == 1
    assert not output.exists()


def test_config_amostra_tem_um_repositorio_e_janela_utc():
    config = load_config(DEMO_CONFIG)
    assert config.mode == "sample"
    assert config.repository == "demo/project"
    assert config.window.start.utcoffset().total_seconds() == 0
    assert config.window.end.utcoffset().total_seconds() == 0


def test_config_estudo_rejeita_liberacao_sem_janela_completa(tmp_path):
    config = json.loads(STUDY_CONFIG.read_text(encoding="utf-8"))
    config["status"] = "ready"
    config["collection_allowed"] = True
    config["window"]["start"] = None
    config["window"]["end"] = None
    invalid = tmp_path / "invalid.json"
    invalid.write_text(json.dumps(config), encoding="utf-8")
    with pytest.raises(ValueError, match="janela oficial completa"):
        load_config(invalid)


def test_config_amostra_rejeita_tamanho_acima_do_suportado(tmp_path):
    config = json.loads(DEMO_CONFIG.read_text(encoding="utf-8"))
    config["sample_size"] = 2
    invalid = tmp_path / "sample.json"
    invalid.write_text(json.dumps(config), encoding="utf-8")
    with pytest.raises(ValueError, match="deve conter 1 repositório"):
        load_config(invalid)


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


def _runs(conclusions):
    from datetime import timedelta
    from lab03.domain import WorkflowRun
    base = timestamp("2025-06-01T00:00:00Z")
    return tuple(
        WorkflowRun(
            id=index, workflow_id=1, workflow_name="CI", branch="main", event="push",
            status="completed", conclusion=conclusion, head_sha=f"s{index}",
            created_at=base + timedelta(hours=index),
            run_started_at=base + timedelta(hours=index),
            updated_at=base + timedelta(hours=index, minutes=10),
        )
        for index, conclusion in enumerate(conclusions)
    )


def test_pipeline_com_workflow_runs_calcula_cfr_e_recuperacao(client, window):
    runs = _runs(["success", "failure", "success", "success", "failure"])
    result = run(client, "demo/project", window, runs)
    assert result["ci_failure_rate"]["rate"] == 0.4
    assert result["recovery"]["episodes_total"] == 2
    assert result["recovery"]["censored_episodes"] == 1
    metrics = result["dora_classification"]["metrics"]
    assert metrics["change_failure_rate"]["points"] == 2   # 40% -> Medium
    assert metrics["change_failure_rate"]["category"] == "Medium"
    assert metrics["recovery_time_hours"]["value"] == pytest.approx(1 + 10 / 60)  # 1h10
    assert result["dora_classification"]["overall"]["status"] == "classified"


def test_pipeline_sem_falhas_deixa_recuperacao_incompleta_com_motivo(client, window):
    result = run(client, "demo/project", window, _runs(["success"] * 5))
    metrics = result["dora_classification"]["metrics"]
    assert metrics["change_failure_rate"]["category"] == "Elite"
    assert metrics["recovery_time_hours"]["category"] is None
    assert metrics["recovery_time_hours"]["missing_reason"] == "no_failure_episodes"


def test_pipeline_so_episodios_censurados_tem_motivo_proprio(client, window):
    result = run(client, "demo/project", window, _runs(["success", "failure"]))
    metrics = result["dora_classification"]["metrics"]
    assert metrics["recovery_time_hours"]["missing_reason"] == "all_failure_episodes_censored"


def test_ctrl_c_sai_com_130_e_orienta_retomada(monkeypatch, tmp_path, capsys):
    def interrupted(*args, **kwargs):
        raise KeyboardInterrupt
    monkeypatch.setattr("lab03.cli.run", interrupted)
    with pytest.raises(SystemExit) as exit_info:
        main(arguments(tmp_path / "out.json"))
    assert exit_info.value.code == 130
    assert "retomar" in capsys.readouterr().err
    assert not (tmp_path / "out.json").exists()

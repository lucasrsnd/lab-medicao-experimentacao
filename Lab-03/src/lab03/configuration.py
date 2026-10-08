"""Leitura e validação dos arquivos de configuração do pipeline."""

import json
import re
import calendar
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path

from lab03.domain import Window, timestamp


@dataclass(frozen=True)
class PipelineConfig:
    mode: str
    repository: str | None
    window: Window | None
    snapshot: Path | None
    collection_allowed: bool
    stars_min_exclusive: int = 1000
    initial_sprint_sample: int = 100
    minimum_releases: int = 5
    minimum_valid_workflow_runs: int = 50
    valid_workflow_conclusions: tuple[str, ...] = (
        "success", "failure", "timed_out", "startup_failure",
    )


def _read_window(raw: object) -> Window:
    if not isinstance(raw, dict):
        raise ValueError("A configuração deve definir window como objeto.")
    start = raw.get("start")
    end = raw.get("end")
    if not isinstance(start, str) or not isinstance(end, str):
        raise ValueError("A configuração precisa definir início e fim ISO 8601 com fuso.")
    try:
        return Window(timestamp(start), timestamp(end))
    except (ValueError, TypeError) as error:
        raise ValueError(f"Janela inválida na configuração: {error}") from error


def load_config(path: Path) -> PipelineConfig:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Não foi possível ler a configuração {path}: {error}") from error
    if not isinstance(raw, dict) or raw.get("schema_version") != 1:
        raise ValueError("Configuração inválida: schema_version deve ser 1.")

    mode = raw.get("mode")
    if mode == "sample":
        repository = raw.get("repository")
        if not isinstance(repository, str) or not re.fullmatch(
            r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository,
        ):
            raise ValueError("A amostra precisa definir repository como owner/repo.")
        sample_size = raw.get("sample_size")
        if sample_size != 1:
            raise ValueError("A amostra offline suportada nesta versão deve conter 1 repositório.")
        snapshot_value = raw.get("snapshot")
        if not isinstance(snapshot_value, str) or not snapshot_value:
            raise ValueError("A amostra precisa definir o caminho do snapshot.")
        snapshot = Path(snapshot_value)
        if not snapshot.is_absolute():
            snapshot = path.parent / snapshot
        if not snapshot.is_file():
            raise ValueError(f"Snapshot não encontrado: {snapshot}")
        window = _read_window(raw.get("window"))
        try:
            snapshot_data = json.loads(snapshot.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ValueError(f"Não foi possível ler o snapshot {snapshot}: {error}") from error
        if not isinstance(snapshot_data, dict) or not isinstance(snapshot_data.get("responses"), dict):
            raise ValueError("Snapshot inválido: responses deve ser um objeto JSON.")
        return PipelineConfig("sample", repository, window, snapshot, False)

    if mode != "study":
        raise ValueError("Configuração deve declarar mode como 'study' ou 'sample'.")

    population = raw.get("population")
    if not isinstance(population, dict):
        raise ValueError("Configuração do estudo deve definir population.")
    raw_window = raw.get("window")
    if not isinstance(raw_window, dict):
        raise ValueError("Configuração do estudo deve definir window.")
    if (raw_window.get("duration_months") != 12
            or population.get("minimum_releases_in_window") != 5
            or population.get("minimum_valid_workflow_runs_in_default_branch") != 50):
        raise ValueError("Duração da janela e critérios de elegibilidade incompatíveis com o protocolo.")
    stars_min_exclusive = population.get("stars_min_exclusive")
    initial_sprint_sample = population.get("initial_sprint_sample")
    if (not isinstance(stars_min_exclusive, int) or isinstance(stars_min_exclusive, bool)
            or stars_min_exclusive < 0 or not isinstance(initial_sprint_sample, int)
            or isinstance(initial_sprint_sample, bool) or initial_sprint_sample < 1):
        raise ValueError("Limiar de estrelas e tamanho da amostra inicial são inválidos.")
    runs = raw.get("workflow_runs")
    valid_conclusions = runs.get("valid_conclusions") if isinstance(runs, dict) else None
    if (not isinstance(runs, dict)
            or runs.get("branch") != "default_branch"
            or runs.get("event") != "push"
            or not isinstance(valid_conclusions, list)
            or any(not isinstance(value, str) for value in valid_conclusions)
            or set(valid_conclusions) != {"success", "failure", "timed_out", "startup_failure"}):
        raise ValueError("Critérios de workflow runs incompatíveis com o protocolo.")
    factors = raw.get("rq06_factors")
    if (not isinstance(factors, list) or any(not isinstance(f, str) for f in factors)
            or len(set(factors)) < 3):
        raise ValueError("RQ06 deve declarar pelo menos três fatores.")
    variants = raw.get("rq07_variants")
    if not isinstance(variants, dict) or not {"C1", "C2", "C3"}.issubset(variants):
        raise ValueError("RQ07 deve declarar as variantes C1, C2 e C3.")

    allowed = raw.get("collection_allowed") is True
    if not isinstance(raw.get("collection_allowed"), bool):
        raise ValueError("collection_allowed deve ser booleano.")
    status = raw.get("status")
    if status not in {"ready", "blocked_pending_professor_window"}:
        raise ValueError("Status de configuração do estudo inválido.")
    window = None
    if raw_window.get("start") is not None or raw_window.get("end") is not None:
        window = _read_window(raw_window)
        start = datetime.fromisoformat(raw_window["start"].replace("Z", "+00:00"))
        last_day = calendar.monthrange(start.year + 1, start.month)[1]
        anniversary = start.replace(year=start.year + 1, day=min(start.day, last_day))
        if window.end != anniversary:
            raise ValueError("A janela do estudo deve corresponder a exatamente 12 meses.")
    if allowed and (status != "ready" or window is None):
        raise ValueError("A coleta só pode ser liberada com status ready e janela oficial completa.")
    return PipelineConfig(
        "study", None, window, None, allowed,
        stars_min_exclusive=stars_min_exclusive,
        initial_sprint_sample=initial_sprint_sample,
        minimum_releases=population["minimum_releases_in_window"],
        minimum_valid_workflow_runs=population["minimum_valid_workflow_runs_in_default_branch"],
        valid_workflow_conclusions=tuple(valid_conclusions),
    )

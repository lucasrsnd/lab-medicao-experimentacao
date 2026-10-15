"""A exceção de compatibilidade não pode liberar outras janelas silenciosamente."""
import json
from pathlib import Path

import pytest

from lab03.configuration import load_config
from lab03.domain import timestamp

STUDY = Path(__file__).parents[1] / "config/estudo.json"


def save(tmp_path, config):
    path = tmp_path / "study.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    return path


def test_authorized_window_matches_frozen_selection():
    config = load_config(STUDY)
    selection = json.loads((STUDY.parent / "selecao-amostra.json").read_text(encoding="utf-8"))
    assert config.window.start == timestamp(selection["window"]["start"])
    assert config.window.end == timestamp(selection["window"]["end"])
    assert (config.window.end - config.window.start).days == 366
    assert config.maximum_push_runs_in_window == 1000
    assert config.maximum_releases_in_window == 500


@pytest.mark.parametrize("mutation", ["missing", "unapproved", "text_boolean", "reason", "boundaries", "two_days"])
def test_extra_day_requires_explicit_matching_exception(tmp_path, mutation):
    config = json.loads(STUDY.read_text(encoding="utf-8"))
    window = config["window"]
    exception = window["compatibility_exception"]
    if mutation == "missing":
        del window["compatibility_exception"]
    elif mutation == "unapproved":
        exception["approved"] = False
    elif mutation == "text_boolean":
        exception["approved"] = "true"
    elif mutation == "reason":
        exception["reason"] = " "
    elif mutation == "boundaries":
        window["start"] = "2025-10-05T00:00:00-03:00"
        window["end"] = "2026-10-06T00:00:00-03:00"
    else:
        window["end"] = exception["end"] = "2026-10-08T00:00:00-03:00"
    with pytest.raises(ValueError, match="12 meses"):
        load_config(save(tmp_path, config))


def test_exact_twelve_months_still_needs_no_exception(tmp_path):
    config = json.loads(STUDY.read_text(encoding="utf-8"))
    config["window"].pop("compatibility_exception")
    config["window"]["end"] = "2026-10-06T00:00:00-03:00"
    assert (load_config(save(tmp_path, config)).window.end - timestamp(config["window"]["start"])).days == 365

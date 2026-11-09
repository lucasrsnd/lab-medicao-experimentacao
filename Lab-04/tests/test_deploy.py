"""Garante que o dashboard continua publicável no Streamlit Community Cloud."""

import re
import tomllib

from packaging.requirements import Requirement

from lab04.config import LAB_ROOT, OUTPUTS_DIR, REAL_PARAMS_PATH, SAMPLE_PATH


def runtime_requirements() -> dict[str, Requirement]:
    data = tomllib.loads((LAB_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    return {Requirement(r).name: Requirement(r) for r in data["project"]["dependencies"]}


def pinned_requirements() -> dict[str, str]:
    pins = {}
    for line in (LAB_ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines():
        line = line.split("#")[0].strip()
        if line:
            name, version = re.fullmatch(r"([A-Za-z0-9_.-]+)==([\w.]+)", line).groups()
            pins[name.lower()] = version
    return pins


def test_requirements_pin_every_runtime_dependency_within_pyproject_range():
    runtime, pins = runtime_requirements(), pinned_requirements()
    assert set(pins) == set(runtime)
    for name, requirement in runtime.items():
        assert requirement.specifier.contains(pins[name]), f"{name}=={pins[name]} fora de {requirement}"


def test_cloud_files_are_next_to_entrypoint():
    # O Cloud procura dependências e config.toml primeiro na pasta do arquivo de entrada.
    assert (LAB_ROOT / "streamlit_app.py").exists()
    assert (LAB_ROOT / "requirements.txt").exists()
    assert (LAB_ROOT / ".streamlit" / "config.toml").exists()


def test_artifacts_read_by_dashboard_are_inside_lab04():
    for path in (SAMPLE_PATH, REAL_PARAMS_PATH, OUTPUTS_DIR / "exemplo_simulado.json"):
        assert path.exists() and LAB_ROOT in path.parents


def test_entrypoint_renders_dashboard():
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file(str(LAB_ROOT / "streamlit_app.py"), default_timeout=120).run()
    assert not at.exception
    assert at.header[0].value == "1. Cenário"

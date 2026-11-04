from pathlib import Path

import pytest

from lab04.config import LAB_ROOT
from lab04.dashboard import content
from lab04.simulation.scenarios import get
from lab04.stats_tests import pearson, spearman

APP = LAB_ROOT / "src" / "lab04" / "dashboard" / "app.py"


def test_missing_artifacts_return_none(tmp_path: Path):
    assert content.section_text("inexistente", base=tmp_path) is None
    assert content.real_sample(tmp_path / "x.csv") is None
    assert content.real_params(tmp_path / "x.json") is None
    assert content.example(tmp_path / "x.json") is None


def test_example_sample_reproduces_saved_statistics():
    ex = content.example()
    sample = content.example_sample(ex, get("realista").params)
    x, y = sample["loc"].to_numpy(), sample["defects"].to_numpy()
    assert pearson(x, y).statistic == pytest.approx(ex.results["pearson"].statistic)
    assert spearman(x, y).statistic == pytest.approx(ex.results["spearman"].statistic)


def test_g1_simulated_follows_real_params():
    real = content.real_params()
    simulated = content.g1_simulated(real.params, n=2_000)
    assert list(simulated.columns) == ["loc", "defects"]
    assert len(simulated) == 2_000


@pytest.mark.parametrize("name", ["01-cenario", "02-dados", "03-testes", "03-g2"])
def test_sprint1_texts_exist(name):
    assert content.section_text(name)


def test_app_renders_sprint1_sections():
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file(str(APP), default_timeout=120).run()
    assert not at.exception
    headers = [h.value for h in at.header]
    assert headers[:7] == [
        "1. Cenário", "2. Os dados", "3. Como os testes funcionam", "4. Erro tipo I",
        "5. Poder", "6. Dados reais", "7. Conclusão",
    ]
    assert len(at.get("plotly_chart")) == 3  # G1 + G2 (Pearson e Spearman)
    assert any("projects/2" in m.value for m in at.markdown)

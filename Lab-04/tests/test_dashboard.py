from pathlib import Path

import pytest

from lab04.config import LAB_ROOT
from lab04.dashboard import content
from lab04.simulation.scenarios import get
from lab04.stats_tests import pearson, spearman

APP = LAB_ROOT / "src" / "lab04" / "dashboard" / "app.py"
SECTION_HEADERS = [
    "1. Cenário", "2. Os dados", "3. Como os testes funcionam", "4. Erro tipo I",
    "5. Poder", "6. Dados reais", "7. Conclusão",
]


def test_missing_artifacts_return_none(tmp_path: Path):
    assert content.section_parts("inexistente", base=tmp_path) is None
    assert content.real_sample(tmp_path / "x.csv") is None
    assert content.real_params(tmp_path / "x.json") is None
    assert content.example(tmp_path / "x.json") is None


def test_section_parts_split_by_heading(tmp_path: Path):
    (tmp_path / "s.md").write_text(
        "Intro.\n\n## O que observar\nOlhe aqui.\n\n## Conclusão\nConcluímos.\n## Vazio\n",
        encoding="utf-8",
    )
    assert content.section_parts("s", base=tmp_path) == {
        "": "Intro.", "O que observar": "Olhe aqui.", "Conclusão": "Concluímos.",
    }


@pytest.mark.parametrize("name, required", [
    ("00-resumo", {"Pergunta", "Expectativa", "Até agora"}),
    ("01-cenario", {"Pergunta e hipóteses", "Erros no cenário"}),
    ("02-dados", {"O que observar", "Conclusão"}),
    ("03-testes", {"Como cada teste funciona", "O que observar", "Conclusão"}),
])
def test_sprint1_texts_have_expected_blocks(name, required):
    assert required <= set(content.section_parts(name))


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


@pytest.fixture(scope="module")
def app():
    from streamlit.testing.v1 import AppTest

    return AppTest.from_file(str(APP), default_timeout=120).run()


def test_app_renders_sections_in_order(app):
    assert not app.exception
    assert [h.value for h in app.header] == SECTION_HEADERS
    assert len(app.get("plotly_chart")) == 3  # G1 + G2 (Pearson e Spearman)


def test_app_has_links_summary_and_pattern(app):
    markdown = " ".join(m.value for m in app.markdown)
    assert "O que observar" in markdown and "Conclusão" in markdown
    assert "Expectativa" in markdown  # cartões do resumo
    assert any("projects/2" in getattr(b, "url", "") for b in app.get("link_button"))


def test_sidebar_lists_progress_and_all_questions(app):
    sidebar = " ".join(m.value for m in app.sidebar.markdown)
    assert "✓ [1. Cenário](#cenario)" in sidebar
    assert "⏳ [4. Erro tipo I](#erro-tipo-i)" in sidebar
    assert sidebar.count("](#") >= len(SECTION_HEADERS) + 15


def test_permutation_toggle(app):
    app.toggle[0].set_value(True).run()
    assert not app.exception
    assert len(app.get("plotly_chart")) == 3
    assert any("escalas verticais" in c.value for c in app.caption)

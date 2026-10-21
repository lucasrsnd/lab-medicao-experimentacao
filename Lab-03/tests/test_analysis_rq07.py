import csv
import json

import pytest

from lab03.analysis import rq07


def row(name, c1=None, c2=None, c3=None):
    data = {"repositorio": name}
    for variant, category in (("C1", c1), ("C2", c2), ("C3", c3)):
        data[f"{variant}_categoria"] = category or ""
        data[f"{variant}_status"] = "classified" if category else "incomplete"
    return data


def test_kappa_ponderado_concordancia_perfeita_e_valor_conhecido():
    perfect = [[2, 0, 0, 0], [0, 1, 0, 0], [0, 0, 3, 0], [0, 0, 0, 1]]
    assert rq07.weighted_kappa(perfect) == pytest.approx(1.0)
    # Discordância adjacente simétrica: po_w = 2/3, pe_w = 5/6, kappa = -1.
    swapped = [[0, 1, 0, 0], [1, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
    assert rq07.weighted_kappa(swapped) == pytest.approx(-1.0)


def test_kappa_ponderado_bate_com_scikit_learn():
    metrics = pytest.importorskip("sklearn.metrics")
    first = [0, 0, 1, 1, 2, 3, 3, 2, 1, 0]
    second = [0, 1, 1, 2, 2, 3, 2, 2, 0, 0]
    matrix = [[0] * 4 for _ in range(4)]
    for a, b in zip(first, second):
        matrix[a][b] += 1
    expected = metrics.cohen_kappa_score(first, second, weights="linear")
    assert rq07.weighted_kappa(matrix) == pytest.approx(expected)


def test_kappa_indefinido_sem_variacao_ou_sem_dados():
    only_one_category = [[5, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
    assert rq07.weighted_kappa(only_one_category) is None
    assert rq07.weighted_kappa([[0] * 4 for _ in range(4)]) is None


def test_compara_par_com_mudanca_direcao_e_exclusoes_por_motivo():
    rows = [
        row("a/a", "High", "High", "Elite"),
        row("b/b", "High", "Medium", "High"),
        row("c/c", "Low", "Medium", "Low"),
        row("d/d", "Medium", None, "Medium"),   # sem C2
        row("e/e", None, None, "Low"),          # sem C1 e sem C2
        row("f/f", None, "Low", "Low"),         # sem C1
    ]
    pair = rq07.compare_pair(rows, "C1", "C2")
    assert pair["n_compared"] == 3
    assert pair["n_excluded"] == 3
    assert pair["exclusions"] == {"C1_sem_categoria": 1, "C2_sem_categoria": 1, "ambas_sem_categoria": 1}
    assert pair["changed"] == 2 and pair["moved_up"] == 1 and pair["moved_down"] == 1
    assert pair["changed_pct"] == pytest.approx(200 / 3)
    counts = pair["matrix"]["counts"]
    assert counts[2][2] == 1 and counts[2][1] == 1 and counts[0][1] == 1


def test_status_incompleto_nao_entra_mesmo_com_categoria():
    incomplete = row("a/a", "High", "High")
    incomplete["C2_status"] = "incomplete"
    pair = rq07.compare_pair([incomplete], "C1", "C2")
    assert pair["n_compared"] == 0
    assert pair["changed_pct"] is None
    assert pair["kappa_undefined_reason"] == "sem repositórios comparáveis"


def test_analisa_os_tres_pares_e_exporta(tmp_path):
    source = tmp_path / "rq07_classificacoes.csv"
    rows = [row("a/a", "High", "High", "Elite"), row("b/b", "Low", "Medium", "Low"),
            row("c/c", "Elite", "High", "Elite")]
    with source.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    out = tmp_path / "rq07"
    assert rq07.main(["--classificacoes", str(source), "--output-dir", str(out)]) == 0
    result = json.loads((out / "rq07_resultados.json").read_text(encoding="utf-8"))
    assert [p["pair"] for p in result["pairs"]] == ["C1xC2", "C1xC3", "C2xC3"]
    assert len(result["input_csv_sha256"]) == 64
    assert (out / "rq07_resultados.md").read_text(encoding="utf-8").startswith("# RQ07")
    lines = (out / "rq07_matrizes.csv").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1 + 3 * 16


def test_hash_da_entrada_nao_depende_do_fim_de_linha(tmp_path):
    """Regressão: com autocrlf, o mesmo CSV tem CRLF no Windows e LF no Linux (CI)."""
    text = "repositorio,C1_categoria,C1_status,C2_categoria,C2_status,C3_categoria,C3_status\n" \
           "a/a,High,classified,Low,classified,High,classified\n"
    digests = []
    for name, newline in (("lf", "\n"), ("crlf", "\r\n")):
        source = tmp_path / f"{name}.csv"
        source.write_bytes(text.replace("\n", newline).encode("utf-8"))
        out = tmp_path / name
        assert rq07.main(["--classificacoes", str(source), "--output-dir", str(out)]) == 0
        digests.append(json.loads((out / "rq07_resultados.json").read_text(encoding="utf-8"))["input_csv_sha256"])
    assert digests[0] == digests[1]


def test_coluna_ausente_e_arquivo_inexistente_falham_com_mensagem(tmp_path, capsys):
    broken = tmp_path / "x.csv"
    broken.write_text("repositorio,C1_categoria\na/a,High\n", encoding="utf-8")
    assert rq07.main(["--classificacoes", str(broken), "--output-dir", str(tmp_path / "o")]) == 1
    assert "Colunas ausentes" in capsys.readouterr().err
    assert rq07.main(["--classificacoes", str(tmp_path / "nao.csv")]) == 1

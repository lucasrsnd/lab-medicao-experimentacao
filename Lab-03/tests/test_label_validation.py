import csv
import json

from lab03.label_validation import complete_ids, main, validate


def write(path, fields, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def sheets(tmp_path, *, tipo="biblioteca/framework", entregas="sim", corretiva=("nao", "sim"),
           notes=""):
    (tmp_path / "amostra_ouro_sorteio.json").write_text(json.dumps({"repositories": 2}))
    write(tmp_path / "amostra_ouro_releases.csv", ("repositorio", "tag", "release_id", "publicada_em"), [
        {"repositorio": "a/x", "tag": "v1.0.1", "release_id": "11", "publicada_em": "t"},
        {"repositorio": "a/x", "tag": "v1.1.0", "release_id": "12", "publicada_em": "t"},
    ])
    write(tmp_path / "rotulos_B_repositorios.csv",
          ("repositorio", "url", "tipo_projeto", "releases_sao_entregas", "observacoes"),
          [{"repositorio": "a/x", "url": "u", "tipo_projeto": tipo,
            "releases_sao_entregas": entregas, "observacoes": notes},
           # sem release rotulável: só a dimensão de repositório
           {"repositorio": "b/sem-release", "url": "u", "tipo_projeto": "outro",
            "releases_sao_entregas": "nao", "observacoes": "monorepo de exemplos"}])
    write(tmp_path / "rotulos_B_releases.csv",
          ("repositorio", "tag", "publicada_em", "url_release", "url_comparacao", "e_corretiva", "observacoes"),
          [{"repositorio": "a/x", "tag": tag, "publicada_em": "t", "url_release": "u",
            "url_comparacao": "c", "e_corretiva": value, "observacoes": ""}
           for tag, value in zip(("v1.0.1", "v1.1.0"), corretiva)])


def test_planilha_completa_e_valida(tmp_path):
    sheets(tmp_path)
    report = validate(tmp_path, "B")
    assert report["errors"] == []
    assert (report["repositories_labeled"], report["releases_labeled"]) == (2, 2)


def test_vazios_so_passam_com_allow_blank(tmp_path):
    sheets(tmp_path, tipo="", corretiva=("", "sim"))
    assert len(validate(tmp_path, "B")["errors"]) == 2
    report = validate(tmp_path, "B", allow_blank=True)
    assert report["errors"] == [] and report["releases_labeled"] == 1
    assert report["repositories_labeled"] == 1


def test_vocabulario_e_justificativa_de_caso_ambiguo(tmp_path):
    sheets(tmp_path, entregas="incerto", corretiva=("talvez", "sim"))
    errors = validate(tmp_path, "B")["errors"]
    assert any("exige justificativa" in e for e in errors)
    assert any("'talvez'" in e for e in errors)
    sheets(tmp_path, entregas="incerto", notes="só tags de marco")
    assert validate(tmp_path, "B")["errors"] == []


def test_release_fora_do_sorteio(tmp_path):
    sheets(tmp_path)
    path = tmp_path / "rotulos_B_releases.csv"
    rows = list(csv.DictReader(path.open(encoding="utf-8-sig")))
    rows[1]["tag"] = "v9"
    write(path, list(rows[0]), rows)
    assert any("divergem do sorteio" in e for e in validate(tmp_path, "B")["errors"])


def test_completa_ids_sem_mudar_rotulos(tmp_path):
    sheets(tmp_path)
    assert complete_ids(tmp_path, "B") == 2
    rows = list(csv.DictReader((tmp_path / "rotulos_B_releases.csv").open(encoding="utf-8-sig")))
    assert [(r["release_id"], r["e_corretiva"]) for r in rows] == [("11", "nao"), ("12", "sim")]
    assert list(rows[0])[:3] == ["repositorio", "tag", "release_id"]
    assert complete_ids(tmp_path, "B") == 0
    assert main(["--rater", "B", "--labels", str(tmp_path)]) == 0

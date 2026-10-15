"""Sorteio reproduzível e planilhas cegas da amostra-ouro."""
import csv
import hashlib
import json

import pytest

from lab03.gold_sample import (
    RATERS, draw_gold_sample, draw_repositories, main,
)


def make_dataset(count=70, releases=8):
    repositories = []
    for number in range(count):
        name = f"org/repo-{number:03d}"
        rels = [
            {"id": number * 100 + i, "tag": f"v1.{i}.0", "published_at": f"2025-{i + 1:02d}-10T00:00:00+00:00",
             "url": f"https://github.com/{name}/releases/tag/v1.{i}.0"}
            for i in range(releases)
        ]
        changes = [
            {"release": rel, "previous": rels[i - 1] if i else None,
             "exclusion": None if i else "no_previous_release", "commits": []}
            for i, rel in enumerate(rels)
        ]
        repositories.append({
            "metadata": {"full_name": name},
            "report": {"catalog": {"releases": rels}, "changes": changes,
                       "delivery_failure_rate": {"rate": 0.5}},
        })
    return {"collected_at": "2026-01-01T00:00:00+00:00", "window": {}, "repositories": repositories}


def test_sorteio_e_reproduzivel_e_independente_da_ordem():
    dataset = make_dataset()
    first = draw_gold_sample(dataset, seed=42)
    dataset["repositories"].reverse()
    assert draw_gold_sample(dataset, seed=42) == first
    assert len(first["repositories"]) == 60
    assert len({r["repositorio"] for r in first["repositories"]}) == 60


def test_semente_diferente_muda_o_sorteio():
    names = [f"org/repo-{n:03d}" for n in range(70)]
    assert draw_repositories(names, 60, 42) != draw_repositories(names, 60, 43)


def test_cinco_releases_por_repositorio_com_comparacao_valida():
    sample = draw_gold_sample(make_dataset(), seed=42)
    assert len(sample["releases"]) == 60 * 5
    for row in sample["releases"]:
        assert row["tag"] != "v1.0.0"  # a primeira não tem commits para rotular
        assert "/compare/" in row["url_comparacao"]


def test_amostra_menor_que_o_necessario_falha():
    with pytest.raises(ValueError):
        draw_gold_sample(make_dataset(count=59))


def test_repo_sem_cinco_releases_comparaveis_nao_reduz_silenciosamente_a_amostra():
    with pytest.raises(ValueError, match="5 releases comparáveis"):
        draw_gold_sample(make_dataset(releases=5))


def test_repo_sem_cinco_releases_comparaveis_nao_e_sorteado():
    dataset = make_dataset()
    invalid = dataset["repositories"][0]
    invalid["report"]["changes"] = invalid["report"]["changes"][:5]
    sample = draw_gold_sample(dataset, seed=42)

    assert len(sample["repositories"]) == 60
    assert len(sample["releases"]) == 300
    assert invalid["metadata"]["full_name"] not in {
        row["repositorio"] for row in sample["repositories"]
    }
    assert sample["repository_sampling"] == {
        "eligible_repository_count": 69,
        "excluded_insufficient_comparable_releases": 1,
    }


def test_planilhas_sao_cegas_e_nao_sobrescrevem(tmp_path, capsys):
    dataset_path = tmp_path / "d.json"
    dataset_path.write_text(json.dumps(make_dataset()), encoding="utf-8")
    out = tmp_path / "labels"
    assert main(["--dataset", str(dataset_path), "--out", str(out)]) == 0
    for rater in RATERS:
        for kind in ("repositorios", "releases"):
            text = (out / f"rotulos_{rater}_{kind}.csv").read_text(encoding="utf-8-sig")
            header = text.splitlines()[0]
            assert "heuristica" not in text.lower() and "cfr" not in header.lower()
            assert "rate" not in header
    rows = list(csv.DictReader((out / "rotulos_A_releases.csv").open(encoding="utf-8-sig")))
    assert all(row["e_corretiva"] == "" for row in rows)
    manifest = json.loads((out / "amostra_ouro_sorteio.json").read_text(encoding="utf-8"))
    assert manifest["seed"] == 42
    assert manifest["source_dataset_sha256"] == hashlib.sha256(dataset_path.read_bytes()).hexdigest()
    assert manifest["repository_sampling"] == {
        "eligible_repository_count": 70,
        "excluded_insufficient_comparable_releases": 0,
    }
    # Nova execução não destrói rótulos já preenchidos.
    (out / "rotulos_A_releases.csv").write_text("preenchido", encoding="utf-8")
    assert main(["--dataset", str(dataset_path), "--out", str(out)]) == 1
    assert (out / "rotulos_A_releases.csv").read_text(encoding="utf-8") == "preenchido"

import csv
import json

import pytest

from lab03.manual_validation import RATERS, calculate_agreement, evaluate_heuristic, heuristic_predictions


def _sample_files(tmp_path):
    repositories = [
        {"repositorio": f"org/repo-{number:03d}", "url": f"https://github.com/org/repo-{number:03d}"}
        for number in range(60)
    ]
    releases = [
        {
            "repositorio": repo["repositorio"],
            "tag": f"v1.0.{release_number}",
            "release_id": str(repo_number * 10 + release_number),
            "publicada_em": f"2025-05-0{release_number}T00:00:00+00:00",
            "url_release": "https://github.com/release",
            "url_comparacao": "https://github.com/compare",
        }
        for repo_number, repo in enumerate(repositories)
        for release_number in range(1, 6)
    ]
    manifest = tmp_path / "sample.json"
    manifest.write_text(json.dumps({"repositories": 60, "releases": 300}), encoding="utf-8")
    repositories_path = tmp_path / "sample-repositories.csv"
    releases_path = tmp_path / "sample-releases.csv"
    _write_csv(repositories_path, repositories)
    _write_csv(releases_path, releases)
    return manifest, repositories_path, releases_path, repositories, releases


def _write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _ratings(tmp_path, repositories, releases, *, missing_release_label=False):
    rater_files = {}
    for rater in RATERS:
        repo_rows = []
        for index, row in enumerate(repositories):
            repo_rows.append({
                "repositorio": row["repositorio"],
                "tipo_projeto": "biblioteca/framework" if index % 2 else "ferramenta CLI",
                "releases_sao_entregas": "sim" if index % 2 else "nao",
            })
        release_rows = [
            {
                "repositorio": row["repositorio"],
                "release_id": row["release_id"],
                "e_corretiva": (
                    "" if missing_release_label and rater == "C" and index == 0
                    else "sim" if index % 2 else "nao"
                ),
            }
            for index, row in enumerate(releases)
        ]
        repo_path = tmp_path / f"{rater}-repositories.csv"
        release_path = tmp_path / f"{rater}-releases.csv"
        _write_csv(repo_path, repo_rows)
        _write_csv(release_path, release_rows)
        rater_files[rater] = {"repositories": repo_path, "releases": release_path}
    return rater_files


def test_fleiss_three_dimensions_and_consensus_drafts(tmp_path):
    pytest.importorskip("statsmodels")
    manifest, repo_path, release_path, repositories, releases = _sample_files(tmp_path)
    rater_files = _ratings(tmp_path, repositories, releases)

    result = calculate_agreement(manifest, repo_path, release_path, rater_files)

    dimensions = result["dimensions"]
    assert dimensions["tipo_projeto"]["expected_items"] == 60
    assert dimensions["releases_sao_entregas"]["fleiss_kappa"] == pytest.approx(1)
    assert dimensions["e_corretiva"]["expected_items"] == 300
    assert dimensions["e_corretiva"]["items_with_three_labels"] == 300
    assert dimensions["e_corretiva"]["fleiss_kappa"] == pytest.approx(1)
    assert all(not row["consenso_e_corretiva"] for row in result["release_consensus_draft"])


def test_fleiss_explicitly_reports_incomplete_labels(tmp_path):
    pytest.importorskip("statsmodels")
    manifest, repo_path, release_path, repositories, releases = _sample_files(tmp_path)
    rater_files = _ratings(
        tmp_path, repositories, releases, missing_release_label=True
    )

    result = calculate_agreement(manifest, repo_path, release_path, rater_files)
    dimension = result["dimensions"]["e_corretiva"]

    assert dimension["expected_items"] == 300
    assert dimension["items_with_three_labels"] == 299
    assert dimension["items_missing_at_least_one_label"] == 1
    assert dimension["missing_labels_by_rater"]["C"] == 1


def test_agreement_rejects_bad_sample_size(tmp_path):
    manifest, repo_path, release_path, repositories, releases = _sample_files(tmp_path)
    bad_manifest = tmp_path / "bad.json"
    bad_manifest.write_text(json.dumps({"repositories": 59, "releases": 300}), encoding="utf-8")

    with pytest.raises(ValueError, match="60 repositórios"):
        calculate_agreement(
            bad_manifest,
            repo_path,
            release_path,
            _ratings(tmp_path, repositories, releases),
        )


def test_predictions_are_aligned_to_sample_release_ids():
    dataset = {
        "repositories": [{
            "metadata": {"full_name": "org/repo"},
            "report": {
                "catalog": {"releases": [{"id": 123, "tag": "v1.0.1"}]},
                "delivery_failure_rate": {
                    "heuristic_version": "v2",
                    "verdicts": [{"tag": "v1.0.1", "corrective": True}],
                },
            },
        }]
    }

    version, rows = heuristic_predictions(dataset, [{
        "repositorio": "org/repo",
        "tag": "v1.0.1",
        "release_id": "123",
    }])

    assert version == "v2"
    assert rows == [{
        "repositorio": "org/repo",
        "release_id": "123",
        "e_corretiva_heuristica": "sim",
    }]


def test_evaluation_reports_metrics_confusion_and_f1_threshold():
    pytest.importorskip("sklearn")
    consensus = [
        {"repositorio": "org/repo", "release_id": str(index), "consenso_e_corretiva": label}
        for index, label in enumerate(("sim", "sim", "nao", "nao"), start=1)
    ]
    predictions = [
        {"repositorio": "org/repo", "release_id": str(index), "e_corretiva_heuristica": label}
        for index, label in enumerate(("sim", "nao", "sim", "nao"), start=1)
    ]

    result = evaluate_heuristic(consensus, predictions, heuristic_version="v2")

    assert result["metrics"]["precision"] == pytest.approx(0.5)
    assert result["metrics"]["recall"] == pytest.approx(0.5)
    assert result["metrics"]["f1"] == pytest.approx(0.5)
    assert result["confusion_matrix"]["values"] == [[1, 1], [1, 1]]
    assert result["refinement_required_if_f1_below_0_70"] is True


def test_evaluation_counts_uncertain_and_missing_cases():
    pytest.importorskip("sklearn")
    consensus = [
        {"repositorio": "org/repo", "release_id": "1", "consenso_e_corretiva": "incerto"},
        {"repositorio": "org/repo", "release_id": "2", "consenso_e_corretiva": "sim"},
        {"repositorio": "org/repo", "release_id": "3", "consenso_e_corretiva": "nao"},
    ]
    predictions = [
        {"repositorio": "org/repo", "release_id": "2", "e_corretiva_heuristica": "sim"},
    ]

    result = evaluate_heuristic(consensus, predictions, heuristic_version="v2")

    assert result["evaluated_releases"] == 1
    assert result["excluded_missing_or_uncertain_consensus"] == 1
    assert result["excluded_missing_prediction"] == 1

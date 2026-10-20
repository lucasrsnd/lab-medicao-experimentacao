import gzip
import hashlib
import json

import pytest

from lab03.analysis import c1_reference, rq01_rq02, rq03_rq04


def analysis_row(name, **values):
    row = {
        "repositorio": name,
        "deployment_frequency_per_week": None,
        "lead_time_a_hours": None,
        "lead_time_b_hours": None,
        "cfr_a": None,
        "cfr_b": None,
        "cfr_b_evaluated": None,
        "cfr_b_censored": None,
        "recovery_hours": None,
        "recovery_episodes": None,
        "recovery_episodes_censored": None,
    }
    row.update(values)
    return row


def test_rq01_rq02_reporta_n_ausentes_e_preserva_outliers():
    rows = [
        analysis_row("a/um", deployment_frequency_per_week=0.0,
                     lead_time_a_hours=10.0, lead_time_b_hours=8.0),
        analysis_row("b/dois", deployment_frequency_per_week=2.0,
                     lead_time_a_hours=1000.0, lead_time_b_hours=12.0),
        analysis_row("c/tres"),
    ]

    result = rq01_rq02.analyze(rows)

    frequency, lead_a, lead_b = result["results"]
    assert (frequency["n_valid"], frequency["n_missing"]) == (2, 1)
    assert frequency["median"] == 1.0
    assert lead_a["median"] == 505.0
    assert lead_b["median"] == 10.0
    assert result["lead_time_variant_median_difference_hours"] == 495.0
    assert "nenhum corte ou winsorização aplicado" in result["outliers"]


def test_rq03_rq04_resume_censura_e_pares_cfr():
    rows = [
        analysis_row(
            "a/um",
            cfr_a=0.1,
            cfr_b=0.4,
            cfr_b_evaluated=3.0,
            cfr_b_censored=1.0,
            recovery_hours=2.0,
            recovery_episodes=2.0,
            recovery_episodes_censored=1.0,
        ),
        analysis_row(
            "b/dois",
            cfr_a=0.2,
            cfr_b=0.0,
            cfr_b_evaluated=2.0,
            cfr_b_censored=0.0,
            recovery_hours=None,
            recovery_episodes=0.0,
            recovery_episodes_censored=0.0,
        ),
        analysis_row("c/tres"),
    ]

    result = rq03_rq04.analyze(rows)

    assert result["results"][0]["n_valid"] == 2
    assert result["censoring"]["cfr_b_releases"]["pooled_proportion"] == pytest.approx(1 / 6)
    recovery = result["censoring"]["recovery_episodes"]
    assert recovery["pooled_proportion"] == pytest.approx(1 / 3)
    assert recovery["n_repositories_without_events"] == 1
    assert recovery["n_repositories_missing"] == 1
    assert result["paired_cfr_b_minus_a"]["n"] == 2
    assert "falha" in rq03_rq04.markdown(result)


def test_gold_validation_exige_hash_da_origem_congelada(tmp_path):
    payload = json.dumps({"repositories": []}, separators=(",", ":")).encode()
    source = tmp_path / "dataset.json.gz"
    with gzip.open(source, "wb") as stream:
        stream.write(payload)
    manifest_path = tmp_path / "gold.json"
    manifest_path.write_text(json.dumps({
        "source_dataset_sha256": hashlib.sha256(payload).hexdigest(),
        "repositories": 60,
        "releases": 300,
    }), encoding="utf-8")

    evidence = rq03_rq04.validation_evidence(manifest_path, source)
    assert evidence["status"] == "source_matches"
    assert evidence["heuristic_f1"] is None
    assert evidence["consensus_status"] == "ausente"

    manifest_path.write_text(json.dumps({"source_dataset_sha256": "different"}), encoding="utf-8")
    evidence = rq03_rq04.validation_evidence(manifest_path, source)
    assert evidence["status"] == "not_linked_to_frozen_dataset"
    assert evidence["heuristic_f1"] is None


def test_c1_reusa_classificador_e_exporta_nao_classificaveis():
    rows = [
        {
            "repositorio": "a/complete",
            "deployment_frequency_per_week": 7.0,
            "deployment_frequency_weeks": 52.0,
            "lead_time_a_hours": 24.0,
            "lead_time_a_releases": 5.0,
            "cfr_a": 0.30,
            "cfr_a_runs": 50.0,
            "recovery_hours": 168.0,
            "recovery_episodes": 3.0,
            "categoria_geral_c1": "High",
        },
        {
            "repositorio": "b/incomplete",
            "deployment_frequency_per_week": 0.0,
            "deployment_frequency_weeks": 52.0,
            "lead_time_a_hours": None,
            "lead_time_a_releases": 0.0,
            "cfr_a": 0.0,
            "cfr_a_runs": 2.0,
            "recovery_hours": 0.0,
            "recovery_episodes": 1.0,
            "categoria_geral_c1": None,
        },
    ]

    classified, distribution = c1_reference.classify_rows(rows)

    complete = classified[0]
    assert complete["deployment_frequency_per_week_categoria"] == "Elite"
    assert complete["lead_time_hours_categoria"] == "High"
    assert complete["change_failure_rate_categoria"] == "High"
    assert complete["recovery_time_hours_categoria"] == "Low"
    assert complete["geral_categoria"] == "High"
    incomplete = classified[1]
    assert incomplete["geral_status"] == "incomplete"
    assert incomplete["geral_categoria"] == ""
    assert any(
        row["metrica"] == "overall"
        and row["categoria"] == "Não classificável"
        and row["n"] == 1
        for row in distribution
    )

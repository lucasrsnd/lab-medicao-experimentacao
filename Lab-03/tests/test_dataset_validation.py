from copy import deepcopy

import pytest

from lab03.dataset_validation import validate_exports
from lab03.metrics import classify_dora
from lab03.variants import VARIANTS, csv_rows


def _classification(variant):
    lead_denominator = 5 if variant == "C1" else 10
    cfr_unit = "evaluable_releases" if variant == "C2" else "valid_ci_runs"
    return classify_dora(
        deployment_frequency_per_week=0,
        lead_time_hours=24,
        change_failure_rate=0,
        recovery_time_hours=None,
        numerators={
            "deployment_frequency_per_week": 0,
            "change_failure_rate": 0,
        },
        denominators={
            "deployment_frequency_per_week": 52,
            "lead_time_hours": lead_denominator,
            "change_failure_rate": 20,
            "recovery_time_hours": 0,
        },
        denominator_units={
            "deployment_frequency_per_week": "weeks",
            "lead_time_hours": "releases" if variant == "C1" else "commits",
            "change_failure_rate": cfr_unit,
            "recovery_time_hours": "recovered_episodes",
        },
        missing_reasons={"recovery_time_hours": "all_failure_episodes_censored"},
    )


def _exports():
    metrics_rows = []
    classification_rows = []
    canonical = {}
    gold_sample = []
    for number in range(300):
        name = f"org/repo-{number:03d}"
        variants = {}
        for variant in VARIANTS:
            variants[variant] = {
                "definition": VARIANTS[variant],
                "classification": _classification(variant),
                "pending_validations": [],
                "complement_available": True,
                "recovery_episodes_censored": 1,
                "cfr_b_censored_releases": 2 if variant == "C2" else None,
            }
        canonical[name] = variants
        for row in csv_rows(name, variants):
            metrics_rows.append({
                key: "" if value is None else str(value)
                for key, value in row.items()
            })
        classification = {"repositorio": name}
        for variant in VARIANTS:
            overall = variants[variant]["classification"]["overall"]
            classification[f"{variant}_categoria"] = overall["category"] or ""
            classification[f"{variant}_status"] = overall["status"]
        classification_rows.append(classification)
        if number < 60:
            for release_number in range(5):
                gold_sample.append({
                    "repositorio": name,
                    "tag": f"v1.0.{release_number}",
                    "release_id": str(number * 10 + release_number),
                    "publicada_em": "2026-01-01T00:00:00Z",
                })
    variants_payload = {
        "coverage": {"status": "complete"},
        "datasets": [{"path": "full.json", "sha256": "frozen-source-hash"}],
        "repositories": canonical,
    }
    gold_manifest = {
        "repositories": 60,
        "releases": 300,
        "source_dataset_sha256": "frozen-source-hash",
    }
    return metrics_rows, classification_rows, variants_payload, gold_sample, gold_manifest


def test_valida_csvs_manifesto_amostra_e_censura():
    result = validate_exports(*_exports())

    assert result["status"] == "validated"
    assert result["repository_count"] == 300
    assert result["metric_rows"] == 900
    assert result["classification_rows"] == 300
    assert result["gold_repository_count"] == 60
    assert result["gold_release_count"] == 300
    assert result["cfr_b_censored_releases"] == 600
    assert result["recovery_episodes_censored"] == 300


def test_zero_observado_nao_e_confundido_com_ausencia():
    metrics, classifications, variants, gold, manifest = _exports()
    frequency = next(
        row for row in metrics
        if row["repositorio"] == "org/repo-000"
        and row["variante"] == "C1"
        and float(row["deployment_frequency_per_week_valor"]) == 0
    )
    assert frequency["deployment_frequency_per_week_motivo_ausencia"] == ""
    assert validate_exports(metrics, classifications, variants, gold, manifest)["status"] == "validated"


def test_rejeita_formula_ou_unidade_inconsistente():
    metrics, classifications, variants, gold, manifest = _exports()
    bad = deepcopy(metrics)
    bad[0]["deployment_frequency_per_week_valor"] = "1"

    with pytest.raises(ValueError, match="fórmula"):
        validate_exports(bad, classifications, variants, gold, manifest)


def test_rejeita_celula_vazia_sem_motivo_de_ausencia():
    metrics, classifications, variants, gold, manifest = _exports()
    bad = deepcopy(metrics)
    row = next(
        row for row in bad
        if row["repositorio"] == "org/repo-000" and row["variante"] == "C1"
    )
    row["lead_time_hours_valor"] = ""

    with pytest.raises(ValueError, match="ausência"):
        validate_exports(bad, classifications, variants, gold, manifest)


def test_rejeita_duplicatas_e_hash_de_origem_divergente():
    metrics, classifications, variants, gold, manifest = _exports()
    with pytest.raises(ValueError, match="duplicada"):
        validate_exports(
            metrics[:-1] + [metrics[0]],
            classifications,
            variants,
            gold,
            manifest,
        )

    bad_manifest = dict(manifest, source_dataset_sha256="other-hash")
    with pytest.raises(ValueError, match="hashes de origem"):
        validate_exports(metrics, classifications, variants, gold, bad_manifest)


def test_rejeita_dataset_abaixo_de_trezentos_repositorios():
    metrics, classifications, variants, gold, manifest = _exports()
    names = set(variants["repositories"])
    removed = set(sorted(names)[-1:])
    variants["repositories"] = {
        name: value for name, value in variants["repositories"].items()
        if name not in removed
    }
    metrics = [row for row in metrics if row["repositorio"] not in removed]
    classifications = [
        row for row in classifications if row["repositorio"] not in removed
    ]

    with pytest.raises(ValueError, match="mínimo 300"):
        validate_exports(metrics, classifications, variants, gold, manifest)

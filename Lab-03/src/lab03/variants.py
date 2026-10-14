"""Cálculo e exportação das combinações C1, C2 e C3 da RQ07 (S02-09).

    python -m lab03.variants --dataset data/parte2.json --complement data/parte2-variantes.json --selection data/selecao-amostra-revisada.json --output-dir data/variantes

| Combinação | Unidade de entrega             | Lead time      | CFR                   |
|------------|--------------------------------|----------------|-----------------------|
| C1         | releases publicadas            | (a) por release| (a) CI                |
| C2         | releases + pré-releases        | (b) por commit | (b) release corretiva |
| C3         | commits marcados por tag       | (b) por commit | (a) CI                |

Recuperação vem sempre dos workflow runs. C1 sai inteiramente do dataset;
C2 e C3 dependem do complemento (`lab03.complement`). Sem ele, as métricas
afetadas ficam sem valor, com `missing_reason = variant_complement_not_collected`:
nada é imputado como zero. A classificação geral só existe com as quatro
métricas. O CFR (b) usa a heurística automática e fica marcado como pendente
até haver avaliação na amostra-ouro (`--heuristic-evaluation`).
"""

import argparse
import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from lab03 import __version__
from lab03.metrics import classify_dora

VARIANTS = {
    "C1": {"delivery_unit": "published_releases", "lead_time": "a_per_release", "cfr": "a_ci_runs"},
    "C2": {"delivery_unit": "published_releases_and_prereleases", "lead_time": "b_per_commit",
           "cfr": "b_corrective_release"},
    "C3": {"delivery_unit": "tagged_commits_on_default_branch", "lead_time": "b_per_commit",
           "cfr": "a_ci_runs"},
}
NOT_COLLECTED = "variant_complement_not_collected"
F1_THRESHOLD = 0.70
METRICS = ("deployment_frequency_per_week", "lead_time_hours", "change_failure_rate",
           "recovery_time_hours")


def _ci(report: dict) -> tuple:
    ci = report.get("ci_failure_rate")
    if ci is None:
        return None, None, None, "workflow_runs_not_collected"
    return ci["rate"], ci["failures"], ci["runs_evaluated"], "no_valid_ci_runs"


def _recovery(report: dict) -> tuple:
    recovery = report.get("recovery")
    if recovery is None:
        return None, None, "workflow_runs_not_collected"
    reason = (
        "all_failure_episodes_censored" if recovery["episodes_total"]
        else "invalid_recovery_timestamps" if recovery["exclusions"]
        else "no_failure_episodes"
    )
    return recovery["median_hours"], recovery["episodes_recovered"], reason


def _classify(values: dict, numerators: dict, denominators: dict, units: dict,
              reasons: dict) -> dict:
    return classify_dora(
        deployment_frequency_per_week=values["deployment_frequency_per_week"],
        lead_time_hours=values["lead_time_hours"],
        change_failure_rate=values["change_failure_rate"],
        recovery_time_hours=values["recovery_time_hours"],
        numerators=numerators, denominators=denominators,
        denominator_units=units, missing_reasons=reasons,
    )


def compute_variants(item: dict, complement: dict | None, *, cfr_b_validation: str) -> dict:
    """Retorna {C1, C2, C3}, cada um com a saída de `classify_dora` e metadados."""
    report = item["report"]
    frequency = report["deployment_frequency"]
    weeks = frequency["window_weeks"]
    lead = report["lead_time"]
    ci_rate, ci_failures, ci_runs, ci_reason = _ci(report)
    rec_value, rec_n, rec_reason = _recovery(report)
    result = {}

    def add(name, values, numerators, denominators, units, reasons, extra):
        values = dict(values, recovery_time_hours=rec_value)
        denominators = dict(denominators, recovery_time_hours=rec_n)
        units = dict(units, recovery_time_hours="recovered_episodes")
        reasons = dict(reasons, recovery_time_hours=rec_reason)
        result[name] = {
            "definition": VARIANTS[name],
            "classification": _classify(values, numerators, denominators, units, reasons),
            **extra,
        }

    ci_metric = {"change_failure_rate": ci_rate}
    ci_den = {"change_failure_rate": ci_runs}
    ci_num = {"change_failure_rate": ci_failures}
    ci_reasons = {"change_failure_rate": ci_reason}

    add("C1", {
        "deployment_frequency_per_week": frequency["releases_per_week"],
        "lead_time_hours": lead["by_release_hours"], **ci_metric,
    }, {
        "deployment_frequency_per_week": frequency["releases_in_window"], **ci_num,
    }, {
        "deployment_frequency_per_week": weeks,
        "lead_time_hours": lead["releases_used"], **ci_den,
    }, {
        "deployment_frequency_per_week": "weeks", "lead_time_hours": "releases",
        "change_failure_rate": "valid_ci_runs",
    }, {
        "lead_time_hours": "no_valid_release_observations", **ci_reasons,
    }, {"pending_validations": [], "complement_available": None})

    catalog = report["catalog"]
    c2_count = len(catalog["releases"]) + len(catalog["prereleases"])
    c2 = (complement or {}).get("c2")
    c2_lead = c2["lead_time"] if c2 else None
    c2_cfr = c2["delivery_failure_rate"] if c2 else None
    add("C2", {
        "deployment_frequency_per_week": c2_count / weeks,
        "lead_time_hours": c2_lead["by_commit_hours"] if c2 else None,
        "change_failure_rate": c2_cfr["rate"] if c2 else None,
    }, {
        "deployment_frequency_per_week": c2_count,
        "change_failure_rate": c2_cfr["failed"] if c2 else None,
    }, {
        "deployment_frequency_per_week": weeks,
        "lead_time_hours": c2_lead["commits_used"] if c2 else None,
        "change_failure_rate": c2_cfr["evaluated"] if c2 else None,
    }, {
        "deployment_frequency_per_week": "weeks", "lead_time_hours": "commits",
        "change_failure_rate": "evaluable_releases",
    }, {
        "lead_time_hours": "no_valid_commit_observations" if c2 else NOT_COLLECTED,
        "change_failure_rate": "no_evaluable_releases" if c2 else NOT_COLLECTED,
    }, {
        "pending_validations": (
            [] if cfr_b_validation == "validated" else ["corrective_release_heuristic_gold_sample"]
        ),
        "cfr_b_validation": cfr_b_validation,
        "cfr_b_heuristic_version": c2_cfr["heuristic_version"] if c2 else None,
        "cfr_b_censored_releases": c2_cfr["censored"] if c2 else None,
        "complement_available": c2 is not None,
    })

    c3 = (complement or {}).get("c3")
    c3_freq = c3["deployment_frequency"] if c3 else None
    c3_lead = c3["lead_time"] if c3 else None
    add("C3", {
        "deployment_frequency_per_week": c3_freq["releases_per_week"] if c3 else None,
        "lead_time_hours": c3_lead["by_commit_hours"] if c3 else None, **ci_metric,
    }, {
        "deployment_frequency_per_week": c3_freq["releases_in_window"] if c3 else None, **ci_num,
    }, {
        "deployment_frequency_per_week": weeks if c3 else None,
        "lead_time_hours": c3_lead["commits_used"] if c3 else None, **ci_den,
    }, {
        "deployment_frequency_per_week": "weeks", "lead_time_hours": "commits",
        "change_failure_rate": "valid_ci_runs",
    }, {
        "deployment_frequency_per_week": None if c3 else NOT_COLLECTED,
        "lead_time_hours": "no_valid_commit_observations" if c3 else NOT_COLLECTED,
        **ci_reasons,
    }, {
        "pending_validations": [],
        "tag_predecessor_status": c3["tag_history"]["predecessor_status"] if c3 else None,
        "tags_unmatched": c3["tag_history"]["tags_unmatched"] if c3 else None,
        "complement_available": c3 is not None,
    })
    return result


def heuristic_validation(path: Path | None, versions: set[str]) -> dict:
    """Sem avaliação na amostra-ouro, o CFR (b) é publicado como pendente."""
    if path is None:
        return {"status": "pending", "source": None}
    evaluation = json.loads(path.read_text(encoding="utf-8"))
    version, f1 = evaluation.get("heuristic_version"), evaluation.get("f1")
    if not isinstance(f1, (int, float)) or isinstance(f1, bool):
        raise ValueError("Avaliação da heurística deve informar f1 numérico.")
    if versions and versions != {version}:
        raise ValueError(f"Avaliação da heurística {version} não corresponde às versões usadas {sorted(versions)}.")
    return {
        "status": "validated" if f1 >= F1_THRESHOLD else "below_threshold",
        "source": {"path": str(path), "sha256": _sha256(path)},
        "heuristic_version": version, "f1": f1, "threshold": F1_THRESHOLD,
    }


def _sha256(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


CSV_FIELDS = (
    "repositorio", "variante", "unidade_entrega", "lead_time_variante", "cfr_variante",
    *(f"{metric}_{suffix}" for metric in METRICS
      for suffix in ("valor", "numerador", "denominador", "unidade_denominador", "categoria",
                     "motivo_ausencia")),
    "categoria_geral", "pontos_gerais", "status_geral", "metricas_ausentes",
    "validacoes_pendentes", "complemento_disponivel",
)


def csv_rows(name: str, variants: dict):
    for variant, data in variants.items():
        classification = data["classification"]
        row = {
            "repositorio": name, "variante": variant,
            "unidade_entrega": data["definition"]["delivery_unit"],
            "lead_time_variante": data["definition"]["lead_time"],
            "cfr_variante": data["definition"]["cfr"],
            "categoria_geral": classification["overall"]["category"],
            "pontos_gerais": classification["overall"]["points"],
            "status_geral": classification["overall"]["status"],
            "metricas_ausentes": ";".join(classification["overall"]["missing_metrics"]),
            "validacoes_pendentes": ";".join(data["pending_validations"]),
            "complemento_disponivel": data["complement_available"],
        }
        for metric in METRICS:
            values = classification["metrics"][metric]
            row.update({
                f"{metric}_valor": values["value"],
                f"{metric}_numerador": values["numerator"],
                f"{metric}_denominador": values["denominator"],
                f"{metric}_unidade_denominador": values["denominator_unit"],
                f"{metric}_categoria": values["category"],
                f"{metric}_motivo_ausencia": values["missing_reason"],
            })
        yield row


def _write_csv(path: Path, fields, rows) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            # None vira célula vazia: ausência, nunca zero.
            writer.writerow({key: "" if value is None else value for key, value in row.items()})
    temporary.replace(path)


def export(datasets: list[Path], complements: list[Path], output_dir: Path,
           selection: Path | None = None, evaluation: Path | None = None) -> dict:
    dataset_hashes = {}
    by_name: dict[str, dict] = {}
    window = None
    for path in datasets:
        data = json.loads(path.read_text(encoding="utf-8"))
        if window is not None and data["window"] != window:
            raise ValueError("Datasets com janelas diferentes.")
        window = data["window"]
        dataset_hashes[_sha256(path)] = str(path)
        for item in data["repositories"]:
            name = item["metadata"]["full_name"]
            if name in by_name:
                raise ValueError(f"Repositório repetido entre datasets: {name}")
            by_name[name] = item
        del data
    complement_by_name: dict[str, dict] = {}
    complement_sources = []
    for path in complements:
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("kind") != "rq07_variant_complement":
            raise ValueError(f"{path} não é um complemento de variantes.")
        if data["dataset"]["sha256"] not in dataset_hashes:
            raise ValueError(f"{path} foi gerado a partir de um dataset não informado.")
        if data["window"] != window:
            raise ValueError(f"{path} usa outra janela.")
        complement_sources.append({"path": str(path), "sha256": _sha256(path),
                                   "dataset_sha256": data["dataset"]["sha256"]})
        for entry in data["repositories"]:
            if entry["full_name"] in complement_by_name:
                raise ValueError(f"Repositório repetido entre complementos: {entry['full_name']}")
            complement_by_name[entry["full_name"]] = entry
    versions = {
        entry["c2"]["delivery_failure_rate"]["heuristic_version"]
        for entry in complement_by_name.values()
    }
    validation = heuristic_validation(evaluation, versions)

    results = {
        name: compute_variants(item, complement_by_name.get(name),
                               cfr_b_validation=validation["status"])
        for name, item in by_name.items()
    }
    expected = None
    if selection is not None:
        chosen = json.loads(selection.read_text(encoding="utf-8"))
        if chosen["window"] != window:
            raise ValueError("Seleção com janela diferente dos datasets.")
        expected = [r["full_name"] for r in chosen["eligible_repositories"]]
    missing = [name for name in expected if name not in by_name] if expected else []
    without_complement = sorted(name for name in by_name if name not in complement_by_name)
    summary = {
        variant: {
            "repositories": len(results),
            "overall_classified": sum(
                r[variant]["classification"]["overall"]["status"] == "classified"
                for r in results.values()
            ),
        }
        for variant in VARIANTS
    }
    metadata = {
        "schema_version": 1,
        "kind": "rq07_variants",
        "pipeline_version": __version__,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "window": window,
        "variants": VARIANTS,
        "datasets": [{"path": p, "sha256": h} for h, p in dataset_hashes.items()],
        "complements": complement_sources,
        "coverage": {
            "status": "complete" if expected is not None and not missing and not without_complement
            else "partial",
            "expected_repositories": len(expected) if expected is not None else None,
            "repositories_with_data": len(by_name),
            "repositories_missing_dataset": missing,
            "repositories_without_complement": without_complement,
        },
        "cfr_b_heuristic_validation": validation,
        "policy": {
            "imputation": "none",
            "missing_values_in_csv": "empty_cell",
            "overall_requires_all_four_metrics": True,
        },
        "summary": summary,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(output_dir / "variantes_metricas.csv", CSV_FIELDS,
               (row for name, variants in results.items() for row in csv_rows(name, variants)))
    _write_csv(
        output_dir / "rq07_classificacoes.csv",
        ("repositorio", *(f"{v}_{s}" for v in VARIANTS for s in ("categoria", "status"))),
        ({"repositorio": name, **{
            f"{v}_{s}": variants[v]["classification"]["overall"][key]
            for v in VARIANTS for s, key in (("categoria", "category"), ("status", "status"))
        }} for name, variants in results.items()),
    )
    payload = dict(metadata, repositories=results)
    temporary = output_dir / "variantes.json.tmp"
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    temporary.replace(output_dir / "variantes.json")
    return metadata


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dataset", type=Path, action="append", required=True,
                        help="JSON da coleta --full (repetível: parte1, parte2...)")
    parser.add_argument("--complement", type=Path, action="append", default=[],
                        help="saída de lab03.complement (repetível)")
    parser.add_argument("--selection", type=Path,
                        help="seleção de referência para medir a cobertura (ex.: 300 elegíveis)")
    parser.add_argument("--heuristic-evaluation", type=Path,
                        help="JSON com heuristic_version e f1 da amostra-ouro")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        metadata = export(args.dataset, args.complement, args.output_dir,
                          args.selection, args.heuristic_evaluation)
    except (ValueError, KeyError, OSError) as error:
        print(f"Erro: {error}", file=sys.stderr)
        return 1
    coverage = metadata["coverage"]
    print(f"{coverage['repositories_with_data']} repositórios -> {args.output_dir}")
    for variant, counts in metadata["summary"].items():
        print(f"{variant}: classificação geral em {counts['overall_classified']}/{counts['repositories']}")
    if coverage["status"] != "complete":
        print(
            f"Cobertura parcial: {len(coverage['repositories_missing_dataset'])} sem dataset, "
            f"{len(coverage['repositories_without_complement'])} sem complemento.",
            file=sys.stderr,
        )
    print(f"CFR (b): validação {metadata['cfr_b_heuristic_validation']['status']}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

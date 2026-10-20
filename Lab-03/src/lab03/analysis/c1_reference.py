"""Classificação DORA de referência C1 a partir da base congelada.

    python -m lab03.analysis.c1_reference

Aplica `classify_dora` às quatro métricas C1, exporta categorias por
repositório e distribuições, e verifica a categoria geral armazenada na base.
"""

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

from lab03.analysis.base import read_csv
from lab03.metrics import classify_dora

METRIC_INPUTS = {
    "deployment_frequency_per_week": ("deployment_frequency_per_week",
                                      "deployment_frequency_weeks"),
    "lead_time_hours": ("lead_time_a_hours", "lead_time_a_releases"),
    "change_failure_rate": ("cfr_a", "cfr_a_runs"),
    "recovery_time_hours": ("recovery_hours", "recovery_episodes"),
}
METRIC_LABELS = {
    "deployment_frequency_per_week": "Frequência",
    "lead_time_hours": "Lead time (a)",
    "change_failure_rate": "CFR (a)",
    "recovery_time_hours": "Recuperação",
    "overall": "Geral",
}
CATEGORY_ORDER = ("Elite", "High", "Medium", "Low", "Não classificável")


def classify_rows(rows: list[dict]) -> tuple[list[dict], list[dict]]:
    classified = []
    for row in rows:
        values = {}
        denominators = {}
        for classifier_name, (value_field, denominator_field) in METRIC_INPUTS.items():
            values[classifier_name] = row[value_field]
            denominators[classifier_name] = row[denominator_field]
        result = classify_dora(**values, denominators=denominators)
        output = {"repositorio": row["repositorio"]}
        for metric, detail in result["metrics"].items():
            output[f"{metric}_categoria"] = detail["category"] or ""
            output[f"{metric}_pontos"] = (
                detail["points"] if detail["points"] is not None else ""
            )
            output[f"{metric}_status"] = detail["status"]
            output[f"{metric}_motivo_ausencia"] = detail["missing_reason"] or ""
        overall = result["overall"]
        output["geral_categoria"] = overall["category"] or ""
        output["geral_pontos"] = overall["points"] if overall["points"] is not None else ""
        output["geral_status"] = overall["status"]
        output["metricas_ausentes"] = ";".join(overall["missing_metrics"])
        stored_category = row["categoria_geral_c1"] or None
        if stored_category != overall["category"]:
            raise ValueError(
                f"{row['repositorio']}: classificação geral recalculada "
                f"({overall['category']}) diverge da base ({stored_category})."
            )
        classified.append(output)

    distributions = []
    for metric, label in METRIC_LABELS.items():
        category_field = "geral_categoria" if metric == "overall" else f"{metric}_categoria"
        counts = {category: 0 for category in CATEGORY_ORDER}
        for row in classified:
            category = row[category_field] or "Não classificável"
            counts[category] += 1
        for category, count in counts.items():
            distributions.append({
                "metrica": metric,
                "rotulo": label,
                "categoria": category,
                "n": count,
                "proporcao": count / len(classified) if classified else None,
            })
    return classified, distributions


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def markdown(distributions: list[dict], repositories: int, source_hash: str) -> str:
    lines = [
        "# Classificação DORA de referência C1",
        "",
        f"Base: {repositories} repositórios. SHA-256 do CSV-base: `{source_hash}`.",
        "O classificador de `lab03.metrics.classification` foi aplicado sem alterar "
        "os cortes; a mediana das quatro pontuações é arredondada para baixo. "
        "A categoria geral recalculada foi conferida contra `categoria_geral_c1`.",
        "",
        "| Métrica | Elite | High | Medium | Low | Não classificável |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for metric, label in METRIC_LABELS.items():
        counts = {
            row["categoria"]: row["n"]
            for row in distributions
            if row["metrica"] == metric
        }
        lines.append(
            f"| {label} | " + " | ".join(str(counts[name]) for name in CATEGORY_ORDER) + " |"
        )
    lines += [
        "",
        "## Regras de fronteira",
        "",
        "A implementação reutilizada e os limites verificados por teste são: "
        "frequência ≥7/semana (Elite), ≥1 (High), ≥12/52 (Medium); lead time "
        "<24 h, <168 h, <720 h; CFR ≤15%, ≤30%, ≤45%; recuperação <1 h, "
        "<24 h, <168 h. Cada limite pertence à categoria mais alta indicada; "
        "o valor exatamente no próximo limite cai na faixa seguinte.",
        "",
        "Valores ausentes ou com denominador zero permanecem não classificáveis. "
        "A categoria geral só é emitida quando as quatro métricas têm denominador "
        "positivo e valor observado.",
    ]
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base", type=Path, default=Path("analysis/base_repositorios.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("analysis/c1_reference"))
    args = parser.parse_args(argv)
    try:
        rows = read_csv(args.base)
        source_hash = hashlib.sha256(args.base.read_bytes()).hexdigest()
        classified, distributions = classify_rows(rows)
    except (OSError, KeyError, ValueError) as error:
        print(f"Erro: {error}", file=sys.stderr)
        return 1

    args.output_dir.mkdir(parents=True, exist_ok=True)
    output_fields = list(classified[0]) if classified else ["repositorio"]
    write_csv(args.output_dir / "c1_classificacoes.csv", classified, output_fields)
    distribution_fields = ["metrica", "rotulo", "categoria", "n", "proporcao"]
    write_csv(args.output_dir / "c1_distribuicao.csv", distributions, distribution_fields)
    result = {
        "repositories": len(rows),
        "input_csv_sha256": source_hash,
        "classification_source": "lab03.metrics.classification.classify_dora",
        "overall_requires_all_four_metrics": True,
        "overall_median_rounding": "floor",
        "category_distribution": distributions,
    }
    (args.output_dir / "c1_resultados.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (args.output_dir / "c1_resultados.md").write_text(
        markdown(distributions, len(rows), source_hash), encoding="utf-8"
    )
    print(f"Classificação C1 de {len(rows)} repositórios gravada em {args.output_dir}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""RQ01–02: frequência e lead time (a/b) na base congelada da S03.

    python -m lab03.analysis.rq01_rq02

Reporta mediana, quartis, IQR, n válido e ausentes por repositório.
Outliers são mantidos e exibidos no gráfico.
"""

import argparse
import hashlib
import json
import random
import sys
from pathlib import Path

from lab03.analysis.base import read_csv
from lab03.analysis.stats import fmt, median_iqr

METRICS = {
    "deployment_frequency_per_week": "Frequência (releases/semana)",
    "lead_time_a_hours": "Lead time (a), por release (horas)",
    "lead_time_b_hours": "Lead time (b), por commit (horas)",
}


def analyze(rows: list[dict]) -> dict:
    results = []
    for field, label in METRICS.items():
        values = [row[field] for row in rows if row[field] is not None]
        results.append({
            "metric": field,
            "label": label,
            "n_valid": len(values),
            "n_missing": len(rows) - len(values),
            **median_iqr(values),
        })
    by_metric = {result["metric"]: result for result in results}
    return {
        "repositories": len(rows),
        "outliers": "preservados; nenhum corte ou winsorização aplicado",
        "results": results,
        "lead_time_variant_median_difference_hours": (
            by_metric["lead_time_a_hours"]["median"]
            - by_metric["lead_time_b_hours"]["median"]
            if by_metric["lead_time_a_hours"]["median"] is not None
            and by_metric["lead_time_b_hours"]["median"] is not None
            else None
        ),
    }


def markdown(analysis: dict) -> str:
    lines = [
        "# RQ01–02 — Frequência e lead time",
        "",
        f"Base congelada: {analysis['repositories']} repositórios. "
        "Estatísticas calculadas entre valores por repositório; ausentes não são imputados.",
        "",
        "| Métrica | n válido | ausentes | mediana | Q1 | Q3 | IQR |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for result in analysis["results"]:
        lines.append(
            f"| {result['label']} | {result['n_valid']} | {result['n_missing']} | "
            f"{fmt(result['median'])} | {fmt(result['q1'])} | {fmt(result['q3'])} | "
            f"{fmt(result['iqr'])} |"
        )
    lines += [
        "",
        "## Interpretação",
        "",
        "A frequência é calculada por repositório como releases na janela divididas "
        "pela duração observada em semanas. As variantes de lead time também são "
        "resumidas entre repositórios: (a) primeiro resume releases dentro de cada "
        "repositório; (b) primeiro resume commits dentro de cada repositório. "
        "A variante (a) dá peso a cada release e pode aumentar quando uma release "
        "inclui um commit antigo; a (b) agrega os commits e reduz o peso relativo "
        "desse commit quando há muitos commits recentes.",
        "",
        f"Diferença entre as medianas (a − b): "
        f"{fmt(analysis['lead_time_variant_median_difference_hours'])} horas. "
        "Isso descreve distribuições agregadas por repositório e não significa que "
        "cada repositório tenha a mesma diferença.",
        "",
        f"Outliers: {analysis['outliers']}. O gráfico usa escala symlog para preservar "
        "zeros e caudas longas; todos os pontos são desenhados.",
    ]
    return "\n".join(lines) + "\n"


def plot(rows: list[dict], analysis: dict, path: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    figure, axes = plt.subplots(1, len(analysis["results"]), figsize=(13, 5))
    rng = random.Random(42)
    for axis, result in zip(axes, analysis["results"]):
        values = [row[result["metric"]] for row in rows if row[result["metric"]] is not None]
        if values:
            axis.boxplot(values, positions=[1], widths=0.45, showfliers=True)
            jitter = [rng.uniform(-0.12, 0.12) for _ in values]
            axis.scatter(
                [1 + offset for offset in jitter],
                values,
                s=13,
                alpha=0.55,
                zorder=3,
            )
        axis.set_yscale("symlog", linthresh=0.1)
        axis.set_xticks([1])
        axis.set_xticklabels(["Repositórios"])
        axis.set_title(
            f"{result['label']}\nn={result['n_valid']}; "
            f"mediana={fmt(result['median'])}; IQR={fmt(result['iqr'])}",
            fontsize=9,
        )
        axis.set_ylabel(result["label"])
        axis.grid(axis="y", alpha=0.3)
    figure.suptitle("RQ01–02 — distribuições por repositório (outliers preservados)")
    figure.tight_layout()
    figure.savefig(path, dpi=160)
    plt.close(figure)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base", type=Path, default=Path("analysis/base_repositorios.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("analysis/rq01_rq02"))
    parser.add_argument("--no-plot", action="store_true", help="não gerar a figura")
    args = parser.parse_args(argv)
    try:
        rows = read_csv(args.base)
        source_hash = hashlib.sha256(args.base.read_bytes()).hexdigest()
    except (OSError, KeyError, ValueError) as error:
        print(f"Erro: {error}", file=sys.stderr)
        return 1

    result = analyze(rows)
    result["input_csv_sha256"] = source_hash
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "rq01_rq02_resultados.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (args.output_dir / "rq01_rq02_resultados.md").write_text(
        markdown(result), encoding="utf-8"
    )
    if not args.no_plot:
        plot(rows, result, args.output_dir / "rq01_rq02_distribuicoes.png")
    print(f"{len(rows)} repositórios analisados; resultados em {args.output_dir}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

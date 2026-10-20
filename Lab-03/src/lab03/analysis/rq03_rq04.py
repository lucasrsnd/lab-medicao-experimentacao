"""RQ03–04: CFR (a/b), recuperação e proporções de censura.

    python -m lab03.analysis.rq03_rq04

Os valores são resumos por repositório. O CFR (a) é proxy de falha de CI;
o CFR (b) é proxy de release corretiva, não de falha em produção.
"""

import argparse
import gzip
import hashlib
import json
import sys
from pathlib import Path

from lab03.analysis.base import read_csv
from lab03.analysis.stats import fmt, median_iqr

METRICS = {
    "cfr_a": "CFR (a) — falha de CI",
    "cfr_b": "CFR (b) — release seguida de corretiva",
    "recovery_hours": "Recuperação (horas)",
}


def _censor_summary(rows: list[dict], observed_field: str, censored_field: str) -> dict:
    proportions = []
    observed_total = censored_total = 0
    repositories_with_counts = repositories_with_events = 0
    for row in rows:
        observed = row[observed_field]
        censored = row[censored_field]
        if observed is None or censored is None:
            continue
        repositories_with_counts += 1
        total = observed + censored
        observed_total += int(observed)
        censored_total += int(censored)
        if total:
            repositories_with_events += 1
            proportions.append(censored / total)
    total = observed_total + censored_total
    return {
        "n_repositories_with_counts": repositories_with_counts,
        "n_repositories_with_events": repositories_with_events,
        "n_repositories_without_events": repositories_with_counts - repositories_with_events,
        "n_repositories_missing": len(rows) - repositories_with_counts,
        "observed": observed_total,
        "censored": censored_total,
        "total": total,
        "pooled_proportion": censored_total / total if total else None,
        "repository_proportions": median_iqr(proportions),
    }


def validation_evidence(manifest_path: Path, source_path: Path) -> dict:
    """Check whether the gold sample was drawn from this frozen dataset."""
    if not manifest_path.is_file() or not source_path.is_file():
        return {
            "status": "unavailable",
            "reason": "manifesto da amostra-ouro ou dataset de origem ausente",
        }
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    digest = hashlib.sha256()
    opener = gzip.open if source_path.suffix == ".gz" else open
    with opener(source_path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    source_hash = digest.hexdigest()
    expected_hash = manifest.get("source_dataset_sha256")
    if expected_hash != source_hash:
        return {
            "status": "not_linked_to_frozen_dataset",
            "gold_repositories": manifest.get("repositories"),
            "gold_releases": manifest.get("releases"),
            "gold_source_sha256": expected_hash,
            "frozen_source_sha256": source_hash,
            "reason": "hash de origem da amostra-ouro difere do dataset congelado",
            "heuristic_f1": None,
            "consensus_status": "ausente",
        }
    return {
        "status": "source_matches",
        "gold_repositories": manifest.get("repositories"),
        "gold_releases": manifest.get("releases"),
        "gold_source_sha256": expected_hash,
        "frozen_source_sha256": source_hash,
        "reason": "origem compatível; consenso/F1 ainda deve ser confirmado",
        "heuristic_f1": None,
        "consensus_status": "ausente",
    }


def analyze(rows: list[dict], gold_validation: dict | None = None) -> dict:
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
    paired = [
        row["cfr_b"] - row["cfr_a"]
        for row in rows
        if row["cfr_a"] is not None and row["cfr_b"] is not None
    ]
    return {
        "repositories": len(rows),
        "results": results,
        "censoring": {
            "cfr_b_releases": _censor_summary(
                rows, "cfr_b_evaluated", "cfr_b_censored"
            ),
            "recovery_episodes": _censor_summary(
                rows, "recovery_episodes", "recovery_episodes_censored"
            ),
        },
        "paired_cfr_b_minus_a": {
            "n": len(paired),
            **median_iqr(paired),
        },
        "gold_validation": gold_validation or {
            "status": "unavailable",
            "reason": "evidência da amostra-ouro não fornecida",
            "heuristic_f1": None,
            "consensus_status": "ausente",
        },
    }


def markdown(analysis: dict) -> str:
    lines = [
        "# RQ03–04 — CFR e recuperação",
        "",
        f"Base congelada: {analysis['repositories']} repositórios. "
        "n válido é o número de repositórios com valor observado; "
        "ausentes não são convertidos em zero.",
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
        "## Censura",
        "",
        "| Processo | repositórios com contagens | com eventos | sem eventos | "
        "ausentes | eventos observados | censurados | total | proporção agrupada | "
        "mediana das proporções por repositório | "
        "Q1–Q3 | IQR |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name, summary in (
        ("Releases CFR (b)", analysis["censoring"]["cfr_b_releases"]),
        ("Episódios de recuperação", analysis["censoring"]["recovery_episodes"]),
    ):
        proportions = summary["repository_proportions"]
        lines.append(
            f"| {name} | {summary['n_repositories_with_counts']} | "
            f"{summary['n_repositories_with_events']} | "
            f"{summary['n_repositories_without_events']} | "
            f"{summary['n_repositories_missing']} | {summary['observed']} | "
            f"{summary['censored']} | {summary['total']} | "
            f"{fmt(summary['pooled_proportion'])} | {fmt(proportions['median'])} | "
            f"{fmt(proportions['q1'])}–{fmt(proportions['q3'])} | {fmt(proportions['iqr'])} |"
        )
    validation = analysis["gold_validation"]
    gold_hash = validation.get("gold_source_sha256")
    frozen_hash = validation.get("frozen_source_sha256")
    validation_hashes = (
        f" Hashes SHA-256 (amostra-ouro/fonte congelada): "
        f"`{gold_hash[:12]}` / `{frozen_hash[:12]}`."
        if gold_hash and frozen_hash
        else ""
    )
    lines += [
        "",
        "## Interpretação e validação",
        "",
        "CFR (a) mede a proporção de execuções válidas de CI que falharam; CFR (b) "
        "marca releases predecessoras de uma release corretiva dentro de sete dias. "
        "São proxies operacionais distintos e sua divergência não demonstra falha "
        "nem sucesso em produção. Para CFR (b), a heurística deve ser interpretada "
        "à luz de rótulos humanos do mesmo dataset; a concordância entre avaliadores "
        "sozinha não substitui a avaliação da heurística.",
        "",
        f"Estado da validação vinculada: **{validation['status']}**. "
        f"{validation['reason']}. F1 da heurística: "
        f"{fmt(validation.get('heuristic_f1'))}; consenso: "
        f"{validation.get('consensus_status', 'ausente')}.{validation_hashes}",
        "",
        f"Nos repositórios com ambos os CFR observados (n={analysis['paired_cfr_b_minus_a']['n']}), "
        f"a mediana da diferença CFR (b) − CFR (a) é "
        f"{fmt(analysis['paired_cfr_b_minus_a']['median'])} "
        f"(IQR {fmt(analysis['paired_cfr_b_minus_a']['iqr'])}). A diferença é descritiva, "
        "não uma comparação de falhas em produção.",
        "",
        "Recuperação reporta a mediana entre episódios recuperados por repositório; "
        "episódios censurados permanecem no denominador das proporções e não são "
        "imputados como tempos de recuperação.",
    ]
    return "\n".join(lines) + "\n"


def plot(rows: list[dict], analysis: dict, path: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fields = ("cfr_a", "cfr_b")
    figure, axis = plt.subplots(figsize=(7, 5))
    values_by_metric = [
        [row[field] for row in rows if row[field] is not None]
        for field in fields
    ]
    axis.boxplot(values_by_metric, showfliers=True)
    axis.set_xticks([1, 2])
    axis.set_xticklabels(["CFR (a) — CI", "CFR (b) — corretiva"])
    for index, values in enumerate(values_by_metric, start=1):
        axis.scatter([index] * len(values), values, s=13, alpha=0.45, zorder=3)
    axis.set_ylabel("Proporção por repositório")
    axis.set_title("RQ03 — CFR (a) e CFR (b), proxies distintas")
    axis.set_ylim(-0.03, 1.03)
    axis.grid(axis="y", alpha=0.3)
    figure.tight_layout()
    figure.savefig(path, dpi=160)
    plt.close(figure)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base", type=Path, default=Path("analysis/base_repositorios.csv"))
    parser.add_argument("--gold-manifest", type=Path,
                        default=Path("labels/reamostragem-v2/amostra_ouro_sorteio.json"))
    parser.add_argument("--source-dataset", type=Path,
                        default=Path("data/amostra_completa.json.gz"))
    parser.add_argument("--output-dir", type=Path, default=Path("analysis/rq03_rq04"))
    parser.add_argument("--no-plot", action="store_true", help="não gerar a figura")
    args = parser.parse_args(argv)
    try:
        rows = read_csv(args.base)
        source_hash = hashlib.sha256(args.base.read_bytes()).hexdigest()
        gold = validation_evidence(args.gold_manifest, args.source_dataset)
    except (OSError, KeyError, ValueError, TypeError, json.JSONDecodeError) as error:
        print(f"Erro: {error}", file=sys.stderr)
        return 1

    result = analyze(rows, gold)
    result["input_csv_sha256"] = source_hash
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "rq03_rq04_resultados.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (args.output_dir / "rq03_rq04_resultados.md").write_text(
        markdown(result), encoding="utf-8"
    )
    if not args.no_plot:
        plot(rows, result, args.output_dir / "rq03_cfr_comparacao.png")
    print(f"{len(rows)} repositórios analisados; resultados em {args.output_dir}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

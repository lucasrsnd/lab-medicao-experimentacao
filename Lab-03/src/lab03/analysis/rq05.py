"""RQ05: Spearman entre frequência de deploy e CFR (a) e (b), separadamente (S03-04).

    python -m lab03.analysis.rq05 --base analysis/base_repositorios.csv --output-dir analysis/rq05

Para cada variante de CFR, usa apenas os repositórios com frequência e CFR
observados (n pareado) e reporta ρ, p-valor bilateral e n. Pares com valor
ausente são descartados e contados, nunca imputados. Se uma das variáveis for
constante (ou n < 3), ρ é indefinido e o resultado registra o motivo em vez de
um número. Empates (muitos CFR = 0) são tratados pelos postos médios do
`scipy.stats.spearmanr`. Como são dois testes, o p-valor ajustado por Holm é
reportado junto ao bruto. Associação não implica causalidade.

Saídas: `rq05_resultados.json`, `rq05_resultados.md` e `rq05_dispersao.png`.
"""

import argparse
import json
import sys
from pathlib import Path

from lab03.analysis.base import read_csv
from lab03.analysis.stats import fmt as _fmt, fmt_p as _fmt_p, holm, median_iqr

FREQUENCY = "deployment_frequency_per_week"
CFR_VARIANTS = {
    "cfr_a": "CFR (a) — runs de CI com falha",
    "cfr_b": "CFR (b) — release seguida de corretiva em 7 dias",
}
ALPHA = 0.05
# Frequência tem zeros (sem release na janela) e cauda longa: symlog mantém os
# zeros visíveis e comprime a cauda. O limiar linear é ~1 release a cada 10 semanas.
SYMLOG_THRESHOLD = 0.1


def strength(rho: float) -> str:
    size = abs(rho)
    return ("desprezível" if size < 0.1 else "fraca" if size < 0.3
            else "moderada" if size < 0.5 else "forte")


def spearman(rows: list[dict], x: str, y: str) -> dict:
    from scipy.stats import spearmanr

    pairs = [(row[x], row[y]) for row in rows if row[x] is not None and row[y] is not None]
    xs, ys = [p[0] for p in pairs], [p[1] for p in pairs]
    result = {
        "x": x, "y": y, "n": len(pairs), "excluded_missing": len(rows) - len(pairs),
        "rho": None, "p_value": None, "undefined_reason": None,
        "x_zeros": sum(v == 0 for v in xs), "y_zeros": sum(v == 0 for v in ys),
        "x_summary": median_iqr(xs), "y_summary": median_iqr(ys),
    }
    if len(pairs) < 3:
        result["undefined_reason"] = "n_insuficiente"
    elif len(set(xs)) < 2 or len(set(ys)) < 2:
        result["undefined_reason"] = "variavel_constante"
    else:
        statistic = spearmanr(xs, ys)
        result["rho"], result["p_value"] = float(statistic.statistic), float(statistic.pvalue)
    return result


def analyze(rows: list[dict]) -> dict:
    results = [dict(spearman(rows, FREQUENCY, cfr), label=label)
               for cfr, label in CFR_VARIANTS.items()]
    for result, adjusted in zip(results, holm([r["p_value"] for r in results])):
        result["p_holm"] = adjusted
        if result["rho"] is not None:
            result["strength"] = strength(result["rho"])
            result["direction"] = "positiva" if result["rho"] > 0 else "negativa"
            result["significant_holm"] = adjusted < ALPHA
    return {"repositories": len(rows), "alpha": ALPHA, "method": "spearman",
            "correction": "holm", "results": results}


def markdown(analysis: dict) -> str:
    lines = [
        "# RQ05 — Frequência de deploy × CFR (Spearman)", "",
        f"Repositórios na tabela-base: {analysis['repositories']}. "
        f"α = {analysis['alpha']}; p ajustado por Holm sobre os {len(analysis['results'])} testes.", "",
        "| Variante | n pareado | excluídos (ausentes) | ρ | p | p (Holm) | força | CFR = 0 |",
        "|---|---:|---:|---:|---:|---:|---|---:|",
    ]
    for r in analysis["results"]:
        lines.append(
            f"| {r['label']} | {r['n']} | {r['excluded_missing']} | {_fmt(r['rho'])} | "
            f"{_fmt_p(r['p_value'])} | {_fmt_p(r['p_holm'])} | "
            f"{r.get('strength') or r['undefined_reason']} | {r['y_zeros']} |"
        )
    lines += ["", "| Variável (n pareado) | mediana | Q1 | Q3 | IQR |", "|---|---:|---:|---:|---:|"]
    for r in analysis["results"]:
        for name, key in ((f"Frequência (rel./semana) — {r['y']}", "x_summary"),
                          (r["label"], "y_summary")):
            s = r[key]
            lines.append(f"| {name} | {_fmt(s['median'])} | {_fmt(s['q1'])} | "
                         f"{_fmt(s['q3'])} | {_fmt(s['iqr'])} |")
    lines += ["", "Interpretação: ρ mede associação monotônica entre postos, não causalidade.",
              "Empates em CFR = 0 usam postos médios. Ver `rq05_dispersao.png`."]
    return "\n".join(lines) + "\n"


def scatter(rows: list[dict], analysis: dict, path: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    figure, axes = plt.subplots(1, len(analysis["results"]), figsize=(10, 4), sharex=True)
    for axis, result in zip(axes, analysis["results"]):
        pairs = [(row[FREQUENCY], row[result["y"]]) for row in rows
                 if row[FREQUENCY] is not None and row[result["y"]] is not None]
        axis.scatter([p[0] for p in pairs], [p[1] for p in pairs], s=14, alpha=0.6)
        axis.set_xscale("symlog", linthresh=SYMLOG_THRESHOLD)
        axis.set_ylim(-0.03, 1.03)
        axis.set_xlabel("Frequência de deploy (releases/semana, symlog)")
        axis.set_ylabel(result["label"])
        axis.set_title(f"ρ = {_fmt(result['rho'])}, p(Holm) = {_fmt_p(result['p_holm'])}, "
                       f"n = {result['n']}", fontsize=9)
        axis.grid(alpha=0.3)
    figure.tight_layout()
    figure.savefig(path, dpi=150)
    plt.close(figure)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base", type=Path, default=Path("analysis/base_repositorios.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("analysis/rq05"))
    parser.add_argument("--no-plot", action="store_true", help="não gerar a dispersão")
    args = parser.parse_args(argv)
    try:
        rows = read_csv(args.base)
    except (OSError, KeyError, ValueError) as error:
        print(f"Erro: {error}", file=sys.stderr)
        return 1
    analysis = analyze(rows)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "rq05_resultados.json").write_text(
        json.dumps(analysis, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (args.output_dir / "rq05_resultados.md").write_text(markdown(analysis), encoding="utf-8")
    if not args.no_plot:
        scatter(rows, analysis, args.output_dir / "rq05_dispersao.png")
    for r in analysis["results"]:
        print(f"{r['y']}: n={r['n']} rho={_fmt(r['rho'])} p={_fmt_p(r['p_value'])} "
              f"p_holm={_fmt_p(r['p_holm'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

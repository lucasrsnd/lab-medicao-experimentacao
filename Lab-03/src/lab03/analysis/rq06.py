"""RQ06: métricas DORA entre subgrupos, com tamanho de efeito e Holm (S03-05).

    python -m lab03.analysis.rq06 --base analysis/base_repositorios.csv --output-dir analysis/rq06

Fatores pré-registrados em `docs/protocolo.md`: linguagem principal, quartis
de estrelas e quartis de contribuidores. Linguagens com menos de
`MIN_LANGUAGE_GROUP` repositórios são agrupadas em "Outras". Fatores numéricos
viram Q1–Q4 pelos quartis da amostra (cortes reportados); um empate no corte
fica no quartil inferior. Métricas: a referência C1 das RQ01–04.

Para cada fator × métrica, só entram os repositórios com a métrica observada.
Com 3+ grupos, Kruskal-Wallis e ε² = H/(n−1); com 2 grupos, Mann-Whitney e
Cliff δ = 2·U₁/(n₁·n₂) − 1. Todos os p-valores formam uma família corrigida por
Holm. Cada grupo reporta n, mediana e IQR. Tipo de projeto não é fator: não foi
escolhido no protocolo e só existe para os 60 repositórios da amostra-ouro.

Saídas: `rq06_resultados.json`, `rq06_resultados.md` e `rq06_grupos.csv`.
"""

import argparse
import csv
import json
import statistics
import sys
from pathlib import Path

from lab03.analysis.base import read_csv
from lab03.analysis.stats import fmt, fmt_p, holm, median_iqr

METRICS = {
    "deployment_frequency_per_week": "Frequência (releases/semana)",
    "lead_time_a_hours": "Lead time (a) (horas)",
    "cfr_a": "CFR (a) CI",
    "recovery_hours": "Recuperação (horas)",
}
FACTORS = {"linguagem": "Linguagem principal", "estrelas": "Quartis de estrelas",
           "contribuidores": "Quartis de contribuidores"}
MIN_LANGUAGE_GROUP = 10
OTHER_LANGUAGES = "Outras"
ALPHA = 0.05


def quartile_groups(rows: list[dict], field: str) -> tuple[dict, list[float]]:
    values = [row[field] for row in rows if row[field] is not None]
    cuts = statistics.quantiles(values, n=4, method="inclusive")
    groups = {}
    for row in rows:
        value = row[field]
        if value is not None:
            groups[row["repositorio"]] = f"Q{1 + sum(value > cut for cut in cuts)}"
    return groups, cuts


def language_groups(rows: list[dict]) -> tuple[dict, list[str]]:
    counts: dict[str, int] = {}
    for row in rows:
        if row["linguagem"]:
            counts[row["linguagem"]] = counts.get(row["linguagem"], 0) + 1
    pooled = sorted(name for name, n in counts.items() if n < MIN_LANGUAGE_GROUP)
    groups = {row["repositorio"]: OTHER_LANGUAGES if row["linguagem"] in pooled else row["linguagem"]
              for row in rows if row["linguagem"]}
    return groups, pooled


def factor_groups(rows: list[dict]) -> dict:
    language, pooled = language_groups(rows)
    stars, star_cuts = quartile_groups(rows, "estrelas")
    contributors, contributor_cuts = quartile_groups(rows, "contribuidores")
    return {
        "linguagem": {"groups": language, "pooled_into_other": pooled},
        "estrelas": {"groups": stars, "cuts": star_cuts},
        "contribuidores": {"groups": contributors, "cuts": contributor_cuts},
    }


def epsilon_label(value: float) -> str:
    # Tomczak & Tomczak (2014) para ε².
    return ("desprezível" if value < 0.01 else "pequeno" if value < 0.08
            else "médio" if value < 0.26 else "grande")


def cliff_label(value: float) -> str:
    # Romano et al. (2006), como no enunciado.
    size = abs(value)
    return ("desprezível" if size < 0.147 else "pequeno" if size < 0.33
            else "médio" if size < 0.474 else "grande")


def compare(samples: dict[str, list[float]]) -> dict:
    """Kruskal-Wallis (3+ grupos) ou Mann-Whitney (2 grupos) com efeito."""
    from scipy.stats import kruskal, mannwhitneyu

    samples = {name: values for name, values in samples.items() if values}
    n = sum(len(values) for values in samples.values())
    result = {"n": n, "k": len(samples), "test": None, "statistic": None, "p_value": None,
              "effect": None, "effect_value": None, "effect_size": None, "undefined_reason": None}
    pooled = [v for values in samples.values() for v in values]
    if len(samples) < 2:
        result["undefined_reason"] = "menos_de_dois_grupos"
    elif len(set(pooled)) < 2:
        result["undefined_reason"] = "metrica_constante"
    elif len(samples) == 2:
        (_, x), (_, y) = samples.items()
        statistic = mannwhitneyu(x, y, alternative="two-sided")
        delta = 2 * statistic.statistic / (len(x) * len(y)) - 1
        result.update(test="mann-whitney", statistic=float(statistic.statistic),
                      p_value=float(statistic.pvalue), effect="cliff_delta",
                      effect_value=float(delta), effect_size=cliff_label(delta))
    else:
        statistic = kruskal(*samples.values())
        epsilon = statistic.statistic / (n - 1)
        result.update(test="kruskal-wallis", statistic=float(statistic.statistic),
                      p_value=float(statistic.pvalue), effect="epsilon_squared",
                      effect_value=float(epsilon), effect_size=epsilon_label(epsilon))
    return result


def _order(name: str) -> tuple:
    return (name == OTHER_LANGUAGES, name)


def analyze(rows: list[dict]) -> dict:
    factors = factor_groups(rows)
    tests = []
    for factor, info in factors.items():
        for metric in METRICS:
            samples: dict[str, list[float]] = {}
            for row in rows:
                group = info["groups"].get(row["repositorio"])
                if group is not None and row[metric] is not None:
                    samples.setdefault(group, []).append(row[metric])
            samples = dict(sorted(samples.items(), key=lambda item: _order(item[0])))
            test = compare(samples)
            test.update(factor=factor, metric=metric, groups=[
                {"group": name, "n": len(values), **median_iqr(values)}
                for name, values in samples.items()
            ])
            test["small_groups"] = [g["group"] for g in test["groups"] if g["n"] < MIN_LANGUAGE_GROUP]
            tests.append(test)
    for test, adjusted in zip(tests, holm([t["p_value"] for t in tests])):
        test["p_holm"] = adjusted
        test["significant_holm"] = None if adjusted is None else adjusted < ALPHA
    factor_summary = {
        name: {
            "sizes": dict(sorted(
                {g: list(info["groups"].values()).count(g) for g in set(info["groups"].values())}.items(),
                key=lambda item: _order(item[0]))),
            **{key: value for key, value in info.items() if key != "groups"},
        }
        for name, info in factors.items()
    }
    return {"repositories": len(rows), "alpha": ALPHA, "correction": "holm",
            "family_size": sum(t["p_value"] is not None for t in tests),
            "factors": factor_summary, "tests": tests}


def markdown(analysis: dict) -> str:
    lines = [
        "# RQ06 — Métricas DORA por subgrupo", "",
        f"Repositórios: {analysis['repositories']}. Família de Holm: "
        f"{analysis['family_size']} testes, α = {analysis['alpha']}.", "",
        "## Fatores e tamanhos dos grupos", "",
    ]
    for name, info in analysis["factors"].items():
        sizes = ", ".join(f"{g} = {n}" for g, n in info["sizes"].items())
        extra = (f" Cortes (Q1/Q2/Q3): {' / '.join(fmt(c, 1) for c in info['cuts'])}."
                 if "cuts" in info else
                 f" Agrupadas em \"{OTHER_LANGUAGES}\" (< {MIN_LANGUAGE_GROUP}): "
                 f"{', '.join(info['pooled_into_other']) or 'nenhuma'}.")
        lines.append(f"- **{FACTORS[name]}:** {sizes}.{extra}")
    lines += ["", "## Testes", "",
              "| Fator | Métrica | Teste | n | k | estatística | p | p (Holm) | efeito | magnitude |",
              "|---|---|---|---:|---:|---:|---:|---:|---:|---|"]
    for t in analysis["tests"]:
        effect = "—" if t["effect"] is None else f"{'ε²' if t['effect'] == 'epsilon_squared' else 'δ'} = {fmt(t['effect_value'])}"
        lines.append(
            f"| {FACTORS[t['factor']]} | {METRICS[t['metric']]} | {t['test'] or t['undefined_reason']} | "
            f"{t['n']} | {t['k']} | {fmt(t['statistic'], 2)} | {fmt_p(t['p_value'])} | "
            f"{fmt_p(t['p_holm'])}{' *' if t['significant_holm'] else ''} | {effect} | "
            f"{t['effect_size'] or '—'} |")
    lines += ["", "\\* significativo após Holm (α = 0,05).", "",
              "## Mediana [Q1–Q3] por grupo", ""]
    for factor in analysis["factors"]:
        tests = [t for t in analysis["tests"] if t["factor"] == factor]
        names = [g["group"] for g in tests[0]["groups"]]
        lines += [f"### {FACTORS[factor]}", "",
                  "| Métrica | " + " | ".join(names) + " |",
                  "|---|" + "---:|" * len(names)]
        for t in tests:
            by_group = {g["group"]: g for g in t["groups"]}
            cells = [f"{fmt(g['median'], 2)} [{fmt(g['q1'], 2)}–{fmt(g['q3'], 2)}] (n={g['n']})"
                     if (g := by_group.get(name)) else "—" for name in names]
            lines.append(f"| {METRICS[t['metric']]} | " + " | ".join(cells) + " |")
        lines.append("")
    return "\n".join(lines)


def write_groups(path: Path, analysis: dict) -> None:
    fields = ("fator", "metrica", "grupo", "n", "mediana", "q1", "q3", "iqr")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for t in analysis["tests"]:
            for g in t["groups"]:
                writer.writerow({"fator": t["factor"], "metrica": t["metric"], "grupo": g["group"],
                                 "n": g["n"], "mediana": g["median"], "q1": g["q1"],
                                 "q3": g["q3"], "iqr": g["iqr"]})


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base", type=Path, default=Path("analysis/base_repositorios.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("analysis/rq06"))
    args = parser.parse_args(argv)
    try:
        rows = read_csv(args.base)
    except (OSError, KeyError, ValueError) as error:
        print(f"Erro: {error}", file=sys.stderr)
        return 1
    analysis = analyze(rows)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "rq06_resultados.json").write_text(
        json.dumps(analysis, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (args.output_dir / "rq06_resultados.md").write_text(markdown(analysis), encoding="utf-8")
    write_groups(args.output_dir / "rq06_grupos.csv", analysis)
    significant = sum(bool(t["significant_holm"]) for t in analysis["tests"])
    print(f"{len(analysis['tests'])} testes; {significant} significativos após Holm.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

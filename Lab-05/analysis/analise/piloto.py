"""Análise da coleta piloto: descritivas, testes, gráficos e repetições necessárias para a S02.

Uso (a partir de Lab-05/analysis):
    python -m analise.piloto ../data/piloto/piloto.csv --saida resultados/piloto [--pareado]
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from analise.config import COLUNAS, PODER_ALVO
from analise.descritiva import summarize, validate
from analise.poder import params_from_pilot, power_by_n, required_n
from analise.testes import compare_all

NS_PADRAO = [5, 10, 15, 20, 30, 40, 60, 80, 100]


def boxplot(data: pd.DataFrame, metrica: str) -> plt.Figure:
    """Boxplot com os pontos de cada tratamento para uma métrica."""
    subset = data[data["metrica"] == metrica]
    names = sorted(subset["tratamento"].unique())
    values = [subset.loc[subset["tratamento"] == name, "valor"].to_numpy() for name in names]
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.boxplot(values, showmeans=True)
    ax.set_xticks(range(1, len(names) + 1), names)
    for i, v in enumerate(values, start=1):
        ax.scatter([i] * v.size, v, s=8, alpha=0.4)
    ax.set_title(f"Piloto: {metrica} por tratamento")
    ax.set_xlabel("Tratamento")
    ax.set_ylabel(metrica)
    fig.tight_layout()
    return fig


def power_figure(power: pd.DataFrame, metrica: str) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(6, 4))
    for test, group in power.groupby("teste", sort=True):
        ax.plot(group["n"], group["poder"], marker="o", label=test)
        ax.fill_between(group["n"], group["ic95_low"], group["ic95_high"], alpha=0.2)
    ax.axhline(PODER_ALVO, linestyle="--", color="gray", label=f"{PODER_ALVO:.0%}")
    ax.set_ylim(0, 1)
    ax.set_title(f"Poder estimado × n: {metrica}")
    ax.set_xlabel("Observações por tratamento (n)")
    ax.set_ylabel("Poder (proporção de rejeições de H0)")
    ax.legend()
    fig.tight_layout()
    return fig


def run(data: pd.DataFrame, saida: Path, pareado: bool, dist: str, ns: list[int], rho: float | None) -> None:
    data = validate(data)
    saida.mkdir(parents=True, exist_ok=True)
    (saida / "figuras").mkdir(exist_ok=True)

    summary = summarize(data)
    summary.to_csv(saida / "descritivas.csv", index=False)
    comparisons = compare_all(data, pareado)
    comparisons.to_csv(saida / "comparacoes.csv", index=False)

    power_tables, needed = [], []
    for metrica in sorted(data["metrica"].unique()):
        fig = boxplot(data, metrica)
        fig.savefig(saida / "figuras" / f"box_{metrica}.png", dpi=150)
        plt.close(fig)

        treatments = sorted(data.loc[data["metrica"] == metrica, "tratamento"].unique())
        if len(treatments) != 2:
            continue
        subset = data[data["metrica"] == metrica]
        metric_dist = dist if (subset["valor"] > 0).all() else "normal"
        metric_rho = 0.0
        if pareado:
            # Mesma unidade de análise do teste pareado: mediana das repetições por unidade.
            medians = subset.groupby(["tratamento", "unidade", "metrica"], as_index=False)["valor"].median()
            wide = medians.pivot(index="unidade", columns="tratamento", values="valor").dropna()
            subset = medians.assign(repeticao=1)
            # Spearman é invariante às marginais; na cópula gaussiana ρ_latente = 2·sen(π·ρ_s/6).
            spearman = float(wide.corr(method="spearman").iloc[0, 1])
            metric_rho = rho if rho is not None else float(2 * np.sin(np.pi * spearman / 6))
            metric_rho = max(min(metric_rho, 0.99), -0.99)
        a, b = params_from_pilot(subset, metrica, *treatments, dist=metric_dist)
        power = power_by_n(a, b, ns, pareado=pareado, rho=metric_rho)
        power.insert(0, "metrica", metrica)
        power_tables.append(power)
        need = required_n(power)
        need.insert(0, "metrica", metrica)
        need["dist"] = metric_dist
        need["rho"] = metric_rho
        needed.append(need)
        fig = power_figure(power, metrica)
        fig.savefig(saida / "figuras" / f"poder_{metrica}.png", dpi=150)
        plt.close(fig)

    if power_tables:
        pd.concat(power_tables).to_csv(saida / "poder.csv", index=False)
        pd.concat(needed).to_csv(saida / "n_necessario.csv", index=False)

    print("Descritivas:\n", summary[["metrica", "tratamento", "n", "mediana", "iqr", "media", "dp", "shapiro_p"]]
          .to_string(index=False))
    print("\nComparações:\n", comparisons[["metrica", "teste", "p_valor", "p_holm", "efeito_nome", "efeito",
                                          "magnitude"]].to_string(index=False))
    if needed:
        print("\nn por tratamento para", f"{PODER_ALVO:.0%}", "de poder:\n", pd.concat(needed).to_string(index=False))
    print(f"\nSaídas em {saida}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Analisa a coleta piloto do Lab05.")
    parser.add_argument("csv", type=Path, help=f"CSV no formato longo com colunas {', '.join(COLUNAS)}.")
    parser.add_argument("--saida", type=Path, default=Path("resultados/piloto"))
    parser.add_argument("--pareado", action="store_true", help="Cada unidade é medida em todos os tratamentos.")
    parser.add_argument("--dist", choices=("lognormal", "normal"), default="lognormal")
    parser.add_argument("--ns", type=int, nargs="+", default=NS_PADRAO)
    parser.add_argument("--rho", type=float, default=None, help="Correlação entre tratamentos (pareado).")
    args = parser.parse_args()
    run(pd.read_csv(args.csv), args.saida, args.pareado, args.dist, args.ns, args.rho)


if __name__ == "__main__":
    main()

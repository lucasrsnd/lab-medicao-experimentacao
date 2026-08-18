"""Gera figuras (matplotlib) a partir das estatísticas de cada RQ, salva em
`Lab-01/reports/figures/`. Um helper genérico (`figura_histograma`) reaproveitado
por qualquer RQ numérica - a diferença entre RQs é só título/rótulo/escala.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")  # sem backend interativo - roda em terminal/CI sem display
import matplotlib.pyplot as plt
import pandas as pd

FIGURES_DIR = Path(__file__).resolve().parents[2] / "reports" / "figures"


def _salvar(fig: plt.Figure, nome_arquivo: str) -> Path:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    caminho = FIGURES_DIR / nome_arquivo
    fig.savefig(caminho, bbox_inches="tight", dpi=120)
    plt.close(fig)
    return caminho


def figura_histograma(
    serie: pd.Series,
    *,
    titulo: str,
    xlabel: str,
    nome_arquivo: str,
    mediana: float | None = None,
    log_x: bool = False,
) -> Path:
    dados = serie.dropna()
    fig, ax = plt.subplots(figsize=(8, 5))

    if log_x:
        # bins tem que nascer em escala log (np.logspace) - so trocar ax.set_xscale
        # depois de um hist() com bins lineares NAO redistribui os dados, so muda o
        # desenho do eixo, distorcendo o grafico (visto na primeira versao da RQ02).
        # log(0) e indefinido, entao valores == 0 sao contados e anotados a parte,
        # em vez de descartados silenciosamente ou forcados pra dentro do log.
        zeros = int((dados == 0).sum())
        positivos = dados[dados > 0]
        bins = np.logspace(np.log10(positivos.min()), np.log10(positivos.max()), 30)
        ax.hist(positivos, bins=bins, color="#4C72B0", edgecolor="white")
        ax.set_xscale("log")
        if zeros:
            ax.text(
                0.02, 0.98, f"+ {zeros} repositório(s) com valor 0 (fora da escala log)",
                transform=ax.transAxes, ha="left", va="top", fontsize=9, color="dimgray",
            )
    else:
        ax.hist(dados, bins=30, color="#4C72B0", edgecolor="white")

    if mediana is not None:
        ax.axvline(mediana, color="firebrick", linestyle="--", label=f"mediana = {mediana:,.2f}")
        ax.legend()
    ax.set_title(titulo)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("quantidade de repositórios")
    return _salvar(fig, nome_arquivo)

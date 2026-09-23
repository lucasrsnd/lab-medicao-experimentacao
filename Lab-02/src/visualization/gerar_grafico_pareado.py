"""Gráfico complementar ao dashboard: comparação pareada por integrante.

Dono: Gustavo. O dashboard principal (`gerar_dashboard.py`, Davi #73) agrega
todos os 9 trials por tratamento num boxplot — mas o teste estatístico real
(Wilcoxon, `src/analysis/stats_utils.py`) pareia por INTEGRANTE (N=3): a
mediana dos 3 trials Com IA de cada pessoa contra a mediana dos 3 Sem IA da
mesma pessoa. Um boxplot agregado não mostra esse pareamento — este gráfico
mostra exatamente o que o teste está comparando: uma linha por integrante,
ligando seu valor Com IA ao seu valor Sem IA.

Uso (CLI, a partir de `Lab-02/`):
    python -m src.visualization.gerar_grafico_pareado
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from src.analysis.dataset import LAB02_ROOT, load_trials_tempo

OUT_DIR = LAB02_ROOT / "reports" / "figures"

# Só RQ1 aqui: a RQ2 empata em 100%/100% para os 3 integrantes (efeito teto,
# ver Seção 5.2 do relatório) — as 3 linhas ficariam perfeitamente
# sobrepostas e ilegíveis. O boxplot+pontos do dashboard principal já mostra
# a RQ2 melhor (inclusive o outlier em 0%).
METRICAS = [
    ("tempo_min", "Tempo até time-to-green (min)", "RQ1 — Tempo, por integrante"),
]


def _preparar_dados() -> pd.DataFrame:
    return load_trials_tempo()


def gerar_grafico_pareado() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = _preparar_dados()

    sns.set_theme(style="whitegrid")
    largura = max(9, 7 * len(METRICAS))
    fig, axes = plt.subplots(1, len(METRICAS), figsize=(largura, 6.5), squeeze=False)
    axes = axes[0]
    fig.suptitle(
        "Comparação pareada por integrante (N=3) — o que o Wilcoxon está testando",
        fontsize=13,
        weight="bold",
    )

    cores = dict(zip(sorted(df["integrante"].unique()), sns.color_palette("Set2", n_colors=3)))

    for ax, (coluna, ylabel, titulo) in zip(axes, METRICAS):
        medianas = df.groupby(["integrante", "tratamento"])[coluna].median().unstack()
        for integrante, linha in medianas.iterrows():
            ax.plot(
                ["Com IA", "Sem IA"],
                [linha["com_ia"], linha["sem_ia"]],
                marker="o",
                markersize=9,
                linewidth=2,
                color=cores[integrante],
                label=integrante,
            )
        ax.set_title(titulo)
        ax.set_ylabel(ylabel)
        ax.margins(x=0.15)

    axes[-1].legend(title="Integrante", loc="best")
    plt.tight_layout(rect=[0, 0, 1, 0.93])

    caminho = OUT_DIR / "rq1_pareado_por_integrante.png"
    plt.savefig(caminho, dpi=300)
    plt.close(fig)
    print(f"Gráfico pareado gerado em: {caminho}")


if __name__ == "__main__":
    gerar_grafico_pareado()

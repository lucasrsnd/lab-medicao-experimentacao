"""Gráfico da análise extra de segurança (Bandit) — Gustavo.

O resultado real é 0 vulnerabilidades nos dois tratamentos (ver
`docs/resultados-seguranca.md`), então o gráfico é, de propósito, duas
"caixas" achatadas em zero com os 9 pontos de cada tratamento sobrepostos —
uma anotação explícita evita que isso pareça um gráfico vazio/quebrado em
vez do resultado real.

Uso (CLI, a partir de `Lab-02/`):
    python -m src.visualization.gerar_grafico_seguranca
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import seaborn as sns

from src.analysis.dataset import LAB02_ROOT, load_trials_seguranca

OUT_DIR = LAB02_ROOT / "reports" / "figures"


def gerar_grafico_seguranca() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = load_trials_seguranca()

    sns.set_theme(style="whitegrid", palette="Set2")
    fig, ax = plt.subplots(figsize=(7, 6))
    fig.suptitle("Análise extra — Vulnerabilidades de segurança (Bandit)", fontsize=13, weight="bold")

    ordem = ["com_ia", "sem_ia"]  # mesma ordem das outras figuras do relatório
    sns.boxplot(data=df, x="tratamento", y="n_vulnerabilidades", ax=ax, order=ordem, width=0.4, showfliers=False)
    sns.stripplot(
        data=df,
        x="tratamento",
        y="n_vulnerabilidades",
        ax=ax,
        order=ordem,
        color="black",
        alpha=0.6,
        size=6,
        jitter=0.15,
    )
    ax.set_title("N = 9 trials por tratamento", fontsize=10)
    ax.set_ylabel("Nº de vulnerabilidades (Bandit)")
    ax.set_xlabel("Tratamento")
    ax.set_ylim(-0.5, 2)
    ax.text(
        0.5,
        0.7,
        "0 vulnerabilidades encontradas\nnos 18 trials (Com IA e Sem IA)",
        transform=ax.transAxes,
        ha="center",
        va="center",
        fontsize=11,
        style="italic",
        bbox=dict(boxstyle="round", facecolor="white", alpha=0.85, edgecolor="gray"),
    )

    plt.tight_layout(rect=[0, 0, 1, 0.93])

    caminho = OUT_DIR / "seguranca_vulnerabilidades.png"
    plt.savefig(caminho, dpi=300)
    plt.close(fig)
    print(f"Gráfico de segurança gerado em: {caminho}")


if __name__ == "__main__":
    gerar_grafico_seguranca()

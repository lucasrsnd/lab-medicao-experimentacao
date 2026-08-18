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


def figura_barra_categorica(
    contagem: pd.Series,
    *,
    titulo: str,
    xlabel: str,
    ylabel: str,
    nome_arquivo: str,
    destacar: list[str] | None = None,
    legenda_destaque: str = "",
) -> Path:
    """Barra de contagem por categoria (ex.: RQ05 - repositórios por linguagem).

    `destacar` pinta de outra cor as categorias que batem com algum critério externo
    (ex.: também aparecem no top do GitHub Octoverse) - dá pra ver de relance quanto
    da nossa amostra "bate" com a referência, sem precisar de uma segunda figura.
    """
    from matplotlib.patches import Patch

    destacar = destacar or []
    fig, ax = plt.subplots(figsize=(9, 5))
    cores = ["firebrick" if cat in destacar else "#4C72B0" for cat in contagem.index]
    ax.bar(contagem.index.astype(str), contagem.values, color=cores, edgecolor="white")
    ax.set_title(titulo)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
    if destacar:
        ax.legend(handles=[Patch(color="firebrick", label=legenda_destaque)])
    return _salvar(fig, nome_arquivo)


def figura_comparacao_por_linguagem(
    df_agrupado: pd.DataFrame,
    *,
    top_n: int,
    nome_arquivo: str,
) -> Path:
    """RQ07 - compara RQ02 (PRs aceitas), RQ03 (releases) e RQ04 (dias desde
    atualização) entre as `top_n` linguagens com mais repositórios na amostra.
    Espera `df_agrupado` no formato de `scripts/rq07_analise.py`
    (`linguagem_primaria`, `quantidade_repos`, `media_prs_aceitas`,
    `media_releases`, `media_dias_atualizacao`).
    """
    top = df_agrupado.nlargest(top_n, "quantidade_repos")
    metricas = [
        ("media_prs_aceitas", "RQ02 - PRs aceitas (média)"),
        ("media_releases", "RQ03 - Releases (média)"),
        ("media_dias_atualizacao", "RQ04 - Dias desde atualização (média)"),
    ]
    fig, eixos = plt.subplots(1, 3, figsize=(17, 5))
    for ax, (coluna, titulo) in zip(eixos, metricas):
        ax.bar(top["linguagem_primaria"], top[coluna], color="#4C72B0", edgecolor="white")
        ax.set_title(titulo)
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
    fig.suptitle(f"RQ07 - top {top_n} linguagens (por qtd. de repositórios) na amostra")
    return _salvar(fig, nome_arquivo)

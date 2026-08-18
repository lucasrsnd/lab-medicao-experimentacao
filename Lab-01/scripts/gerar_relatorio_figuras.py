"""
Análise e visualização RQ01+RQ02 [S03] (#15)
Análise e visualização RQ03+RQ04 [S03] (#16)
Análise e visualização RQ05+RQ06+RQ07 [S03] (#17)

Gera as figuras estáticas (PNG, em `reports/figures/`) e imprime o resumo (mediana,
contagem por categoria etc.) de cada RQ - o material bruto pra colar na seção de
resultados do relatório final.

RQ01-04 e RQ06 são histogramas numéricos (mesmo formato, tabela HISTOGRAMAS). RQ05
(categórica, comparada com o ranking do GitHub Octoverse) e RQ07 (agrupada por
linguagem, usa `data/processed/rq07_resultado_agrupado.csv` gerado por
`rq07_analise.py`) têm formato próprio, tratadas à parte.

Uso (a partir de Lab-01/):
    python scripts/gerar_relatorio_figuras.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.analysis import figures, stats
from src.analysis.referencias import OCTOVERSE_EDICAO, OCTOVERSE_FONTE_URL

DATASET_PATH = Path(__file__).resolve().parent.parent / "data" / "raw" / "repositorios_s02.csv"
RQ07_PATH = Path(__file__).resolve().parent.parent / "data" / "processed" / "rq07_resultado_agrupado.csv"

# Uma entrada por RQ com histograma numérico (mesmo formato de figura, só muda
# coluna/rótulo/escala). RQ05 (categórica) e RQ07 (agrupada por linguagem) não se
# encaixam nesse formato - tratadas à parte, depois do loop.
HISTOGRAMAS = [
    {
        "nome": "RQ01 (idade)",
        "coluna": "idade_anos",
        "resumo": stats.resumo_rq01_idade,
        "titulo": "RQ01 - Idade do repositório",
        "xlabel": "idade (anos)",
        "arquivo": "rq01_idade.png",
        "log_x": False,
    },
    {
        "nome": "RQ02 (PRs aceitas)",
        "coluna": "prs_aceitas",
        "resumo": stats.resumo_rq02_prs_aceitas,
        "titulo": "RQ02 - PRs aceitas (merged)",
        "xlabel": "PRs aceitas (escala log)",
        "arquivo": "rq02_prs_aceitas.png",
        "log_x": True,
    },
    {
        "nome": "RQ03 (releases)",
        "coluna": "total_releases",
        "resumo": stats.resumo_rq03_releases,
        "titulo": "RQ03 - Total de releases",
        "xlabel": "releases (escala log)",
        "arquivo": "rq03_releases.png",
        "log_x": True,
    },
    {
        "nome": "RQ04 (dias desde atualização)",
        "coluna": "dias_desde_atualizacao",
        "resumo": stats.resumo_rq04_atualizacao,
        "titulo": "RQ04 - Dias desde a última atualização",
        "xlabel": "dias (escala log)",
        "arquivo": "rq04_atualizacao.png",
        "log_x": True,
    },
    {
        "nome": "RQ06 (% issues fechadas)",
        "coluna": "razao_fechadas",
        "resumo": stats.resumo_rq06_razao_fechadas,
        "titulo": "RQ06 - Razão de issues fechadas",
        "xlabel": "issues fechadas / total",
        "arquivo": "rq06_issues.png",
        "log_x": False,
    },
]


def gerar_rq05(df: pd.DataFrame) -> None:
    resumo = stats.resumo_rq05_linguagens(df, top_n=10)
    caminho = figures.figura_barra_categorica(
        resumo["contagem_top"],
        titulo="RQ05 - Top 10 linguagens primárias",
        xlabel="linguagem",
        ylabel="quantidade de repositórios",
        nome_arquivo="rq05_linguagens.png",
        destacar=resumo["linguagens_top_tambem_no_octoverse"],
        legenda_destaque=f"também no top 10 Octoverse {OCTOVERSE_EDICAO}",
    )
    print(
        f"RQ05 (linguagens): {resumo['total_linguagens_distintas']} linguagens distintas | "
        f"{resumo['na_count']} repositório(s) sem linguagem (N/A)"
    )
    print(
        f"  {resumo['qtd_top_tambem_no_octoverse']}/10 das linguagens mais comuns na amostra "
        f"também estão no top 10 do GitHub Octoverse {OCTOVERSE_EDICAO} ({OCTOVERSE_FONTE_URL}): "
        f"{', '.join(resumo['linguagens_top_tambem_no_octoverse'])}"
    )
    print(f"  figura: {caminho}\n")


def gerar_rq07() -> None:
    if not RQ07_PATH.exists():
        print(f"RQ07: {RQ07_PATH} não encontrado - rode 'scripts/rq07_analise.py' primeiro.\n")
        return
    df_agrupado = pd.read_csv(RQ07_PATH)
    caminho = figures.figura_comparacao_por_linguagem(df_agrupado, top_n=8, nome_arquivo="rq07_combinada.png")
    print(f"RQ07 (combinada): comparação das top 8 linguagens (por qtd. de repositórios)")
    print(f"  figura: {caminho}\n")


def main() -> None:
    if not DATASET_PATH.exists():
        print(f"Erro: dataset não encontrado em {DATASET_PATH}.")
        print("Rode 'scripts/script_unico_s02.py' primeiro para gerar os dados.")
        return

    df = pd.read_csv(DATASET_PATH)
    print(f"Dataset: {len(df)} repositórios\n")

    for rq in HISTOGRAMAS:
        resumo = rq["resumo"](df)
        caminho = figures.figura_histograma(
            df[rq["coluna"]],
            titulo=rq["titulo"],
            xlabel=rq["xlabel"],
            nome_arquivo=rq["arquivo"],
            mediana=resumo["mediana"],
            log_x=rq["log_x"],
        )
        print(
            f"{rq['nome']}: mediana={resumo['mediana']:.2f} | média={resumo['media']:.2f} | "
            f"min={resumo['min']:.2f} | max={resumo['max']:.2f}"
        )
        print(f"  figura: {caminho}\n")

    gerar_rq05(df)
    gerar_rq07()


if __name__ == "__main__":
    main()

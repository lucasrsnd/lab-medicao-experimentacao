"""
Análise e visualização RQ01+RQ02 [S03] (#15)
Análise e visualização RQ03+RQ04 [S03] (#16)

Gera as figuras estáticas (PNG, em `reports/figures/`) e imprime o resumo (mediana
etc.) de cada RQ - o material bruto pra colar na seção de resultados do relatório
final. Cobertura atual: RQ01-RQ04 (histograma numérico). RQ05-07 (#17) têm formato
de gráfico diferente (categórico/agrupado) e entram à parte, não nesta tabela.

Uso (a partir de Lab-01/):
    python scripts/gerar_relatorio_figuras.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.analysis import figures, stats

DATASET_PATH = Path(__file__).resolve().parent.parent / "data" / "raw" / "repositorios_s02.csv"

# Uma entrada por RQ com histograma numérico. RQ05 (categórica) e RQ07 (agrupada
# por linguagem) não se encaixam nesse formato - tratadas à parte quando chegar a #17.
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
]


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


if __name__ == "__main__":
    main()

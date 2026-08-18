"""
Análise e visualização RQ01+RQ02 [S03] (#15)

Gera as figuras estáticas (PNG, em `reports/figures/`) e imprime o resumo (mediana
etc.) de cada RQ - o material bruto pra colar na seção de resultados do relatório
final. Cobertura atual: RQ01, RQ02. RQ03-04 (#16) e RQ05-07 (#17) entram aqui
conforme essas Issues avançam.

Uso (a partir de Lab-01/):
    python scripts/gerar_relatorio_figuras.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.analysis import figures, stats

DATASET_PATH = Path(__file__).resolve().parent.parent / "data" / "raw" / "repositorios_s02.csv"


def main() -> None:
    if not DATASET_PATH.exists():
        print(f"Erro: dataset não encontrado em {DATASET_PATH}.")
        print("Rode 'scripts/script_unico_s02.py' primeiro para gerar os dados.")
        return

    df = pd.read_csv(DATASET_PATH)
    print(f"Dataset: {len(df)} repositórios\n")

    resumo_rq01 = stats.resumo_rq01_idade(df)
    caminho_rq01 = figures.figura_histograma(
        df["idade_anos"],
        titulo="RQ01 - Idade do repositório",
        xlabel="idade (anos)",
        nome_arquivo="rq01_idade.png",
        mediana=resumo_rq01["mediana"],
    )
    print(
        f"RQ01 (idade): mediana={resumo_rq01['mediana']:.2f} anos | "
        f"média={resumo_rq01['media']:.2f} | min={resumo_rq01['min']:.2f} | max={resumo_rq01['max']:.2f}"
    )
    print(f"  figura: {caminho_rq01}\n")

    resumo_rq02 = stats.resumo_rq02_prs_aceitas(df)
    caminho_rq02 = figures.figura_histograma(
        df["prs_aceitas"],
        titulo="RQ02 - PRs aceitas (merged)",
        xlabel="PRs aceitas (escala log)",
        nome_arquivo="rq02_prs_aceitas.png",
        mediana=resumo_rq02["mediana"],
        log_x=True,
    )
    print(
        f"RQ02 (PRs aceitas): mediana={resumo_rq02['mediana']:.0f} | "
        f"média={resumo_rq02['media']:.0f} | min={resumo_rq02['min']:.0f} | max={resumo_rq02['max']:.0f}"
    )
    print(f"  figura: {caminho_rq02}")


if __name__ == "__main__":
    main()

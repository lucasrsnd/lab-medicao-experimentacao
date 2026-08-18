"""
Validação individual RQ03+RQ04 em 1000 repos + hipótese informal [S02]

Checa distribuição, outliers e valores ausentes das métricas de RQ03 (total de
releases) e RQ04 (dias desde última atualização) na base completa gerada pela
tarefa de paginação do Gustavo (`data/raw/repositorios_s02.csv`, 998/1000
repositórios - ver nota no README dele sobre o porquê de não ser 1000 exato).

Mesmo padrão de `validacao_s02_rq01_rq02.py`, aplicado às colunas `total_releases`
e `dias_desde_atualizacao`.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

DATASET_PATH = Path(__file__).resolve().parent.parent / "data" / "raw" / "repositorios_s02.csv"


def resumo_outliers_iqr(serie: pd.Series) -> dict:
    q1, q3 = serie.quantile(0.25), serie.quantile(0.75)
    iqr = q3 - q1
    limite_inferior, limite_superior = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    outliers = serie[(serie < limite_inferior) | (serie > limite_superior)]
    return {
        "q1": q1,
        "q3": q3,
        "iqr": iqr,
        "limite_inferior": limite_inferior,
        "limite_superior": limite_superior,
        "qtd_outliers": len(outliers),
        "pct_outliers": round(100 * len(outliers) / len(serie), 2),
    }


def validar_coluna(df: pd.DataFrame, coluna: str, nome_rq: str) -> None:
    serie = df[coluna]
    nulos = serie.isna().sum()
    validos = serie.dropna()

    print(f"\n=== {nome_rq} ({coluna}) ===")
    print(f"Valores ausentes/nulos: {nulos} de {len(df)} ({round(100 * nulos / len(df), 2)}%)")
    print(validos.describe().to_string())

    outliers = resumo_outliers_iqr(validos)
    print(
        f"\nOutliers (regra IQR, 1.5x): {outliers['qtd_outliers']} "
        f"({outliers['pct_outliers']}%) fora de "
        f"[{outliers['limite_inferior']:.2f}, {outliers['limite_superior']:.2f}]"
    )

    print("\nTop 5 maiores:")
    print(df.nlargest(5, coluna)[["nameWithOwner", coluna]].to_string(index=False))
    print("\nTop 5 menores:")
    print(df.nsmallest(5, coluna)[["nameWithOwner", coluna]].to_string(index=False))


def main() -> None:
    if not DATASET_PATH.exists():
        print(f"Erro: dataset não encontrado em {DATASET_PATH}.")
        print("Rode 'scripts/script_unico_s02.py' primeiro para gerar os dados.")
        return

    df = pd.read_csv(DATASET_PATH)
    print(f"Dataset carregado: {len(df)} repositórios.")

    validar_coluna(df, "total_releases", "RQ03 - total de releases")
    validar_coluna(df, "dias_desde_atualizacao", "RQ04 - dias desde última atualização")

    zero_releases = (df["total_releases"] == 0).sum()
    print(
        f"\nObs. RQ03: {zero_releases} de {len(df)} repositórios "
        f"({100 * zero_releases / len(df):.1f}%) têm 0 releases."
    )

    ultima_semana = (df["dias_desde_atualizacao"] <= 7).sum()
    print(
        f"Obs. RQ04: {ultima_semana} de {len(df)} repositórios "
        f"({100 * ultima_semana / len(df):.1f}%) foram atualizados na última semana."
    )


if __name__ == "__main__":
    main()

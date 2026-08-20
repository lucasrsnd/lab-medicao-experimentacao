"""
Validação individual RQ05+RQ06+RQ07 em 1000 repos + hipótese informal [S02]

Checa distribuição, outliers e valores ausentes das métricas de RQ05 (linguagem
primária), RQ06 (taxa de issues fechadas) e a consistência do cruzamento de dados
da RQ07 na base completa gerada pela tarefa de paginação (data/raw/repositorios_s02.csv).

Mesmo padrão de `validacao_s02_rq01_rq02.py` e `validacao_s02_rq03_rq04.py`, aplicado
às colunas `linguagem_primaria` e `razao_fechadas`, com funções adaptadas para
suportar colunas categóricas e realizar o agrupamento das métricas combinadas.
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


def validar_coluna_numerica(df: pd.DataFrame, coluna: str, nome_rq: str) -> None:
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


def validar_coluna_categorica(df: pd.DataFrame, coluna: str, nome_rq: str) -> None:
    serie = df[coluna]
    nulos = (serie == "N/A").sum() + serie.isna().sum()
    validos = serie[(serie.notna()) & (serie != "N/A")]

    print(f"\n=== {nome_rq} ({coluna}) ===")
    print(f"Valores ausentes/nulos ('N/A'): {nulos} de {len(df)} ({round(100 * nulos / len(df), 2)}%)")

    print("\nTop 10 mais frequentes:")
    print(validos.value_counts().head(10).to_string())


def validar_agrupamento_rq07(df: pd.DataFrame) -> None:
    print("\n=== RQ07 - Consistência do Agrupamento ===")
    df_validos = df[df["linguagem_primaria"] != "N/A"].copy()

    if df_validos.empty:
        print("Não há dados válidos para agrupar.")
        return

    analise = df_validos.groupby("linguagem_primaria").agg(
        quantidade_repos=("nameWithOwner", "count"),
        mediana_prs_aceitas=("prs_aceitas", "median"),
        mediana_releases=("total_releases", "median"),
        mediana_dias_atualizacao=("dias_desde_atualizacao", "median")
    ).sort_values(by="quantidade_repos", ascending=False)

    print("\nMétricas medianas por linguagem (Top 10 maiores linguagens):")
    print(analise.head(10).to_string())


def main() -> None:
    if not DATASET_PATH.exists():
        print(f"Erro: dataset não encontrado em {DATASET_PATH}.")
        return

    df = pd.read_csv(DATASET_PATH)
    print(f"Dataset carregado: {len(df)} repositórios.")

    validar_coluna_categorica(df, "linguagem_primaria", "RQ05 - linguagem primária")
    validar_coluna_numerica(df, "razao_fechadas", "RQ06 - taxa de issues fechadas")
    validar_agrupamento_rq07(df)

    if "total_issues" in df.columns:
        zero_issues = (df["total_issues"] == 0).sum()
        print(
            f"\nObs. RQ06: {zero_issues} de {len(df)} repositórios "
            f"({100 * zero_issues / len(df):.1f}%) têm 0 issues cadastradas."
        )


if __name__ == "__main__":
    main()
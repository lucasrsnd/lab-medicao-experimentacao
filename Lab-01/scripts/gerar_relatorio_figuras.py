"""
Análise e visualização RQ01+RQ02 [S03] (#15)
Análise e visualização RQ03+RQ04 [S03] (#16)
Análise e visualização RQ05+RQ06+RQ07 [S03] (#17)

Gera as figuras estáticas (PNG, em `reports/figures/`), imprime o resumo (mediana,
contagem por categoria etc.) de cada RQ e salva `reports/figures/legendas.md` com uma
legenda por figura, na ordem de apresentação - material pronto pra colar na seção de
resultados do relatório final.

A ordem e o texto de cada RQ vêm de `src/analysis/rq_config.py`, a mesma fonte usada
pelo dashboard (`app_streamlit.py`), pra garantir que as duas apresentações não
divirjam (já aconteceu do RQ05 aparecer depois do RQ06 antes dessa refatoração).

Uso (a partir de Lab-01/):
    python scripts/gerar_relatorio_figuras.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.analysis import figures, rq_config, stats
from src.analysis.referencias import OCTOVERSE_EDICAO

DATASET_PATH = Path(__file__).resolve().parent.parent / "data" / "raw" / "repositorios_s02.csv"
RQ07_PATH = Path(__file__).resolve().parent.parent / "data" / "processed" / "rq07_resultado_agrupado.csv"


def _gerar_numerica(df: pd.DataFrame, rq: dict) -> Path:
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
        f"{rq['id']}: mediana={resumo['mediana']:.2f} | média={resumo['media']:.2f} | "
        f"min={resumo['min']:.2f} | max={resumo['max']:.2f}"
    )
    return caminho


def _gerar_categorica(df: pd.DataFrame, rq: dict) -> Path:
    resumo = stats.resumo_rq05_linguagens(df, top_n=10)
    caminho = figures.figura_barra_categorica(
        resumo["contagem_top"],
        titulo=rq["titulo"],
        xlabel="linguagem",
        ylabel="quantidade de repositórios",
        nome_arquivo=rq["arquivo"],
        destacar=resumo["linguagens_top_tambem_no_octoverse"],
        legenda_destaque=f"também no top 10 Octoverse {OCTOVERSE_EDICAO}",
    )
    print(
        f"{rq['id']}: {resumo['total_linguagens_distintas']} linguagens distintas | "
        f"{resumo['na_count']} repositório(s) sem linguagem (N/A)"
    )
    print(
        f"  {resumo['qtd_top_tambem_no_octoverse']}/10 das linguagens mais comuns na amostra "
        f"também estão no top 10 do GitHub Octoverse {OCTOVERSE_EDICAO}: "
        f"{', '.join(resumo['linguagens_top_tambem_no_octoverse'])}"
    )
    return caminho


def _gerar_combinada(rq: dict) -> Path | None:
    if not RQ07_PATH.exists():
        print(f"{rq['id']}: {RQ07_PATH} não encontrado - rode 'scripts/rq07_analise.py' primeiro.\n")
        return None
    df_agrupado = pd.read_csv(RQ07_PATH)
    caminho = figures.figura_comparacao_por_linguagem(df_agrupado, top_n=8, nome_arquivo=rq["arquivo"])
    print(f"{rq['id']}: comparação das top 8 linguagens (por qtd. de repositórios)")
    return caminho


def main() -> None:
    if not DATASET_PATH.exists():
        print(f"Erro: dataset não encontrado em {DATASET_PATH}.")
        print("Rode 'scripts/script_unico_s02.py' primeiro para gerar os dados.")
        return

    df = pd.read_csv(DATASET_PATH)
    print(f"Dataset: {len(df)} repositórios\n")

    legendas = []
    for numero, rq in enumerate(rq_config.RQS, start=1):
        if rq["tipo"] == "numerica":
            caminho = _gerar_numerica(df, rq)
        elif rq["tipo"] == "categorica":
            caminho = _gerar_categorica(df, rq)
        else:  # combinada
            caminho = _gerar_combinada(rq)

        if caminho is None:
            continue

        print(f"  figura: {caminho}\n")
        legendas.append(f"**Figura {numero} - {rq['titulo']}**\n\n{rq['legenda']}")

    legendas_path = figures.FIGURES_DIR / "legendas.md"
    legendas_path.write_text("\n\n".join(legendas) + "\n", encoding="utf-8")
    print(f"Legendas das figuras salvas em: {legendas_path}")


if __name__ == "__main__":
    main()

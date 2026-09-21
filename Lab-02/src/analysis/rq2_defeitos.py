"""RQ2 — O uso de assistente de IA reduz a quantidade de defeitos (testes que
falham) no código produzido?

Dono: Gustavo, Issue [S03] "RQ2 — Defeitos".

Uso (CLI, a partir de `Lab-02/`):
    python -m src.analysis.rq2_defeitos

Métricas (via `data/raw/trials_tempo.csv`, colunas `testes_passando`/
`testes_total`, gravadas por `src/timing/trial_timer.py` ao final do
time-box — inclusive em trials censurados):

- `taxa_sucesso_pct` = testes_passando / testes_total * 100 — métrica
  primária (normaliza katas com números diferentes de testes).
- `n_testes_falhando` = testes_total - testes_passando — métrica
  complementar.

Mesma estrutura de RQ1 (dois cenários, mediana/IQR, outliers IQR, Wilcoxon
pareado por integrante N=3) — ver `src/analysis/stats_utils.py` para a
justificativa do pareamento.

Grava `reports/analysis/rq2_defeitos.md` e `reports/analysis/rq2_defeitos.json`.
"""

from __future__ import annotations

import json

from src.analysis.dataset import LAB02_ROOT, load_trials_tempo, split_scenarios
from src.analysis.stats_utils import (
    descritivas_por_tratamento,
    identificar_outliers_iqr,
    medianas_pareadas_por_participante,
)

OUT_DIR = LAB02_ROOT / "reports" / "analysis"


def _adicionar_colunas_derivadas(df):
    df = df.copy()
    df["taxa_sucesso_pct"] = (df["testes_passando"] / df["testes_total"] * 100).round(2)
    df["n_testes_falhando"] = df["testes_total"] - df["testes_passando"]
    return df


def _analisar_cenario(df) -> dict:
    resultado = {}
    for coluna, chave in (("taxa_sucesso_pct", "taxa_sucesso"), ("n_testes_falhando", "testes_falhando")):
        descritivas = descritivas_por_tratamento(df, coluna)
        outliers = identificar_outliers_iqr(df, coluna)
        wilcoxon = medianas_pareadas_por_participante(df, coluna)

        resultado[chave] = {
            "descritivas_por_tratamento": [d.__dict__ for d in descritivas],
            "outliers_iqr": outliers[["kata", "integrante", "tratamento", coluna]].to_dict("records"),
            "wilcoxon_pareado_por_integrante": {
                "n_pares": wilcoxon.n_pares,
                "pares": [
                    {"integrante": i, "mediana_com_ia": c, "mediana_sem_ia": s}
                    for i, c, s in wilcoxon.pares
                ],
                "estatistica": wilcoxon.estatistica,
                "p_valor": wilcoxon.p_valor,
                "erro": wilcoxon.erro,
            },
        }
    return resultado


def _formatar_bloco_markdown(titulo: str, unidade: str, dados: dict) -> list[str]:
    linhas = [f"### {titulo}\n"]
    linhas.append(f"| Tratamento | N | Mediana ({unidade}) | IQR | Mín | Máx |")
    linhas.append("|---|---|---|---|---|---|")
    for d in dados["descritivas_por_tratamento"]:
        linhas.append(
            f"| {d['tratamento']} | {d['n']} | {d['mediana']:.2f} | {d['iqr']:.2f} "
            f"| {d['minimo']:.2f} | {d['maximo']:.2f} |"
        )
    linhas.append("")

    if dados["outliers_iqr"]:
        linhas.append(f"Outliers (regra IQR): {len(dados['outliers_iqr'])} ponto(s) — "
                       + ", ".join(f"{o['integrante']}/{o['kata']}/{o['tratamento']}" for o in dados["outliers_iqr"]))
        linhas.append("")

    w = dados["wilcoxon_pareado_por_integrante"]
    linhas.append(f"Wilcoxon pareado por integrante (N={w['n_pares']} pares): ")
    if w["erro"]:
        linhas.append(f"não calculado ({w['erro']}).\n")
    else:
        linhas.append(f"estatística = {w['estatistica']:.3f}, p-valor = {w['p_valor']:.4f}\n")
    return linhas


def _formatar_markdown(resultados: dict) -> str:
    linhas = ["# RQ2 — Defeitos (testes falhando)", ""]
    linhas.append(
        "RQ2: O uso de assistente de IA reduz a quantidade de defeitos "
        "(testes que falham) no código produzido?\n"
    )

    for nome_cenario, dados in resultados.items():
        titulo = "Todos os trials" if nome_cenario == "todos_os_trials" else "Excluindo outliers de instrumentação"
        linhas.append(f"## Cenário: {titulo}\n")
        linhas += _formatar_bloco_markdown("Taxa de sucesso (% testes passando)", "%", dados["taxa_sucesso"])
        linhas += _formatar_bloco_markdown("Nº de testes falhando", "testes", dados["testes_falhando"])
        linhas.append(
            "> N=3 (um par por integrante) é uma amostra muito pequena para poder "
            "estatístico — interpretar o p-valor com cautela na discussão.\n"
        )

    return "\n".join(linhas)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = _adicionar_colunas_derivadas(load_trials_tempo())
    cenarios = split_scenarios(df)

    resultados = {nome: _analisar_cenario(cenario_df) for nome, cenario_df in cenarios.items()}

    (OUT_DIR / "rq2_defeitos.json").write_text(
        json.dumps(resultados, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (OUT_DIR / "rq2_defeitos.md").write_text(_formatar_markdown(resultados), encoding="utf-8")

    print(f"RQ2 gravado em {OUT_DIR / 'rq2_defeitos.md'} e {OUT_DIR / 'rq2_defeitos.json'}")


if __name__ == "__main__":
    main()

"""RQ1 — O uso de assistente de IA reduz o tempo necessário para resolver
uma tarefa de programação?

Dono: Gustavo, Issue [S03] "RQ1 — Tempo".

Uso (CLI, a partir de `Lab-02/`):
    python -m src.analysis.rq1_tempo

Métrica primária: tempo até "time-to-green" (`data/raw/trials_tempo.csv`,
coluna `tempo_min`; trials censurados já vêm gravados em 35min, não
descartados — conforme o enunciado). Calcula, para os dois cenários (todos os
trials, e excluindo outliers de instrumentação conhecidos — ver
`src/analysis/dataset.py`):

- Mediana/IQR por tratamento (métrica agregada recomendada, dado o N pequeno).
- Outliers via IQR, por tratamento.
- Mediana por integrante, pareada com_ia vs sem_ia (N=3), com Wilcoxon
  signed-rank — a decisão de pareamento está documentada em
  `src/analysis/stats_utils.py`.

Grava `reports/analysis/rq1_tempo.md` (leitura humana, pro relatório final) e
`reports/analysis/rq1_tempo.json` (pro dashboard da S03, Davi).
"""

from __future__ import annotations

import json
from pathlib import Path

from src.analysis.dataset import LAB02_ROOT, load_trials_tempo, split_scenarios
from src.analysis.stats_utils import (
    descritivas_por_tratamento,
    identificar_outliers_iqr,
    medianas_pareadas_por_participante,
)

OUT_DIR = LAB02_ROOT / "reports" / "analysis"
VALOR_COL = "tempo_min"


def _analisar_cenario(df) -> dict:
    descritivas = descritivas_por_tratamento(df, VALOR_COL)
    outliers = identificar_outliers_iqr(df, VALOR_COL)
    wilcoxon = medianas_pareadas_por_participante(df, VALOR_COL)

    censura = (
        df.groupby("tratamento")["censurado"]
        .agg(n_trials="count", n_censurados="sum")
        .reset_index()
        .to_dict("records")
    )

    return {
        "descritivas_por_tratamento": [d.__dict__ for d in descritivas],
        "censura_por_tratamento": censura,
        "outliers_iqr": outliers[["kata", "integrante", "tratamento", VALOR_COL]].to_dict("records"),
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


def _formatar_markdown(resultados: dict) -> str:
    linhas = ["# RQ1 — Tempo (time-to-green)", ""]
    linhas.append(
        "RQ1: O uso de assistente de IA reduz o tempo necessário para resolver "
        "uma tarefa de programação?\n"
    )

    for nome_cenario, dados in resultados.items():
        titulo = "Todos os trials" if nome_cenario == "todos_os_trials" else "Excluindo outliers de instrumentação"
        linhas.append(f"## Cenário: {titulo}\n")

        linhas.append("### Mediana/IQR por tratamento (minutos)\n")
        linhas.append("| Tratamento | N | Mediana | IQR | Mín | Máx |")
        linhas.append("|---|---|---|---|---|---|")
        for d in dados["descritivas_por_tratamento"]:
            linhas.append(
                f"| {d['tratamento']} | {d['n']} | {d['mediana']:.2f} | {d['iqr']:.2f} "
                f"| {d['minimo']:.2f} | {d['maximo']:.2f} |"
            )
        linhas.append("")

        linhas.append("### Censura (time-box atingido sem sucesso)\n")
        linhas.append("| Tratamento | Trials | Censurados |")
        linhas.append("|---|---|---|")
        for c in dados["censura_por_tratamento"]:
            linhas.append(f"| {c['tratamento']} | {c['n_trials']} | {c['n_censurados']} |")
        linhas.append("")

        if dados["outliers_iqr"]:
            linhas.append("### Outliers (regra IQR, por tratamento)\n")
            for o in dados["outliers_iqr"]:
                linhas.append(f"- {o['integrante']} / {o['kata']} / {o['tratamento']}: {o[VALOR_COL]:.2f}min")
            linhas.append("")

        w = dados["wilcoxon_pareado_por_integrante"]
        linhas.append(f"### Wilcoxon pareado por integrante (N={w['n_pares']} pares)\n")
        linhas.append("| Integrante | Mediana Com IA | Mediana Sem IA |")
        linhas.append("|---|---|---|")
        for p in w["pares"]:
            linhas.append(f"| {p['integrante']} | {p['mediana_com_ia']:.2f} | {p['mediana_sem_ia']:.2f} |")
        linhas.append("")
        if w["erro"]:
            linhas.append(f"**Wilcoxon não calculado**: {w['erro']}\n")
        else:
            linhas.append(f"**Estatística** = {w['estatistica']:.3f}, **p-valor** = {w['p_valor']:.4f}\n")
        linhas.append(
            "> N=3 (um par por integrante) é uma amostra muito pequena para poder "
            "estatístico — interpretar o p-valor com cautela na discussão.\n"
        )

    return "\n".join(linhas)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = load_trials_tempo()
    cenarios = split_scenarios(df)

    resultados = {nome: _analisar_cenario(cenario_df) for nome, cenario_df in cenarios.items()}

    (OUT_DIR / "rq1_tempo.json").write_text(json.dumps(resultados, indent=2, ensure_ascii=False), encoding="utf-8")
    (OUT_DIR / "rq1_tempo.md").write_text(_formatar_markdown(resultados), encoding="utf-8")

    print(f"RQ1 gravado em {OUT_DIR / 'rq1_tempo.md'} e {OUT_DIR / 'rq1_tempo.json'}")


if __name__ == "__main__":
    main()

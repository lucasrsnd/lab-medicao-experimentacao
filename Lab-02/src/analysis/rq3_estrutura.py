"""RQ3 — O uso de assistente de IA altera a complexidade ciclomática ou a
duplicação do código produzido?

Dono: Lucas, Issue [S03] #72 "RQ3 — Complexidade ciclomática e duplicação".

Uso (CLI, a partir de `Lab-02/`):
    python -m src.analysis.rq3_estrutura

Métricas (via `data/raw/trials_metricas.csv`, gravado por
`src/metrics/static_metrics.py` — Radon cc/raw/mi + jscpd, ignorando
`test_*.py`/`conftest.py`):

- `complexidade_media`: CC (McCabe) média por função — métrica primária.
- `duplicacao_pct`: % de linhas duplicadas (jscpd) — métrica primária.
- `sloc`: LOC de controle, obrigatória pelo enunciado sempre que se reporta
  complexidade/duplicação (código de IA pode ser mais verboso).
- `cc_por_10_sloc` = complexidade_total / sloc * 10 — complexidade
  normalizada por LOC, para separar "código mais complexo" de "código maior".
- `mi`: Índice de Manutenibilidade (Radon mi) — aprofundamento opcional.

Mesma estrutura de RQ1/RQ2 (dois cenários, mediana/IQR, outliers IQR,
Wilcoxon pareado por integrante N=3). A mais, um Wilcoxon complementar
pareado **por kata** (N=6): a estrutura do código depende muito do problema
(K1, parser de log, tem CC bem maior que os demais), e cada kata foi resolvido
nos dois tratamentos — parear por kata controla esse efeito, o que o
pareamento por integrante não faz.

Grava `reports/analysis/rq3_estrutura.md` e `reports/analysis/rq3_estrutura.json`.
"""

from __future__ import annotations

import json

from src.analysis.dataset import LAB02_ROOT, load_trials_metricas, split_scenarios
from src.analysis.stats_utils import (
    descritivas_por_tratamento,
    identificar_outliers_iqr,
    medianas_pareadas_por_participante,
)

OUT_DIR = LAB02_ROOT / "reports" / "analysis"

# (coluna, chave no JSON, título no markdown, unidade)
METRICAS = [
    ("complexidade_media", "complexidade_media", "Complexidade ciclomática média por função (Radon cc)", "CC"),
    ("duplicacao_pct", "duplicacao", "Duplicação de código (jscpd)", "%"),
    ("sloc", "sloc", "SLOC — métrica de controle", "linhas"),
    ("cc_por_10_sloc", "cc_por_10_sloc", "Complexidade normalizada por LOC (CC por 10 SLOC)", "CC/10 SLOC"),
    ("mi", "mi", "Índice de Manutenibilidade (Radon mi, opcional)", "MI"),
]


def _adicionar_colunas_derivadas(df):
    df = df.copy()
    df["cc_por_10_sloc"] = (df["complexidade_total"] / df["sloc"] * 10).round(2)
    return df


def _wilcoxon_para_dict(wilcoxon, chave: str) -> dict:
    return {
        "n_pares": wilcoxon.n_pares,
        "pares": [
            {chave: k, "mediana_com_ia": c, "mediana_sem_ia": s}
            for k, c, s in wilcoxon.pares
        ],
        "estatistica": wilcoxon.estatistica,
        "p_valor": wilcoxon.p_valor,
        "erro": wilcoxon.erro,
    }


def _analisar_cenario(df) -> dict:
    resultado = {}
    for coluna, chave, _, _ in METRICAS:
        outliers = identificar_outliers_iqr(df, coluna)
        resultado[chave] = {
            "descritivas_por_tratamento": [d.__dict__ for d in descritivas_por_tratamento(df, coluna)],
            "outliers_iqr": outliers[["kata", "integrante", "tratamento", coluna]].to_dict("records"),
            "wilcoxon_pareado_por_integrante": _wilcoxon_para_dict(
                medianas_pareadas_por_participante(df, coluna), "integrante"
            ),
            "wilcoxon_pareado_por_kata": _wilcoxon_para_dict(
                medianas_pareadas_por_participante(df, coluna, chave="kata"), "kata"
            ),
        }
    return resultado


def _formatar_wilcoxon(rotulo: str, w: dict) -> str:
    if w["erro"]:
        return f"- {rotulo} (N={w['n_pares']} pares): não calculado ({w['erro']})."
    return (
        f"- {rotulo} (N={w['n_pares']} pares): estatística = {w['estatistica']:.3f}, "
        f"p-valor = {w['p_valor']:.4f}"
    )


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

    linhas.append(_formatar_wilcoxon("Wilcoxon pareado por integrante", dados["wilcoxon_pareado_por_integrante"]))
    linhas.append(_formatar_wilcoxon("Wilcoxon pareado por kata", dados["wilcoxon_pareado_por_kata"]))
    linhas.append("")

    pares_kata = dados["wilcoxon_pareado_por_kata"]["pares"]
    if pares_kata:
        linhas.append("| Kata | Mediana Com IA | Mediana Sem IA |")
        linhas.append("|---|---|---|")
        for p in pares_kata:
            linhas.append(f"| {p['kata']} | {p['mediana_com_ia']:.2f} | {p['mediana_sem_ia']:.2f} |")
        linhas.append("")
    return linhas


def _formatar_markdown(resultados: dict) -> str:
    linhas = ["# RQ3 — Estrutura do código (complexidade e duplicação)", ""]
    linhas.append(
        "RQ3: O uso de assistente de IA altera a complexidade ciclomática ou a "
        "duplicação do código produzido?\n"
    )

    for nome_cenario, dados in resultados.items():
        titulo = "Todos os trials" if nome_cenario == "todos_os_trials" else "Excluindo outliers de instrumentação"
        linhas.append(f"## Cenário: {titulo}\n")
        for _, chave, titulo_metrica, unidade in METRICAS:
            linhas += _formatar_bloco_markdown(titulo_metrica, unidade, dados[chave])
        linhas.append(
            "> N=3 (por integrante) e N=6 (por kata) são amostras muito pequenas "
            "para poder estatístico — interpretar o p-valor com cautela na discussão.\n"
        )

    return "\n".join(linhas)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = _adicionar_colunas_derivadas(load_trials_metricas())
    cenarios = split_scenarios(df)

    resultados = {nome: _analisar_cenario(cenario_df) for nome, cenario_df in cenarios.items()}

    (OUT_DIR / "rq3_estrutura.json").write_text(
        json.dumps(resultados, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (OUT_DIR / "rq3_estrutura.md").write_text(_formatar_markdown(resultados), encoding="utf-8")

    print(f"RQ3 gravado em {OUT_DIR / 'rq3_estrutura.md'} e {OUT_DIR / 'rq3_estrutura.json'}")


if __name__ == "__main__":
    main()

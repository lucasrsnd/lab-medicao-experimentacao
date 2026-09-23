"""RQ extra (exploratória, contribuição do grupo) — O uso de assistente de
IA altera a quantidade de vulnerabilidades de segurança introduzidas no
código produzido?

Dono: Gustavo. Não é uma das RQ1-RQ3 fixas do enunciado — complementar à
RQ3 (estrutura do código), na mesma linha do que o Lab-01 do grupo fez com
frentes de contribuição própria além do pedido.

Uso (CLI, a partir de `Lab-02/`):
    python -m src.analysis.rq_extra_seguranca

Fonte: `data/raw/trials_seguranca.csv` (`src/security/bandit_scan.py`).
Mesma estrutura de RQ1/RQ2 (mediana/IQR por tratamento, Wilcoxon pareado por
integrante N=3) — ver `src/analysis/stats_utils.py`.

Grava `reports/analysis/rq_extra_seguranca.md` e `.json`.
"""

from __future__ import annotations

import json

from src.analysis.dataset import LAB02_ROOT, load_trials_seguranca
from src.analysis.stats_utils import descritivas_por_tratamento, medianas_pareadas_por_participante

OUT_DIR = LAB02_ROOT / "reports" / "analysis"
VALOR_COL = "n_vulnerabilidades"


def _analisar() -> dict:
    df = load_trials_seguranca()

    descritivas = descritivas_por_tratamento(df, VALOR_COL)
    wilcoxon = medianas_pareadas_por_participante(df, VALOR_COL)

    return {
        "n_trials": len(df),
        "total_vulnerabilidades": int(df[VALOR_COL].sum()),
        "descritivas_por_tratamento": [d.__dict__ for d in descritivas],
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


def _formatar_markdown(resultado: dict) -> str:
    linhas = ["# RQ extra (exploratória) — Vulnerabilidades de segurança (Bandit)", ""]
    linhas.append(
        "O uso de assistente de IA altera a quantidade de vulnerabilidades de "
        "segurança introduzidas no código produzido? Contribuição extra do "
        "grupo, não uma das RQ1-RQ3 fixas do enunciado.\n"
    )
    linhas.append(
        f"**Resultado**: {resultado['total_vulnerabilidades']} vulnerabilidade(s) "
        f"encontrada(s) em {resultado['n_trials']} trials (Com IA e Sem IA).\n"
    )

    linhas.append("| Tratamento | N | Mediana | IQR | Mín | Máx |")
    linhas.append("|---|---|---|---|---|---|")
    for d in resultado["descritivas_por_tratamento"]:
        linhas.append(
            f"| {d['tratamento']} | {d['n']} | {d['mediana']:.2f} | {d['iqr']:.2f} "
            f"| {d['minimo']:.2f} | {d['maximo']:.2f} |"
        )
    linhas.append("")

    w = resultado["wilcoxon_pareado_por_integrante"]
    if w["erro"]:
        linhas.append(f"Wilcoxon pareado por integrante (N={w['n_pares']}): não calculado ({w['erro']}).\n")
    else:
        linhas.append(
            f"Wilcoxon pareado por integrante (N={w['n_pares']}): "
            f"estatística = {w['estatistica']:.3f}, p-valor = {w['p_valor']:.4f}.\n"
        )

    linhas.append(
        "**Interpretação**: com 0 vulnerabilidades nos dois tratamentos, o "
        "teste não tem o que detectar (todas as diferenças pareadas são "
        "zero) — resultado nulo, não ausência de diferença estatisticamente "
        "comprovada. Ver `docs/resultados-seguranca.md` para a discussão "
        "completa de por que isso é esperado nesta amostra."
    )

    return "\n".join(linhas)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    resultado = _analisar()

    (OUT_DIR / "rq_extra_seguranca.json").write_text(
        json.dumps(resultado, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (OUT_DIR / "rq_extra_seguranca.md").write_text(_formatar_markdown(resultado), encoding="utf-8")

    print(f"RQ extra (segurança) gravada em {OUT_DIR / 'rq_extra_seguranca.md'}")


if __name__ == "__main__":
    main()

"""Dashboard de visualização (Passo 6 do enunciado) — Milestone Lab02S03.

Dono: Davi, Issue [S03] #73. Lê `data/processed/dataset_consolidado.csv`
(Davi, #69) e gera `reports/figures/dashboard_tratamentos.png`.

Fix 2026-09-23 (Gustavo): os painéis de Tempo e Taxa de Sucesso ficavam em
branco porque o código checava `if 'tempo' in df.columns` / `'sucesso'`, mas
as colunas reais são `tempo_min` e `testes_passando`/`testes_total` (ver
`data/processed/dataset_consolidado.csv`) — as condições nunca eram
verdadeiras e os dois painéis mais importantes do experimento (RQ1 e RQ2)
nunca apareciam na imagem. Também trocado o proxy de "sucesso" (`tempo < 35`,
que mede só se o trial não foi censurado) pela taxa de sucesso real da RQ2
(`testes_passando / testes_total`, a mesma usada em
`src/analysis/rq2_defeitos.py`).

Ampliado 2026-09-23 (Gustavo) de 2x2 para 2x3: a RQ3 discute 5 métricas em
`docs/resultados-rq3.md` (CC, duplicação, SLOC, CC/10SLOC, MI) e só 2 tinham
painel (CC crua e SLOC). Adicionado MI (satura em 100 em arquivos pequenos —
visível nos pontos empilhados no teto) e CC normalizada por LOC (a métrica
que o texto trata como mais confiável que a CC crua, já que mistura tamanho
com complexidade). Duplicação continua de fora: é 0% constante nos 18
trials, sem variância nenhuma para um gráfico mostrar.

Uso (CLI, a partir de `Lab-02/`):
    python -m src.visualization.gerar_dashboard
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path


def gerar_dashboard():
    caminho_dados = Path("data/processed/dataset_consolidado.csv")
    dir_saida = Path("reports/figures")
    dir_saida.mkdir(parents=True, exist_ok=True)

    try:
        df = pd.read_csv(caminho_dados)
    except FileNotFoundError:
        print(f"Erro: Arquivo não encontrado em {caminho_dados}")
        return

    if "testes_passando" in df.columns and "testes_total" in df.columns:
        df["taxa_sucesso_pct"] = df["testes_passando"] / df["testes_total"] * 100

    if "complexidade_total" in df.columns and "sloc" in df.columns:
        # mesma fórmula de docs/resultados-rq3.md: CC total normalizada por LOC,
        # pra separar "código mais complexo" de "código só maior"
        df["cc_por_10_sloc"] = df["complexidade_total"] / df["sloc"] * 10

    # Configuração visual do Seaborn
    sns.set_theme(style="whitegrid", palette="Set2")
    fig, axes = plt.subplots(2, 3, figsize=(22, 12))
    fig.suptitle("Resultados do Experimento de IA — RQ1/RQ2/RQ3 (Sprint 03)", fontsize=18, weight="bold")

    def _boxplot_com_pontos(ax, coluna, titulo, ylabel):
        """Boxplot (mediana/IQR, como recomendado no enunciado) + pontos
        individuais sobrepostos (stripplot) — com N=9 por caixa, um boxplot
        sozinho esconde a amostra pequena; os pontos deixam isso visível."""
        sns.boxplot(data=df, x="tratamento", y=coluna, ax=ax, width=0.4, showfliers=False)
        sns.stripplot(data=df, x="tratamento", y=coluna, ax=ax, color="black", alpha=0.6, size=5, jitter=0.15)
        ax.set_title(titulo)
        ax.set_ylabel(ylabel)
        ax.set_xlabel("Tratamento")

    if "tempo_min" in df.columns:
        _boxplot_com_pontos(axes[0, 0], "tempo_min", "RQ1 — Tempo até time-to-green", "Minutos")

    if "taxa_sucesso_pct" in df.columns:
        _boxplot_com_pontos(axes[0, 1], "taxa_sucesso_pct", "RQ2 — Taxa de sucesso dos testes", "% testes passando")
        axes[0, 1].set_ylim(-5, 105)

    if "complexidade_media" in df.columns:
        _boxplot_com_pontos(axes[1, 0], "complexidade_media", "RQ3 — Complexidade Ciclomática Média (Radon)", "Complexidade")

    if "sloc" in df.columns:
        _boxplot_com_pontos(axes[1, 1], "sloc", "RQ3 — Linhas de Código Fonte (SLOC, controle)", "Quantidade de Linhas")

    if "cc_por_10_sloc" in df.columns:
        _boxplot_com_pontos(axes[1, 2], "cc_por_10_sloc", "RQ3 — Complexidade Ciclomática por 10 SLOC", "CC / 10 SLOC")
    else:
        axes[1, 2].set_visible(False)

    if "mi" in df.columns:
        _boxplot_com_pontos(axes[0, 2], "mi", "RQ3 — Índice de Manutenibilidade (Radon MI)", "MI (0-100)")
        axes[0, 2].set_ylim(0, 105)
    else:
        axes[0, 2].set_visible(False)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])

    caminho_figura = dir_saida / "dashboard_tratamentos.png"
    plt.savefig(caminho_figura, dpi=300)
    plt.close(fig)
    print(f"Dashboard gerado com sucesso! Arquivo salvo em: {caminho_figura}")


if __name__ == "__main__":
    gerar_dashboard()

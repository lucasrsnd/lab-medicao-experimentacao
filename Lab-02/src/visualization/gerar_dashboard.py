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

    if 'tempo' in df.columns:
        df['sucesso'] = df['tempo'] < 35.0

    # Configuração visual do Seaborn
    sns.set_theme(style="whitegrid", palette="Set2")
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle("Resultados do Experimento de IA (Sprint 02)", fontsize=18, weight='bold')

    if 'tempo' in df.columns:
        sns.boxplot(data=df, x="tratamento", y="tempo", ax=axes[0, 0], width=0.4)
        axes[0, 0].set_title("Tempo de Conclusão (Minutos)")
        axes[0, 0].set_ylabel("Minutos")
        axes[0, 0].set_xlabel("Tratamento")

    if 'sucesso' in df.columns:
        sucesso_pct = df.groupby('tratamento')['sucesso'].mean() * 100
        sns.barplot(x=sucesso_pct.index, y=sucesso_pct.values, ax=axes[0, 1])
        axes[0, 1].set_title("Taxa de Sucesso (Time-to-Green < 35 min)")
        axes[0, 1].set_ylabel("Porcentagem (%)")
        axes[0, 1].set_xlabel("Tratamento")
        axes[0, 1].set_ylim(0, 100)

    if 'complexidade_media' in df.columns:
        sns.boxplot(data=df, x="tratamento", y="complexidade_media", ax=axes[1, 0], width=0.4)
        axes[1, 0].set_title("Complexidade Ciclomática Média (Radon)")
        axes[1, 0].set_ylabel("Complexidade")
        axes[1, 0].set_xlabel("Tratamento")

    if 'sloc' in df.columns:
        sns.boxplot(data=df, x="tratamento", y="sloc", ax=axes[1, 1], width=0.4)
        axes[1, 1].set_title("Linhas de Código Fonte (SLOC)")
        axes[1, 1].set_ylabel("Quantidade de Linhas")
        axes[1, 1].set_xlabel("Tratamento")

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    
    caminho_figura = dir_saida / "dashboard_tratamentos.png"
    plt.savefig(caminho_figura, dpi=300)
    print(f"Dashboard gerado com sucesso! Arquivo salvo em: {caminho_figura}")

if __name__ == "__main__":
    gerar_dashboard()
"""
RQ07 - Sistemas em linguagens populares recebem mais contribuição, releases e atualizações?
Métrica: Divisão dos resultados de PRs (RQ02), Releases (RQ03) e Dias desde Atualização (RQ04) pela Linguagem (RQ05).

Issue: RQ07 - análise combinada [sprint:S01]

Uso (a partir de Lab-01/):
    1) pip install pandas
    2) python scripts/rq07_analise.py
"""

import pandas as pd
from pathlib import Path

# Ajustado para ler da pasta raw e buscar o CSV gerado pelo script unico.
# NOTA (#17): apontava pra repositorios_s01.csv (100 repos, dataset antigo da S01) -
# corrigido pra usar o dataset da S02 (998 repos), senao a analise da S03 roda em
# cima de dado desatualizado.
DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
DATASET_PATH = DATA_DIR / "repositorios_s02.csv"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"

def realizar_analise():
    if not DATASET_PATH.exists():
        print(f"Erro: Dataset não encontrado em {DATASET_PATH}.")
        print("Rode o 'script_unico_grupo.py' primeiro para gerar os dados.")
        return

    # Garante que a pasta processed exista para salvar o resultado
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(DATASET_PATH)

    # Filtrar repositórios que não possuem linguagem
    df_validos = df[df['linguagem_primaria'] != "N/A"]

    # Agrupar por linguagem primária calculando as médias
    analise = df_validos.groupby('linguagem_primaria').agg(
        quantidade_repos=('nameWithOwner', 'count'),
        media_prs_aceitas=('prs_aceitas', 'mean'),
        media_releases=('total_releases', 'mean'),
        media_dias_atualizacao=('dias_desde_atualizacao', 'mean')
    ).reset_index()

    # Ordenar pelas linguagens que mais aparecem
    analise = analise.sort_values(by='quantidade_repos', ascending=False)

    print("\n=== Análise RQ07: Agrupamento por Linguagem Primária ===")
    print(analise.to_string(index=False, float_format="%.2f"))
    
    # Salvar resultados
    caminho_saida = OUTPUT_DIR / "rq07_resultado_agrupado.csv"
    analise.to_csv(caminho_saida, index=False)
    print(f"\nResultado da análise salvo em: {caminho_saida}")

if __name__ == "__main__":
    realizar_analise()
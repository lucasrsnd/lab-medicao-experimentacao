import pandas as pd
from pathlib import Path

def consolidar_datasets():
    dir_raw = Path("data/raw")
    dir_processed = Path("data/processed")
    
    path_tempo = dir_raw / "trials_tempo.csv"
    path_metricas = dir_raw / "trials_metricas.csv"
    path_saida = dir_processed / "dataset_consolidado.csv"
    
    dir_processed.mkdir(parents=True, exist_ok=True)
    
    df_tempo = pd.read_csv(path_tempo)
    df_metricas = pd.read_csv(path_metricas)
    
    df_consolidado = pd.merge(
        df_tempo, 
        df_metricas, 
        on=["kata", "integrante", "tratamento"], 
        how="outer" 
    )
    
    df_consolidado.to_csv(path_saida, index=False)
    print(f"Dataset consolidado com sucesso! Salvo em: {path_saida}")
    print(f"Total de registros: {len(df_consolidado)}")

if __name__ == "__main__":
    consolidar_datasets()
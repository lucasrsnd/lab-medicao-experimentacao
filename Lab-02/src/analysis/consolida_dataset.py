import pandas as pd
from pathlib import Path

def consolidar_datasets():
    # Caminhos dos arquivos (assumindo execução a partir da raiz Lab-02)
    dir_raw = Path("data/raw")
    dir_processed = Path("data/processed")
    
    path_tempo = dir_raw / "trials_tempo.csv"
    path_metricas = dir_raw / "trials_metricas.csv"
    path_saida = dir_processed / "dataset_consolidado.csv"
    
    # Cria o diretório de saída se não existir
    dir_processed.mkdir(parents=True, exist_ok=True)
    
    # Carrega os CSVs
    df_tempo = pd.read_csv(path_tempo)
    df_metricas = pd.read_csv(path_metricas)
    
    # Realiza o merge das tabelas baseado nas chaves compostas
    df_consolidado = pd.merge(
        df_tempo, 
        df_metricas, 
        on=["kata", "integrante", "tratamento"], 
        how="outer" # Garante que nenhum dado seja perdido caso haja divergência
    )
    
    # Salva o arquivo final consolidado
    df_consolidado.to_csv(path_saida, index=False)
    print(f"Dataset consolidado com sucesso! Salvo em: {path_saida}")
    print(f"Total de registros: {len(df_consolidado)}")

if __name__ == "__main__":
    consolidar_datasets()
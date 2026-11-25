"""Parâmetros fixos da análise (ver docs/plano-analise.md)."""

SEED = 42
ALPHA = 0.05
ALPHA_NORMALIDADE = 0.05
N_SIMS = 2_000
PODER_ALVO = 0.80

# Formato longo dos dados coletados: uma linha por observação.
COLUNAS = ("tratamento", "unidade", "repeticao", "metrica", "valor")

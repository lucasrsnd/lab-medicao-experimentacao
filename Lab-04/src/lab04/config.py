"""Parâmetros globais do estudo e caminhos do projeto.

Toda aleatoriedade deriva de ``SEED``; os demais módulos importam daqui em vez
de repetir constantes.
"""

from pathlib import Path

SEED = 42
ALPHA = 0.05
N_SIMS = 10_000
# Correlação latente ρ da cópula gaussiana (≥ 5 valores, começando em zero).
EFFECTS = (0.0, 0.1, 0.2, 0.3, 0.4, 0.5)
N_REAL = 30
TESTS = ("pearson", "spearman")

LAB_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = LAB_ROOT / "data"
REAL_DATA_DIR = DATA_DIR / "real"
OUTPUTS_DIR = LAB_ROOT / "outputs"
DASHBOARD_TEXTS_DIR = LAB_ROOT / "docs" / "dashboard"

SAMPLE_PATH = REAL_DATA_DIR / "amostra.csv"
REAL_PARAMS_PATH = OUTPUTS_DIR / "real_params.json"
EXAMPLE_PATH = OUTPUTS_DIR / "exemplo_simulado.json"
SIMULATIONS_PATH = OUTPUTS_DIR / "simulacoes.csv"

REPO_URL = "https://github.com/lucasrsnd/lab-medicao-experimentacao"
PROJECTS_URL = "https://github.com/users/lucasrsnd/projects/2"

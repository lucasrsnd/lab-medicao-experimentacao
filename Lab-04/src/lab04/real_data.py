"""Dados reais: carga do dataset PROMISE, amostra de ~30 módulos e ajuste das marginais.

Fonte: PROMISE / tera-PROMISE (Jureczko & Madeyski), sistema Apache Ant 1.7,
métricas CK por classe Java, com ``loc`` e ``bug`` (contagem de defeitos).
Ver ``data/real/README.md``.

A lógica é pura (recebe e devolve DataFrames); o I/O fica em ``load_sample`` e
``write_real_params``, usados por ``main``.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from lab04.config import N_REAL, REAL_DATA_DIR, REAL_PARAMS_PATH, SAMPLE_PATH, SEED
from lab04.contracts import SAMPLE_COLUMNS, MarginalParams

RAW_PATH = REAL_DATA_DIR / "raw" / "ant-1.7.csv"
SOURCE = "PROMISE / tera-PROMISE (Jureczko & Madeyski) — Apache Ant 1.7, via klainfo/DefectData (MIT)"
# Valor de k quando a variância amostral não excede a média (sem superdispersão):
# a binomial negativa degenera em Poisson, aproximada por k grande.
MAX_DISPERSION = 1e6


def load_raw(path: Path = RAW_PATH) -> pd.DataFrame:
    """Lê o CSV bruto e devolve ``module_id, loc, defects`` (apenas classes com LOC > 0)."""
    raw = pd.read_csv(path)
    # O cabeçalho original repete "name" (sistema e classe); a classe é a 3ª coluna.
    module_col = raw.columns[2]
    df = pd.DataFrame(
        {
            "module_id": raw[module_col].astype(str),
            "loc": raw["loc"].astype(int),
            "defects": raw["bug"].astype(int),
        }
    )
    return df[df["loc"] > 0].reset_index(drop=True)[list(SAMPLE_COLUMNS)]


def draw_sample(raw: pd.DataFrame, n: int = N_REAL, seed: int = SEED) -> pd.DataFrame:
    """Sorteia ``n`` módulos sem reposição, de forma reprodutível."""
    if n > len(raw):
        raise ValueError(f"n={n} maior que o número de módulos ({len(raw)}).")
    rng = np.random.default_rng(seed)
    idx = rng.choice(len(raw), size=n, replace=False)
    return raw.iloc[np.sort(idx)].reset_index(drop=True)[list(SAMPLE_COLUMNS)]


def load_sample(
    raw_path: Path = RAW_PATH,
    out_path: Path = SAMPLE_PATH,
    n: int = N_REAL,
    seed: int = SEED,
) -> pd.DataFrame:
    """Sorteia ``n`` módulos com a semente fixa e grava ``data/real/amostra.csv``."""
    sample = draw_sample(load_raw(raw_path), n=n, seed=seed)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sample.to_csv(out_path, index=False)
    return sample


def fit_params(df: pd.DataFrame) -> MarginalParams:
    """Ajusta lognormal à LOC (MLE) e binomial negativa aos defeitos (momentos)."""
    if len(df) < 3:
        raise ValueError("São necessárias ao menos 3 observações para o ajuste.")
    loc = df["loc"].to_numpy(dtype=float)
    defects = df["defects"].to_numpy(dtype=float)
    if (loc <= 0).any():
        raise ValueError("LOC deve ser positiva para o ajuste lognormal.")

    log_loc = np.log(loc)
    mean = float(defects.mean())
    if mean <= 0:
        raise ValueError("Todos os defeitos são zero: a binomial negativa não é identificável.")
    var = float(defects.var(ddof=1))
    # Var = m + m²/k  =>  k = m² / (var - m); sem superdispersão, k é limitado.
    dispersion = mean**2 / (var - mean) if var > mean else MAX_DISPERSION
    return MarginalParams(
        loc_mu=float(log_loc.mean()),
        loc_sigma=float(log_loc.std(ddof=1)),
        defects_mean=mean,
        defects_dispersion=float(min(dispersion, MAX_DISPERSION)),
    )


def observed_stats(df: pd.DataFrame) -> dict[str, float]:
    """Estatísticas observadas que o dashboard compara com a simulação."""
    pearson_r = float(stats.pearsonr(df["loc"], df["defects"]).statistic)
    spearman_rho = float(stats.spearmanr(df["loc"], df["defects"]).statistic)
    return {
        "pearson_r": pearson_r,
        "spearman_rho": spearman_rho,
        "assimetria_loc": float(stats.skew(df["loc"], bias=False)),
        "assimetria_defects": float(stats.skew(df["defects"], bias=False)),
        "prop_zeros": float((df["defects"] == 0).mean()),
    }


def build_real_params(df: pd.DataFrame, source: str = SOURCE) -> dict:
    """Monta o conteúdo de ``outputs/real_params.json``."""
    return {
        "fonte": source,
        "n": int(len(df)),
        "params": fit_params(df).to_dict(),
        "observado": observed_stats(df),
    }


def write_real_params(df: pd.DataFrame, path: Path = REAL_PARAMS_PATH) -> dict:
    content = build_real_params(df)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(content, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return content


def read_real_params(path: Path = REAL_PARAMS_PATH) -> tuple[MarginalParams, dict]:
    """Lê ``real_params.json`` e devolve (parâmetros, bloco ``observado``)."""
    data = json.loads(path.read_text(encoding="utf-8"))
    return MarginalParams.from_dict(data["params"]), data["observado"]


def main() -> None:
    sample = load_sample()
    content = write_real_params(sample)
    population = load_raw()
    print(f"amostra: {len(sample)} módulos de {len(population)} -> {SAMPLE_PATH}")
    print(f"parâmetros -> {REAL_PARAMS_PATH}")
    print(json.dumps(content, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

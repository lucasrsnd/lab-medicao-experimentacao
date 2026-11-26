"""Validação dos dados e estatística descritiva por métrica e tratamento."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from analise.config import COLUNAS


def validate(df: pd.DataFrame) -> pd.DataFrame:
    """Confere o formato longo e devolve uma cópia com tipos normalizados."""
    missing = [c for c in COLUNAS if c not in df.columns]
    if missing:
        raise ValueError(f"Colunas ausentes: {missing}. Esperado: {list(COLUNAS)}.")
    data = df.loc[:, list(COLUNAS)].copy()
    for col in ("tratamento", "unidade", "metrica"):
        data[col] = data[col].astype(str)
    data["repeticao"] = pd.to_numeric(data["repeticao"], errors="raise").astype(int)
    data["valor"] = pd.to_numeric(data["valor"], errors="coerce")
    if not np.isfinite(data["valor"]).all():
        raise ValueError("A coluna valor deve conter apenas números finitos.")
    duplicated = data.duplicated(["tratamento", "unidade", "repeticao", "metrica"])
    if duplicated.any():
        raise ValueError(f"{int(duplicated.sum())} linhas duplicadas (tratamento, unidade, repeticao, metrica).")
    return data


def _shapiro_p(values: np.ndarray) -> float:
    if values.size < 3 or values.size > 5000 or np.ptp(values) == 0:
        return float("nan")
    return float(stats.shapiro(values).pvalue)


def _row(values: np.ndarray) -> dict[str, float]:
    n = values.size
    mean = float(values.mean())
    sd = float(values.std(ddof=1)) if n > 1 else float("nan")
    q1, median, q3 = np.percentile(values, (25, 50, 75))
    iqr = q3 - q1
    margin = stats.t.ppf(0.975, n - 1) * sd / np.sqrt(n) if n > 1 else float("nan")
    outliers = int(((values < q1 - 1.5 * iqr) | (values > q3 + 1.5 * iqr)).sum())
    return {
        "n": n,
        "media": mean,
        "dp": sd,
        "ic95_media_low": mean - margin,
        "ic95_media_high": mean + margin,
        "mediana": float(median),
        "q1": float(q1),
        "q3": float(q3),
        "iqr": float(iqr),
        "minimo": float(values.min()),
        "maximo": float(values.max()),
        "cv": sd / mean if mean != 0 else float("nan"),
        "outliers_iqr": outliers,
        "shapiro_p": _shapiro_p(values),
    }


def summarize(df: pd.DataFrame) -> pd.DataFrame:
    """Uma linha por (metrica, tratamento) com tendência central, dispersão, IC e normalidade."""
    data = validate(df)
    rows = [
        {"metrica": metric, "tratamento": treatment, **_row(group["valor"].to_numpy())}
        for (metric, treatment), group in data.groupby(["metrica", "tratamento"], sort=True)
    ]
    return pd.DataFrame(rows)

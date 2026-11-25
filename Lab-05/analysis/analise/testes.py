"""Escolha do teste de hipótese, tamanho do efeito e correção de Holm.

Árvore de decisão (docs/plano-analise.md):

| Grupos | Desenho       | Normal (Shapiro)        | Não normal                        |
|--------|---------------|-------------------------|-----------------------------------|
| 2      | independente  | t de Welch + Hedges g   | Mann-Whitney + Cliff δ            |
| 2      | pareado       | t pareado + Cohen d_z   | Wilcoxon + correlação rank-biserial|
| k > 2  | independente  | ANOVA + η²              | Kruskal-Wallis + ε²               |
| k > 2  | pareado       | Friedman + Kendall W    | Friedman + Kendall W              |

No desenho pareado, as repetições de cada (unidade, tratamento) são resumidas pela mediana
antes do teste, para que cada unidade conte uma vez. No independente, cada observação conta.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd
from scipy import stats

from analise.config import ALPHA, ALPHA_NORMALIDADE
from analise.descritiva import validate

METODOS = ("auto", "parametrico", "nao_parametrico")

# Limites (desprezível | pequeno | médio | grande) de cada medida de efeito.
_LIMITES = {
    "hedges_g": (0.2, 0.5, 0.8),
    "cohen_dz": (0.2, 0.5, 0.8),
    "cliff_delta": (0.147, 0.33, 0.474),  # Romano et al. (2006)
    "rank_biserial": (0.1, 0.3, 0.5),
    "eta2": (0.01, 0.06, 0.14),
    "epsilon2": (0.01, 0.06, 0.14),
    "kendall_w": (0.1, 0.3, 0.5),
}


@dataclass(frozen=True)
class Comparison:
    metrica: str
    teste: str
    pareado: bool
    n_grupos: int
    n_por_grupo: str
    normalidade_ok: bool
    estatistica: float
    p_valor: float
    efeito_nome: str
    efeito: float
    magnitude: str
    referencia: str  # sentido do efeito: "A vs B" (positivo = A maior)


def magnitude(nome: str, efeito: float) -> str:
    """Classifica |efeito| como desprezível, pequeno, médio ou grande."""
    small, medium, large = _LIMITES[nome]
    value = abs(efeito)
    if not np.isfinite(value):
        return "indefinido"
    if value < small:
        return "desprezível"
    if value < medium:
        return "pequeno"
    if value < large:
        return "médio"
    return "grande"


def hedges_g(x: np.ndarray, y: np.ndarray) -> float:
    """Diferença de médias padronizada pelo desvio combinado, com correção de viés."""
    nx, ny = x.size, y.size
    pooled = np.sqrt(((nx - 1) * x.var(ddof=1) + (ny - 1) * y.var(ddof=1)) / (nx + ny - 2))
    if pooled == 0:
        return float("nan")
    correction = 1.0 - 3.0 / (4.0 * (nx + ny) - 9.0)
    return float((x.mean() - y.mean()) / pooled * correction)


def cliffs_delta(x: np.ndarray, y: np.ndarray) -> float:
    """P(X > Y) − P(X < Y) sobre todos os pares."""
    diff = np.subtract.outer(x, y)
    return float((np.sign(diff)).mean())


def cohen_dz(diff: np.ndarray) -> float:
    sd = diff.std(ddof=1)
    return float(diff.mean() / sd) if sd > 0 else float("nan")


def rank_biserial_paired(diff: np.ndarray) -> float:
    """(W+ − W−) / (W+ + W−) com postos de |d| e diferenças nulas descartadas."""
    nonzero = diff[diff != 0]
    if nonzero.size == 0:
        return 0.0
    ranks = stats.rankdata(np.abs(nonzero))
    positive = ranks[nonzero > 0].sum()
    negative = ranks[nonzero < 0].sum()
    return float((positive - negative) / (positive + negative))


def holm(pvalues: np.ndarray) -> np.ndarray:
    """Correção de Holm-Bonferroni (controla o erro familiar)."""
    p = np.asarray(pvalues, dtype=float)
    order = np.argsort(p)
    m = p.size
    adjusted = np.empty(m)
    running = 0.0
    for rank, index in enumerate(order):
        running = max(running, (m - rank) * p[index])
        adjusted[index] = min(running, 1.0)
    return adjusted


def _is_normal(*samples: np.ndarray) -> bool:
    for sample in samples:
        if sample.size < 3 or np.ptp(sample) == 0:
            return False
        if stats.shapiro(sample).pvalue <= ALPHA_NORMALIDADE:
            return False
    return True


def _groups(data: pd.DataFrame, pareado: bool) -> tuple[list[str], list[np.ndarray]]:
    if pareado:
        wide = (
            data.groupby(["unidade", "tratamento"])["valor"].median().unstack("tratamento").dropna()
        )
        if len(wide) < 3:
            raise ValueError("Desenho pareado exige ao menos 3 unidades medidas em todos os tratamentos.")
        names = list(wide.columns)
        return names, [wide[name].to_numpy() for name in names]
    names = sorted(data["tratamento"].unique())
    return names, [data.loc[data["tratamento"] == name, "valor"].to_numpy() for name in names]


def compare(df: pd.DataFrame, metrica: str, pareado: bool, metodo: str = "auto") -> Comparison:
    """Compara os tratamentos de uma métrica seguindo a árvore de decisão do módulo."""
    if metodo not in METODOS:
        raise ValueError(f"metodo deve ser um de {METODOS}.")
    data = validate(df)
    data = data[data["metrica"] == metrica]
    if data.empty:
        raise ValueError(f"Métrica sem dados: {metrica}.")
    names, samples = _groups(data, pareado)
    k = len(samples)
    if k < 2:
        raise ValueError("São necessários ao menos 2 tratamentos.")
    if any(s.size < 3 for s in samples):
        raise ValueError("Cada tratamento precisa de ao menos 3 observações.")

    checked = [samples[0] - samples[1]] if pareado and k == 2 else samples
    normal = _is_normal(*checked)
    parametric = metodo == "parametrico" or (metodo == "auto" and normal)
    reference = f"{names[0]} vs {names[1]}" if k == 2 else " vs ".join(names)

    if k == 2 and not pareado:
        x, y = samples
        if parametric:
            res = stats.ttest_ind(x, y, equal_var=False)
            test, effect_name, effect = "t de Welch", "hedges_g", hedges_g(x, y)
        else:
            res = stats.mannwhitneyu(x, y, alternative="two-sided")
            test, effect_name, effect = "Mann-Whitney U", "cliff_delta", cliffs_delta(x, y)
    elif k == 2:
        diff = samples[0] - samples[1]
        if parametric:
            res = stats.ttest_rel(samples[0], samples[1])
            test, effect_name, effect = "t pareado", "cohen_dz", cohen_dz(diff)
        else:
            res = stats.wilcoxon(samples[0], samples[1])
            test, effect_name, effect = "Wilcoxon", "rank_biserial", rank_biserial_paired(diff)
    elif not pareado:
        n_total = sum(s.size for s in samples)
        if parametric:
            res = stats.f_oneway(*samples)
            grand = np.concatenate(samples).mean()
            between = sum(s.size * (s.mean() - grand) ** 2 for s in samples)
            total = sum(((s - grand) ** 2).sum() for s in samples)
            test, effect_name, effect = "ANOVA", "eta2", float(between / total)
        else:
            res = stats.kruskal(*samples)
            test, effect_name = "Kruskal-Wallis", "epsilon2"
            effect = float(res.statistic * (n_total + 1) / (n_total**2 - 1))
    else:
        res = stats.friedmanchisquare(*samples)
        n = samples[0].size
        test, effect_name = "Friedman", "kendall_w"
        effect = float(res.statistic / (n * (k - 1)))

    return Comparison(
        metrica=metrica,
        teste=test,
        pareado=pareado,
        n_grupos=k,
        n_por_grupo=", ".join(f"{name}={s.size}" for name, s in zip(names, samples)),
        normalidade_ok=normal,
        estatistica=float(res.statistic),
        p_valor=float(res.pvalue),
        efeito_nome=effect_name,
        efeito=effect,
        magnitude=magnitude(effect_name, effect),
        referencia=reference,
    )


def compare_all(df: pd.DataFrame, pareado: bool, metodo: str = "auto", alpha: float = ALPHA) -> pd.DataFrame:
    """Compara todas as métricas e aplica Holm entre elas."""
    data = validate(df)
    rows = [asdict(compare(data, metric, pareado, metodo)) for metric in sorted(data["metrica"].unique())]
    result = pd.DataFrame(rows)
    result["p_holm"] = holm(result["p_valor"].to_numpy())
    result["rejeita_h0"] = result["p_holm"] < alpha
    return result

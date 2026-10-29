"""Identidade visual comum: a mesma cor para cada teste em todos os gráficos."""

import plotly.graph_objects as go

# Paleta Okabe-Ito (segura para daltonismo).
TEST_COLORS = {"pearson": "#0072B2", "spearman": "#E69F00"}
TEST_LABELS = {"pearson": "Pearson (r)", "spearman": "Spearman (ρ)"}
# Real × simulado no G1.
DATA_COLORS = {"real": "#555555", "simulado": "#009E73"}
REFERENCE_COLOR = "#D55E00"  # linhas de referência, ex.: α = 5% no G3
TEMPLATE = "plotly_white"


def apply_layout(fig: go.Figure, title: str, x_title: str, y_title: str) -> go.Figure:
    """Aplica título, eixos e legenda; devolve a mesma figura para encadear."""
    if not (title and x_title and y_title):
        raise ValueError("Título e nomes dos eixos são obrigatórios.")
    fig.update_layout(
        title={"text": title, "x": 0.0, "xanchor": "left"},
        template=TEMPLATE,
        showlegend=True,
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "x": 0.0},
        margin={"l": 60, "r": 20, "t": 90, "b": 60},
    )
    fig.update_xaxes(title_text=x_title)
    fig.update_yaxes(title_text=y_title)
    return fig

"""Configuração única (fonte da verdade) de cada RQ: ordem de apresentação,
título, coluna/tipo de gráfico e legenda.

Usada tanto por `scripts/gerar_relatorio_figuras.py` (figuras estáticas do
relatório) quanto por `app_streamlit.py` (dashboard) - evita manter duas
listas à mão que podem ficar fora de ordem ou com legendas divergentes entre
as duas apresentações (foi o caso do RQ05 aparecendo depois do RQ06 antes
desta refatoração).
"""

from __future__ import annotations

from src.analysis import stats

# Ordem = ordem de apresentação em ambas as saídas (relatório e dashboard).
RQS = [
    {
        "id": "RQ01",
        "tipo": "numerica",
        "coluna": "idade_anos",
        "resumo": stats.resumo_rq01_idade,
        "titulo": "RQ01 - Idade do repositório",
        "xlabel": "idade (anos)",
        "arquivo": "rq01_idade.png",
        "log_x": False,
        "casas": 2,
        "legenda": "Distribuição da idade dos repositórios (anos desde a criação), com a mediana destacada.",
    },
    {
        "id": "RQ02",
        "tipo": "numerica",
        "coluna": "prs_aceitas",
        "resumo": stats.resumo_rq02_prs_aceitas,
        "titulo": "RQ02 - PRs aceitas (merged)",
        "xlabel": "PRs aceitas (escala log)",
        "arquivo": "rq02_prs_aceitas.png",
        "log_x": True,
        "casas": 0,
        "legenda": "Distribuição do total de pull requests aceitas (merged) por repositório, em escala log.",
    },
    {
        "id": "RQ03",
        "tipo": "numerica",
        "coluna": "total_releases",
        "resumo": stats.resumo_rq03_releases,
        "titulo": "RQ03 - Total de releases",
        "xlabel": "releases (escala log)",
        "arquivo": "rq03_releases.png",
        "log_x": True,
        "casas": 0,
        "legenda": "Distribuição do total de releases publicadas por repositório, em escala log.",
    },
    {
        "id": "RQ04",
        "tipo": "numerica",
        "coluna": "dias_desde_atualizacao",
        "resumo": stats.resumo_rq04_atualizacao,
        "titulo": "RQ04 - Dias desde a última atualização",
        "xlabel": "dias (escala log)",
        "arquivo": "rq04_atualizacao.png",
        "log_x": True,
        "casas": 0,
        "legenda": "Distribuição de dias entre o último push (pushedAt) e a data da coleta, em escala log.",
    },
    {
        "id": "RQ05",
        "tipo": "categorica",
        "titulo": "RQ05 - Top 10 linguagens primárias",
        "arquivo": "rq05_linguagens.png",
        "legenda": (
            "Top 10 linguagens primárias entre os repositórios da amostra, com destaque para as "
            "que também aparecem no top 10 do GitHub Octoverse."
        ),
    },
    {
        "id": "RQ06",
        "tipo": "numerica",
        "coluna": "razao_fechadas",
        "resumo": stats.resumo_rq06_razao_fechadas,
        "titulo": "RQ06 - Razão de issues fechadas",
        "xlabel": "issues fechadas / total",
        "arquivo": "rq06_issues.png",
        "log_x": False,
        "casas": 2,
        "legenda": "Distribuição da razão entre issues fechadas e o total de issues por repositório.",
    },
    {
        "id": "RQ07",
        "tipo": "combinada",
        "titulo": "RQ07 - Comparação por linguagem",
        "arquivo": "rq07_combinada.png",
        "legenda": (
            "Comparação das médias de PRs aceitas (RQ02), releases (RQ03) e dias desde a última "
            "atualização (RQ04) entre as linguagens mais frequentes na amostra (RQ05)."
        ),
    },
]

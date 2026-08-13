"""Extração/cálculo das métricas de cada RQ a partir do nó bruto devolvido pela API
(ver `src.queries` pelo "o que perguntar"). Um `extract_rqXX` por RQ: "o que fazer
com a resposta" - puxar o campo certo e, quando necessário, calcular o valor
derivado (idade, dias). Funções puras (sem I/O), fáceis de testar isoladas.
"""

from __future__ import annotations

from datetime import datetime, timezone


def _parse_iso8601(valor: str) -> datetime:
    return datetime.fromisoformat(valor.replace("Z", "+00:00"))


def extract_rq01_idade_anos(node: dict, agora: datetime | None = None) -> float | None:
    """RQ01 - idade do repositório em anos, a partir de `createdAt`."""
    created_at = node.get("createdAt")
    if not created_at:
        return None
    agora = agora or datetime.now(timezone.utc)
    dias = (agora - _parse_iso8601(created_at)).days
    return round(dias / 365.25, 2)


def extract_rq02_prs_aceitas(node: dict) -> int | None:
    """RQ02 - total de pull requests aceitas (merged)."""
    pull_requests = node.get("pullRequests")
    return pull_requests["totalCount"] if pull_requests is not None else None


def extract_rq03_total_releases(node: dict) -> int | None:
    """RQ03 - total de releases."""
    releases = node.get("releases")
    return releases["totalCount"] if releases is not None else None


def extract_rq04_dias_desde_atualizacao(node: dict, agora: datetime | None = None) -> int | None:
    """RQ04 - dias desde a última atualização (`pushedAt`) do repositório.

    Repositórios muito ativos podem ser atualizados a poucos segundos da consulta -
    combinado com o skew normal de relógio entre máquinas, isso pode gerar uma
    diferença negativa de frações de segundo, que o `timedelta.days` arredonda para
    -1 (não para 0). Como o repositório não pode logicamente ter sido atualizado "no
    futuro", tratamos qualquer negativo como 0 (atualizado agora).
    """
    pushed_at = node.get("pushedAt")
    if not pushed_at:
        return None
    agora = agora or datetime.now(timezone.utc)
    dias = (agora - _parse_iso8601(pushed_at)).days
    return max(dias, 0)

def extract_rq05_linguagem(repo: dict) -> str:
    lang_node = repo.get("primaryLanguage")
    if lang_node and isinstance(lang_node, dict):
        return lang_node.get("name", "N/A")
    return "N/A"

def extract_rq06_razao_issues(repo: dict) -> tuple[int, int, float]:
    total = repo.get("issues_total", {}).get("totalCount", 0)
    closed = repo.get("issues_closed", {}).get("totalCount", 0)
    razao = round(closed / total, 4) if total > 0 else 0.0
    return total, closed, razao

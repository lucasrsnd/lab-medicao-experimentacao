"""Validações genéricas reaproveitadas pelos runners de cada RQ nesta pasta.

Vive em `scripts/` (não em `src/`) porque são checagens específicas de "os dados
desta amostra fazem sentido" - parte do papel de cada runner como "validador do
requisito" - não lógica de negócio/infra reaproveitável fora daqui.
"""

from __future__ import annotations


def validar_amostra_nao_vazia(repos: list[dict]) -> list[str]:
    if len(repos) == 0:
        return ["Amostra veio vazia - verifique o token/rate limit."]
    return []


def validar_campo_presente(repos: list[dict], campo: str) -> list[str]:
    problemas = []
    for repo in repos:
        nome = repo.get("nameWithOwner", "<sem nome>")
        if repo.get(campo) in (None, ""):
            problemas.append(f"{nome}: {campo} ausente/nulo")
    return problemas


def validar_campo_nao_negativo(repos: list[dict], campo: str) -> list[str]:
    problemas = []
    for repo in repos:
        nome = repo.get("nameWithOwner", "<sem nome>")
        valor = repo.get(campo)
        if valor is not None and valor < 0:
            problemas.append(f"{nome}: {campo} negativo ({valor}) - inconsistente")
    return problemas

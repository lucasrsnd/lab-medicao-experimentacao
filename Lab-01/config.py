"""Configuração compartilhada do Lab01: token do GitHub e URL da API GraphQL, lidos do `.env`."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

LAB01_ROOT = Path(__file__).resolve().parent
ENV_PATH = LAB01_ROOT / ".env"
ENV_EXAMPLE_PATH = LAB01_ROOT / ".env.example"

load_dotenv(dotenv_path=ENV_PATH)

# Override via GITHUB_GRAPHQL_URL no .env só é útil para testes (apontar pra um
# servidor fake) - no dia a dia sempre cai no endpoint real do GitHub.
GRAPHQL_URL = os.getenv("GITHUB_GRAPHQL_URL", "https://api.github.com/graphql")


def load_github_token() -> str:
    """Lê GITHUB_TOKEN do `.env` na raiz do Lab-01.

    Encerra o programa com uma mensagem clara (em vez de um KeyError confuso) se o
    token não estiver configurado.
    """
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        sys.exit(
            f"GITHUB_TOKEN não encontrado. Copie {ENV_EXAMPLE_PATH} para {ENV_PATH} "
            f"e preencha com um token seu."
        )
    return token


def load_project_config() -> tuple[str, int]:
    """Lê GITHUB_PROJECT_OWNER e GITHUB_PROJECT_NUMBER do `.env` (usado pelo
    snapshot do GitHub Projects, `scripts/snapshot_project.py`).

    - GITHUB_PROJECT_OWNER: usuário dono do GitHub Projects (conta pessoal do
      grupo, não organização) - ex.: "lucasrsnd", sem o @.
    - GITHUB_PROJECT_NUMBER: número do project, visível na própria URL dele
      (github.com/users/<owner>/projects/<numero>).
    """
    owner = os.getenv("GITHUB_PROJECT_OWNER")
    number_raw = os.getenv("GITHUB_PROJECT_NUMBER")
    if not owner or not number_raw:
        sys.exit(
            "GITHUB_PROJECT_OWNER e/ou GITHUB_PROJECT_NUMBER não encontrados no .env.\n"
            f"Adicione ambos em {ENV_PATH} (ver {ENV_EXAMPLE_PATH} para o formato)."
        )
    try:
        number = int(number_raw)
    except ValueError:
        sys.exit(f"GITHUB_PROJECT_NUMBER precisa ser um número inteiro, veio: {number_raw!r}")
    return owner, number

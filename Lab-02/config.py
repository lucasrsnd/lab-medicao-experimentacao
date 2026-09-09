"""Configuração compartilhada do Lab02: assistente de IA, time-box e credenciais
do GitHub Projects (reaproveitadas do Lab01), lidas do `.env`."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

LAB02_ROOT = Path(__file__).resolve().parent
ENV_PATH = LAB02_ROOT / ".env"
ENV_EXAMPLE_PATH = LAB02_ROOT / ".env.example"

load_dotenv(dotenv_path=ENV_PATH)

DEFAULT_TIMEBOX_MIN = 35


def load_timebox_min() -> int:
    """Lê TRIAL_TIMEBOX_MIN do `.env` (default: 35 min, o teto do enunciado).

    Só é válido reduzir esse valor (com justificativa no relatório) — nunca
    aumentar. O script de cronometragem não valida isso automaticamente, é uma
    decisão do grupo antes de rodar os trials.
    """
    raw = os.getenv("TRIAL_TIMEBOX_MIN", str(DEFAULT_TIMEBOX_MIN))
    try:
        minutes = int(raw)
    except ValueError:
        sys.exit(f"TRIAL_TIMEBOX_MIN precisa ser um número inteiro, veio: {raw!r}")
    if minutes <= 0:
        sys.exit("TRIAL_TIMEBOX_MIN precisa ser positivo.")
    return minutes


def load_ai_assistant() -> tuple[str, str]:
    """Lê AI_ASSISTANT_NAME e AI_ASSISTANT_VERSION do `.env`.

    Encerra com mensagem clara se não estiver preenchido — o mesmo assistente
    precisa ser usado em todos os trials com IA do experimento.
    """
    name = os.getenv("AI_ASSISTANT_NAME")
    version = os.getenv("AI_ASSISTANT_VERSION", "")
    if not name:
        sys.exit(
            f"AI_ASSISTANT_NAME não encontrado. Copie {ENV_EXAMPLE_PATH} para {ENV_PATH} "
            f"e preencha com o assistente de IA fixado para o experimento."
        )
    return name, version


def load_project_config() -> tuple[str, int]:
    """Lê GITHUB_PROJECT_OWNER e GITHUB_PROJECT_NUMBER do `.env` (usado pelo
    snapshot do GitHub Projects, reaproveitado de `Lab-01/scripts/snapshot_project.py`).
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

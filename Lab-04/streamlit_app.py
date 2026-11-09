"""Ponto de entrada do dashboard, local e no Streamlit Community Cloud.

Local (no diretório Lab-04):   streamlit run streamlit_app.py
Cloud:                          arquivo de entrada = Lab-04/streamlit_app.py

O Cloud executa a partir da raiz do repositório e instala só o
requirements.txt desta pasta (o pacote lab04 não é instalado), por isso
src/ entra no sys.path aqui. Os caminhos de dados vêm de lab04.config,
relativos a este diretório, e não dependem do diretório de trabalho.
"""

import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from lab04.dashboard.app import main  # noqa: E402

main()

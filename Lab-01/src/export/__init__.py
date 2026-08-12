"""Persistência dos resultados (CSV/JSON) em disco.

As saídas ficam sempre em `Lab-01/data/` - `raw/` para os dados coletados,
`snapshots/` para os fechamentos de sprint do GitHub Projects (ver `Enunciado_Lab-01.md`,
Parte 2, item 6).
"""

from __future__ import annotations

import csv
import json
from pathlib import Path


def salvar_csv(repos: list[dict], fieldnames: list[str], caminho: Path) -> Path:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(repos)
    return caminho


def salvar_json(repos: list[dict], caminho: Path) -> Path:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open("w", encoding="utf-8") as f:
        json.dump(repos, f, ensure_ascii=False, indent=2)
    return caminho

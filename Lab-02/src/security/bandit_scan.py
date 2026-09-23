"""Scanner de vulnerabilidades por trial via Bandit (análise exploratória
extra, complementar à RQ3: "o assistente de IA introduz mais/menos
vulnerabilidades de segurança que o desenvolvimento manual?").

Dono: Gustavo.

Uso (CLI, a partir de `Lab-02/`):
    python -m src.security.bandit_scan

Roda `bandit -f json <solution.py>` para cada um dos 18 trials listados em
`data/raw/trials_tempo.csv` (deriva o caminho `katas/<kata>/<tratamento>/
<integrante>/solution.py`), ignorando `test_*.py`/`conftest.py` (mesmo
critério de `src/metrics/static_metrics.py` — só o código produzido no
trial, não o scaffold de teste do Davi). Usa o bloco `metrics._totals` do
JSON do Bandit (contagem por severidade/confiança), não a lista `results`
crua, para não depender do formato exato da chave de arquivo entre SOs.

Grava uma linha por trial em `data/raw/trials_seguranca.csv`.
"""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

LAB02_ROOT = Path(__file__).resolve().parents[2]
TRIALS_TEMPO_CSV = LAB02_ROOT / "data" / "raw" / "trials_tempo.csv"
DEFAULT_OUT_CSV = LAB02_ROOT / "data" / "raw" / "trials_seguranca.csv"

CSV_FIELDS = [
    "kata",
    "integrante",
    "tratamento",
    "n_vulnerabilidades",
    "n_severidade_baixa",
    "n_severidade_media",
    "n_severidade_alta",
    "n_confianca_alta",
]


@dataclass
class ResultadoScan:
    kata: str
    integrante: str
    tratamento: str
    n_vulnerabilidades: int
    n_severidade_baixa: int
    n_severidade_media: int
    n_severidade_alta: int
    n_confianca_alta: int


def scan_arquivo(caminho: Path) -> dict:
    """Roda `bandit -f json` num único arquivo e devolve o bloco
    `metrics._totals` (contagens por severidade/confiança). Bandit retorna
    exit code != 0 quando encontra achados — isso não é erro do processo,
    então não usamos `check=True`."""
    proc = subprocess.run(
        [sys.executable, "-m", "bandit", "-f", "json", str(caminho)],
        capture_output=True,
        text=True,
    )
    if not proc.stdout.strip():
        raise RuntimeError(f"Bandit não produziu saída para {caminho}: {proc.stderr}")
    dados = json.loads(proc.stdout)
    return dados["metrics"]["_totals"]


def scan_trial(kata: str, integrante: str, tratamento: str) -> ResultadoScan:
    caminho = LAB02_ROOT / "katas" / kata / tratamento / integrante / "solution.py"
    totais = scan_arquivo(caminho)
    return ResultadoScan(
        kata=kata,
        integrante=integrante,
        tratamento=tratamento,
        n_vulnerabilidades=int(totais["SEVERITY.LOW"] + totais["SEVERITY.MEDIUM"] + totais["SEVERITY.HIGH"]),
        n_severidade_baixa=int(totais["SEVERITY.LOW"]),
        n_severidade_media=int(totais["SEVERITY.MEDIUM"]),
        n_severidade_alta=int(totais["SEVERITY.HIGH"]),
        n_confianca_alta=int(totais["CONFIDENCE.HIGH"]),
    )


def scan_todos_os_trials(trials_csv: Path = TRIALS_TEMPO_CSV) -> list[ResultadoScan]:
    with trials_csv.open(encoding="utf-8") as f:
        linhas = list(csv.DictReader(f))
    return [scan_trial(l["kata"], l["integrante"], l["tratamento"]) for l in linhas]


def gravar_csv(resultados: list[ResultadoScan], out_csv: Path = DEFAULT_OUT_CSV) -> None:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for r in resultados:
            writer.writerow(asdict(r))


def main() -> None:
    resultados = scan_todos_os_trials()
    gravar_csv(resultados)
    total = sum(r.n_vulnerabilidades for r in resultados)
    print(f"Scan de segurança: {len(resultados)} trials, {total} achado(s) no total -> {DEFAULT_OUT_CSV}")


if __name__ == "__main__":
    main()

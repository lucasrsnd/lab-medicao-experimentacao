"""Cronometragem de trials — "time-to-green" com censura em time-box.

Uso (CLI):
    python -m src.timing.trial_timer \\
        --kata k1 --participante gustavoprehl --tratamento com_ia \\
        --tests katas/k1/com_ia/gustavoprehl

Roda `pytest` em polling (padrão a cada 10s) contra o caminho de testes do
trial, sem interromper o participante. Registra em `data/raw/trials_tempo.csv`:

- `tempo_min` = minutos até todos os testes passarem ("time-to-green"), ou o
  time-box inteiro se o trial não fechar a tempo.
- `censurado` = True quando o time-box é atingido sem sucesso — o trial
  **nunca é descartado**, só marcado como censurado (RQ1, enunciado do Lab02).
- `testes_passando` / `testes_total` — sempre gravados, mesmo em censura
  (necessário para o RQ2 independente do time-to-green).
"""

from __future__ import annotations

import argparse
import csv
import re
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

LAB02_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CSV_PATH = LAB02_ROOT / "data" / "raw" / "trials_tempo.csv"
DEFAULT_POLL_INTERVAL_SEC = 10

_SUMMARY_RE = re.compile(r"(\d+) (passed|failed|error)")

CSV_FIELDS = [
    "timestamp_inicio",
    "timestamp_fim",
    "kata",
    "integrante",
    "tratamento",
    "tempo_min",
    "censurado",
    "testes_passando",
    "testes_total",
]


@dataclass
class PytestSummary:
    passed: int
    failed: int
    errors: int

    @property
    def total(self) -> int:
        return self.passed + self.failed + self.errors

    @property
    def all_green(self) -> bool:
        return self.total > 0 and self.failed == 0 and self.errors == 0


@dataclass
class TrialResult:
    timestamp_inicio: str
    timestamp_fim: str
    kata: str
    integrante: str
    tratamento: str
    tempo_min: float
    censurado: bool
    testes_passando: int
    testes_total: int


def run_pytest(test_path: Path) -> PytestSummary:
    """Roda pytest uma vez em `test_path` e parseia a linha de resumo.

    Não propaga o exit code do pytest como exceção — falha de teste é um
    resultado esperado a cada poll, não um erro do script.
    """
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "--tb=no", "-q", str(test_path)],
        capture_output=True,
        text=True,
    )
    output = proc.stdout + proc.stderr
    counts = {"passed": 0, "failed": 0, "error": 0}
    for value, kind in _SUMMARY_RE.findall(output):
        counts[kind] += int(value)
    return PytestSummary(passed=counts["passed"], failed=counts["failed"], errors=counts["error"])


def poll_until_green(
    *,
    kata: str,
    integrante: str,
    tratamento: str,
    test_path: Path,
    timebox_min: int,
    poll_interval_sec: int = DEFAULT_POLL_INTERVAL_SEC,
    runner: Callable[[Path], PytestSummary] = run_pytest,
    clock: Callable[[], float] = time.monotonic,
    sleep_fn: Callable[[float], None] = time.sleep,
    now_fn: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
) -> TrialResult:
    """Faz polling de `runner(test_path)` até todos os testes passarem ou o
    time-box acabar. `runner`/`clock`/`sleep_fn`/`now_fn` são injetáveis para
    testar a lógica de censura sem esperar `timebox_min` minutos de verdade.
    """
    timebox_sec = timebox_min * 60
    start_monotonic = clock()
    timestamp_inicio = now_fn().isoformat()

    last_summary = PytestSummary(0, 0, 0)
    while True:
        last_summary = runner(test_path)
        elapsed_sec = clock() - start_monotonic

        if last_summary.all_green:
            return TrialResult(
                timestamp_inicio=timestamp_inicio,
                timestamp_fim=now_fn().isoformat(),
                kata=kata,
                integrante=integrante,
                tratamento=tratamento,
                tempo_min=round(elapsed_sec / 60, 2),
                censurado=False,
                testes_passando=last_summary.passed,
                testes_total=last_summary.total,
            )

        if elapsed_sec >= timebox_sec:
            return TrialResult(
                timestamp_inicio=timestamp_inicio,
                timestamp_fim=now_fn().isoformat(),
                kata=kata,
                integrante=integrante,
                tratamento=tratamento,
                tempo_min=float(timebox_min),
                censurado=True,
                testes_passando=last_summary.passed,
                testes_total=last_summary.total,
            )

        sleep_fn(poll_interval_sec)


def append_result(result: TrialResult, csv_path: Path = DEFAULT_CSV_PATH) -> None:
    """Adiciona `result` a `csv_path`, criando o arquivo com cabeçalho se
    ainda não existir."""
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    is_new = not csv_path.exists()
    with csv_path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        if is_new:
            writer.writeheader()
        writer.writerow(asdict(result))


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kata", required=True, help='ex.: "k1"')
    parser.add_argument("--participante", required=True, help='ex.: "gustavoprehl"')
    parser.add_argument("--tratamento", required=True, choices=["com_ia", "sem_ia"])
    parser.add_argument("--tests", required=True, type=Path, help="caminho passado ao pytest")
    parser.add_argument("--timebox-min", type=int, default=None, help="default: TRIAL_TIMEBOX_MIN do .env")
    parser.add_argument("--poll-interval", type=int, default=DEFAULT_POLL_INTERVAL_SEC)
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV_PATH)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)

    timebox_min = args.timebox_min
    if timebox_min is None:
        sys.path.insert(0, str(LAB02_ROOT))
        from config import load_timebox_min  # import tardio: só precisa do .env na CLI

        timebox_min = load_timebox_min()

    print(
        f"Iniciando trial: kata={args.kata} integrante={args.participante} "
        f"tratamento={args.tratamento} timebox={timebox_min}min "
        f"(poll a cada {args.poll_interval}s). Ctrl+C não é seguro — deixe rodar até o fim."
    )

    result = poll_until_green(
        kata=args.kata,
        integrante=args.participante,
        tratamento=args.tratamento,
        test_path=args.tests,
        timebox_min=timebox_min,
        poll_interval_sec=args.poll_interval,
    )

    append_result(result, csv_path=args.csv)

    status = "CENSURADO (time-box)" if result.censurado else "TIME-TO-GREEN"
    print(
        f"[{status}] tempo={result.tempo_min}min "
        f"testes={result.testes_passando}/{result.testes_total} -> {args.csv}"
    )


if __name__ == "__main__":
    main()

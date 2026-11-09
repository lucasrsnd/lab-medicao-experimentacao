"""Comando único de reprodução: ``python -m lab04 [etapa]``.

Sem argumento, roda ``tudo``: cada etapa grava os artefatos que a seguinte e o
dashboard leem. Todas usam a semente de ``lab04.config``, então rodar de novo
produz exatamente os mesmos arquivos.

    amostra   data/real/amostra.csv e outputs/real_params.json   (real_data)
    exemplo   outputs/exemplo_simulado.json                       (scripts/)
    simular   outputs/simulacoes.csv                              (scripts/)
"""

from __future__ import annotations

import argparse
import runpy
import sys
import time
from collections.abc import Callable

from lab04.config import LAB_ROOT


def _script(name: str) -> Callable[[], None]:
    # Os scripts não fazem parte do pacote; são executados como em `python scripts/x.py`.
    return lambda: runpy.run_path(str(LAB_ROOT / "scripts" / name), run_name="__main__")


def _sample() -> None:
    from lab04 import real_data

    real_data.main()


# Ordem importa: a simulação lê os parâmetros que a etapa "amostra" grava.
STEPS: dict[str, tuple[str, Callable[[], None]]] = {
    "amostra": ("amostra real e parâmetros da simulação", _sample),
    "exemplo": ("exemplo simulado com os dois testes (G2)", _script("exemplo_simulado.py")),
    "simular": ("Monte Carlo: erro tipo I e poder (G3, G4)", _script("simular.py")),
}


def run(steps: list[str]) -> None:
    for name in steps:
        description, step = STEPS[name]
        print(f"\n▶ {name}: {description}", flush=True)
        start = time.perf_counter()
        step()
        print(f"  concluído em {time.perf_counter() - start:.1f} s", flush=True)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="python -m lab04",
        description="Reproduz os artefatos do Lab04 (semente fixa). Sem argumento, roda tudo.",
    )
    parser.add_argument("etapa", nargs="?", default="tudo", choices=["tudo", *STEPS])
    args = parser.parse_args(argv)
    run(list(STEPS) if args.etapa == "tudo" else [args.etapa])
    print("\nPronto. Abra o dashboard com: streamlit run streamlit_app.py")


if __name__ == "__main__":
    main(sys.argv[1:])

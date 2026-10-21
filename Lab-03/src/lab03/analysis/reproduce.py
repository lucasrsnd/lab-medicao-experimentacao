"""Reproduz todas as análises a partir do dataset congelado e grava um manifesto.

Execute na pasta Lab-03. Cada etapa chama o `main` do módulo correspondente com
os argumentos explícitos, de modo que a saída só depende de `data/` e `labels/`.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
import tempfile
from pathlib import Path

from lab03.analysis import (
    base,
    c1_reference,
    cfr_b_validation,
    rq01_rq02,
    rq03_rq04,
    rq05,
    rq06,
    rq07,
)

# Entrada opcional: só existe depois da coleta complementar (C2 e C3).
RQ07_INPUT = "validation/dataset-v1/rq07_classificacoes.csv"
INPUTS = (
    "data/amostra_completa.json.gz",
    "labels/amostra_ouro_releases.csv",
    "labels/rotulos_A_releases.csv",
    "labels/rotulos_B_releases.csv",
    "labels/reamostragem-v2/amostra_ouro_sorteio.json",
    RQ07_INPUT,
)
BASE = "base_repositorios.csv"
MANIFEST_NAME = "MANIFESTO.json"
# PNG depende da versão do matplotlib; entra no manifesto, mas não na comparação.
VOLATILE_SUFFIXES = (".png",)


def steps(output: Path):
    base_csv = str(output / BASE)
    optional = ()
    if Path(RQ07_INPUT).is_file():
        optional = (("rq07", rq07.main, ["--classificacoes", RQ07_INPUT, "--output-dir", str(output / "rq07")]),)
    return optional + (
        ("base", base.main, ["--output", base_csv]),
        ("rq01_rq02", rq01_rq02.main, ["--base", base_csv, "--output-dir", str(output / "rq01_rq02")]),
        ("rq03_rq04", rq03_rq04.main, ["--base", base_csv, "--output-dir", str(output / "rq03_rq04")]),
        ("c1_reference", c1_reference.main, ["--base", base_csv, "--output-dir", str(output / "c1_reference")]),
        ("rq05", rq05.main, ["--base", base_csv, "--output-dir", str(output / "rq05")]),
        ("rq06", rq06.main, ["--base", base_csv, "--output-dir", str(output / "rq06")]),
        ("cfr_b_validation", cfr_b_validation.main, ["--output-dir", str(output / "validacao_cfr_b")]),
    )


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _rounded(value):
    if isinstance(value, float):
        return float(f"{value:.9g}")
    if isinstance(value, list):
        return [_rounded(item) for item in value]
    if isinstance(value, dict):
        return {key: _rounded(item) for key, item in value.items()}
    return value


TEXT_SUFFIXES = (".md", ".csv", ".json", ".txt")


def canonical_sha256(path: Path) -> str:
    """Hash do conteúdo, igual no Windows e no Linux.

    Em texto, CRLF vira LF (o checkout e a escrita de arquivos mudam o fim de linha).
    Em JSON, ainda ignora ruído de ponto flutuante entre versões do scipy.
    """
    if path.suffix not in TEXT_SUFFIXES:
        return sha256(path)
    text = path.read_bytes().decode("utf-8").replace("\r\n", "\n")
    if path.suffix == ".json":
        text = json.dumps(_rounded(json.loads(text)), sort_keys=True)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_manifest(output: Path, manifest_name: str) -> dict:
    outputs = {}
    for path in sorted(p for p in output.rglob("*") if p.is_file()):
        relative = path.relative_to(output).as_posix()
        if relative in (manifest_name, "README.md"):  # README é texto escrito à mão
            continue
        outputs[relative] = {
            "sha256": sha256(path),
            "canonical_sha256": canonical_sha256(path),
            "bytes": path.stat().st_size,
            "stable": path.suffix not in VOLATILE_SUFFIXES,
        }
    return {
        "inputs": {name: canonical_sha256(Path(name)) for name in INPUTS if Path(name).is_file()},
        "python": platform.python_version(),
        "outputs": outputs,
    }


def compare(expected: dict, actual: dict) -> list[str]:
    """Lista divergências entre dois manifestos, ignorando saídas instáveis."""
    problems = []
    for name, entry in expected["outputs"].items():
        found = actual["outputs"].get(name)
        if found is None:
            problems.append(f"ausente: {name}")
        elif entry["stable"] and entry["canonical_sha256"] != found["canonical_sha256"]:
            problems.append(f"diferente: {name}")
    for name in actual["outputs"]:
        if name not in expected["outputs"]:
            problems.append(f"nova saída fora do manifesto: {name}")
    if expected["inputs"] != actual["inputs"]:
        problems.append("entradas congeladas diferem do manifesto")
    return problems


def run_all(output: Path, manifest_name: str) -> dict | None:
    for name, run, step_args in steps(output):
        print(f"== {name}")
        if run(step_args) != 0:
            print(f"Erro: a etapa {name} falhou.", file=sys.stderr)
            return None
    return build_manifest(output, manifest_name)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--output", type=Path, default=Path("analysis"))
    parser.add_argument("--manifest", default=MANIFEST_NAME, help="nome dentro de --output")
    parser.add_argument(
        "--check",
        action="store_true",
        help="recalcula numa pasta temporária e falha se algo estável divergir do manifesto em --output",
    )
    args = parser.parse_args(argv)

    manifest_path = args.output / args.manifest
    expected = None
    if args.check:
        try:
            expected = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            print(f"Erro: manifesto ilegível em {manifest_path}: {error}", file=sys.stderr)
            return 1

    if expected is not None:
        with tempfile.TemporaryDirectory() as scratch:
            actual = run_all(Path(scratch), args.manifest)
            if actual is None:
                return 1
        problems = compare(expected, actual)
        if problems:
            print("Reprodução divergente do manifesto:", *problems, sep="\n  ", file=sys.stderr)
            return 1
        print(f"Reprodução idêntica ao manifesto ({len(actual['outputs'])} saídas).")
        return 0

    actual = run_all(args.output, args.manifest)
    if actual is None:
        return 1
    manifest_path.write_text(json.dumps(actual, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{len(actual['outputs'])} saídas registradas em {manifest_path}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

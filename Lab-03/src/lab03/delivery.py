"""#136: verificação da entrega final em checkout limpo.

Confere arquivos obrigatórios, ausência de segredos e caminhos pessoais nos
arquivos de texto e, com --reproduce, refaz as análises e compara com o manifesto.
Execute na pasta Lab-03.
"""

from __future__ import annotations

import argparse
import gzip
import json
import re
import sys
from pathlib import Path

REQUIRED = (
    "README.md",
    "pyproject.toml",
    "docs/dicionario-dados.md",
    "docs/protocolo.md",
    "data/amostra_completa.json.gz",
    "analysis/base_repositorios.csv",
    "analysis/MANIFESTO.json",
    "article/main.tex",
)
SECRET = re.compile(r"(?:ghp|gho|ghs|ghu|ghr)_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{20,}")
PERSONAL_PATH = re.compile(
    r"[A-Za-z]:[\\/]+Users[\\/]+[^\\/\s\"']+|/Users/[A-Za-z0-9._-]+/|/home/[A-Za-z0-9._-]+/"
)
SKIPPED_DIRS = {"data", ".git", ".venv", "__pycache__", ".pytest_cache", "htmlcov", "build", "dist"}
BINARY_SUFFIXES = {".gz", ".sqlite3", ".png", ".pdf", ".pyc", ".xml"}
# Caminhos de exemplo em arquivos que explicam o que NÃO versionar.
ALLOWED_PERSONAL_PATH = {"docs/integracao-parte2.md"}


def text_files(root: Path):
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if not path.is_file() or SKIPPED_DIRS & set(relative.parts):
            continue
        if path.suffix in BINARY_SUFFIXES or path.name == "coverage.xml" or path.name == ".env":
            continue
        yield relative, path


def scan(root: Path) -> list[str]:
    problems = []
    for relative, path in text_files(root):
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if SECRET.search(text):
            problems.append(f"possível token em {relative.as_posix()}")
        if relative.as_posix() not in ALLOWED_PERSONAL_PATH and PERSONAL_PATH.search(text):
            problems.append(f"caminho pessoal em {relative.as_posix()}")
    return problems


def dataset_warnings(root: Path) -> list[str]:
    """Avisos (não bloqueiam) sobre o dataset congelado, que não pode ser editado sem mudar o hash."""
    path = root / "data" / "amostra_completa.json.gz"
    try:
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            execution = json.load(handle).get("execution", {})
    except (OSError, ValueError):
        return []
    if PERSONAL_PATH.search(json.dumps(execution)):
        return ["dataset congelado: execution.cache.path guarda caminho local (metadado, não editado)"]
    return []


def check(root: Path) -> list[str]:
    problems = [f"ausente: {name}" for name in REQUIRED if not (root / name).is_file()]
    if (root / ".env").exists():
        problems.append(".env presente na pasta (confira que não é versionado)")
    return problems + scan(root)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--reproduce", action="store_true", help="também roda analysis.reproduce --check")
    args = parser.parse_args(argv)

    problems = check(args.root)
    for warning in dataset_warnings(args.root):
        print(f"aviso: {warning}", file=sys.stderr)
    for problem in problems:
        print(f"- {problem}", file=sys.stderr)
    if args.reproduce:
        from lab03.analysis import reproduce

        if reproduce.main(["--output", str(args.root / "analysis"), "--check"]) != 0:
            problems.append("reprodução diverge do manifesto")
    if problems:
        print(f"Entrega com {len(problems)} problema(s).", file=sys.stderr)
        return 1
    print("Entrega conferida: arquivos obrigatórios, sem segredos nem caminhos pessoais.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

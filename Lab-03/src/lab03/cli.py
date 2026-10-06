"""Comando único para amostra explícita de um repositório ou snapshot offline."""

import argparse
import json
import os
from datetime import datetime
from pathlib import Path

from lab03.domain import Window, timestamp
from lab03.github import ApiError, DataError, GitHubClient, HttpTransport, SnapshotTransport
from lab03.pipeline import run


def json_default(value):
    if isinstance(value, datetime):
        return value.isoformat()
    raise TypeError(f"Tipo não serializável: {type(value).__name__}")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, help="owner/repo")
    parser.add_argument("--start", required=True, help="ISO 8601 com timezone, inclusivo")
    parser.add_argument("--end", required=True, help="ISO 8601 com timezone, exclusivo")
    parser.add_argument("--snapshot", type=Path, help="Respostas REST locais; sem rede")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        window = Window(timestamp(args.start), timestamp(args.end))
        if args.snapshot:
            snapshot = json.loads(args.snapshot.read_text(encoding="utf-8"))
            transport = SnapshotTransport(snapshot["responses"])
        else:
            token = os.environ.get("GITHUB_TOKEN")
            if not token:
                parser.error("Defina GITHUB_TOKEN ou use --snapshot para demonstração offline.")
            transport = HttpTransport(token)
        output = run(GitHubClient(transport), args.repo, window)
        output["source"] = "snapshot" if args.snapshot else "github"
        args.output.parent.mkdir(parents=True, exist_ok=True)
        # Não persistir resultado parcial em caso de erro de coleta.
        temporary = args.output.with_suffix(args.output.suffix + ".tmp")
        temporary.write_text(
            json.dumps(output, default=json_default, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary.replace(args.output)
    except (ApiError, DataError, ValueError, KeyError, OSError, RuntimeError) as error:
        parser.exit(1, f"Erro: {error}\n")
    print(f"Resultado: {args.output}")
    return 0


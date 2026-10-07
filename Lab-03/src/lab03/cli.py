"""Executa a coleta de um repositório a partir de uma configuração validada."""

import argparse
import json
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

from lab03 import __version__
from lab03.cache import SQLiteCacheTransport
from lab03.configuration import load_config
from lab03.github import (
    ApiError, DataError, GitHubClient, HttpTransport, SnapshotTransport,
)
from lab03.pipeline import run
from lab03.collectors.candidates import select_candidates
from lab03.pilot import run_pilot
from lab03.resilience import ResilientTransport


def json_default(value):
    if isinstance(value, datetime):
        return value.isoformat()
    raise TypeError(f"Tipo não serializável: {type(value).__name__}")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True, help="Configuração JSON do estudo ou da amostra")
    parser.add_argument("--repo", help="owner/repo; obrigatório para coleta real")
    parser.add_argument(
        "--select-candidates", action="store_true",
        help="selecionar a amostra inicial e gerar o funil do estudo",
    )
    parser.add_argument(
        "--pilot", action="store_true",
        help="coletar o piloto integrado com 100 repositórios elegíveis",
    )
    parser.add_argument(
        "--cache", type=Path, default=Path("data/cache.sqlite3"),
        help="cache SQLite persistente para retomada (padrão: data/cache.sqlite3)",
    )
    parser.add_argument("--output", type=Path, help="Arquivo JSON de saída")
    parser.add_argument("--validate-config", action="store_true", help="Validar configuração sem coletar")
    args = parser.parse_args(argv)
    cache = None
    try:
        config = load_config(args.config)
        if args.validate_config:
            if config.mode == "study" and not config.collection_allowed:
                print("Configuração válida; coleta bloqueada até a janela oficial ser confirmada.")
            else:
                print(f"Configuração válida para modo {config.mode}.")
            return 0
        if args.output is None:
            parser.error("Defina --output para executar o pipeline.")
        if args.pilot and args.select_candidates:
            parser.error("Não combine --pilot com --select-candidates.")

        if config.mode == "sample":
            if args.select_candidates or args.pilot:
                parser.error("--select-candidates e --pilot só podem ser usados no modo study.")
            if args.repo and args.repo != config.repository:
                parser.error("No modo sample, o repositório é fixado pelo arquivo de configuração.")
            if config.repository is None or config.window is None or config.snapshot is None:
                raise ValueError("Configuração da amostra incompleta.")
            repository = config.repository
            window = config.window
            transport = SnapshotTransport(
                json.loads(config.snapshot.read_text(encoding="utf-8"))["responses"]
            )
            cache = resilient = None
            source = "snapshot"
        else:
            if not config.collection_allowed or config.window is None:
                parser.exit(
                    2,
                    "Coleta bloqueada: confirme a janela oficial no arquivo de configuração "
                    "antes de iniciar consultas à API.\n",
                )
            if (args.select_candidates or args.pilot) and args.repo:
                parser.error("Não combine --select-candidates ou --pilot com --repo.")
            if not (args.select_candidates or args.pilot):
                if not args.repo:
                    parser.error("Defina --repo owner/repo para a coleta real.")
                repository = args.repo
            token = os.environ.get("GITHUB_TOKEN")
            if not token:
                parser.error("Defina GITHUB_TOKEN no ambiente para a coleta real.")
            window = config.window
            cache_path = args.cache
            if not cache_path.is_absolute():
                cache_path = Path.cwd() / cache_path
            resilient = ResilientTransport(
                HttpTransport(token),
                notify=lambda message: print(message, file=sys.stderr, flush=True),
            )
            cache = SQLiteCacheTransport(resilient, cache_path)
            transport = cache
            source = "github"

        client = GitHubClient(transport)
        if args.pilot:
            if config.mode != "study":
                parser.error("--pilot só pode ser usado no modo study.")
            output = run_pilot(
                client,
                window=window,
                target_size=config.initial_sprint_sample,
                stars_min_exclusive=config.stars_min_exclusive,
                minimum_releases=config.minimum_releases,
                minimum_valid_runs=config.minimum_valid_workflow_runs,
                valid_conclusions=config.valid_workflow_conclusions,
            )
            output["execution"] = {
                "command": (
                    f"python -m lab03 --config {args.config} --pilot "
                    f"--output {args.output} --cache {args.cache}"
                ),
                "config": str(args.config),
                "pipeline_version": __version__,
                "cache": {
                    "path": str(cache_path),
                    "hits": cache.hits,
                    "misses": cache.misses,
                },
                "resilience": {
                    "retries": resilient.retries,
                    "rate_limit_waits": resilient.rate_limit_waits,
                    "waited_seconds": round(resilient.waited_seconds, 1),
                },
                "counts": {
                    "eligible_repositories": len(output["repositories"]),
                    "metadata_records": len(output["repositories"]),
                    "releases": sum(
                        len(item["report"]["catalog"]["releases"])
                        for item in output["repositories"]
                    ),
                    "commits": sum(
                        len(change["commits"])
                        for item in output["repositories"]
                        for change in item["report"]["changes"]
                    ),
                    "workflow_runs": sum(
                        len(item["workflow_runs"]) for item in output["repositories"]
                    ),
                },
            }
        elif args.select_candidates:
            output = select_candidates(
                client,
                window.start,
                window.end,
                stars_min_exclusive=config.stars_min_exclusive,
                sample_size=config.initial_sprint_sample,
                minimum_releases=config.minimum_releases,
                minimum_valid_runs=config.minimum_valid_workflow_runs,
                valid_conclusions=config.valid_workflow_conclusions,
            )
        else:
            output = run(client, repository, window)
        output["source"] = source
        args.output.parent.mkdir(parents=True, exist_ok=True)
        temporary = args.output.with_suffix(args.output.suffix + ".tmp")
        temporary.write_text(
            json.dumps(output, default=json_default, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary.replace(args.output)
    except KeyboardInterrupt:
        parser.exit(130, (
            "Interrompido. Respostas já coletadas estão no cache; rode o mesmo "
            "comando para retomar de onde parou.\n"
        ))
    except (
        ApiError, DataError, ValueError, KeyError, OSError, RuntimeError, sqlite3.Error,
    ) as error:
        parser.exit(1, f"Erro: {error}\n")
    finally:
        if cache is not None:
            cache.close()
    print(f"Resultado: {args.output}")
    return 0
